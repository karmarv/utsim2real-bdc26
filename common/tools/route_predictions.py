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
    # S7.6: one candidate per class, the incumbent fusion with the extended bags in place of their seeds or 3-seed bag;
    # the budget's floor loss also bounded on the pooled A+B frames
    python common/tools/route_predictions.py fuse model-v2x-track/routed-g12 --pooled-rule --swap-to bagvr5x bagpv5x
    python common/tools/route_predictions.py budget model-v2x-track/routed-g12 --pooled
    # S8.2: members missing from route_table.json enter it with their uncalibrated joint AP (so fuse can rank them)
    python common/tools/route_predictions.py extend model-lumpi-track/routed-g11c
    # S7 sparse-box demotion (V2X): per class the threshold k (fewer points -> ranked last) with the best realval-A AP,
    # kept by the pooled rule and a k - 1 robustness check; writes model.yaml `sparse_demotion`, then validates
    python common/tools/route_predictions.py sparse model-v2x-track/routed-g9
    # merge predictions json files with the route in model.yaml (and the `calibration` and `fusion`, if any; the S7
    # stage counts points of the kit test frames, or of --frames <dataset>)
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


def extend_table(model_dir: Path, card: dict, track) -> list:
    """S8.2: members of model.yaml missing from route_table.json enter it as `select --rule joint` would rank them without
    calibration (A, B, joint = mean of A and B, or A without B GT; calibration None), so `fuse` can rank them; the
    existing rows and the route are not touched. Returns the added members."""
    path = model_dir / "validation" / "results" / "route_table.json"
    table = json.loads(path.read_text())
    root = data_path(track, card["data"]["realval"])
    gts = {s_: sc.load_split(root, s_) for s_ in ("val", "valB")}
    classes = [c for c in track.classes if c in table]
    added = []
    for n, m in card["members"].items():
        if all(n in table[c]["members"] for c in classes):
            continue
        fl = {s_: sc.flags_for(validation_predictions(model_dir.parent / m["model"], card, s_, tag=member_tag(m)), gts[s_],
                               list(track.classes)) for s_ in gts}
        for c in classes:
            a_, b_ = sc.ap_from_flags(fl["val"][c], "3d@0.5"), sc.ap_from_flags(fl["valB"][c], "3d@0.5")
            if n in table[c]["members"] or a_ is None:
                continue
            table[c]["members"][n] = {"A": a_, "B": b_, "joint": (a_ + b_) / 2 if b_ is not None else a_, "calibration": None}
        added.append(n)
        print(n, {c: round(table[c]["members"][n]["joint"], 4) for c in classes if n in table[c]["members"]}, flush=True)
    path.write_text(json.dumps(table, indent=2))
    return added


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


def merge_card(card: dict, preds: dict, points_of=None) -> dict:
    """The routed model's predictions: classes in `fusion` from the fused members (each with its own gated z
    calibration), the other classes from their routed member with the class-level `calibration`; then score floors,
    tail copies and (S7) the sparse-box demotion, which needs the frames' points (`points_of(frame_id)`, frame_points)."""
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
    out = apply_tail_copies(apply_budget(out, card.get("budget")), card.get("tail_copies"))
    # S8.3 `final_copies` (same spec as tail_copies), after the sparse stage: scored below every box of the class,
    # demoted ones included, so they cannot lower AP even where the S7 stage reorders the tail
    out = apply_tail_copies(apply_sparse_demotion(out, card.get("sparse_demotion"), points_of), card.get("final_copies"))
    return apply_size_calibration(out, card.get("size_calibration"))


