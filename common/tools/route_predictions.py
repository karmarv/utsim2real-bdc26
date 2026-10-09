#!/usr/bin/env python
"""Per-class routing of several models' predictions (module M11). Per-class AP is independent, so each class can
come from the member that is best for it on real validation.

    # choose the route from the members' real-validation results (best on split A; near-ties broken by split B)
    python common/tools/route_predictions.py select model-lumpi-track/routed-g1
    # joint rule (docs/decisions/README.md Section 3.2): rank by the mean of realval-A and realval-B AP; a class leaves
    # its current member only through the class gate (dB >= 0.01, paired bootstrap P(gain) >= 0.9, dA >= -0.005)
    python common/tools/route_predictions.py select model-lumpi-track/routed-g2 --rule joint
    # range-dependent z calibration after routing (S1 close-out C1): select on realval-A, keep a class only if
    # realval-B passes the class gate; writes model.yaml `calibration` and the calibrated validation predictions
    python common/tools/route_predictions.py calibrate model-v2x-track/routed-g1z
    # merge predictions json files with the route in model.yaml (and the `calibration`, if any)
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

from _common import data_path, member_tag, model_info, validation_predictions
from bdc26 import scorecard as sc
from bdc26.detect import zcalib


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


def select_joint(model_dir: Path, card: dict, track, n_boot: int, seed: int) -> tuple:
    """Joint rule: candidate = best mean(A, B) AP (A alone where B has no GT); the incumbent (current route in
    model.yaml) is replaced only when the candidate passes the class gate on realval-B."""
    names = list(card["members"])
    A = {n: member_results(model_dir, card, n, "val") for n in names}
    B = {n: member_results(model_dir, card, n, "valB") for n in names}
    root = data_path(track, card["data"]["realval"])
    gts = {}
    cache = {}

    def flags(n, split):
        if (n, split) not in cache:
            gts.setdefault(split, sc.load_split(root, split))
            m = card["members"][n]
            path = validation_predictions(model_dir.parent / m["model"], card, split, tag=member_tag(m))
            cache[(n, split)] = sc.flags_for(path, gts[split], track.classes)
        return cache[(n, split)]

    incumbent = card.get("route") or {}
    route, table = {}, {}
    for c in track.classes:
        cands = [n for n in names if A[n].get(c) is not None]
        if not cands:
            route[c] = names[0]
            continue
        joint = {n: (A[n][c] + B[n][c]) / 2 if B[n].get(c) is not None else A[n][c] for n in cands}
        best = max(cands, key=lambda n: (joint[n], A[n][c]))
        inc = incumbent.get(c) if incumbent.get(c) in cands else None
        row = {"members": {n: {"A": A[n][c], "B": B[n].get(c), "joint": joint[n]} for n in cands},
               "incumbent": inc, "candidate": best}
        if inc is None:
            route[c], row["decision"] = best, "no incumbent: best joint AP"
        elif best == inc:
            route[c], row["decision"] = inc, "the incumbent has the best joint AP"
        elif B[best].get(c) is None or B[inc].get(c) is None:
            route[c], row["decision"] = inc, "kept: no realval-B GT for this class"
        else:
            boot = sc.paired_bootstrap({c: flags(inc, "valB")[c]}, {c: flags(best, "valB")[c]}, [c], n_boot, seed)[c]
            dA = A[best][c] - A[inc][c]
            ok = sc.class_gate(boot["delta"], boot["p_gain"], dA)
            route[c] = best if ok else inc
            row.update({"dB": boot["delta"], "p_gain": boot["p_gain"], "ci90": boot["ci90"], "dA": dA,
                        "decision": "switched (class gate passed)" if ok else "kept (class gate failed)"})
        table[c] = row
    scored = list(track["classes_with_test_gt"])
    est = {s: sum((A if s == "A" else B)[route[c]].get(c) or 0.0 for c in scored) / len(scored) for s in ("A", "B")}
    return route, table, est


def calibrate(model_dir: Path, card: dict, track, classes, n_boot: int, seed: int) -> None:
    """Select a range-dependent z calibration per class on realval-A; keep it where realval-B passes the class
    gate. Input: the uncalibrated merged validation predictions (validation/output/<data>_<split>_merged.json;
    created from the current _routed.json on first use). Output: model.yaml `calibration`, the calibrated
    _routed.json files that the scorecard reads, and validation/results/calibration.json."""
    import shutil
    data = card["data"]["realval"].replace("/", "_")
    out_dir = model_dir / "validation" / "output"
    root = data_path(track, card["data"]["realval"])
    merged, routed, gts = {}, {}, {}
    for split in ("val", "valB"):
        merged[split] = out_dir / f"{data}_{split}_merged.json"
        routed[split] = out_dir / f"{data}_{split}_routed.json"
        if not merged[split].exists():
            if card.get("calibration"):
                raise SystemExit(f"{merged[split]} missing and the routed predictions are already calibrated")
            shutil.copy(routed[split], merged[split])
        gts[split] = sc.load_split(root, split)
    P = {s_: json.loads(merged[s_].read_text()) for s_ in merged}
    classes = classes or list(track["classes_with_test_gt"])
    report, calib = {}, {}
    for c in classes:
        res = zcalib.ZSearch(P["val"], gts["val"], c).search(zcalib.Z0_GRID, zcalib.K_GRID)
        entry = {"A_search": res}
        if res["z0"] == 0.0 and res["z_per_m"] == 0.0:
            entry["decision"] = "no correction selected on realval-A"
        else:
            cc = {c: {"z0": res["z0"], "z_per_m": res["z_per_m"]}}
            fb_base = sc.frame_flags({i: P["valB"].get(i, []) for i in gts["valB"]}, gts["valB"], [c])
            fb_cal = sc.frame_flags(zcalib.apply({i: P["valB"].get(i, []) for i in gts["valB"]}, cc), gts["valB"], [c])
            fa_base = sc.frame_flags({i: P["val"].get(i, []) for i in gts["val"]}, gts["val"], [c])
            fa_cal = sc.frame_flags(zcalib.apply({i: P["val"].get(i, []) for i in gts["val"]}, cc), gts["val"], [c])
            bb = sc.paired_bootstrap(fb_base, fb_cal, [c], n_boot, seed).get(c)
            ba = sc.paired_bootstrap(fa_base, fa_cal, [c], 0, seed).get(c)
            if bb is None:
                entry["decision"] = "kept off: no realval-B GT"
            else:
                ok = sc.class_gate(bb["delta"], bb["p_gain"], ba["delta"])
                entry.update({"A_exact_delta": ba["delta"], "B_delta": bb["delta"], "B_p_gain": bb["p_gain"], "B_ci90": bb["ci90"],
                              "decision": "kept (class gate passed)" if ok else "dropped (class gate failed)"})
                if ok:
                    calib.update(cc)
        report[c] = entry
        print(c, json.dumps(entry))
    for split in ("val", "valB"):
        routed[split].write_text(json.dumps(zcalib.apply(P[split], calib)))
    text = (model_dir / "model.yaml").read_text()
    text = text.split("\ncalibration:")[0].rstrip() + "\n"
    text += yaml.safe_dump({"calibration": calib or {}}, sort_keys=False)
    (model_dir / "model.yaml").write_text(text)
    (model_dir / "validation" / "results").mkdir(parents=True, exist_ok=True)
    (model_dir / "validation" / "results" / "calibration.json").write_text(json.dumps(report, indent=2))
    print("calibration:", calib or "none")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["select", "merge", "calibrate"])
    ap.add_argument("model_dir")
    ap.add_argument("--pred", action="append", default=[], help="member=predictions.json (merge)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--tie", type=float, default=0.005)
    ap.add_argument("--rule", choices=["a", "joint"], default="a", help="a: the S1 rule; joint: the class gate of docs/decisions/README.md Section 3.2")
    ap.add_argument("--bootstrap", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--classes", nargs="*", default=None, help="calibrate: classes to try (default: all with test GT)")
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    if a.mode == "select":
        if a.rule == "joint":
            route, table, est = select_joint(model_dir, card, track, a.bootstrap, a.seed)
            rule = ("joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only "
                    f"through the class gate (dB >= 0.01, paired bootstrap x{a.bootstrap} P(gain) >= 0.9, dA >= -0.005)")
        else:
            route, table, est = select(model_dir, card, track, a.tie)
            rule = f"best realval-A AP; within {a.tie} of the best, the higher realval-B AP"
        card["route"] = route
        card["route_selection"] = {"rule": rule, "estimate_mAP_A": round(est["A"], 4), "estimate_mAP_B": round(est["B"], 4)}
        text = (model_dir / "model.yaml").read_text().split("\nroute:")[0].rstrip() + "\n"
        text += yaml.safe_dump({"route": route, "route_selection": card["route_selection"]}, sort_keys=False)
        if card.get("calibration") is not None:                 # keep a calibration chosen by `calibrate`
            text += yaml.safe_dump({"calibration": card["calibration"]}, sort_keys=False)
        (model_dir / "model.yaml").write_text(text)
        (model_dir / "validation" / "results").mkdir(parents=True, exist_ok=True)
        (model_dir / "validation" / "results" / "route_table.json").write_text(json.dumps(table, indent=2))
        print(json.dumps({"route": route, **card["route_selection"]}, indent=2))
        return
    if a.mode == "calibrate":
        calibrate(model_dir, card, track, a.classes, a.bootstrap, a.seed)
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
    out = zcalib.apply(out, card.get("calibration") or {})
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out))
    print(f"{len(out)} frames, {sum(len(v) for v in out.values())} boxes -> {a.out}")


if __name__ == "__main__":
    main()
