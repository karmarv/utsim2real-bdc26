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
    # S3 cross-member fusion per class (pairs of two different checkpoints among the top-4 members, IoU in
    # {0.3, 0.5, 0.7}, class gate vs the route); needs a prior `select --rule joint --calibrated` (route_table.json);
    # writes model.yaml `fusion`, then validates; --max-members 3 (S4) also tries triples
    python common/tools/route_predictions.py fuse model-v2x-track/routed-g3
    # R3 on: --pooled adds the pooled A+B condition to every gate of select, fuse and calibrate
    python common/tools/route_predictions.py fuse model-lumpi-track/routed-g6 --max-members 3 --pooled
    # R3 final gate after budget: class gate + pooled condition on the final predictions against the confirmed entry;
    # failing classes revert to the entry's configuration, then validates
    python common/tools/route_predictions.py gate model-lumpi-track/routed-g6 --vs model-lumpi-track/routed-g4
    # S3 server-cost budget: per class the highest score floor costing <= 0.002 AP on realval-A and on realval-B;
    # writes model.yaml `budget` (applied last by merge), then validates
    python common/tools/route_predictions.py budget model-v2x-track/routed-g3
    # merge predictions json files with the route in model.yaml (and the `calibration` and `fusion`, if any)
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

import numpy as np
import yaml

from _common import data_path, member_tag, model_info, validation_predictions
from bdc26 import scorecard as sc
from bdc26.detect import zcalib


def member_results(model_dir: Path, card: dict, name: str, split: str) -> dict:
    m = card["members"][name]
    res_dir = model_dir.parent / m["model"] / "validation" / "results"
    run = member_tag(m)                                                   # <tag>_checkpoint_epoch_N[_tta]
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


