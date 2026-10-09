#!/usr/bin/env python
"""Score a predictions.json against the labels of a dataset split with the challenge-style evaluator.

    python common/tools/eval_predictions.py --track v2x --pred predictions.json --data pcdet/realval-v1 --split val \
        --out model-v2x-track/pointpillars-ut/validation/results/realval-v1_ep40.json [--model pointpillars-ut --run run1]
Only frames present in both the split and the predictions are scored. Optionally appends a registry row.

    # a subset of the split (one frame id per line), e.g. the late-A frames of docs/decisions/README.md Section 3.1
    ... --frames-from late_a.txt
    # error breakdowns (bdc26.diagnostics): box errors of BEV-matched pairs, AP by range band, recall by points in box
    ... --breakdown          # writes <out stem>_breakdown.json
"""
import argparse
import json
from pathlib import Path

from _common import data_path, load_track
from bdc26 import registry
from bdc26.evalap import evaluate
from bdc26.pcdet_export import read_labels_txt


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--track", required=True)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--split", default="val")
    ap.add_argument("--out", default=None)
    ap.add_argument("--model", default=None, help="log a registry row for this model")
    ap.add_argument("--run", default="")
    ap.add_argument("--frames-from", default=None, help="score only the frame ids listed in this file")
    ap.add_argument("--breakdown", action="store_true", help="also write box-error, range and points breakdowns")
    a = ap.parse_args()
    t = load_track(a.track)
    root = data_path(t, a.data)
    preds = json.loads(Path(a.pred).read_text())
    ids = [i for i in (root / "ImageSets" / f"{a.split}.txt").read_text().split() if i in preds]
    if a.frames_from:
        keep = set(Path(a.frames_from).read_text().split())
        ids = [i for i in ids if i in keep]
    gts = {i: read_labels_txt(root / "labels" / f"{i}.txt") for i in ids}
    res = evaluate({i: preds[i] for i in ids}, gts, t.classes)
    res["n_frames"], res["data"], res["split"] = len(ids), a.data, a.split
    summary = {c: (v["3d@0.5"]["AP_R40"] if v["3d@0.5"] else None) for c, v in res["per_class"].items()}
    # the challenge averages over the classes that have test GT (LUMPI: Unknown has none)
    scored = [c for c in t["classes_with_test_gt"] if summary.get(c) is not None]
    res["mAP_challenge_3d_0.5_R40"] = float(sum(summary[c] for c in scored) / max(len(scored), 1))
    res["challenge_classes"] = scored
    print(json.dumps({"mAP_challenge_3d_0.5_R40": res["mAP_challenge_3d_0.5_R40"],
                      "mAP_3d_0.5_R40": res["mAP_3d_0.5_R40"], "mAP_bev_0.5_R40": res["mAP_bev_0.5_R40"],
                      "per_class_3d_0.5": summary, "n_frames": len(ids)}, indent=2))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=2))
    if a.breakdown:
        import numpy as np
        from bdc26 import diagnostics as dg
        bins = t.cfg.get("diagnostics", {"range_bins": [0, 15, 30, 45], "point_bins": [1, 10, 30, 100]})
        sub = {i: preds[i] for i in ids}
        bd = {"box_errors": {}, "ap_by_range": dg.ap_by_range(sub, gts, scored, bins["range_bins"]),
              "recall_by_points": dg.recall_by_points(sub, gts, lambda f: np.load(root / "points" / f"{f}.npy"), scored,
                                                      bins["point_bins"])}
        for c in scored:
            bd["box_errors"][c] = dg.error_table(dg.box_errors(dg.matched_pairs(sub, gts, c)), bins["range_bins"])
        bpath = Path(a.out).with_name(Path(a.out).stem + "_breakdown.json") if a.out else Path("breakdown.json")
        bpath.parent.mkdir(parents=True, exist_ok=True)
        bpath.write_text(json.dumps(bd, indent=2))
        print(f"breakdown -> {bpath}")
    if a.model:
        registry.append(t, kind="eval", model=a.model, run=a.run, data_version=a.data, metric_source=f"{a.data}:{a.split}",
                        **{"mAP_3d_0.5_R40": f"{res['mAP_challenge_3d_0.5_R40']:.4f}"}, per_class=json.dumps(summary),
                        notes="mAP over the classes with test GT")


if __name__ == "__main__":
    main()
