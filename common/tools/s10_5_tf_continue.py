#!/usr/bin/env python
"""Release 10.5 record Section 10.5, the continuation rule of the TransFusion line (fixed before any result): continue to
the bag and L11 if L10's fuse kept a TransFusion member in at least one class, or tf6's 4-view realval AP ((A+B)/2) is
within 0.02 of the best single member of L9's card in at least one of Person, Car, Truck and Van.
    python common/tools/s10_5_tf_continue.py <run>/events.txt routed-s10-5-l10   # PASS or FAIL with the reasons; exit 0 / 3
L10's fused sets are read from the driver's "fused sets:" event (after fuse, before the rare-class freeze and the check).
"""
import json
import re
import sys
from pathlib import Path

import yaml

TD = Path("model-lumpi-track")
CLASSES = ["Person", "Car", "Truck", "Van"]


def ap(model: str, tag: str = "_tta") -> dict | None:
    f = TD / model / "validation" / "results" / f"local_scores{tag}.json"
    if not f.exists():
        return None
    d = json.loads(f.read_text())
    a, b = d.get("realval_A_per_class") or {}, d.get("realval_B_per_class") or {}
    return {c: ((a.get(c) or 0) + (b.get(c) or 0)) / 2 for c in CLASSES}


def main():
    ev, sysname = Path(sys.argv[1]).read_text().splitlines(), sys.argv[2]
    line = [l for l in ev if f"{sysname}: fused sets: " in l]
    sets = line[-1].split(f"{sysname}: fused sets: ", 1)[1].split("; ") if line else []
    kept = sorted({x.split(" ", 1)[0] for x in sets if "tf6" in x})
    card = yaml.safe_load((TD / "routed-s10-5-l9" / "model.yaml").read_text())
    models = sorted({m["model"] for m in card["members"].values()})
    best = {c: max(((ap(m) or {}).get(c, -1), m) for m in models) for c in CLASSES}
    tf = ap("transfusion-rosf-g1v6")
    near = [c for c in CLASSES if tf and tf[c] >= best[c][0] - 0.02]
    for c in CLASSES:
        print(f"{c:7s} tf6 4-view {tf[c] if tf else float('nan'):.4f}  best L9 member {best[c][0]:.4f} ({best[c][1]})")
    ok = bool(kept or near)
    print(("PASS" if ok else "FAIL") + f": fuse kept TransFusion in {kept or 'no class'}; within 0.02 of the best in {near or 'no class'}")
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
