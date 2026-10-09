#!/usr/bin/env python
"""Scorecard of a model on real validation (docs/decisions/README.md Section 3.1) and paired bootstrap against another.

    python common/tools/scorecard.py model-v2x-track/routed-g1
    python common/tools/scorecard.py model-v2x-track/routed-g2 --vs model-v2x-track/routed-g1 --bootstrap 200
    python common/tools/scorecard.py model-lumpi-track/routed-g1 --realism       # exact realism of the latest zip

Metrics: realval-A and realval-B challenge mAP (3D@0.5 R40), late-A (track.yaml `late_a`), B/A ratio, per-class
B AP, BEV-3D gap and 3D@0.7 on B, realism R (mean of held-out proxies 4-5), the combined estimate with the B
mAP, the server cost recorded by check_submission.py --official, and the leaderboard record if one exists.
Inputs are the post-processed validation predictions written by tune_and_eval.sh (routed models: by
route_predictions.py merge). With --vs, per-class deltas come with a paired frame bootstrap and the class gate.
Writes <model>/validation/results/scorecard.json and prints a row of the progression tracker.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from _common import data_path, model_info, validation_predictions
from bdc26 import scorecard as sc

PROXIES = ("pcdet/realism-proxy-4", "pcdet/realism-proxy-5")


def latest_submission(model_dir: Path) -> Path | None:
    subs = sorted((model_dir / "submissions").glob("*_*/manifest.json"))
    return subs[-1].parent if subs else None


def realism_exact(track, zip_path: Path) -> dict:
    from bdc26 import realism
    from score_realism import load_frames
    syn = load_frames(track, str(zip_path))
    res = {r: realism.score(syn, load_frames(track, r), track.name, exact_emd=True)["R"] for r in PROXIES}
    return {"per_proxy": res, "R": float(np.mean(list(res.values()))), "source": f"{zip_path} (exact EMD)"}


def evaluate_model(model_dir: Path, card: dict, track, gts_by_split: dict, exact) -> dict:
    flags = {}
    for split, gts in gts_by_split.items():
        flags[split] = sc.flags_for(validation_predictions(model_dir, card, split), gts, track.classes, exact)
    return flags


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir")
    ap.add_argument("--vs", default=None, help="baseline model folder for deltas and the class gate")
    ap.add_argument("--bootstrap", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--realism", action="store_true", help="recompute the exact realism of the latest submission zip")
    ap.add_argument("--fast", action="store_true", help="float32 IoU (OpenPCDet op) instead of the exact polygons")
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    exact = False if a.fast else None
    root = data_path(track, card["data"]["realval"])
    gts = {"val": sc.load_split(root, "val"), "valB": sc.load_split(root, "valB")}
    cwg = list(track["classes_with_test_gt"])
    flags = evaluate_model(model_dir, card, track, gts, exact)
    A, B = sc.summarize(flags["val"], cwg), sc.summarize(flags["valB"], cwg)
    late = sc.late_a_ids(track, list(gts["val"]))
    L = sc.summarize(sc.subset(flags["val"], late), cwg) if late else None

    out_path = model_dir / "validation" / "results" / "scorecard.json"
    prev = json.loads(out_path.read_text()) if out_path.exists() else {}
    sub = latest_submission(model_dir)
    man = json.loads((sub / "manifest.json").read_text()) if sub else {}
    realism = prev.get("realism")
    if a.realism and sub and (sub / "submission.zip").exists():
        realism = realism_exact(track, sub / "submission.zip")
    elif realism is None and man.get("local_scores", {}).get("realism_R_heldout"):
        r = {k: v for k, v in man["local_scores"]["realism_R_heldout"].items() if k.startswith("pcdet/")}
        realism = {"per_proxy": r, "R": float(np.mean(list(r.values()))), "source": "manifest (capped EMD; run --realism for exact)"}
    lb = None
    if sub:
        recs = sorted(sub.glob("codabench_*.json"))
        if recs:
            rec = json.loads(recs[-1].read_text())
            s = rec["scores"]
            lb = {"id": rec["codabench_submission_id"], "combined": s["score_combined"], "mAP": s["mAP_3d_0.5_R40"],
                  "R": s["score_realism"], "per_class": {k.removeprefix("AP_3d_0.5_R40_"): v for k, v in s.items()
                                                        if k.startswith("AP_3d_0.5_R40_")}}
    b_map, a_map = B["mAP"]["3d@0.5"], A["mAP"]["3d@0.5"]
    card_out = {
        "model": card["name"], "track": track.name, "strategy": card.get("strategy"), "time": time.strftime("%Y-%m-%d %H:%M"),
        "iou": "fast float32" if a.fast else "exact (official)",
        "A_mAP": a_map, "B_mAP": b_map, "lateA_mAP": L["mAP"]["3d@0.5"] if L else None, "lateA_frames": len(late),
        "B_over_A": b_map / a_map if a_map else None,
        "B_bev_3d_gap": B["bev_3d_gap"], "B_3d07_mAP": B["mAP"]["3d@0.7"], "A_bev_3d_gap": A["bev_3d_gap"],
        "per_class": {c: {"A": A["per_class"][c]["3d@0.5"], "B": B["per_class"][c]["3d@0.5"],
                          "lateA": L["per_class"][c]["3d@0.5"] if L else None,
                          "B_bev": B["per_class"][c]["bev@0.5"], "B_3d07": B["per_class"][c]["3d@0.7"],
                          "n_gt_A": A["per_class"][c]["n_gt"], "n_gt_B": B["per_class"][c]["n_gt"]} for c in track.classes},
        "realism": realism,
        "estimate_B": sc.combined_estimate(b_map, realism["R"]) if realism else None,
        "estimate_A": sc.combined_estimate(a_map, realism["R"]) if realism else None,
        "server_check": man.get("official_local_eval"),
        "leaderboard": lb,
    }
    if lb and b_map:
        card_out["leaderboard"]["LB_over_B"] = lb["mAP"] / b_map
    if a.vs:
        vdir, vcard, vtrack = model_info(a.vs)
        assert vtrack.name == track.name
        vflags = evaluate_model(vdir, vcard, track, gts, exact)
        boot = {s: sc.paired_bootstrap(vflags[s], flags[s], cwg, a.bootstrap, a.seed) for s in ("val", "valB")}
        gate = {c: sc.class_gate(boot["valB"][c]["delta"], boot["valB"][c]["p_gain"], boot["val"].get(c, {}).get("delta"))
                for c in boot["valB"] if c != "mAP"}
        card_out["vs"] = {"model": vcard["name"], "bootstrap": a.bootstrap, "A": boot["val"], "B": boot["valB"], "class_gate": gate}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(card_out, indent=2))

    f = lambda v, d=3: "-" if v is None else f"{v:.{d}f}"
    chk = card_out["server_check"] or {}
    row = (f"| {card_out['strategy'] or '?'} | {track.name.split('-')[0].upper()} | {f(a_map)} | {f(b_map)} | {f(card_out['B_over_A'], 2)} | "
           f"{f(B['bev_3d_gap'])} | {f(B['mAP']['3d@0.7'])} | {f(realism['R'] if realism else None)} | {f(card_out['estimate_B'])} | "
           f"{(str(round(chk['wall_s'])) + ' s') if chk.get('wall_s') else '-'} | {f(lb['combined'], 4) if lb else '-'} | "
           f"{f(lb['mAP'], 4) if lb else '-'} | {f(lb['R'], 4) if lb else '-'} | {f(card_out['leaderboard'].get('LB_over_B') if lb else None, 2)} |")
    print(json.dumps({k: card_out[k] for k in ("model", "A_mAP", "B_mAP", "lateA_mAP", "B_over_A", "B_bev_3d_gap", "B_3d07_mAP",
                                               "estimate_B")}, indent=2))
    print("per class (A / B / late-A):", {c: (f(v["A"]), f(v["B"]), f(v["lateA"])) for c, v in card_out["per_class"].items()})
    if a.vs:
        print(f"vs {card_out['vs']['model']} (B, paired bootstrap x{a.bootstrap}):")
        for c, v in card_out["vs"]["B"].items():
            print(f"  {c:11s} dB {v['delta']:+.4f}  P(gain) {f(v['p_gain'], 2)}  CI90 {v['ci90']}  gate {card_out['vs']['class_gate'].get(c, '')}")
    print("tracker row:\n" + row)
    print(f"-> {out_path}")


if __name__ == "__main__":
    sys.exit(main())