def apply_size_calibration(preds: dict, spec: dict | None) -> dict:
    """S9 close-out anchored size calibration (model.yaml `size_calibration: {anchors: [[x, y], ...], classes:
    {class: {dl, dw, dh}}}`; record Section 15.31), the last stage: l += dl, w += dw, h += dh, z += dh / 2 (the box
    bottom stays) and, with dl set, the box end nearest an anchor (a sensor's xy, the face the LiDAR sees) stays, so
    the centre moves by dl / 2 along the heading axis. No box is added or removed."""
    if not spec or not spec.get("classes"):
        return preds
    anchors = np.asarray(spec.get("anchors") or [[0.0, 0.0]], dtype=np.float64).reshape(-1, 2)
    cal = spec["classes"]
    out = {}
    for fid, dets in preds.items():
        new = []
        for d in dets:
            k = cal.get(d["class"])
            if k:
                dl, dw, dh = float(k.get("dl", 0.0)), float(k.get("dw", 0.0)), float(k.get("dh", 0.0))
                b = np.array(d["box"], dtype=np.float64)
                if dl:
                    u = np.array([np.cos(b[6]), np.sin(b[6])])
                    ends = np.stack([b[:2] + b[3] / 2 * u, b[:2] - b[3] / 2 * u])     # front, back
                    dist = np.linalg.norm(ends[:, None, :] - anchors[None], axis=2).min(1)
                    b[:2] += (-1.0 if dist[0] < dist[1] else 1.0) * dl / 2 * u
                b[3] = max(0.05, b[3] + dl); b[4] = max(0.05, b[4] + dw); b[5] = max(0.05, b[5] + dh); b[2] += dh / 2
                d = dict(d, box=b.tolist())
            new.append(d)
        out[fid] = new
    return out


def frame_points(track, data: str | None = "kit"):
    """Points of a frame by id, for the sparse stage: 'kit' (the 50 starting-kit test frames, inference only) or a
    dataset folder such as the card's data.realval."""
    if data in (None, "kit"):
        from bdc26.io.kit import read_test_frame
        return lambda fid: read_test_frame(track, fid)
    root = data_path(track, data)
    return lambda fid: np.load(root / "points" / f"{fid}.npy")


def box_point_counts(preds: dict, classes, points_of) -> dict:
    """Per frame, the points inside each box of `classes` (counted per box, nulls excluded), -1 for the other boxes."""
    from bdc26.boxes import count_points_per_box
    out = {}
    for f, v in preds.items():
        n = np.full(len(v), -1, dtype=np.int64)
        idx = [j for j, d in enumerate(v) if d["class"] in classes]
        if idx:
            n[idx] = count_points_per_box(points_of(f), np.array([v[j]["box"] for j in idx], dtype=np.float64))
        out[f] = n
    return out


def apply_sparse_demotion(preds: dict, spec: dict | None, points_of=None, counts: dict | None = None) -> dict:
    """S7 sparse-box demotion (model.yaml `sparse_demotion: {class: k}`; docs/decisions/2026-10-18-s7-visibility-rule.md):
    a box of class c with fewer than k points inside it is re-scored s * g, g = 0.99 * (smallest score of the class in
    this prediction set) / (largest), so it ranks below every other box of its class and keeps its order among the
    demoted ones; nothing is deleted. The real V2X labels skip objects the sensor sees with fewer than about 6 points,
    so such a box is almost always a false positive, and ranking it last moves it to the tail of the precision-recall
    curve. Applied last (after score floors and tail copies). `counts` (box_point_counts) skips the point lookup."""
    if not spec:
        return preds
    if counts is None:
        if points_of is None:
            raise ValueError("sparse_demotion needs the frames' points: pass points_of (route_predictions.frame_points)")
        counts = box_point_counts(preds, set(spec), points_of)
    g = {}
    for c in spec:
        s = [d["score"] for v in preds.values() for d in v if d["class"] == c]
        if s and max(s) > 0:
            g[c] = 0.99 * min(s) / max(s)
    out = {}
    for f, v in preds.items():
        n = counts[f]
        out[f] = [({**d, "score": d["score"] * g[d["class"]]} if d["class"] in g and 0 <= n[j] < int(spec[d["class"]]) else d)
                  for j, d in enumerate(v)]
    return out