def select_joint(model_dir: Path, card: dict, track, n_boot: int, seed: int, calibrated: bool = False,
                 pooled: bool = False) -> tuple:
    """Joint rule: candidate = best mean(A, B) AP (A alone where B has no GT); the incumbent (current route in
    model.yaml) is replaced only when the candidate passes the class gate on realval-B.

    calibrated=True compares every member at its own gated z calibration (bdc26.detect.zcalib: selected on A, kept
    only if B passes the class gate), the same rule `calibrate` applies after routing. Without it, a member whose z
    bias the calibration would remove could lose a class it should win. pooled=True (R3 on): every switch and every
    calibration also needs a gain on the pooled A+B frames (scorecard.pooled_gate). Returns (route, table, estimate,
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
        if sc.class_gate(boot["delta"], boot["p_gain"], dA) and (
                not pooled or sc.pooled_gate({"val": fa, "valB": fb}, {"val": fa_c, "valB": fb_c}, c, n_boot, seed)["ok"]):
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
            if pooled:
                pg = sc.pooled_gate({"val": V[inc][1], "valB": V[inc][2]}, {"val": V[best][1], "valB": V[best][2]}, c, n_boot, seed)
                row["pooled"] = {"delta": pg["delta"], "p_gain": pg["p_gain"]}
                ok_b, ok = ok, ok and pg["ok"]
            route[c] = best if ok else inc
            row.update({"dB": boot["delta"], "p_gain": boot["p_gain"], "ci90": boot["ci90"], "dA": dA,
                        "decision": "switched (class gate passed)" if ok else
                        "kept (pooled A+B condition failed)" if pooled and ok_b else "kept (class gate failed)"})
        if V[route[c]][0]:
            calib[c] = V[route[c]][0]
        table[c] = row
    scored = list(track["classes_with_test_gt"])
    est = {s_: sum(((A if s_ == "A" else B)[c][route[c]] or 0.0) for c in scored) / len(scored) for s_ in ("A", "B")}
    return route, table, est, calib


def calibrate(model_dir: Path, card: dict, track, classes, n_boot: int, seed: int, pooled: bool = False) -> None:
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
                if pooled:
                    pg = sc.pooled_gate({"val": fa_base[c], "valB": fb_base[c]}, {"val": fa_cal[c], "valB": fb_cal[c]}, c, n_boot, seed)
                    entry["pooled"] = {"delta": pg["delta"], "p_gain": pg["p_gain"]}
                    ok = ok and pg["ok"]
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


def merge_card(card: dict, preds: dict) -> dict:
    """The routed model's predictions: classes in `fusion` from the fused members (each with its own gated z
    calibration), the other classes from their routed member with the class-level `calibration`."""
    from bdc26.detect.fusion import fuse_dets
    fusion = card.get("fusion") or {}
    route = {c: m for c, m in card["route"].items() if c not in fusion}
    calib = {c: v for c, v in (card.get("calibration") or {}).items() if c not in fusion}
    out = zcalib.apply(merge_route(route, {n: preds[n] for n in set(route.values()) if n in preds}), calib)
    ids = sorted(set().union(*[set(p) for p in preds.values()]))
    for c, fz in fusion.items():
        srcs = []
        for n in fz["members"]:
            pc = {f: [d for d in preds[n].get(f, []) if d["class"] == c] for f in ids}
            cal = (fz.get("calibration") or {}).get(n)
            srcs.append(zcalib.apply(pc, {c: cal}) if cal else pc)
        for f in ids:
            out.setdefault(f, []).extend(fuse_dets([s_[f] for s_ in srcs], fz["iou"], fz.get("weights")))
    return apply_tail_copies(apply_budget(out, card.get("budget")), card.get("tail_copies"))


def apply_tail_copies(preds: dict, spec: dict | None) -> dict:
    """R5 walker tail copies (model.yaml `tail_copies: {class: {r: metres, n: copies}}`): every box of the class gets
    n copies shifted by r in BEV (directions k * 2 pi / n), scored s * f with f = 0.99 * (smallest score of the class
    in this prediction set) / (largest), so every copy ranks below every original box of its class. The scorer
    matches in score order inside a frame and pools all frames by score, so the originals keep their matches and
    their place on the precision-recall curve; a copy can only match a GT box that no original matched at IoU 0.5.
    Adding boxes below all existing scores cannot lower an interpolated AP (R40 takes the maximum precision at
    recall >= r), so the knob can only help the class on any frame set; it is still gated like any other."""
    if not spec:
        return preds
    out = {f: list(v) for f, v in preds.items()}
    for c, sp in spec.items():
        s = [d["score"] for v in preds.values() for d in v if d["class"] == c]
        if not s or max(s) <= 0:
            continue
        f = 0.99 * min(s) / max(s)
        r, n = float(sp["r"]), int(sp.get("n", 4))
        offs = [(r * np.cos(2 * np.pi * k / n), r * np.sin(2 * np.pi * k / n)) for k in range(n)]
        for fid, v in preds.items():
            for d in v:
                if d["class"] != c:
                    continue
                for dx, dy in offs:
                    b = list(d["box"])
                    b[0] += dx
                    b[1] += dy
                    out[fid].append({"box": b, "score": d["score"] * f, "class": c})
    return out


def tail_select(model_dir: Path, card: dict, track, classes, radii=(0.1, 0.15, 0.2), n_copies: int = 4,
                n_boot: int = 200, seed: int = 0) -> dict:
    """R5: per walker class, the copy radius with the best realval-A AP; kept only through the class gate on B and the
    pooled A+B condition against the same predictions without copies. Writes model.yaml `tail_copies`."""
    root = data_path(track, card["data"]["realval"])
    base_card = {**card, "tail_copies": None}
    merged, gts = {}, {}
    for split in ("val", "valB"):
        gts[split] = sc.load_split(root, split)
        merged[split] = merge_card(base_card, {n: json.loads(validation_predictions(
            model_dir.parent / card["members"][n]["model"], card, split, tag=member_tag(card["members"][n])).read_text())
            for n in used_members(card)})
    spec, report = {}, {}
    for c in classes:
        fl0 = {s_: sc.frame_flags({i: merged[s_].get(i, []) for i in gts[s_]}, gts[s_], [c])[c] for s_ in gts}
        if sc.ap_from_flags(fl0["valB"], "3d@0.5") is None:
            continue
        rows, cand = [], {}
        for r in radii:
            cp = {s_: apply_tail_copies(merged[s_], {c: {"r": r, "n": n_copies}}) for s_ in gts}
            fl = {s_: sc.frame_flags({i: cp[s_].get(i, []) for i in gts[s_]}, gts[s_], [c])[c] for s_ in gts}
            cand[r] = fl
            rows.append({"r": r, "A": sc.ap_from_flags(fl["val"], "3d@0.5"), "B": sc.ap_from_flags(fl["valB"], "3d@0.5")})
        best = max(rows, key=lambda x: x["A"])
        fl = cand[best["r"]]
        boot = sc.paired_bootstrap({c: fl0["valB"]}, {c: fl["valB"]}, [c], n_boot, seed)[c]
        dA = best["A"] - sc.ap_from_flags(fl0["val"], "3d@0.5")
        pg = sc.pooled_gate(fl0, fl, c, n_boot, seed)
        # copies cannot lower AP on any frame set (apply_tail_copies), so the 0.01 noise bar of the class gate, which
        # guards changes that can go either way, is waived; a gain on B and on the pooled frames (P >= 0.9) is still
        # required (R5; decided after the first V2X run measured dB +0.0098, recorded in docs/02-STRATEGY.md 8.9)
        ok = sc.class_gate(boot["delta"], boot["p_gain"], dA, min_gain=1e-9) and pg["ok"]
        report[c] = {"base": {"A": sc.ap_from_flags(fl0["val"], "3d@0.5"), "B": sc.ap_from_flags(fl0["valB"], "3d@0.5")},
                     "grid": rows, "chosen_r": best["r"], "dB": boot["delta"], "p_gain": boot["p_gain"], "dA": dA,
                     "pooled": {"delta": pg["delta"], "p_gain": pg["p_gain"]}, "kept": ok}
        print(c, json.dumps(report[c]), flush=True)
        if ok:
            spec[c] = {"r": best["r"], "n": n_copies}
    card["tail_copies"] = spec or None
    (model_dir / "model.yaml").write_text(yaml.safe_dump({k: v for k, v in card.items() if v is not None or k != "tail_copies"},
                                                         sort_keys=False))
    (model_dir / "validation" / "results" / "tail_table.json").write_text(json.dumps(report, indent=2))
    return spec


def apply_budget(preds: dict, budget: dict | None) -> dict:
    """Drop boxes below the class's score floor (model.yaml `budget`, chosen by `budget_select`)."""
    if not budget:
        return preds
    return {f: [d for d in v if d["score"] >= budget.get(d["class"], 0.0)] for f, v in preds.items()}


