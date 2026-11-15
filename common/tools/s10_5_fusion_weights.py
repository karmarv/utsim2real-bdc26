#!/usr/bin/env python
"""Release 10.5 attempt C2 (record docs/decisions/2026-11-14-s10-10.5-final-push.md Section 11; rule fixed before any
result): per-class member weights of the weighted box fusion on a scored card. Every fusion of the parent uses equal
weights; for each fused class that is not frozen (LUMPI: Person, Car, Truck), a small grid of weight vectors is scored
on realval A and B through merge_card (every stage of the card applied), and the best by pooled A+B AP is kept only if
against the parent: pooled paired-bootstrap P(gain) >= 0.97 (stricter than 0.9: the best of several candidates),
neither split drops by more than 0.005, and (LUMPI) late-A does not drop. Members, sets, IoUs and every other stage
are unchanged.
    python common/tools/s10_5_fusion_weights.py lumpi routed-s10-5-l9 routed-s10-5-l12w --candidate L12w
Writes the new card (exit 0) or reports that no class passes (exit 3); validation/results/fusion_weights.json.
"""
import argparse
import copy
import itertools
import multiprocessing as mp
import json
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import data_path, member_tag, validation_predictions  # noqa: E402
from bdc26 import scorecard as sc  # noqa: E402
from bdc26.config import load_track  # noqa: E402
from route_predictions import merge_card, used_members  # noqa: E402

REC = "docs/decisions/2026-11-14-s10-10.5-final-push.md"
FROZEN = {"lumpi": {"Bicycle", "Motorcycle", "Bus"}, "v2x": set()}
P_MIN = 0.97
_SCORE = None


def _run(job):
    return _SCORE(job)