def sparse_select(model_dir: Path, card: dict, track, classes, grid=(2, 3, 4, 5, 6, 7, 8), n_boot: int = 200,
                  seed: int = 0, max_drop: float = 0.005) -> dict:
    """S7 (pre-registered in docs/decisions/2026-10-18-s7-visibility-rule.md): per class, the demotion threshold k of
    `grid` with the best realval-A AP (ties: the smaller k), on the final predictions without the stage. Kept only if
    the pooled A+B gain has paired-bootstrap P(gain) >= 0.9, neither split drops by more than max_drop (the 6.0 pooled
    rule), and k - 1 also gains on the pooled frames (no lone spike next to a cliff). Writes model.yaml
    `sparse_demotion` and validation/results/sparse_table.json."""
    root = data_path(track, card["data"]["realval"])
    base_card = {**card, "sparse_demotion": None}
    points_of = frame_points(track, card["data"]["realval"])
    gts, base, counts = {}, {}, {}
    for split in ("val", "valB"):
        gts[split] = sc.load_split(root, split)
        base[split] = merge_card(base_card, {n: json.loads(validation_predictions(
            model_dir.parent / card["members"][n]["model"], card, split, tag=member_tag(card["members"][n])).read_text())
            for n in used_members(card)})
        base[split] = {i: base[split].get(i, []) for i in gts[split]}
        counts[split] = box_point_counts(base[split], set(classes), points_of)
    spec, report = {}, {}
    for c in classes:
        fl0 = {s_: sc.frame_flags(base[s_], gts[s_], [c])[c] for s_ in gts}
        ap0 = {s_: sc.ap_from_flags(fl0[s_], "3d@0.5") for s_ in gts}
        if ap0["valB"] is None:
            continue
        fl, rows = {}, []
        for k in grid:
            fl[k] = {s_: sc.frame_flags(apply_sparse_demotion(base[s_], {c: k}, counts=counts[s_]), gts[s_], [c])[c] for s_ in gts}
            pg = sc.pooled_gate(fl0, fl[k], c, n_boot, seed)
            rows.append({"k": k, "A": sc.ap_from_flags(fl[k]["val"], "3d@0.5"), "B": sc.ap_from_flags(fl[k]["valB"], "3d@0.5"),
                         "pooled_delta": pg["delta"], "p_gain": pg["p_gain"], "pooled_ok": pg["ok"]})
        best = max(rows, key=lambda r: (r["A"], -r["k"]))
        prev = next((r for r in rows if r["k"] == best["k"] - 1), None)
        drops = {s_: ap0[s_] - best["A" if s_ == "val" else "B"] for s_ in gts}
        ok = (best["pooled_ok"] and all(v <= max_drop for v in drops.values())
              and (prev is None or prev["pooled_delta"] > 0))
        report[c] = {"base": {"A": ap0["val"], "B": ap0["valB"]}, "grid": rows, "chosen_k": best["k"],
                     "dA": best["A"] - ap0["val"], "dB": best["B"] - ap0["valB"], "pooled": {"delta": best["pooled_delta"],
                     "p_gain": best["p_gain"]}, "k_minus_1_pooled_delta": prev and prev["pooled_delta"], "kept": ok}
        print(c, json.dumps({k_: v for k_, v in report[c].items() if k_ != "grid"}), flush=True)
        if ok:
            spec[c] = best["k"]
    card["sparse_demotion"] = spec or None
    (model_dir / "model.yaml").write_text(yaml.safe_dump({k: v for k, v in card.items() if v is not None or k != "sparse_demotion"},
                                                         sort_keys=False))
    (model_dir / "validation" / "results" / "sparse_table.json").write_text(json.dumps(report, indent=2))
    return spec