def used_members(card: dict) -> list[str]:
    fusion = card.get("fusion") or {}
    return sorted({m for c, m in card["route"].items() if c not in fusion} | {n for fz in fusion.values() for n in fz["members"]})


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
    used = used_members(card)
    tag = " + calibration" if card.get("calibration") else ""
    tag += (" + fusion (" + ", ".join(sorted(card["fusion"])) + ")") if card.get("fusion") else ""
    tag += " + budget" if card.get("budget") else ""
    scores = {"run": "routed (official metric)" + tag}
    for split, k in (("val", "A"), ("valB", "B")):
        preds = {}
        for n in used:
            m = card["members"][n]
            preds[n] = json.loads(validation_predictions(model_dir.parent / m["model"], card, split, tag=member_tag(m)).read_text())
        merged = merge_route(card["route"], {n: preds[n] for n in set(card["route"].values()) if n in preds})
        (out_dir / f"{D}_{split}_merged.json").write_text(json.dumps(merged))
        routed = merge_card(card, preds)
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
                        notes="routed" + tag + "; mAP over the classes with test GT")
    (res_dir / "local_scores.json").write_text(json.dumps(scores, indent=2))
    print(json.dumps({k: v for k, v in scores.items() if "mAP" in k or k == "run"}, indent=2))
    return scores


_FUSE = {}


def _fuse_eval(job):
    """Worker: fused A and B AP of one (class, member pair, IoU) candidate (fast float32 IoU during the search)."""
    from bdc26 import evalap
    from bdc26.detect.fusion import fuse_dets
    evalap.EXACT_IOU = False
    c, pair, thr = job
    out = {}
    for split in ("val", "valB"):
        P = [_FUSE["preds"][(n, split)] for n in pair]
        gts = _FUSE["gts"][split]
        F = {f: fuse_dets([p_[f] for p_ in P], thr) for f in gts}
        out[split] = evalap.evaluate(F, gts, [c])["per_class"][c]["3d@0.5"]["AP_R40"]
        if split == "val" and _FUSE.get("late"):          # R5 late-A rank (the late realval-A frames only)
            lg = {f: gts[f] for f in _FUSE["late"] if f in gts}
            out["lateA"] = evalap.evaluate({f: F[f] for f in lg}, lg, [c])["per_class"][c]["3d@0.5"]["AP_R40"]
    return job, out


