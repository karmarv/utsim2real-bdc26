#!/usr/bin/env python
"""Per-class routing of several models' predictions (module M11). Per-class AP is independent, so each class can
come from the member that is best for it on real validation.

    # choose the route from the members' real-validation results (best on split A; near-ties broken by split B)
    python common/tools/route_predictions.py select model-lumpi-track/routed-g1
    # merge predictions json files with the route in model.yaml
    python common/tools/route_predictions.py merge model-lumpi-track/routed-g1 --pred g1=a.json --pred g1v3=b.json --out c.json

model.yaml of a routed model:
    members: {g1: {model: pointpillars-g1, ckpt: train/output/.../checkpoint_epoch_40.pth}, g1v3: {...}}
    route: {Person: g1v3, Car: g1, ...}            # written by `select`
Each member's predictions are already post-processed with that member's test/postprocess.yaml (hedged copies
included), which is exactly what its per-class validation AP measured.
"""
import argparse
import json
from pathlib import Path

import yaml

from _common import model_info


def member_results(model_dir: Path, card: dict, name: str, split: str) -> dict:
    m = card["members"][name]
    res_dir = model_dir.parent / m["model"] / "validation" / "results"
    run = Path(m["ckpt"]).parts[-3] + "_" + Path(m["ckpt"]).stem         # <tag>_checkpoint_epoch_N
    data = card["data"]["realval"].replace("/", "_")
    r = json.loads((res_dir / f"{data}_{split}_{run}.json").read_text())
    return {c: (v["3d@0.5"]["AP_R40"] if v["3d@0.5"] else None) for c, v in r["per_class"].items()}


def select(model_dir: Path, card: dict, track, tie: float) -> dict:
    names = list(card["members"])
    A = {n: member_results(model_dir, card, n, "val") for n in names}
    B = {n: member_results(model_dir, card, n, "valB") for n in names}
    route, table = {}, {}
    for c in track.classes:
        cands = [n for n in names if A[n].get(c) is not None]
        if not cands:
            route[c] = names[0]
            continue
        best = max(A[n][c] for n in cands)
        near = [n for n in cands if A[n][c] >= best - tie]
        route[c] = max(near, key=lambda n: (B[n].get(c) or 0.0, A[n][c]))
        table[c] = {n: {"A": A[n][c], "B": B[n].get(c)} for n in cands}
    scored = [c for c in track["classes_with_test_gt"]]
    est = {s: sum((A if s == "A" else B)[route[c]].get(c) or 0.0 for c in scored) / len(scored) for s in ("A", "B")}
    return route, table, est


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["select", "merge"])
    ap.add_argument("model_dir")
    ap.add_argument("--pred", action="append", default=[], help="member=predictions.json (merge)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--tie", type=float, default=0.005)
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    if a.mode == "select":
        route, table, est = select(model_dir, card, track, a.tie)
        card["route"] = route
        card["route_selection"] = {"rule": f"best realval-A AP; within {a.tie} of the best, the higher realval-B AP",
                                   "estimate_mAP_A": round(est["A"], 4), "estimate_mAP_B": round(est["B"], 4)}
        text = (model_dir / "model.yaml").read_text().split("\nroute:")[0].rstrip() + "\n"
        text += yaml.safe_dump({"route": route, "route_selection": card["route_selection"]}, sort_keys=False)
        (model_dir / "model.yaml").write_text(text)
        (model_dir / "validation" / "results").mkdir(parents=True, exist_ok=True)
        (model_dir / "validation" / "results" / "route_table.json").write_text(json.dumps(table, indent=2))
        print(json.dumps({"route": route, **card["route_selection"]}, indent=2))
        return
    preds = {}
    for spec in a.pred:
        name, path = spec.split("=", 1)
        preds[name] = json.loads(Path(path).read_text())
    route = card["route"]
    missing = set(route.values()) - set(preds)
    if missing:
        raise SystemExit(f"missing member predictions: {sorted(missing)}")
    ids = sorted(set().union(*[set(p) for p in preds.values()]))
    out = {fid: [d for name, p in preds.items() for d in p.get(fid, []) if route.get(d["class"]) == name] for fid in ids}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out))
    print(f"{len(out)} frames, {sum(len(v) for v in out.values())} boxes -> {a.out}")


if __name__ == "__main__":
    main()
