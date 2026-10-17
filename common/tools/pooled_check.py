#!/usr/bin/env python
"""Pooled condition on the final predictions (the pooled half of the final gate, route_predictions.final_gate):
for each class, the paired bootstrap of the AP gain of a routed model over a reference on the realval-A and realval-B
frames pooled into one set (bdc26.scorecard.pooled_gate, P(gain) >= 0.9), from the two models' saved final
validation predictions (validation/output/<data>_<split>_routed.json). Read-only.

    python common/tools/pooled_check.py model-v2x-track/routed-g8b --vs model-v2x-track/routed-g7 [--classes vehicle truck]
"""
import argparse
import json

from _common import data_path, model_info, validation_predictions
from bdc26 import scorecard as sc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir")
    ap.add_argument("--vs", required=True)
    ap.add_argument("--classes", nargs="*", default=None)
    ap.add_argument("--bootstrap", type=int, default=200)
    a = ap.parse_args()
    md, card, track = model_info(a.model_dir)
    vd, vcard, _ = model_info(a.vs)
    root = data_path(track, card["data"]["realval"])
    classes = a.classes or list(track["classes_with_test_gt"])
    gts = {s: sc.load_split(root, s) for s in ("val", "valB")}
    flags = {}
    for name, d, c_ in (("new", md, card), ("inc", vd, vcard)):
        flags[name] = {s: sc.frame_flags(json.loads(validation_predictions(d, c_, s).read_text()), gts[s], classes) for s in gts}
    out = {}
    for c in classes:
        r = sc.pooled_gate({s: flags["inc"][s][c] for s in gts}, {s: flags["new"][s][c] for s in gts}, c, n=a.bootstrap)
        out[c] = r
        print(f"{c:12s} pooled delta {r['delta']:+.4f}  P(gain) {r['p_gain']:.2f}  {'passes' if r['ok'] else 'fails'}")
    return out


if __name__ == "__main__":
    main()