def grid(n: int) -> list:
    """Weight vectors for an n-member fusion: one member up (2.0, 1.5) or down (0.5, 0.67) against the others at 1."""
    out = []
    for i, w in itertools.product(range(n), (2.0, 1.5, 0.67, 0.5)):
        v = [1.0] * n
        v[i] = w
        out.append(v)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track", choices=["lumpi", "v2x"])
    ap.add_argument("parent")
    ap.add_argument("name")
    ap.add_argument("--candidate", required=True)
    a = ap.parse_args()
    T = load_track(f"{a.track}-track")
    td = T.model_dir
    parent = yaml.safe_load((td / a.parent / "model.yaml").read_text())
    root = data_path(T, parent["data"]["realval"])
    gts = {sp: sc.load_split(root, sp) for sp in ("val", "valB")}
    late = sc.late_a_ids(T, list(gts["val"]))
    preds = {sp: {n: json.loads(validation_predictions(td / parent["members"][n]["model"], parent, sp,
                                                       tag=member_tag(parent["members"][n])).read_text())
                  for n in used_members(parent)} for sp in ("val", "valB")}
    classes = [c for c in (parent.get("fusion") or {}) if c in list(T["classes_with_test_gt"]) and c not in FROZEN[a.track]]

    def one_class(card, c):
        """The card reduced to class c (its route and fusion entry, every stage kept) and the members' boxes of c: exact
        for c, since no stage moves boxes into Person, Car or Truck (cross-class copies go to Bicycle and Bus)."""
        k = copy.deepcopy(card)
        k["route"] = {c: card["route"][c]}
        k["fusion"] = {c: card["fusion"][c]} if c in (card.get("fusion") or {}) else {}
        return k

    pc = {c: {sp: {n: {f: [d for d in v if d["class"] == c] for f, v in preds[sp][n].items()} for n in preds[sp]}
              for sp in ("val", "valB")} for c in classes}

    def flags(card, c):
        out = {}
        for sp in ("val", "valB"):
            m = merge_card(one_class(card, c), pc[c][sp])
            out[sp] = sc.frame_flags({i: [d for d in m.get(i, []) if d["class"] == c] for i in gts[sp]}, gts[sp], [c])[c]
        return out

    def score(job):
        c, w = job
        card = copy.deepcopy(parent)
        if w is not None:
            card["fusion"][c]["weights"] = w
        return job, flags(card, c)

    jobs = [(c, None) for c in classes] + [(c, w) for c in classes for w in grid(len(parent["fusion"][c]["members"]))]
    global _SCORE
    _SCORE = score
    with mp.get_context("fork").Pool(min(12, len(jobs))) as pool:
        res = dict(((c, None if w is None else tuple(w)), f) for (c, w), f in pool.imap_unordered(_run, jobs))

    rows, keep, new = {}, {}, copy.deepcopy(parent)
    for c in classes:
        base = res[(c, None)]
        best = None
        for w in grid(len(parent["fusion"][c]["members"])):
            f = res[(c, tuple(w))]
            pg = sc.pooled_gate(base, f, c)
            dA = (sc.ap_from_flags(f["val"], "3d@0.5") or 0) - (sc.ap_from_flags(base["val"], "3d@0.5") or 0)
            dB = (sc.ap_from_flags(f["valB"], "3d@0.5") or 0) - (sc.ap_from_flags(base["valB"], "3d@0.5") or 0)
            dL = None
            if late:
                dL = ((sc.ap_from_flags(sc.subset({c: f["val"]}, late)[c], "3d@0.5") or 0)
                      - (sc.ap_from_flags(sc.subset({c: base["val"]}, late)[c], "3d@0.5") or 0))
            r = {"weights": w, "delta_A": dA, "delta_B": dB, "delta_lateA": dL, "pooled_delta": pg["delta"],
                 "p_gain": pg["p_gain"]}
            print(f"{c:8s} {w}  A {dA:+.4f} B {dB:+.4f} late-A {'' if dL is None else f'{dL:+.4f}'} pooled "
                  f"{(pg['delta'] or 0):+.4f} P {pg['p_gain'] if pg['p_gain'] is not None else float('nan'):.2f}", flush=True)
            if best is None or (pg["delta"] or -9) > (best["pooled_delta"] or -9):
                best = r
        ok = bool(best and (best["pooled_delta"] or 0) > 0 and (best["p_gain"] or 0) >= P_MIN and best["delta_A"] >= -0.005
                  and best["delta_B"] >= -0.005 and (best["delta_lateA"] is None or c != "Person" or best["delta_lateA"] >= 0))
        rows[c] = {"best": best, "rule": "PASS" if ok else "FAIL"}
        print(f"{c:8s} best {best['weights']}: {'PASS' if ok else 'FAIL'}", flush=True)
        if ok:
            keep[c] = best["weights"]
            new["fusion"][c]["weights"] = best["weights"]
    dst = td / a.name
    for sub in ("validation/output", "validation/results", "test/output", "train"):
        (dst / sub).mkdir(parents=True, exist_ok=True)
    res = {"parent": a.parent, "rule": f"best weight vector per class; pooled P(gain) >= {P_MIN}, A and B drop <= 0.005, "
           "Person late-A >= 0 (fixed before results)", "classes": rows, "kept": keep}
    (dst / "validation" / "results" / "fusion_weights.json").write_text(json.dumps(res, indent=1, default=float))
    if not keep:
        print("no class passes: no system")
        return 3
    for f in ("make_submission.sh", "synthetic_ids.txt"):
        shutil.copy2(td / a.parent / "test" / f, dst / "test" / f)
    new.update({"name": a.name, "strategy": "S10-5", "candidate": a.candidate, "derived_from": a.parent,
                "status": f"S10-5 {a.candidate}: {a.parent} with fusion weights {keep} ({REC} Section 11, attempt C2)",
                "notes": f"S10-5 {a.candidate} ({REC} Section 11): {a.parent} unchanged except the fusion weights of "
                         f"{', '.join(keep)} (rule: pooled P >= {P_MIN}, splits not down > 0.005, Person late-A not down).\n"})
    (dst / "model.yaml").write_text(yaml.safe_dump(new, sort_keys=False))
    print("kept:", keep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
