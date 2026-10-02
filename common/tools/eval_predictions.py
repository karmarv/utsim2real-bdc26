#!/usr/bin/env python
"""Score a predictions.json against the labels of a dataset split with the challenge-style evaluator.

    python common/tools/eval_predictions.py --track v2x --pred predictions.json --data pcdet/realval-v1 --split val \
        --out model-v2x-track/pointpillars-ut/validation/results/realval-v1_ep40.json [--model pointpillars-ut --run run1]
Only frames present in both the split and the predictions are scored. Optionally appends a registry row.
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
    a = ap.parse_args()
    t = load_track(a.track)
    root = data_path(t, a.data)
    preds = json.loads(Path(a.pred).read_text())
    ids = [i for i in (root / "ImageSets" / f"{a.split}.txt").read_text().split() if i in preds]
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
    if a.model:
        registry.append(t, kind="eval", model=a.model, run=a.run, data_version=a.data, metric_source=f"{a.data}:{a.split}",
                        **{"mAP_3d_0.5_R40": f"{res['mAP_challenge_3d_0.5_R40']:.4f}"}, per_class=json.dumps(summary),
                        notes="mAP over the classes with test GT")


if __name__ == "__main__":
    main()
