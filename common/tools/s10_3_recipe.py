#!/usr/bin/env python
"""Release 10.3 (docs/decisions/2026-11-13-s10-10.3-final-system.md): a scored routed system's recipe on its members
retrained on the calibrated generator, with no new selection.

Every member model of the parent card is replaced by its retrained sibling: a model `X-g1v6...` by `X-g1v6...<suffix>`
(made by s10_2_members.py; its card must name the parent model in `derived_from`), and a seed bag `bag-X-g1v6x...` by
`bag-X-g1v6<suffix>x...`, a new bag folder whose seeds are the retrained siblings of the parent bag's seeds (same iou,
no knob of its own). Route, fusion, calibration, budget, copies, stages and size calibration are copied unchanged;
members the route and fusion do not use are left out. `realism_frames` and `data.train` become the calibrated corpus,
so rule 1b can check that the 50 frames come from the shipped detector's training data. The 50 ids are the parent's.
With --final-adjust-from, the card also takes that model's `final_adjust` block (P, record 2026-11-12 Section 11.4).

    python common/tools/s10_3_recipe.py lumpi routed-c0 routed-s10-3-l3 --suffix n1 --frames pcdet/g1-v6n1 --candidate L3
    python common/tools/s10_3_recipe.py lumpi routed-s10-3-l3 routed-s10-3-l6 --same-members --candidate L6 \
        --final-adjust-from routed-s10-2-l5
    python common/tools/s10_3_recipe.py v2x routed-c2r routed-s10-3-v3x --suffix aw --frames pcdet/g1-v6aw --candidate V3x --dry-run
Prints the member mapping; with --dry-run it writes nothing and exits 1 if a retrained sibling is missing.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bdc26.config import load_track  # noqa: E402
from route_predictions import used_members  # noqa: E402

REC = "docs/decisions/2026-11-13-s10-10.3-final-system.md"
BAG = re.compile(r"^(bag-.+-g1v6)(x\d*)$")


def sibling(name: str, suffix: str) -> str:
    """The retrained sibling's folder name: bag-X-g1v6x5 -> bag-X-g1v6<suffix>x5, X-g1v6d2 -> X-g1v6d2<suffix>."""
    m = BAG.match(name)
    if m:
        return m.group(1) + suffix + m.group(2)
    if "-g1v6" not in name:
        raise SystemExit(f"{name}: not a g1-v6 member, no retrained sibling")
    return name + suffix


def load(track_dir: Path, name: str) -> dict:
    p = track_dir / name / "model.yaml"
    if not p.exists():
        raise FileNotFoundError(name)
    return yaml.safe_load(p.read_text())


