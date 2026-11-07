#!/usr/bin/env python
"""Select the anchored box-size calibration of a routed model (S9 close-out, docs/decisions/2026-11-02-s9-clean-twin-plan.md
Section 15.31; applied by route_predictions.apply_size_calibration as the last stage of merge_card).

    python common/tools/size_calibration.py model-v2x-track/routed-g19 --write

Reads the routed realval-A and realval-B predictions that `route_predictions.py validate` wrote (the card must have no
size_calibration yet). Per class of the pre-registered grid, candidates rank by the mean of A and B AP 3D@0.5 (LUMPI
Person by late-A, R5). The best is kept only under the 6.0 pooled rule against no calibration: pooled A+B P(gain) >= 0.9
and neither split down by more than 0.005. --write stores the kept classes in model.yaml `size_calibration`; run
`route_predictions.py validate` afterwards. Anchors: V2X the frame origin (the sensor), LUMPI the five sensors' xy.
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import data_path, model_info  # noqa: E402
from bdc26 import scorecard as sc  # noqa: E402
from route_predictions import apply_size_calibration  # noqa: E402

GRID = {                                              # record Section 15.31, fixed before any build: (dl, dw, dh)
    "v2x": {
        "vehicle": [(dl, 0.0, dh) for dl in (0.0, -0.1, -0.2, -0.3, -0.4, -0.5, -0.6) for dh in (0.0, 0.03)],
        "pedestrian": [(0.0, 0.0, dh) for dh in (0.0, 0.03, 0.05)],
        "truck": [(dl, 0.0, 0.0) for dl in (0.0, -0.25, -0.5)],
    },
    "lumpi": {
        "Car": [(dl, dw, dh) for dl in (0.0, -0.1, -0.2) for dw, dh in ((0.0, 0.0), (0.04, 0.035), (0.08, 0.07))],
        "Person": [(0.0, 0.0, dh) for dh in (0.0, 0.03, 0.05)],
    },
}
LATE_RANK = {"lumpi": ("Person",)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    m = Path(a.model_dir)
    _, card, track = model_info(m)
    t = "lumpi" if track.name.startswith("lumpi") else "v2x"
    if card.get("size_calibration"):
        raise SystemExit("the card already has a size_calibration: select on uncalibrated routed predictions")
    anchors = (json.loads((track.gen / "walker_scalars_v6.json").read_text())["range_from"] if t == "lumpi" else [[0.0, 0.0]])
    root = data_path(track, card["data"]["realval"])
    gts = {s: sc.load_split(root, s) for s in ("val", "valB")}
    preds = {s: json.loads((m / "validation" / "output" / f"pcdet_realval-v1_{s}_routed.json").read_text()) for s in gts}
    late = sc.late_a_ids(track, list(gts["val"]))
    kept, report = {}, {}
    for c, grid in GRID[t].items():
        pc = {s: {f: [d for d in v if d["class"] == c] for f, v in preds[s].items()} for s in gts}
        flags, res = {}, []
        for off in grid:
            spec = {"anchors": anchors, "classes": {c: dict(zip(("dl", "dw", "dh"), off))}}
            fl = {s: sc.frame_flags(apply_size_calibration(pc[s], spec), gts[s], [c])[c] for s in gts}
            flags[off] = fl
            r = {"off": off, "A": sc.ap_from_flags(fl["val"], "3d@0.5"), "B": sc.ap_from_flags(fl["valB"], "3d@0.5")}
            r["lateA"] = sc.ap_from_flags(sc.subset({c: fl["val"]}, late)[c], "3d@0.5") if late else None
            res.append(r)
            print(f"  {c:10s} dl {off[0]:+.2f} dw {off[1]:+.2f} dh {off[2]:+.3f}: A {r['A']:.4f} B {r['B']:.4f}"
                  + (f" lateA {r['lateA']:.4f}" if r["lateA"] is not None else ""), flush=True)
        rank = (lambda r: r["lateA"]) if c in LATE_RANK.get(t, ()) else (lambda r: (r["A"] + r["B"]) / 2)
        base = next(r for r in res if r["off"] == (0.0, 0.0, 0.0))
        best = max(res, key=rank)
        g = sc.pooled_gate(flags[(0.0, 0.0, 0.0)], flags[best["off"]], c, n=200, seed=0)
        dA, dB = best["A"] - base["A"], best["B"] - base["B"]
        ok = best["off"] != (0.0, 0.0, 0.0) and g["ok"] and dA >= -0.005 and dB >= -0.005
        report[c] = {"best": dict(zip(("dl", "dw", "dh"), best["off"])), "dA": dA, "dB": dB,
                     "dlateA": (best["lateA"] - base["lateA"]) if base["lateA"] is not None else None,
                     "pooled": {"delta": g["delta"], "p_gain": g["p_gain"]}, "kept": bool(ok),
                     "rank": "late-A" if c in LATE_RANK.get(t, ()) else "joint A/B", "grid": res}
        print(f"{c}: best {best['off']} dA {dA:+.4f} dB {dB:+.4f} pooled {g['delta']} P {g['p_gain']} -> {'KEPT' if ok else 'not kept'}", flush=True)
        if ok:
            kept[c] = {k: float(v) for k, v in zip(("dl", "dw", "dh"), best["off"]) if v}
    (m / "validation" / "results").mkdir(parents=True, exist_ok=True)
    (m / "validation" / "results" / "size_calibration.json").write_text(json.dumps(report, indent=1, default=float))
    print("size_calibration:", kept or "none")
    if a.write and kept:
        p = m / "model.yaml"
        d = yaml.safe_load(p.read_text())
        d["size_calibration"] = {"anchors": [[float(x), float(y)] for x, y in anchors], "classes": kept}
        p.write_text(yaml.safe_dump(d, sort_keys=False))
        print("written to", p)


if __name__ == "__main__":
    main()
