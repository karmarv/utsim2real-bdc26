#!/usr/bin/env python
"""S10 rule 14 (docs/decisions/2026-11-08-s10-clean-final-plan.md Section 15.12): the grouped final gate of a new
version against the best scored clean version, on the FINAL validation predictions of both
(validation/output/<data>_<split>_routed.json), realval A and B pooled.

Reports the frame-level paired bootstrap (as rules 2 and 10), the grouped bootstrap (V2X scenarios, LUMPI 100 s
recording windows), leave-one-group-out deltas, the per-class deltas and the share of the gain carried by classes the
test window cannot validate (LUMPI Bicycle, Motorcycle, Bus; the s9iu and S5 lessons). The level follows the
margins adopted on 2026-11-08 and calibrated on 13 past uploads with known leaderboard outcomes (Section 15.12):
  GO        mAP delta > 0, grouped P(gain) >= 0.75, every leave-one-group-out delta >= -margin (0.002 mAP), and the
            classes the test window cannot validate carry less than half of the gain
  JUDGEMENT mAP delta > 0 and grouped P(gain) >= 0.5, but one of the GO conditions fails: the entrant decides with the
            nuanced assessment (the leaderboard history of similar changes, Section 15.12)
  NO-GO     mAP delta <= 0 or grouped P(gain) < 0.5
Read-only. Usage:
    python common/tools/s10_grouped_gate.py model-lumpi-track/routed-c1 model-lumpi-track/routed-c0 [--margin 0.002]
"""
import argparse
import json
from pathlib import Path

import numpy as np

from _common import data_path, model_info
from bdc26 import scorecard as sc

RARE = {"lumpi": ("Bicycle", "Motorcycle", "Bus")}


def pooled_flags(model_dir: Path, card: dict, track, gts: dict) -> dict:
    D = card["data"]["realval"].replace("/", "_")
    fl = {s_: sc.flags_for(model_dir / "validation" / "output" / f"{D}_{s_}_routed.json", gts[s_], list(track.classes))
          for s_ in ("val", "valB")}
    return {c: fl["val"][c] + fl["valB"][c] for c in fl["val"]}, fl


def gate(new_dir: Path, ref_dir: Path, n: int = 1000, seed: int = 0, margin: float = 0.002, block: int = 1000,
         go_p: float = 0.75, min_p: float = 0.5) -> dict:
    _, card, track = model_info(new_dir)
    _, rcard, _ = model_info(ref_dir)
    assert card["data"]["realval"] == rcard["data"]["realval"], "both versions must use the same realval data"
    root = data_path(track, card["data"]["realval"])
    gts = {s_: sc.load_split(root, s_) for s_ in ("val", "valB")}
    fb, fb_split = pooled_flags(new_dir, card, track, gts)
    fa, fa_split = pooled_flags(ref_dir, rcard, track, gts)
    classes = [c for c in track["classes_with_test_gt"]]
    fids = [r["fid"] for r in fa[classes[0]]]
    groups = [sc.frame_group(f, track.name, block) for f in fids]
    frame = sc.paired_bootstrap(fa, fb, classes, 200, seed)
    grp = sc.grouped_bootstrap(fa, fb, classes, groups, n, seed)
    logo = sc.leave_one_group_out(fa, fb, classes, groups)
    per_split = {}
    for s_ in ("val", "valB"):
        aps = {c: (sc.ap_from_flags(fa_split[s_][c], "3d@0.5"), sc.ap_from_flags(fb_split[s_][c], "3d@0.5")) for c in classes}
        ok = [c for c in classes if aps[c][0] is not None]
        per_split[s_] = {"mAP": float(np.mean([aps[c][1] for c in ok]) - np.mean([aps[c][0] for c in ok])),
                         "classes": {c: (aps[c][1] - aps[c][0]) if aps[c][0] is not None else None for c in classes}}
    pooled_cls = {c: frame[c]["delta"] for c in classes if c in frame}
    gain = sum(max(0.0, v) for v in pooled_cls.values())
    rare = RARE.get(track.name.lower()[:5], ())
    rare_share = (sum(max(0.0, pooled_cls.get(c, 0.0)) for c in rare) / gain) if gain > 0 else 0.0
    worst = min(logo.items(), key=lambda kv: kv[1])
    d, p = grp["delta"], grp["p_gain"]
    go = [d > 0, p >= go_p, worst[1] >= -margin, rare_share < 0.5]
    level = "GO" if all(go) else ("NO-GO" if (d <= 0 or p < min_p) else "JUDGEMENT")
    why = [w for w, ok in zip(("mAP delta <= 0", f"grouped P(gain) < {go_p}", f"a leave-one-group-out delta below -{margin}",
                               "rare classes carry half or more of the gain"), go) if not ok]
    out = {"new": new_dir.name, "ref": ref_dir.name, "level": level, "why": why,
           "pooled_mAP_delta": d, "frame_p_gain": frame["mAP"]["p_gain"], "grouped_p_gain": p, "grouped_ci90": grp["ci90"],
           "n_groups": grp["n_groups"], "logo_worst": {"group": worst[0], "delta": worst[1]},
           "logo_negative": sum(v < 0 for v in logo.values()), "rare_share": rare_share,
           "split_mAP_delta": {s_: per_split[s_]["mAP"] for s_ in per_split},
           "class_delta": {c: {"A": per_split["val"]["classes"][c], "B": per_split["valB"]["classes"][c],
                               "pooled": pooled_cls.get(c), "frame_p_gain": frame.get(c, {}).get("p_gain")} for c in classes}}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("new_dir", type=Path)
    ap.add_argument("ref_dir", type=Path)
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--margin", type=float, default=0.002)
    ap.add_argument("--block", type=int, default=1000)
    ap.add_argument("--go-p", type=float, default=0.75)
    ap.add_argument("--min-p", type=float, default=0.5)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    r = gate(a.new_dir.resolve(), a.ref_dir.resolve(), a.n, a.seed, a.margin, a.block, a.go_p, a.min_p)
    print(f"{r['new']} vs {r['ref']}: {r['level']}" + (f" ({'; '.join(r['why'])})" if r["why"] else ""))
    print(f"  pooled mAP delta {r['pooled_mAP_delta']:+.4f} (A {r['split_mAP_delta']['val']:+.4f}, B {r['split_mAP_delta']['valB']:+.4f}); "
          f"P(gain) frame {r['frame_p_gain']:.2f}, grouped {r['grouped_p_gain']:.2f} over {r['n_groups']} groups, "
          f"90% CI [{r['grouped_ci90'][0]:+.4f}, {r['grouped_ci90'][1]:+.4f}]")
    print(f"  leave-one-group-out: worst {r['logo_worst']['delta']:+.4f} without {r['logo_worst']['group']}, "
          f"{r['logo_negative']} of {r['n_groups']} removals negative; rare-class share of the gain {r['rare_share']:.2f}")
    for c, v in r["class_delta"].items():
        f = lambda x: "  n/a " if x is None else f"{x:+.4f}"
        print(f"    {c:11s} A {f(v['A'])}  B {f(v['B'])}  pooled {f(v['pooled'])}  P {v['frame_p_gain'] if v['frame_p_gain'] is not None else float('nan'):.2f}")
    if a.json:
        a.json.write_text(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