def fuse_select(model_dir: Path, card: dict, track, n_boot: int, seed: int, classes=None, iou_grid=(0.3, 0.5, 0.7),
                top: int = 4, workers: int = 32, max_members: int = 2, pooled: bool = False,
                late_rank=(), gate_top: int = 1) -> dict:
    """S3 cross-member fusion (docs/02-STRATEGY.md Section 8.3): per class, fuse each pair of the top-`top` members
    (joint realval-A/B AP after their gated z calibration, from route_table.json of `select --calibrated`) with equal
    weights at each IoU of iou_grid; the best joint candidate replaces the routed member only through the class gate
    (exact official IoU, paired bootstrap on realval-B). Two knobs per class: the set and the IoU. A set needs
    different checkpoints: a member and its own TTA variant are views of one model, which TTA already fuses.
    max_members=3 (S4) also tries the triples among the top members, so three architecture families can be fused.
    Cumulative strategies: a class that already has a `fusion` in model.yaml keeps it as the incumbent (its set is
    always a candidate, with its stored calibrations), so a new member can replace an earlier fusion only through the
    class gate against that fusion, never against the single routed member. pooled=True (R3 on): a fusion also
    needs a gain on the pooled A+B frames (scorecard.pooled_gate).
    late_rank (R5, pre-registered for LUMPI Person): those classes rank their candidates by late-A AP (track.yaml
    `late_a`) instead of the joint A/B mean, and the top `gate_top` candidates go through the same gates in that order;
    the first that passes is kept. Reason: the early realval-A Person labels are almost all manually corrected (0.97-0.99)
    with 24-34 persons per frame, the late ones 0.69 corrected with 10.8 per frame, like the test window's 10.2."""
    import itertools
    from concurrent.futures import ProcessPoolExecutor
    import multiprocessing as mp
    from bdc26.detect.fusion import fuse_dets
    table = json.loads((model_dir / "validation" / "results" / "route_table.json").read_text())
    root = data_path(track, card["data"]["realval"])
    gts = {s_: sc.load_split(root, s_) for s_ in ("val", "valB")}
    classes = classes or list(track["classes_with_test_gt"])
    raw = {}

    def member_preds(n, split):
        if (n, split) not in raw:
            m = card["members"][n]
            raw[(n, split)] = json.loads(validation_predictions(model_dir.parent / m["model"], card, split, tag=member_tag(m)).read_text())
        return raw[(n, split)]

    def class_preds(n, split, c, cal="table"):
        cal = table[c]["members"].get(n, {}).get("calibration") if cal == "table" else cal
        pc = {f: [d for d in member_preds(n, split).get(f, []) if d["class"] == c] for f in gts[split]}
        return zcalib.apply(pc, {c: cal}) if cal else pc

    prior = card.get("fusion") or {}                    # the incumbent fusion of each class, if any

    ranked = {c: sorted(table[c]["members"], key=lambda n: -(table[c]["members"][n]["joint"] or 0.0))[:top] for c in classes}
    ckpt = lambda n: (card["members"][n]["model"], card["members"][n]["ckpt"])
    sets = lambda c: [m for k in range(2, max_members + 1) for m in itertools.combinations(ranked[c], k)
                      if len({ckpt(n) for n in m}) == len(m)]
    jobs = [(c, members, thr) for c in classes for members in sets(c) for thr in iou_grid]
    for c, fz in prior.items():
        if c in classes and (c, tuple(fz["members"]), fz["iou"]) not in jobs:
            jobs.append((c, tuple(fz["members"]), fz["iou"]))
    _FUSE.clear()
    _FUSE["gts"] = gts
    late_rank = [c for c in (late_rank or ()) if c in classes]
    results = {}
    for c in classes:                                   # one pool per class: the workers see that class's predictions
        need = set(ranked[c]) | set(prior.get(c, {}).get("members", []))
        _FUSE["preds"] = {(n, split): class_preds(n, split, c) for n in need for split in ("val", "valB")}
        cj = [j for j in jobs if j[0] == c]
        _FUSE["late"] = sc.late_a_ids(track, list(gts["val"])) if c in late_rank else None
        with ProcessPoolExecutor(max_workers=min(workers, len(cj)), mp_context=mp.get_context("fork")) as ex:
            for job, out in ex.map(_fuse_eval, cj):
                results[job] = out
                print(f"  {c:11s} {'+'.join(job[1]):24s} iou {job[2]}: A {out['val']:.4f} B {out['valB']:.4f}", flush=True)
    fusion, report = {c: fz for c, fz in prior.items() if c not in classes}, {}
    for c in classes:
        cand = {j: r for j, r in results.items() if j[0] == c}
        if not cand:
            continue
        if c in late_rank:
            order = sorted(cand, key=lambda j: -(cand[j].get("lateA") or 0.0))[:max(1, gate_top)]
        else:
            order = [max(cand, key=lambda j: (cand[j]["val"] + cand[j]["valB"]) / 2)]
        mem = table[c]["members"]
        pz = prior.get(c)
        if pz:                                          # incumbent: the earlier fusion, with its stored calibrations
            inc = "fusion " + "+".join(pz["members"]) + f"@{pz['iou']}"
            I = {s_: {f: fuse_dets([class_preds(n, s_, c, (pz.get("calibration") or {}).get(n))[f] for n in pz["members"]], pz["iou"])
                      for f in gts[s_]} for s_ in ("val", "valB")}
        else:
            inc = card["route"][c]
            I = {s_: class_preds(inc, s_, c) for s_ in ("val", "valB")}
        tested = []
        for best in order:
            _, pair, thr = best
            F = {s_: {f: fuse_dets([class_preds(n, s_, c)[f] for n in pair], thr) for f in gts[s_]} for s_ in ("val", "valB")}
            fl = {(k, s_): sc.frame_flags(X[s_], gts[s_], [c]) for k, X in (("fused", F), ("inc", I)) for s_ in ("val", "valB")}
            boot = sc.paired_bootstrap(fl[("inc", "valB")], fl[("fused", "valB")], [c], n_boot, seed)[c]
            dA = sc.ap_from_flags(fl[("fused", "val")][c], "3d@0.5") - sc.ap_from_flags(fl[("inc", "val")][c], "3d@0.5")
            same = bool(pz) and tuple(pz["members"]) == tuple(pair) and pz["iou"] == thr
            ok = not same and boot["p_gain"] is not None and sc.class_gate(boot["delta"], boot["p_gain"], dA)
            pg = sc.pooled_gate({s_: fl[("inc", s_)][c] for s_ in ("val", "valB")},
                                {s_: fl[("fused", s_)][c] for s_ in ("val", "valB")}, c, n_boot, seed) if pooled else None
            ok_b, ok = ok, ok and (pg is None or pg["ok"])
            tested.append({"members": list(pair), "iou": thr, "lateA": cand[best].get("lateA"), "dB": boot["delta"],
                           "p_gain": boot["p_gain"], "dA": dA, "pooled": pg and {"delta": pg["delta"], "p_gain": pg["p_gain"]},
                           "passed": ok})
            if ok or same:
                break
        report[c] = {"incumbent": inc, "incumbent_A": sc.ap_from_flags(fl[("inc", "val")][c], "3d@0.5"),
                     "incumbent_B": sc.ap_from_flags(fl[("inc", "valB")][c], "3d@0.5"),
                     "best": {"members": list(pair), "iou": thr, "A": sc.ap_from_flags(fl[("fused", "val")][c], "3d@0.5"),
                              "B": sc.ap_from_flags(fl[("fused", "valB")][c], "3d@0.5")},
                     "dB": boot["delta"], "p_gain": boot["p_gain"], "ci90": boot["ci90"], "dA": dA,
                     "pooled": {"delta": pg["delta"], "p_gain": pg["p_gain"]} if pg else None,
                     "decision": ("fused (class gate passed)" if ok else "incumbent fusion kept (it is the best candidate)" if same
                                  else "kept (pooled A+B condition failed)" if ok_b
                                  else "incumbent fusion kept (class gate failed)" if pz else "routed member kept (class gate failed)"),
                     "search_fast_iou": {f"{'+'.join(j[1])}@{j[2]}": r for j, r in cand.items()},
                     "rank": "late-A, top %d through the gates" % max(1, gate_top) if c in late_rank else "joint A/B, best only",
                     "tested": tested}
        a_best = max(cand, key=lambda j: cand[j]["val"])      # selection-bias check: the pick of realval-A alone
        report[c]["a_only_pick"] = {"members": list(a_best[1]), "iou": a_best[2], "A": cand[a_best]["val"], "B": cand[a_best]["valB"]}
        if ok:
            fusion[c] = {"members": list(pair), "weights": [1.0] * len(pair), "iou": thr,
                         "calibration": {n: mem[n]["calibration"] for n in pair if mem[n]["calibration"]}}
        elif pz:
            fusion[c] = pz
        print(c, json.dumps({k: v for k, v in report[c].items() if k != "search_fast_iou"}), flush=True)
    card["fusion"] = fusion
    text = (model_dir / "model.yaml").read_text().split("\nfusion:")[0].rstrip() + "\n"
    text += yaml.safe_dump({"fusion": fusion}, sort_keys=False)
    if card.get("budget"):
        text += yaml.safe_dump({"budget": card["budget"]}, sort_keys=False)
    (model_dir / "model.yaml").write_text(text)
    (model_dir / "validation" / "results" / "fusion_table.json").write_text(json.dumps(report, indent=2))
    return fusion