def apply_tail_copies(preds: dict, spec: dict | None) -> dict:
    """R5 walker tail copies (model.yaml `tail_copies: {class: {r: metres, n: copies}}`): every box of the class gets
    n copies shifted by r in BEV (directions k * 2 pi / n), scored s * f with f = 0.99 * (smallest score of the class
    in this prediction set) / (largest), so every copy ranks below every original box of its class. The scorer
    matches in score order inside a frame and pools all frames by score, so the originals keep their matches and
    their place on the precision-recall curve; a copy can only match a GT box that no original matched at IoU 0.5.
    Adding boxes below all existing scores cannot lower an interpolated AP (R40 takes the maximum precision at
    recall >= r), so the knob can only help the class on any frame set; it is still gated like any other.
    S8: `min_score: t` copies only the boxes scored >= t (f still from all boxes of the class, so the copies stay below
    every original); a constant frozen on realval-A, which halves the added boxes at the same local gain."""
    if not spec:
        return preds
    out = {f: list(v) for f, v in preds.items()}
    for c, sp in spec.items():
        s = [d["score"] for v in preds.values() for d in v if d["class"] == c]
        if not s or max(s) <= 0:
            continue
        f = 0.99 * min(s) / max(s)
        r, n, t = float(sp["r"]), int(sp.get("n", 4)), float(sp.get("min_score", -np.inf))
        offs = [(r * np.cos(2 * np.pi * k / n), r * np.sin(2 * np.pi * k / n)) for k in range(n)]
        for fid, v in preds.items():
            for d in v:
                if d["class"] != c or d["score"] < t:
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
    base_card = {**card, "tail_copies": None, "sparse_demotion": None}      # tail copies come before the S7 stage
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
    tag += " + sparse demotion" if card.get("sparse_demotion") else ""
    scores = {"run": "routed (official metric)" + tag}
    for split, k in (("val", "A"), ("valB", "B")):
        preds = {}
        for n in used:
            m = card["members"][n]
            preds[n] = json.loads(validation_predictions(model_dir.parent / m["model"], card, split, tag=member_tag(m)).read_text())
        merged = merge_route(card["route"], {n: preds[n] for n in set(card["route"].values()) if n in preds})
        (out_dir / f"{D}_{split}_merged.json").write_text(json.dumps(merged))
        routed = merge_card(card, preds, frame_points(track, data))
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
        if split == "val" and _FUSE.get("early"):         # S6 judge: rank on early realval-A
            eg = {f: gts[f] for f in _FUSE["early"] if f in gts}
            out["earlyA"] = evalap.evaluate({f: F[f] for f in eg}, eg, [c])["per_class"][c]["3d@0.5"]["AP_R40"]
    return job, out


def member_weights(model_dir: Path, card: dict, n: str) -> set:
    """The checkpoints behind member n, as (model folder, ckpt) pairs: one for a detector (its TTA variant shares it), every
    seed for an S6 bag. A fusion set may not use a checkpoint twice (a bag with one of its own seeds counts that seed twice)."""
    m = card["members"][n]
    mc = yaml.safe_load((model_dir.parent / m["model"] / "model.yaml").read_text())
    if mc.get("type") == "bag":
        return {(s_, "train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth") for s_ in mc["members"]}
    return {(m["model"], m["ckpt"])}


def swap_candidates(model_dir: Path, card: dict, prior: dict, classes, bags) -> dict:
    """S7.6 bag swap (docs/decisions/2026-10-26-s7-final-revisions.md): per class, the incumbent fusion with every member
    that is a seed of an extended bag in `bags` (plain member keys), or a bag whose seeds that bag contains, replaced by
    the extended bag with the same TTA setting; one candidate per class, the incumbent's IoU. Classes without such a
    member, and candidates that would use a checkpoint twice, get none. Returns {class: member tuple}."""
    seeds_of = lambda k: set(yaml.safe_load((model_dir.parent / card["members"][k]["model"] / "model.yaml").read_text()).get("members") or [])
    sw = {}
    for b in bags:
        seeds = seeds_of(b)
        for k, m in card["members"].items():
            if k in (b, b + "_tta"):
                continue
            mc = yaml.safe_load((model_dir.parent / m["model"] / "model.yaml").read_text())
            if m["model"] in seeds or (mc.get("type") == "bag" and set(mc["members"]) <= seeds):
                sw[k] = b + "_tta" if m.get("tta") else b
    out = {}
    for c in classes:
        pz = prior.get(c)
        if not pz or not any(n in sw for n in pz["members"]):
            continue
        new = tuple(dict.fromkeys(sw.get(n, n) for n in pz["members"]))
        W = [member_weights(model_dir, card, n) for n in new]
        if len(new) >= 2 and len(set().union(*W)) == sum(len(w) for w in W):
            out[c] = new
    return out


