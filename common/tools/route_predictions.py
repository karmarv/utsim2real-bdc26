#!/usr/bin/env python
"""Per-class routing of several models' predictions (module M11). Per-class AP is independent, so each class can
come from the member that is best for it on real validation.

    # choose the route from the members' real-validation results (best on split A; near-ties broken by split B)
    python common/tools/route_predictions.py select model-lumpi-track/routed-g1
    # joint rule (docs/decisions/README.md Section 3.2): rank by the mean of realval-A and realval-B AP; a class leaves
    # its current member only through the class gate (dB >= 0.01, paired bootstrap P(gain) >= 0.9, dA >= -0.005)
    python common/tools/route_predictions.py select model-lumpi-track/routed-g2 --rule joint
    # ... and compare members after their own gated z calibration (writes `calibration` with the route)
    python common/tools/route_predictions.py select model-v2x-track/routed-g2 --rule joint --calibrated
    # range-dependent z calibration after routing (S1 close-out C1): select on realval-A, keep a class only if
    # realval-B passes the class gate; writes model.yaml `calibration` and the calibrated validation predictions
    python common/tools/route_predictions.py calibrate model-v2x-track/routed-g1z
    # real-validation predictions and scores of the routed model from its members' validation outputs:
    # validation/output/<data>_<split>_merged.json (route only) and _routed.json (route + calibration),
    # validation/results/<data>_<split>_routed.json and local_scores.json (what make_submission.sh and scorecard.py read)
    python common/tools/route_predictions.py validate model-v2x-track/routed-g2
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


def select_joint(model_dir: Path, card: dict, track, n_boot: int, seed: int, calibrated: bool = False) -> tuple:
    """Joint rule: candidate = best mean(A, B) AP (A alone where B has no GT); the incumbent (current route in
    model.yaml) is replaced only when the candidate passes the class gate on realval-B.

    calibrated=True compares every member at its own gated z calibration (bdc26.detect.zcalib: selected on A, kept
    only if B passes the class gate), the same rule `calibrate` applies after routing. Without it, a member whose z
    bias the calibration would remove could lose a class it should win. Returns (route, table, estimate,
    calibration of the routed members)."""
    names = list(card["members"])
    root = data_path(track, card["data"]["realval"])
    gts = {s_: sc.load_split(root, s_) for s_ in ("val", "valB")}
    raw, flg = {}, {}

    def preds(n, split):
        if (n, split) not in raw:
            m = card["members"][n]
            path = validation_predictions(model_dir.parent / m["model"], card, split, tag=member_tag(m))
            raw[(n, split)] = json.loads(path.read_text())
            flg[(n, split)] = sc.flags_for(path, gts[split], track.classes)
        return raw[(n, split)]

    def variant(n, c):
        """(calibration or None, A flags, B flags) of member n for class c."""
        preds(n, "val"), preds(n, "valB")
        fa, fb = flg[(n, "val")][c], flg[(n, "valB")][c]
        if not calibrated or sc.ap_from_flags(fb, "3d@0.5") is None or sc.ap_from_flags(fa, "3d@0.5") is None:
            return None, fa, fb, None
        res = zcalib.ZSearch(preds(n, "val"), gts["val"], c).search(zcalib.Z0_GRID, zcalib.K_GRID)
        if res["z0"] == 0.0 and res["z_per_m"] == 0.0:
            return None, fa, fb, res
        cc = {c: {"z0": res["z0"], "z_per_m": res["z_per_m"]}}
        fa_c = sc.frame_flags(zcalib.apply({i: preds(n, "val").get(i, []) for i in gts["val"]}, cc), gts["val"], [c])[c]
        fb_c = sc.frame_flags(zcalib.apply({i: preds(n, "valB").get(i, []) for i in gts["valB"]}, cc), gts["valB"], [c])[c]
        boot = sc.paired_bootstrap({c: fb}, {c: fb_c}, [c], n_boot, seed)[c]
        dA = sc.ap_from_flags(fa_c, "3d@0.5") - sc.ap_from_flags(fa, "3d@0.5")
        if sc.class_gate(boot["delta"], boot["p_gain"], dA):
            return cc[c], fa_c, fb_c, res
        return None, fa, fb, res

    incumbent = card.get("route") or {}
    route, table, calib = {}, {}, {}
    A, B = {}, {}
    for c in track.classes:
        V = {n: variant(n, c) for n in names}
        a_ = {n: sc.ap_from_flags(V[n][1], "3d@0.5") for n in names}
        b_ = {n: sc.ap_from_flags(V[n][2], "3d@0.5") for n in names}
        A[c], B[c] = a_, b_
        cands = [n for n in names if a_[n] is not None]
        if not cands:
            route[c] = names[0]
            continue
        joint = {n: (a_[n] + b_[n]) / 2 if b_[n] is not None else a_[n] for n in cands}
        best = max(cands, key=lambda n: (joint[n], a_[n]))
        inc = incumbent.get(c) if incumbent.get(c) in cands else None
        row = {"members": {n: {"A": a_[n], "B": b_[n], "joint": joint[n], "calibration": V[n][0]} for n in cands},
               "incumbent": inc, "candidate": best, "compared": "with gated calibration" if calibrated else "as post-processed"}
        if inc is None:
            route[c], row["decision"] = best, "no incumbent: best joint AP"
        elif best == inc:
            route[c], row["decision"] = inc, "the incumbent has the best joint AP"
        elif b_[best] is None or b_[inc] is None:
            route[c], row["decision"] = inc, "kept: no realval-B GT for this class"
        else:
            boot = sc.paired_bootstrap({c: V[inc][2]}, {c: V[best][2]}, [c], n_boot, seed)[c]
            dA = a_[best] - a_[inc]
            ok = sc.class_gate(boot["delta"], boot["p_gain"], dA)
            route[c] = best if ok else inc
            row.update({"dB": boot["delta"], "p_gain": boot["p_gain"], "ci90": boot["ci90"], "dA": dA,
                        "decision": "switched (class gate passed)" if ok else "kept (class gate failed)"})
        if V[route[c]][0]:
            calib[c] = V[route[c]][0]
        table[c] = row
    scored = list(track["classes_with_test_gt"])
    est = {s_: sum(((A if s_ == "A" else B)[c][route[c]] or 0.0) for c in scored) / len(scored) for s_ in ("A", "B")}
    return route, table, est, calib


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


def merge_route(route: dict, preds: dict) -> dict:
    """Per frame, each class from its routed member (member predictions already post-processed)."""
    ids = sorted(set().union(*[set(p) for p in preds.values()]))
    return {fid: [d for name, p in preds.items() for d in p.get(fid, []) if route.get(d["class"]) == name] for fid in ids}


def validate(model_dir: Path, card: dict, track, registry_run: str = "routed") -> dict:
    """Merge the members' validation predictions with the route, apply the calibration, evaluate (official metric)."""
    from bdc26 import registry
    from bdc26.evalap import evaluate
    data = card["data"]["realval"]
    D = data.replace("/", "_")
    out_dir, res_dir = model_dir / "validation" / "output", model_dir / "validation" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    res_dir.mkdir(parents=True, exist_ok=True)
    root = data_path(track, data)
    used = sorted(set(card["route"].values()))
    scores = {"run": "routed (official metric)" + (" + calibration" if card.get("calibration") else "")}
    for split, k in (("val", "A"), ("valB", "B")):
        preds = {}
        for n in used:
            m = card["members"][n]
            preds[n] = json.loads(validation_predictions(model_dir.parent / m["model"], card, split, tag=member_tag(m)).read_text())
        merged = merge_route(card["route"], preds)
        (out_dir / f"{D}_{split}_merged.json").write_text(json.dumps(merged))
        routed = zcalib.apply(merged, card.get("calibration") or {})
        (out_dir / f"{D}_{split}_routed.json").write_text(json.dumps(routed))
        gts = sc.load_split(root, split)
        res = evaluate({i: routed.get(i, []) for i in gts}, gts, track.classes)
        summary = {c: (v["3d@0.5"]["AP_R40"] if v["3d@0.5"] else None) for c, v in res["per_class"].items()}
        cwg = [c for c in track["classes_with_test_gt"] if summary.get(c) is not None]
        res["mAP_challenge_3d_0.5_R40"] = float(sum(summary[c] for c in cwg) / max(len(cwg), 1))
        res["challenge_classes"], res["n_frames"], res["data"], res["split"] = cwg, len(gts), data, split
        (res_dir / f"{D}_{split}_routed.json").write_text(json.dumps(res, indent=2))
        scores[f"realval_{k}_mAP_3d_0.5_R40"] = res["mAP_challenge_3d_0.5_R40"]
        scores[f"realval_{k}_per_class"] = summary
        registry.append(track, kind="eval", model=card["name"], run=registry_run, data_version=data, metric_source=f"{data}:{split}",
                        **{"mAP_3d_0.5_R40": f"{res['mAP_challenge_3d_0.5_R40']:.4f}"}, per_class=json.dumps(summary),
                        notes="routed" + (" + calibration" if card.get("calibration") else "") + "; mAP over the classes with test GT")
    (res_dir / "local_scores.json").write_text(json.dumps(scores, indent=2))
    print(json.dumps({k: v for k, v in scores.items() if "mAP" in k or k == "run"}, indent=2))
    return scores


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["select", "merge", "calibrate", "validate"])
    ap.add_argument("model_dir")
    ap.add_argument("--pred", action="append", default=[], help="member=predictions.json (merge)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--tie", type=float, default=0.005)
    ap.add_argument("--rule", choices=["a", "joint"], default="a", help="a: the S1 rule; joint: the class gate of docs/decisions/README.md Section 3.2")
    ap.add_argument("--bootstrap", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--classes", nargs="*", default=None, help="calibrate: classes to try (default: all with test GT)")
    ap.add_argument("--calibrated", action="store_true", help="select --rule joint: compare members with their gated z calibration")
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    if a.mode == "select":
        if a.rule == "joint":
            route, table, est, calib = select_joint(model_dir, card, track, a.bootstrap, a.seed, a.calibrated)
            rule = ("joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only "
                    f"through the class gate (dB >= 0.01, paired bootstrap x{a.bootstrap} P(gain) >= 0.9, dA >= -0.005)"
                    + ("; members compared with their gated z calibration" if a.calibrated else ""))
            if a.calibrated:
                card["calibration"] = calib
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
        _, card, _ = model_info(model_dir)
        validate(model_dir, card, track, registry_run="routed + calibration")
        return
    if a.mode == "validate":
        validate(model_dir, card, track)
        return
    preds = {}
    for spec in a.pred:
        name, path = spec.split("=", 1)
        preds[name] = json.loads(Path(path).read_text())
    route = card["route"]
    missing = set(route.values()) - set(preds)
    if missing:
        raise SystemExit(f"missing member predictions: {sorted(missing)}")
    out = zcalib.apply(merge_route(route, preds), card.get("calibration") or {})
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out))
    print(f"{len(out)} frames, {sum(len(v) for v in out.values())} boxes -> {a.out}")


if __name__ == "__main__":
    main()
