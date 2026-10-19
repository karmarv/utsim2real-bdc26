#!/usr/bin/env python
"""Freeze classes of a routed model at the configuration of a reference portfolio (R5 rule 4, S6 rule 4: LUMPI
Bicycle, Motorcycle and Bus follow no local split, docs/02-STRATEGY.md Sections 8.9 and 8.6).

    python common/tools/freeze_classes.py model-lumpi-track/routed-g8 --from model-lumpi-track/routed-g7 Bicycle Motorcycle Bus

Copies route, calibration, fusion, score floor, tail copies and the S7 sparse threshold of each class from the reference and checks that every
member the class uses is the same member (model folder, checkpoint, TTA) in both. Run `route_predictions.py validate`
afterwards.
"""
import argparse
from pathlib import Path

import yaml


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir")
    ap.add_argument("--from", dest="ref", required=True)
    ap.add_argument("classes", nargs="+")
    a = ap.parse_args()
    ref = yaml.safe_load((Path(a.ref) / "model.yaml").read_text())
    p = Path(a.model_dir) / "model.yaml"
    card = yaml.safe_load(p.read_text())
    for c in a.classes:
        card["route"][c] = ref["route"][c]
        for key in ("calibration", "fusion", "budget", "tail_copies", "sparse_demotion"):
            d = card.get(key) or {}
            if (ref.get(key) or {}).get(c) is None:
                d.pop(c, None)
            else:
                d[c] = ref[key][c]
            card[key] = d or None
        used = {ref["route"][c]} | set(((ref.get("fusion") or {}).get(c) or {}).get("members", []))
        for n in used:
            if card["members"].get(n) != ref["members"][n]:
                raise SystemExit(f"{c}: member {n} differs between {a.model_dir} and {a.ref}")
        print(f"frozen {c}: route {card['route'][c]}, fusion {(card.get('fusion') or {}).get(c)}, floor {(card.get('budget') or {}).get(c)}")
    p.write_text(yaml.safe_dump({k: v for k, v in card.items() if v is not None or k not in ("tail_copies", "sparse_demotion")},
                                sort_keys=False))


if __name__ == "__main__":
    main()