FLOORS = (0.0, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3)


def budget_select(model_dir: Path, card: dict, track, max_loss: float = 0.002) -> dict:
    """Server-cost budget (docs/02-STRATEGY.md Section 8.3 step 6): per class, the highest score floor whose AP loss
    is at most max_loss on realval-A and on realval-B. Exact and cheap: matching is greedy in score order, so
    removing every box below a floor leaves the matches of the boxes above it unchanged, and the AP at a floor is
    the AP of the truncated flags. Fusion and TTA make many low-score single-source boxes; they sit in the tail of
    the precision-recall curve, where R40 gives them little weight. Reads the unbudgeted routed predictions."""
    D = card["data"]["realval"].replace("/", "_")
    root = data_path(track, card["data"]["realval"])
    out_dir = model_dir / "validation" / "output"
    budget, report = {}, {}
    flags, counts = {}, {}
    for split in ("val", "valB"):
        gts = sc.load_split(root, split)
        merged = merge_card({**card, "budget": None}, {n: json.loads(validation_predictions(
            model_dir.parent / card["members"][n]["model"], card, split, tag=member_tag(card["members"][n])).read_text())
            for n in used_members(card)})
        flags[split] = sc.frame_flags({i: merged.get(i, []) for i in gts}, gts, track.classes)
        counts[split] = (len(gts), {c: np.array([d["score"] for v in merged.values() for d in v if d["class"] == c])
                                    for c in track.classes})

    def trunc(recs, floor):
        out = []
        for r in recs:
            m = r["scores"] >= floor
            out.append({"n_gt": r["n_gt"], "scores": r["scores"][m], "3d@0.5": r["3d@0.5"][m]})
        return out

    for c in track.classes:
        base = {s_: sc.ap_from_flags(flags[s_][c], "3d@0.5") for s_ in ("val", "valB")}
        best, rows = 0.0, []
        for fl in FLOORS:
            ap_ = {s_: sc.ap_from_flags(trunc(flags[s_][c], fl), "3d@0.5") for s_ in ("val", "valB")}
            loss = {s_: (base[s_] - ap_[s_]) if base[s_] is not None else 0.0 for s_ in ap_}
            n = counts["val"][1][c]
            rows.append({"floor": fl, "A": ap_["val"], "B": ap_["valB"], "boxes_per_frame_A": float((n >= fl).sum() / counts["val"][0])})
            if all(v <= max_loss for v in loss.values()):
                best = fl
        if best > 0:
            budget[c] = best
        report[c] = {"floor": best, "A_full": base["val"], "B_full": base["valB"], "grid": rows}
        r = next(x for x in rows if x["floor"] == best)
        print(f"  {c:11s} floor {best:<6} A {base['val'] or 0:.4f} -> {r['A'] or 0:.4f}  B {base['valB'] or 0:.4f} -> {(r['B'] or 0):.4f}  "
              f"boxes/frame {rows[0]['boxes_per_frame_A']:.0f} -> {r['boxes_per_frame_A']:.0f}", flush=True)
    card["budget"] = budget
    text = (model_dir / "model.yaml").read_text().split("\nbudget:")[0].rstrip() + "\n"
    text += yaml.safe_dump({"budget": budget}, sort_keys=False)
    (model_dir / "model.yaml").write_text(text)
    (model_dir / "validation" / "results" / "budget_table.json").write_text(json.dumps(report, indent=2))
    return budget


