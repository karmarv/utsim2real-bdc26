#!/usr/bin/env python
"""S9 rule 3 (docs/decisions/2026-11-02-s9-clean-twin-plan.md Section 8): the member check of a new member against its
family's incumbent before it may enter a portfolio search. Per class and variant (plain, 8-view TTA): the AP on
realval-A and realval-B and the paired bootstrap P(gain) on the pooled A+B frames (bdc26.scorecard.pooled_gate), from
the members' tuned validation predictions (a seed bag, model.yaml `type: bag`, from its fused predictions written by
common/tools/bag_predictions.py). A member passes on a class with P(gain) >= 0.9 and neither split down by more than
0.005 (the 6.0 pooled rule). Read-only; prints one line per class and a PASS/FAIL line.

    python common/tools/s9_member_check.py lumpi voxelrcnn-ros-g1v6 voxelrcnn-ros-g1v4
    python common/tools/s9_member_check.py v2x bag-voxelrcnn-ros-g1v6 bag-voxelrcnn-ros-g1v5
"""
import argparse
import json

import yaml

from _common import data_path, load_track
from bdc26 import scorecard as sc
from bdc26.evalap import evaluate

PRED = "validation/output/pcdet_realval-v1_{split}_{run}_checkpoint_epoch_40{x}.json"


def run_of(model_dir) -> str:
    """'bag' for a seed bag (its fused predictions), 'run1' for a trained member."""
    return "bag" if yaml.safe_load((model_dir / "model.yaml").read_text()).get("type") == "bag" else "run1"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track")
    ap.add_argument("new")
    ap.add_argument("incumbent")
    ap.add_argument("--variants", nargs="*", default=["", "_tta"])
    ap.add_argument("--bootstrap", type=int, default=200)
    a = ap.parse_args()
    t = load_track(a.track)
    root = data_path(t, "pcdet/realval-v1")
    classes = list(t["classes_with_test_gt"])
    gts = {s: sc.load_split(root, s) for s in ("val", "valB")}
    passed = []
    for x in a.variants:
        preds = {m: {s: json.loads((t.model_dir / m / PRED.format(split=s, run=run_of(t.model_dir / m), x=x)).read_text())
                     for s in gts}
                 for m in (a.new, a.incumbent)}
        ap_ = {m: {s: evaluate({i: preds[m][s].get(i, []) for i in gts[s]}, gts[s], classes)["per_class"] for s in gts}
               for m in preds}
        flags = {m: {s: sc.frame_flags(preds[m][s], gts[s], classes) for s in gts} for m in preds}
        for c in classes:
            r = sc.pooled_gate({s: flags[a.incumbent][s][c] for s in gts}, {s: flags[a.new][s][c] for s in gts}, c,
                               n=a.bootstrap)
            d = {s: (ap_[a.new][s][c]["3d@0.5"] or {}).get("AP_R40", 0.0) - (ap_[a.incumbent][s][c]["3d@0.5"] or {}).get("AP_R40", 0.0)
                 for s in gts}
            ok = r["p_gain"] >= 0.9 and min(d.values()) >= -0.005
            if ok:
                passed.append(f"{c}{x}")
            new_a = (ap_[a.new]["val"][c]["3d@0.5"] or {}).get("AP_R40", 0.0)
            new_b = (ap_[a.new]["valB"][c]["3d@0.5"] or {}).get("AP_R40", 0.0)
            print(f"{c:11s}{x or '_plain':6s} A {new_a:.3f} ({d['val']:+.3f})  B {new_b:.3f} ({d['valB']:+.3f})  "
                  f"pooled {r['delta']:+.4f} P {r['p_gain']:.2f}  {'pass' if ok else '-'}")
    print(("PASS " + " ".join(passed)) if passed else "FAIL")


if __name__ == "__main__":
    main()