def plan(track_dir: Path, card: dict, suffix: str, only: set | None = None) -> tuple[dict, dict, list]:
    """(model map parent -> sibling for the used members, new bags {name: card}, missing siblings).
    With `only`, just those single (non-bag) parent models are mapped to their siblings; every other member stays."""
    mapping, bags, missing = {}, {}, []
    for n in used_members(card):
        parent = card["members"][n]["model"]
        if only is not None and parent not in only:
            mapping[parent] = parent
            continue
        new = sibling(parent, suffix)
        pc = load(track_dir, parent)
        if only is not None and pc.get("type") == "bag":
            raise SystemExit(f"--only {parent}: a bag; a partial swap replaces single models only")
        if pc.get("type") == "bag":
            seeds = []
            for s in pc["members"]:
                ss = sibling(s, suffix)
                try:
                    sc = load(track_dir, ss)
                except FileNotFoundError:
                    missing.append(ss)
                    continue
                if sc.get("derived_from") != s:
                    raise SystemExit(f"{ss}: derived_from {sc.get('derived_from')} is not {s}")
                seeds.append((ss, sc))
            bc = dict(pc)
            bc.update({"name": new, "members": [s for s, _ in seeds], "strategy": "S10-3", "derived_from": parent,
                       "data": {**pc.get("data", {}), "train": " + ".join(c["data"]["train"] for _, c in seeds)},
                       "realism_frames": seeds[0][1].get("realism_frames") if seeds else None,
                       "status": f"S10-3: {parent}'s seed bag on the retrained seeds",
                       "notes": f"S10-3 ({REC}): {parent} with every seed retrained on the calibrated generator; same iou, "
                                "no checkpoint and no tuned knob of its own.\n"})
            bags[new] = bc
        else:
            try:
                sc = load(track_dir, new)
                if sc.get("derived_from") != parent:
                    raise SystemExit(f"{new}: derived_from {sc.get('derived_from')} is not {parent}")
            except FileNotFoundError:
                missing.append(new)
        mapping[parent] = new
    return mapping, bags, sorted(set(missing))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track", choices=["lumpi", "v2x"])
    ap.add_argument("parent")
    ap.add_argument("name")
    ap.add_argument("--suffix", default=None, help="corpus suffix of the retrained siblings (n1, aw)")
    ap.add_argument("--frames", default=None, help="the calibrated corpus of the 50 frames")
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--same-members", action="store_true", help="copy the parent's members as they are (P versions)")
    ap.add_argument("--final-adjust-from", default=None, help="model folder whose final_adjust block (P) is copied")
    ap.add_argument("--only", default=None,
                    help="partial swap (L7, record Section 12): only these parent models (comma list, single models) are "
                         "replaced by their retrained siblings; the card keeps the parent's frames and training corpus")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    T = load_track(f"{a.track}-track")
    td = T.model_dir
    src = td / a.parent
    card = yaml.safe_load((src / "model.yaml").read_text())
    used = used_members(card)
    new = dict(card)
    new["members"] = {n: dict(card["members"][n]) for n in used}
    bags = {}
    only = set(a.only.split(",")) if a.only else None
    if not a.same_members:
        if not (a.suffix and (a.frames or only)):
            raise SystemExit("--suffix and --frames (or --only) are needed unless --same-members")
        if only and a.frames:
            raise SystemExit("--only keeps the parent's frames: no --frames")
        mapping, bags, missing = plan(td, card, a.suffix, only)
        if only and not only <= set(mapping):
            raise SystemExit(f"--only names models the parent does not use: {sorted(only - set(mapping))}")
        for n in used:
            print(f"{n}: {card['members'][n]['model']} -> {mapping[card['members'][n]['model']]}")
        if missing:
            print("MISSING", " ".join(missing))
            if a.dry_run:
                return 1
            raise SystemExit("retrained siblings missing")
        for n in used:
            new["members"][n]["model"] = mapping[card["members"][n]["model"]]
        if not only:
            new["data"] = {**card.get("data", {}), "train": a.frames}
            new["realism_frames"] = a.frames
    if a.final_adjust_from:
        new["final_adjust"] = yaml.safe_load((td / a.final_adjust_from / "model.yaml").read_text())["final_adjust"]
    new.update({"name": a.name, "strategy": "S10-3", "candidate": a.candidate, "derived_from": a.parent,
                "status": f"S10-3 {a.candidate}: {a.parent}'s recipe" + ("" if a.same_members else
                          f" with {len(only)} member(s) retrained ({a.suffix})" if only else " on the retrained members")
                          + (" plus P (final_adjust)" if a.final_adjust_from else "") + f" ({REC})",
                "notes": f"S10-3 {a.candidate} ({REC}): route, fusion, calibration, budget, copies, stages and size "
                         f"calibration of {a.parent} unchanged, no new selection"
                         + ("" if a.same_members else
                            f"; only {', '.join(sorted(only))} replaced by their siblings retrained on the '{a.suffix}' "
                            f"corpora, every other member and the 50 frames ({card.get('realism_frames')}) as in "
                            f"{a.parent}" if only else
                            f"; every member retrained on the calibrated generator ({a.frames}), "
                            "the organizers' path of 2026-11-12 (calibration in the training data, detector retrained on "
                            "it, the 50 frames from that data)")
                         + (f"; P copied from {a.final_adjust_from}" if a.final_adjust_from else "") + ".\n"})
    if a.dry_run:
        print(f"dry run: {len(bags)} new bags {sorted(bags)}; card {a.name} not written")
        return 0
    dst = td / a.name
    if dst.exists():
        raise SystemExit(f"{dst} exists")
    for b, bc in bags.items():
        bd = td / b
        if bd.exists():
            if yaml.safe_load((bd / "model.yaml").read_text())["members"] != bc["members"]:
                raise SystemExit(f"{bd} exists with other seeds")
            continue
        for sub in ("validation/output", "validation/results", "test/output"):
            (bd / sub).mkdir(parents=True, exist_ok=True)
        (bd / "model.yaml").write_text(yaml.safe_dump(bc, sort_keys=False))
        print(f"bag {b}: {bc['members']}")
    for sub in ("validation/output", "validation/results", "test/output", "train"):
        (dst / sub).mkdir(parents=True, exist_ok=True)
    for f in ("make_submission.sh", "synthetic_ids.txt"):
        shutil.copy2(src / "test" / f, dst / "test" / f)
    (dst / "model.yaml").write_text(yaml.safe_dump(new, sort_keys=False))
    print(f"card {dst.relative_to(T.model_dir.parent)} written ({len(used)} members)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
