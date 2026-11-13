#!/usr/bin/env python
"""Release 10.3: the final validation predictions of a system against another (gate G-D's numbers beside rule 14's
grouped gate): official mAP on realval-A, realval-B and, where the track defines it, late-A (LUMPI Measurement4
4800-6399, the frames just before the test window), the per-class deltas and the late-A paired bootstrap of the
classes that changed. Read-only apart from the json it writes.

    python common/tools/s10_3_compare.py model-lumpi-track/routed-s10-3-l3 model-lumpi-track/routed-c0 [--out x.json]
"""
import argparse
import json
from pathlib import Path

from _common import data_path, model_info
from bdc26 import scorecard as sc
from bdc26.evalap import evaluate


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model")
    ap.add_argument("ref")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    m, ref = Path(a.model), Path(a.ref)
    _, card, track = model_info(m)
    data = card["data"]["realval"]
    D, root = data.replace("/", "_"), data_path(track, data)
    cls = list(track["classes_with_test_gt"])
    res = {}
    for split in ("val", "valB", "lateA"):
        sp = "val" if split == "lateA" else split
        gts = sc.load_split(root, sp)
        if split == "lateA":
            keep = set(sc.late_a_ids(track, list(gts)))
            if not keep:
                continue
            gts = {f: g for f, g in gts.items() if f in keep}
        P = {k: json.loads((d / "validation" / "output" / f"{D}_{sp}_routed.json").read_text()) for k, d in (("new", m), ("ref", ref))}
        r = {k: evaluate({i: P[k].get(i, []) for i in gts}, gts, track.classes) for k in P}
        pc = {k: {c: (r[k]["per_class"][c]["3d@0.5"] or {}).get("AP_R40") for c in cls} for k in r}
        cw = [c for c in cls if pc["ref"][c] is not None and pc["new"][c] is not None]
        mp = {k: sum(pc[k][c] for c in cw) / len(cw) for k in pc}
        row = {"n_frames": len(gts), "mAP_ref": mp["ref"], "mAP_new": mp["new"], "delta": mp["new"] - mp["ref"],
               "per_class_delta": {c: pc["new"][c] - pc["ref"][c] for c in cw if abs(pc["new"][c] - pc["ref"][c]) > 1e-9}}
        if split == "lateA" and row["per_class_delta"]:
            ch = list(row["per_class_delta"])
            f0 = sc.frame_flags({i: P["ref"].get(i, []) for i in gts}, gts, ch)
            f1 = sc.frame_flags({i: P["new"].get(i, []) for i in gts}, gts, ch)
            row["bootstrap"] = {c: {k: v for k, v in b.items() if k in ("delta", "p_gain", "ci90")}
                                for c, b in sc.paired_bootstrap(f0, f1, ch, 200, 0).items()}
        res[split] = row
        print(split, f"{mp['ref']:.4f} -> {mp['new']:.4f} ({row['delta']:+.4f})",
              {c: f"{v:+.4f}" for c, v in row["per_class_delta"].items()},
              {c: f"P {b['p_gain']:.2f}" for c, b in row.get("bootstrap", {}).items()}, flush=True)
    out = Path(a.out) if a.out else m / "validation" / "results" / f"vs_{ref.name}.json"
    out.write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
