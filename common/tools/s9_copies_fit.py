#!/usr/bin/env python
"""S9 rule 1(b) (docs/decisions/2026-11-02-s9-clean-twin-plan.md Section 15): the walker tail-copy threshold of a routed
model, re-derived for its own route. t = the lowest realval-A quantile in --ladder of the route's pre-copy scores of the
class whose kit prediction keeps at most --max-boxes boxes in total (the box count of a zip the server has scored in
time; box counts are load-independent, kit wall times are not). If no rung fits, the class gets no copies. Copies are
scored below every original box, so the threshold only trades local AP for boxes. Needs the members' kit predictions
in <model>/test/output/predictions_<member>.json (written by test/make_submission.sh).

    python common/tools/s9_copies_fit.py lumpi model-lumpi-track/routed-g13 --max-boxes 38466 [--write]
"""
import argparse
import json

import numpy as np
import yaml

from _common import data_path, load_track
from bdc26 import scorecard as sc
from route_predictions import apply_tail_copies, member_tag, merge_card, used_members, validation_predictions


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track")
    ap.add_argument("model")
    ap.add_argument("--max-boxes", type=int, required=True)
    ap.add_argument("--cls", default="Person")
    ap.add_argument("--ladder", type=float, nargs="*", default=[0.95, 0.96, 0.97, 0.98, 0.99])
    ap.add_argument("--write", action="store_true", help="write the chosen threshold into model.yaml")
    a = ap.parse_args()
    t = load_track(a.track)
    m = t.model_dir / a.model.split("/")[-1]
    card = yaml.safe_load((m / "model.yaml").read_text())
    spec = dict((card.get("tail_copies") or {}).get(a.cls) or {"r": 0.2, "n": 4})
    base = {**card, "tail_copies": {k: v for k, v in (card.get("tail_copies") or {}).items() if k != a.cls}}
    used = used_members(card)
    gts = {s: sc.load_split(data_path(t, card["data"]["realval"]), s) for s in ("val", "valB")}
    pre = {s: merge_card(base, {n: json.loads(validation_predictions(m.parent / card["members"][n]["model"], card, s,
                                                                     tag=member_tag(card["members"][n])).read_text())
                                for n in used}) for s in gts}
    pre["kit"] = merge_card(base, {n: json.loads((m / "test" / "output" / f"predictions_{n}.json").read_text()) for n in used})
    scores = np.array([d["score"] for v in pre["val"].values() for d in v if d["class"] == a.cls])

    def ap_of(preds, s):
        fl = sc.frame_flags({i: preds.get(i, []) for i in gts[s]}, gts[s], [a.cls])[a.cls]
        return sc.ap_from_flags(fl, "3d@0.5")

    rows, chosen = [], None
    for q in [None] + sorted(a.ladder):
        tq = None if q is None else round(float(np.quantile(scores, q)), 4)
        sp = None if tq is None else {a.cls: {**spec, "min_score": tq}}
        out = {s: apply_tail_copies(pre[s], sp) for s in pre}
        nk = sum(len(v) for v in out["kit"].values())
        rows.append({"q": q, "t": tq, "A": ap_of(out["val"], "val"), "B": ap_of(out["valB"], "valB"), "kit_boxes": nk})
        if q is not None and chosen is None and nk <= a.max_boxes:
            chosen = rows[-1]
    for r in rows:
        print(f"q {r['q'] if r['q'] is not None else 'none':>5}  t {r['t'] if r['t'] is not None else '-':>7}  "
              f"{a.cls} A {r['A']:.4f} B {r['B']:.4f}  kit boxes {r['kit_boxes']}")
    old = spec.get("min_score")
    if chosen is None:
        new_tc = base["tail_copies"]
        verdict = f"SET no {a.cls} copies (no rung keeps the kit at or under {a.max_boxes} boxes)"
    else:
        new_tc = {**base["tail_copies"], a.cls: {**spec, "min_score": chosen["t"]}}
        verdict = (f"UNCHANGED t={old}" if chosen["t"] == old else f"SET t={chosen['t']} (q{chosen['q']}, "
                   f"{chosen['kit_boxes']} kit boxes, at most {a.max_boxes}; was {old})")
    if a.write and not verdict.startswith("UNCHANGED"):
        card["tail_copies"] = new_tc
        (m / "model.yaml").write_text(yaml.safe_dump(card, sort_keys=False))
    print(verdict)


if __name__ == "__main__":
    main()