def variant_candidates(card: dict, prior: dict, classes, tag: str) -> dict:
    """S8 view-set swap (docs/decisions/2026-10-29-s8-last-day-strategy.md): per class, the incumbent fusion with every
    TTA member that has a sibling of the same checkpoint with `tta_tag: tag` replaced by that sibling; one candidate per
    class, the incumbent's IoU. Classes without such a member get none. Returns {class: member tuple}."""
    sib = {(m["model"], m["ckpt"]): k for k, m in card["members"].items() if m.get("tta") and m.get("tta_tag") == tag}
    sw = {k: sib[(m["model"], m["ckpt"])] for k, m in card["members"].items()
          if m.get("tta") and not m.get("tta_tag") and (m["model"], m["ckpt"]) in sib}
    out = {}
    for c in classes:
        pz = prior.get(c)
        if pz and any(n in sw for n in pz["members"]):
            out[c] = tuple(sw.get(n, n) for n in pz["members"])
    return out


def fuse_select(model_dir: Path, card: dict, track, n_boot: int, seed: int, classes=None, iou_grid=(0.3, 0.5, 0.7),
                top: int = 4, workers: int = 16, max_members: int = 2, pooled: bool = False,
                late_rank=(), gate_top: int = 1, judge=(), judge_top: int = 6, pooled_rule: bool = False,
                swap_to=(), swap_variant=None) -> dict:
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
    with 24-34 persons per frame, the late ones 0.69 corrected with 10.8 per frame, like the test window's 10.2.
    judge (S6, pre-registered for LUMPI Van): realval-B is not used for those classes (its LUMPI class 6 labels are not
    vans); the member pool is the judge_top members by early-A AP (Measurement4 frames before late_a), candidates are
    ranked by early-A AP, and the first of the top gate_top that gains at least 0.01 on late-A with paired-bootstrap
    P(gain) >= 0.9 is kept (no pooled condition).
    pooled_rule (from 6.0 on, docs/decisions/README.md Section 3.2): the best candidate is kept when the pooled A+B gain
    has P(gain) >= 0.9 and neither split drops by more than 0.005; the +0.01-on-B requirement is dropped.
    swap_to (S7.6): no search; the only candidate of a class is its incumbent fusion with the extended bags swapped in
    (swap_candidates), ranked and gated against the incumbent as above; the other classes keep their fusion.
    swap_variant (S8): the same with the incumbent's TTA members replaced by their `tta_tag` siblings (variant_candidates)."""
    import gc
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
    swaps = (swap_candidates(model_dir, card, prior, classes, swap_to) if swap_to else
             variant_candidates(card, prior, classes, swap_variant) if swap_variant else None)
    if swaps is not None:
        classes = list(swaps)
        print("  swap candidates: " + (", ".join(f"{c} {'+'.join(m)}@{prior[c]['iou']}" for c, m in swaps.items()) or "none"), flush=True)

    ranked ={c: sorted(table[c]["members"], key=lambda n: -(table[c]["members"][n]["joint"] or 0.0))[:top] for c in classes}
    judge = [c for c in (judge or ()) if c in classes]
    late_ids = sc.late_a_ids(track, list(gts["val"]))
    early_ids = [f for f in gts["val"] if f not in set(late_ids)]
    early_ap = {}
    for c in judge:                                     # S6 judge: the member pool by early-A AP
        early_ap[c] = {}
        for n in table[c]["members"]:
            fl_ = sc.subset(sc.frame_flags(class_preds(n, "val", c), gts["val"], [c]), early_ids)[c]
            early_ap[c][n] = sc.ap_from_flags(fl_, "3d@0.5") or 0.0
        ranked[c] = sorted(early_ap[c], key=lambda n: -early_ap[c][n])[:judge_top]
        print(f"  {c}: judge pool by early-A " + ", ".join(f"{n} {early_ap[c][n]:.4f}" for n in ranked[c]), flush=True)
    W = {n: member_weights(model_dir, card, n) for c in classes for n in ranked[c]}
    sets = lambda c: [m for k in range(2, max_members + 1) for m in itertools.combinations(ranked[c], k)
                      if len(set().union(*(W[n] for n in m))) == sum(len(W[n]) for n in m)]   # no checkpoint used twice
    jobs = [(c, members, thr) for c in classes for members in sets(c) for thr in iou_grid]
    if swaps is not None:                               # S7.6: the swap candidate and the incumbent only
        jobs = [(c, m, prior[c]["iou"]) for c, m in swaps.items()]
        ranked = {c: list(m) for c, m in swaps.items()}
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
        _FUSE["late"] = late_ids if (c in late_rank or c in judge) else None
        _FUSE["early"] = early_ids if c in judge else None
        gc.collect(); gc.freeze()                       # S9 s9h OOM: the workers' gc no longer copies the parent's heap
        with ProcessPoolExecutor(max_workers=min(workers, len(cj)), mp_context=mp.get_context("fork")) as ex:
            for job, out in ex.map(_fuse_eval, cj):
                results[job] = out
                print(f"  {c:11s} {'+'.join(job[1]):24s} iou {job[2]}: A {out['val']:.4f} B {out['valB']:.4f}", flush=True)
        gc.unfreeze()
    fusion, report = {c: fz for c, fz in prior.items() if c not in classes}, {}
    for c in classes:
        cand = {j: r for j, r in results.items() if j[0] == c}
        if not cand:
            continue
        if c in judge:
            order = sorted(cand, key=lambda j: -(cand[j].get("earlyA") or 0.0))[:max(1, gate_top)]
        elif c in late_rank:
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
                                {s_: fl[("fused", s_)][c] for s_ in ("val", "valB")}, c, n_boot, seed) if pooled or pooled_rule else None
            if pooled_rule:                             # 6.0 pooled rule: no +0.01 on B; neither split down by > 0.005
                ok = not same and boot["delta"] >= -0.005 and dA >= -0.005
            ok_b, ok = ok, ok and (pg is None or pg["ok"])
            if c in judge:                              # S6 judge: late-A gain >= 0.01 at P >= 0.9, no B, no pooled
                bl = sc.paired_bootstrap({c: sc.subset(fl[("inc", "val")], late_ids)[c]},
                                         {c: sc.subset(fl[("fused", "val")], late_ids)[c]}, [c], n_boot, seed)[c]
                ok = ok_b = not same and bl["p_gain"] is not None and sc.class_gate(bl["delta"], bl["p_gain"], None)
                pg = {"delta": bl["delta"], "p_gain": bl["p_gain"], "ok": ok, "judge": "late-A"}
            tested.append({"members": list(pair), "iou": thr, "lateA": cand[best].get("lateA"), "earlyA": cand[best].get("earlyA"), "dB": boot["delta"],
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
                     "decision": ("fused (pooled rule passed)" if ok and pooled_rule else "fused (class gate passed)" if ok else "incumbent fusion kept (it is the best candidate)" if same
                                  else "kept (pooled A+B condition failed)" if ok_b
                                  else "incumbent fusion kept (class gate failed)" if pz else "routed member kept (class gate failed)"),
                     "search_fast_iou": {f"{'+'.join(j[1])}@{j[2]}": r for j, r in cand.items()},
                     "gate": "pooled rule (6.0)" if pooled_rule else "class gate" + (" + pooled" if pooled else ""),
                     "rank": ("early-A rank, late-A gate (judge), top %d" % max(1, gate_top)) if c in judge else
                             ("late-A, top %d through the gates" % max(1, gate_top) if c in late_rank else "joint A/B, best only"),
                     "tested": tested}
        a_best = max(cand, key=lambda j: cand[j]["val"])      # selection-bias check: the pick of realval-A alone
        report[c]["a_only_pick"] = {"members": list(a_best[1]), "iou": a_best[2], "A": cand[a_best]["val"], "B": cand[a_best]["valB"]}
        if ok:
            fusion[c] = {"members": list(pair), "weights": [1.0] * len(pair), "iou": thr,
                         "calibration": {n: mem[n]["calibration"] for n in pair if (mem.get(n) or {}).get("calibration")}}
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


def _trunc(recs: list, floor: float) -> list:
    return [{"n_gt": r["n_gt"], "scores": r["scores"][r["scores"] >= floor], "3d@0.5": r["3d@0.5"][r["scores"] >= floor]}
            for r in recs]


def floor_aps(fa: list, fb: list, floor: float, pooled: bool = False) -> dict:
    """AP on realval-A ('val'), realval-B ('valB') and, if pooled, on both pooled, after removing every box of the class
    below `floor` (per-frame flags of one class; budget_select)."""
    ta, tb = _trunc(fa, floor), _trunc(fb, floor)
    out = {"val": sc.ap_from_flags(ta, "3d@0.5"), "valB": sc.ap_from_flags(tb, "3d@0.5")}
    if pooled:
        out["pooled"] = sc.ap_from_flags(ta + tb, "3d@0.5")
    return out


def budget_select(model_dir: Path, card: dict, track, max_loss: float = 0.002, pooled: bool = False) -> dict:
    """Server-cost budget (docs/02-STRATEGY.md Section 8.3 step 6): per class, the highest score floor whose AP loss
    is at most max_loss on realval-A and on realval-B; pooled=True (S7.6) also on the pooled A+B frames, which the final
    pooled check reads: a floor can keep both split APs and still cut the last true positives under an R40 recall level
    of the pooled frames (S7.5 LUMPI Car: floor 0.01, A and B unchanged, pooled AP -0.0085). Exact and cheap: matching is greedy in score order, so
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
        merged = merge_card({**card, "budget": None, "sparse_demotion": None}, {n: json.loads(validation_predictions(
            model_dir.parent / card["members"][n]["model"], card, split, tag=member_tag(card["members"][n])).read_text())
            for n in used_members(card)})
        flags[split] = sc.frame_flags({i: merged.get(i, []) for i in gts}, gts, track.classes)
        counts[split] = (len(gts), {c: np.array([d["score"] for v in merged.values() for d in v if d["class"] == c])
                                    for c in track.classes})

    for c in track.classes:
        base = floor_aps(flags["val"][c], flags["valB"][c], 0.0, pooled)
        best, rows = 0.0, []
        for fl in FLOORS:
            ap_ = floor_aps(flags["val"][c], flags["valB"][c], fl, pooled)
            loss = {s_: (base[s_] - ap_[s_]) if base[s_] is not None else 0.0 for s_ in ap_}
            n = counts["val"][1][c]
            rows.append({"floor": fl, "A": ap_["val"], "B": ap_["valB"], **({"pooled": ap_["pooled"]} if pooled else {}),
                         "boxes_per_frame_A": float((n >= fl).sum() / counts["val"][0])})
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
            (card.get("budget") or {}).get(c), (card.get("tail_copies") or {}).get(c), (card.get("sparse_demotion") or {}).get(c))


def final_gate(model_dir: Path, card: dict, track, vs_dir: Path, n_boot: int, seed: int, judge=()) -> dict:
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
        if c in judge:                                  # S6 judge (LUMPI Van): late-A gain >= 0.01 at P >= 0.9
            late = sc.late_a_ids(track, list(gts["val"]))
            bl = sc.paired_bootstrap({c: sc.subset(fl[("inc", "val")], late)[c]}, {c: sc.subset(fl[("new", "val")], late)[c]},
                                     [c], n_boot, seed)[c]
            ok = bl["p_gain"] is not None and sc.class_gate(bl["delta"], bl["p_gain"], None)
            row = {"A": [ap[("inc", "val")], ap[("new", "val")]], "late_A_delta": bl["delta"], "p_gain": bl["p_gain"],
                   "decision": "kept (judge: late-A gain passed)" if ok else "reverted (judge: late-A gain failed)"}
        elif ap[("inc", "valB")] is None:
            ok, row = False, {"decision": "reverted: no realval-B GT"}
        else:
            boot = sc.paired_bootstrap({c: fl[("inc", "valB")][c]}, {c: fl[("new", "valB")][c]}, [c], n_boot, seed)[c]
            dA = ap[("new", "val")] - ap[("inc", "val")]
            pg = sc.pooled_gate({s_: fl[("inc", s_)][c] for s_ in ("val", "valB")}, {s_: fl[("new", s_)][c] for s_ in ("val", "valB")},
                                c, n_boot, seed)
            cn, ci = _class_config(card, c), _class_config(vs_card, c)
            only_tail = cn[:4] == ci[:4] and cn[5:] == ci[5:]           # R5: copies are the only change
            gate_b = sc.class_gate(boot["delta"], boot["p_gain"], dA, min_gain=1e-9 if only_tail else 0.01)
            ok = gate_b and pg["ok"]
            row = {"A": [ap[("inc", "val")], ap[("new", "val")]], "B": [ap[("inc", "valB")], ap[("new", "valB")]],
                   "dB": boot["delta"], "p_gain": boot["p_gain"], "dA": dA, "pooled": {"delta": pg["delta"], "p_gain": pg["p_gain"]},
                   "decision": "kept (class gate and pooled condition passed)" if ok else
                   ("reverted (pooled A+B condition failed)" if gate_b else "reverted (class gate failed)")}
        if not ok:
            route, cal, fus, bud, tail, sparse = _class_config(vs_card, c)
            need = set(fus["members"]) if fus else {route}
            missing = [n for n in need if n not in card["members"] or card["members"][n] != vs_card["members"][n]]
            if missing:
                raise SystemExit(f"{c}: incumbent members {missing} are not the same in {model_dir.name}")
            card["route"][c] = route
            for key, val in (("calibration", cal), ("fusion", fus), ("budget", bud), ("tail_copies", tail), ("sparse_demotion", sparse)):
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
    ap.add_argument("mode", choices=["select", "merge", "calibrate", "validate", "fuse", "budget", "tail", "gate", "sparse", "extend"])
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
    ap.add_argument("--judge", nargs="*", default=[], help="fuse/gate (S6): classes judged on early-A (rank) and late-A (gate) "
                                                          "instead of realval-B (LUMPI Van, whose B labels are not vans)")
    ap.add_argument("--gate-top", type=int, default=1, help="fuse (R5): candidates of a --late-rank class tested through the gates")
    ap.add_argument("--vs", default=None, help="gate: the confirmed portfolio to compare the final predictions with")
    ap.add_argument("--pooled", action="store_true", help="select/fuse/calibrate: the class gate also needs a gain on the pooled "
                                                          "A+B frames with P(gain) >= 0.9 (docs/decisions/README.md Section 3.2, R3 on); "
                                                          "budget (S7.6): the floor's AP loss is also bounded on the pooled frames")
    ap.add_argument("--swap-to", nargs="*", default=[], help="fuse (S7.6): extended bags (plain member keys) swapped into each "
                                                             "incumbent fusion in place of their seeds or 3-seed bag; no search")
    ap.add_argument("--swap-variant", default=None, help="fuse (S8): the incumbent fusions with their TTA members swapped "
                    "for the siblings with this tta_tag (e.g. tta12), one candidate per class")
    ap.add_argument("--pooled-rule", action="store_true", help="fuse: the 6.0 pooled rule (pooled A+B P(gain) >= 0.9, neither split "
                                                                 "down by more than 0.005, no +0.01 on B; docs/decisions/README.md 3.2)")
    ap.add_argument("--frames", default="kit", help="merge: frames whose points the S7 sparse stage counts ('kit' or a dataset)")
    ap.add_argument("--grid", type=int, nargs="*", default=[2, 3, 4, 5, 6, 7, 8], help="sparse: thresholds k to try")
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    if a.mode == "sparse":
        sparse_select(model_dir, card, track, a.classes or list(track["classes_with_test_gt"]), tuple(a.grid), a.bootstrap, a.seed)
        _, card, _ = model_info(model_dir)
        validate(model_dir, card, track, registry_run="routed + fusion + budget + tail copies + sparse demotion")
        return
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
    if a.mode == "extend":
        extend_table(model_dir, card, track)
        return
    if a.mode == "budget":
        budget_select(model_dir, card, track, pooled=a.pooled)
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
        res = final_gate(model_dir, card, track, Path(a.vs).resolve(), a.bootstrap, a.seed, judge=a.judge)
        if res["reverted"]:
            _, card, _ = model_info(model_dir)
            validate(model_dir, card, track, registry_run="routed + fusion + budget + final gate")
        return
    if a.mode == "fuse":
        fuse_select(model_dir, card, track, a.bootstrap, a.seed, a.classes, max_members=a.max_members, pooled=a.pooled,
                    late_rank=a.late_rank, gate_top=a.gate_top, judge=a.judge, pooled_rule=a.pooled_rule, swap_to=a.swap_to,
                    swap_variant=a.swap_variant)
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
    out = merge_card(card, preds, frame_points(track, a.frames) if card.get("sparse_demotion") else None)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out))
    print(f"{len(out)} frames, {sum(len(v) for v in out.values())} boxes -> {a.out}")


if __name__ == "__main__":
    main()