def _class_config(card: dict, c: str) -> tuple:
    return (card.get("route", {}).get(c), (card.get("calibration") or {}).get(c), (card.get("fusion") or {}).get(c),
            (card.get("budget") or {}).get(c), (card.get("tail_copies") or {}).get(c))


def final_gate(model_dir: Path, card: dict, track, vs_dir: Path, n_boot: int, seed: int) -> dict:
    """R3 final gate: every class whose configuration (route, calibration, fusion, score floor) differs from the
    confirmed portfolio `vs_dir` must pass the class gate on B and the pooled A+B condition on the FINAL validation
    predictions of both (validation/output/<data>_<split>_routed.json), where the pooled rule was validated (S3-S5:
    16 of 17 leaderboard signs). The per-step checks of select and fuse run before the score floors; a fusion can gain
    on A and on B there and still be flat once both splits are ranked together (R3: LUMPI Car, pooled +0.010 at P 1.00
    in fuse, +0.0006 at P 0.64 final). A failing class is reverted to the incumbent's configuration, then the model is
    validated again. Writes validation/results/final_gate.json."""
    _, vs_card, _ = model_info(vs_dir)
    root = data_path(track, card["data"]["realval"])
    D = card["data"]["realval"].replace("/", "_")
    gts = {s_: sc.load_split(root, s_) for s_ in ("val", "valB")}
    path = lambda m, s_: m / "validation" / "output" / f"{D}_{s_}_routed.json"
    fl = {(k, s_): sc.flags_for(path(m, s_), gts[s_], list(track.classes)) for k, m in (("inc", vs_dir), ("new", model_dir))
          for s_ in ("val", "valB")}
    report, reverted = {}, []
    for c in track["classes_with_test_gt"]:
        if _class_config(card, c) == _class_config(vs_card, c):
            report[c] = {"decision": "same configuration as the incumbent"}
            continue
        ap = {(k, s_): sc.ap_from_flags(fl[(k, s_)][c], "3d@0.5") for k in ("inc", "new") for s_ in ("val", "valB")}
        if ap[("inc", "valB")] is None:
            ok, row = False, {"decision": "reverted: no realval-B GT"}
        else:
            boot = sc.paired_bootstrap({c: fl[("inc", "valB")][c]}, {c: fl[("new", "valB")][c]}, [c], n_boot, seed)[c]
            dA = ap[("new", "val")] - ap[("inc", "val")]
            pg = sc.pooled_gate({s_: fl[("inc", s_)][c] for s_ in ("val", "valB")}, {s_: fl[("new", s_)][c] for s_ in ("val", "valB")},
                                c, n_boot, seed)
            only_tail = _class_config(card, c)[:4] == _class_config(vs_card, c)[:4]   # R5: copies are the only change
            gate_b = sc.class_gate(boot["delta"], boot["p_gain"], dA, min_gain=1e-9 if only_tail else 0.01)
            ok = gate_b and pg["ok"]
            row = {"A": [ap[("inc", "val")], ap[("new", "val")]], "B": [ap[("inc", "valB")], ap[("new", "valB")]],
                   "dB": boot["delta"], "p_gain": boot["p_gain"], "dA": dA, "pooled": {"delta": pg["delta"], "p_gain": pg["p_gain"]},
                   "decision": "kept (class gate and pooled condition passed)" if ok else
                   ("reverted (pooled A+B condition failed)" if gate_b else "reverted (class gate failed)")}
        if not ok:
            route, cal, fus, bud, tail = _class_config(vs_card, c)
            need = set(fus["members"]) if fus else {route}
            missing = [n for n in need if n not in card["members"] or card["members"][n] != vs_card["members"][n]]
            if missing:
                raise SystemExit(f"{c}: incumbent members {missing} are not the same in {model_dir.name}")
            card["route"][c] = route
            for key, val in (("calibration", cal), ("fusion", fus), ("budget", bud), ("tail_copies", tail)):
                d = card.get(key) or {}
                if val is None:
                    d.pop(c, None)
                else:
                    d[c] = val
                card[key] = d
            reverted.append(c)
        report[c] = row
        print(c, json.dumps(row), flush=True)
    if reverted:
        (model_dir / "model.yaml").write_text(yaml.safe_dump(card, sort_keys=False))
    (model_dir / "validation" / "results" / "final_gate.json").write_text(json.dumps({"vs": vs_dir.name, "classes": report,
                                                                                       "reverted": reverted}, indent=2))
    print("reverted:", reverted or "none")
    return {"reverted": reverted, "classes": report}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["select", "merge", "calibrate", "validate", "fuse", "budget", "tail", "gate"])
    ap.add_argument("model_dir")
    ap.add_argument("--pred", action="append", default=[], help="member=predictions.json (merge)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--tie", type=float, default=0.005)
    ap.add_argument("--rule", choices=["a", "joint"], default="a", help="a: the S1 rule; joint: the class gate of docs/decisions/README.md Section 3.2")
    ap.add_argument("--bootstrap", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--classes", nargs="*", default=None, help="calibrate: classes to try (default: all with test GT)")
    ap.add_argument("--calibrated", action="store_true", help="select --rule joint: compare members with their gated z calibration")
    ap.add_argument("--max-members", type=int, default=2, help="fuse: largest member set (2: pairs, as in S3; 3: also triples)")
    ap.add_argument("--late-rank", nargs="*", default=[], help="fuse (R5): classes ranked by late-A AP (LUMPI Person)")
    ap.add_argument("--gate-top", type=int, default=1, help="fuse (R5): candidates of a --late-rank class tested through the gates")
    ap.add_argument("--vs", default=None, help="gate: the confirmed portfolio to compare the final predictions with")
    ap.add_argument("--pooled", action="store_true", help="select/fuse/calibrate: the class gate also needs a gain on the pooled "
                                                          "A+B frames with P(gain) >= 0.9 (docs/decisions/README.md Section 3.2, R3 on)")
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    if a.mode == "select":
        if a.rule == "joint":
            route, table, est, calib = select_joint(model_dir, card, track, a.bootstrap, a.seed, a.calibrated, a.pooled)
            rule = ("joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only "
                    f"through the class gate (dB >= 0.01, paired bootstrap x{a.bootstrap} P(gain) >= 0.9, dA >= -0.005)"
                    + ("; members compared with their gated z calibration" if a.calibrated else "")
                    + ("; also a gain on the pooled A+B frames (P(gain) >= 0.9)" if a.pooled else ""))
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
        if card.get("fusion"):                                    # keep a fusion chosen by `fuse`
            text += yaml.safe_dump({"fusion": card["fusion"]}, sort_keys=False)
        if card.get("budget"):                                    # keep a budget chosen by `budget`
            text += yaml.safe_dump({"budget": card["budget"]}, sort_keys=False)
        (model_dir / "model.yaml").write_text(text)
        (model_dir / "validation" / "results").mkdir(parents=True, exist_ok=True)
        (model_dir / "validation" / "results" / "route_table.json").write_text(json.dumps(table, indent=2))
        print(json.dumps({"route": route, **card["route_selection"]}, indent=2))
        return
    if a.mode == "calibrate":
        calibrate(model_dir, card, track, a.classes, a.bootstrap, a.seed, a.pooled)
        _, card, _ = model_info(model_dir)
        validate(model_dir, card, track, registry_run="routed + calibration")
        return
    if a.mode == "validate":
        validate(model_dir, card, track)
        return
    if a.mode == "budget":
        budget_select(model_dir, card, track)
        _, card, _ = model_info(model_dir)
        validate(model_dir, card, track, registry_run="routed + fusion + budget")
        return
    if a.mode == "tail":
        walkers = [c for c in track["classes_with_test_gt"] if c.lower() in ("person", "pedestrian")]
        tail_select(model_dir, card, track, a.classes or walkers, n_boot=a.bootstrap, seed=a.seed)
        _, card, _ = model_info(model_dir)
        validate(model_dir, card, track, registry_run="routed + fusion + budget + tail copies")
        return
    if a.mode == "gate":
        if not a.vs:
            raise SystemExit("gate needs --vs <confirmed routed model>")
        res = final_gate(model_dir, card, track, Path(a.vs).resolve(), a.bootstrap, a.seed)
        if res["reverted"]:
            _, card, _ = model_info(model_dir)
            validate(model_dir, card, track, registry_run="routed + fusion + budget + final gate")
        return
    if a.mode == "fuse":
        fuse_select(model_dir, card, track, a.bootstrap, a.seed, a.classes, max_members=a.max_members, pooled=a.pooled,
                    late_rank=a.late_rank, gate_top=a.gate_top)
        _, card, _ = model_info(model_dir)
        validate(model_dir, card, track, registry_run="routed + fusion")
        return
    preds = {}
    for spec in a.pred:
        name, path = spec.split("=", 1)
        preds[name] = json.loads(Path(path).read_text())
    missing = set(used_members(card)) - set(preds)
    if missing:
        raise SystemExit(f"missing member predictions: {sorted(missing)}")
    out = merge_card(card, preds)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out))
    print(f"{len(out)} frames, {sum(len(v) for v in out.values())} boxes -> {a.out}")


if __name__ == "__main__":
    main()
