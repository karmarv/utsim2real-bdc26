#!/usr/bin/env python
"""S10 rule 1 (docs/decisions/2026-11-08-s10-clean-final-plan.md Section 8): is a model clean, that is, trained only on
corpora into which no real label row entered? The organizers' clarification of 2026-11-07: "real labels and object
points cut out with real boxes must not enter the training set".

    python common/tools/clean_check.py model-v2x-track/routed-g19          # a routed model: used members + realism frames
    python common/tools/clean_check.py model-lumpi-track/bag-voxelrcnn-ros-g1v6x
    python common/tools/clean_check.py --track lumpi --all                  # every member folder of the track

A corpus is clean when its card (`<corpus>/dataset.yaml`) names no real label rows in `real_data_use`, its walkers are
placed on the twin's scene map (or not inserted at all), and its G2 clutter is anchored on the map; a union corpus is
clean when every part is; the UrbanTwin data alone is clean. A card that cannot be read is not clean. Prints one line
per member (CLEAN or LABEL, with the reason) and exits 1 if anything is not clean.
"""
import argparse
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import data_path, model_info  # noqa: E402
from bdc26.config import load_track  # noqa: E402
from route_predictions import used_members  # noqa: E402


def corpus_status(track, corpus: str, _seen=None) -> tuple:
    """(clean, reason) of one corpus, from its card."""
    try:
        path = data_path(track, corpus)
        card = yaml.safe_load((Path(path) / "dataset.yaml").read_text())
    except Exception as e:                                # noqa: BLE001
        return False, f"{corpus}: card not readable ({e})"
    parts = card.get("parts")
    if parts:
        if isinstance(parts, str):
            parts = yaml.safe_load(parts)
        bad = [r for ok, r in (corpus_status(track, p["data"]) for p in parts) if not ok]
        return (not bad), (f"{corpus}: union of clean parts" if not bad else "; ".join(bad))
    rdu = card.get("real_data_use")
    p = card.get("params") or {}
    v6 = p.get("v6") or {}
    if rdu is None:
        src = str(card.get("source", ""))
        if src.startswith("UT-") and "+" not in src:
            return True, f"{corpus}: UrbanTwin data alone"
        return False, f"{corpus}: no real_data_use on the card"
    if "label row" in str(rdu).lower():
        return False, f"{corpus}: real label rows ({str(rdu)[:90]})"
    if v6.get("static_anchors") and os.environ.get("BDC_ALLOW_R1") != "1":    # S10 R1 interlock (records 15.13, 15.14)
        return False, (f"{corpus}: S10 R1 static anchors from unlabelled real frames (allowed by the organizers' answer to "
                       "question (c), 2026-11-10; in the report): set BDC_ALLOW_R1=1 to use such a corpus deliberately")
    placement = v6.get("placement", p.get("placement"))
    if placement == "prior" or (p.get("persons") and placement != "map"):
        return False, f"{corpus}: walkers placed from the label prior"
    if p.get("g2") and v6.get("clutter_anchors", "prior") != "map":
        return False, f"{corpus}: G2 clutter anchored at real walker positions"
    return True, f"{corpus}: {str(rdu)[:60]}"


def corpora_of(card: dict) -> list:
    return [c.strip() for c in str(card["data"]["train"]).split("+") if c.strip()]


def member_status(track, model_dir: Path) -> tuple:
    """(clean, reasons) of one member folder; a seed bag is clean when every seed is."""
    card = yaml.safe_load((model_dir / "model.yaml").read_text())
    if card.get("type") == "bag":
        res = [member_status(track, model_dir.parent / s) for s in card["members"]]
        return all(ok for ok, _ in res), [r for _, rs in res for r in rs]
    res = [corpus_status(track, c) for c in corpora_of(card)]
    return all(ok for ok, _ in res), [r for _, r in res]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir", nargs="?")
    ap.add_argument("--track", choices=["lumpi", "v2x"])
    ap.add_argument("--all", action="store_true", help="every member folder of --track")
    a = ap.parse_args()
    bad = 0
    if a.all:
        t = load_track(f"{a.track}-track")
        for d in sorted(p for p in t.model_dir.iterdir() if (p / "model.yaml").exists() and not p.name.startswith("routed")):
            try:
                ok, rs = member_status(t, d)
            except Exception as e:                        # noqa: BLE001
                ok, rs = False, [f"unreadable ({e})"]
            print(f"{'CLEAN' if ok else 'LABEL'} {d.name}: {' | '.join(rs)}")
        return 0
    m = Path(a.model_dir)
    _, card, track = model_info(m)
    if "route" in card or "fusion" in card:
        seen = {}
        for k in used_members(card):
            name = card["members"][k]["model"]
            if name not in seen:
                seen[name] = member_status(track, m.parent / name)
        for name, (ok, rs) in seen.items():
            bad += not ok
            print(f"{'CLEAN' if ok else 'LABEL'} {name}: {' | '.join(rs)}")
        ok, r = corpus_status(track, card["realism_frames"])
        bad += not ok
        print(f"{'CLEAN' if ok else 'LABEL'} realism frames {r}")
        print(f"{'PASS' if not bad else 'FAIL'} {m.name}: {len(seen)} member models, {bad} not clean")
    else:
        ok, rs = member_status(track, m)
        bad += not ok
        print(f"{'CLEAN' if ok else 'LABEL'} {m.name}: {' | '.join(rs)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
