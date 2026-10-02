#!/usr/bin/env python
"""Resolve the challenge's V2X frame IDs ("<scenario index>_<frame>") to V2X-Real scenario folders.

The index -> folder mapping is not documented, and without it the ForbiddenGuard cannot block the forbidden
frames, so every V2X real-data reader refuses to run until this script has written kit/id_mapping.json.

Method (uses the 50 released test frames ONLY to identify what to block; nothing is fitted to them):
  1. For each test ID k_f, compare the test frame with every raw agent -1 frame numbered f: the organizers'
     frames are subsets of raw points, so the right folder matches (nearly) every point exactly.
  2. Check that each index k maps to one folder consistently.
  3. Try to explain the resolved pairs by a sorted ordering of folders (per split, or all splits); if one
     ordering explains all of them, use it to fill the indices that only occur among the realism-reference IDs.
  4. Otherwise, if the resolved indices are monotone in the sorted folder list of one split (the challenge
     indexes a sorted SUBSET of scenes: 2026-10-02, all 26 resolved indices are increasing positions in the
     sorted V2X-Real train split), an unresolved index lies strictly between its resolved neighbours: it maps to
     the LIST of candidate folders in that gap, and the guard blocks its frames in every candidate.
  5. Indices still unresolved map to "*": the guard then blocks that frame number (+/- buffer) in EVERY folder.
Needs: ingest_kit.py (kit) and fetch_real.py --points (raw bins).
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from bdc26.config import load_track  # noqa: E402
from bdc26.frames import strip_nulls  # noqa: E402
from bdc26.guard import read_forbidden_ids  # noqa: E402
from bdc26.io import kit, v2x  # noqa: E402

T = load_track("v2x-track")


def main():
    raw = T.real / "raw"
    agent = T["real"]["agent"]
    by_frame = defaultdict(list)                      # frame number -> [(split, scenario, path)]
    folders = defaultdict(set)                        # split -> scenarios
    for p in raw.glob(f"*/*/{agent}/*.bin"):
        split, scen = p.parts[-4], p.parts[-3]
        by_frame[int(p.stem)].append((split, scen, p))
        folders[split].add(scen)
    if not by_frame:
        sys.exit(f"no raw agent {agent} bins under {raw}: run fetch_real.py --accept-licence --points")
    rng = np.random.default_rng(0)
    resolved, evidence = {}, []
    for fid in kit.test_ids(T):
        k, f = fid.split("_")
        tp = strip_nulls(kit.read_test_frame(T, fid))[:, :3]
        sample = tp[rng.choice(len(tp), min(300, len(tp)), replace=False)]
        best = (0.0, None)
        for split, scen, path in by_frame.get(int(f), []):
            xyz = strip_nulls(v2x.read_bin(path))[:, :3]
            d, _ = cKDTree(xyz).query(sample, k=1)
            frac = float((d < 1e-4).mean())
            if frac > best[0]:
                best = (frac, (split, scen))
        evidence.append({"id": fid, "match_fraction": best[0], "folder": best[1]})
        if best[0] >= 0.95:
            if k in resolved and resolved[k] != best[1]:
                sys.exit(f"inconsistent mapping for index {k}: {resolved[k]} vs {best[1]}")
            resolved[k] = best[1]
    # 3. ordering hypotheses
    orderings = {f"sorted({s})": sorted(v) for s, v in folders.items()}
    orderings["sorted(all splits)"] = sorted(set().union(*folders.values()))
    explained = None
    for name, order in (orderings.items() if len(resolved) >= 5 else []):   # too few pairs: do not infer
        if all(int(k) < len(order) and order[int(k)] == scen for k, (_, scen) in resolved.items()):
            explained = (name, order)
            break
    mapping = {k: scen for k, (_, scen) in resolved.items()}
    forbidden_idx = sorted({i.split("_")[0] for i in read_forbidden_ids(T)}, key=int)
    # 4. monotone-subset bounds (one split, increasing positions)
    mono = None
    splits = {sp for sp, _ in resolved.values()}
    if not explained and len(resolved) >= 5 and len(splits) == 1:
        order = sorted(folders[splits.pop()])
        pos = sorted((int(k), order.index(scen)) for k, (_, scen) in resolved.items())
        if all(b[1] > a[1] for a, b in zip(pos, pos[1:])):
            mono = (order, pos)
    for k in forbidden_idx:
        if k in mapping:
            continue
        if explained and int(k) < len(explained[1]):
            mapping[k] = explained[1][int(k)]
        elif mono:
            order, pos = mono
            lo = max([pp for i, pp in pos if i < int(k)], default=-1)
            hi = min([pp for i, pp in pos if i > int(k)], default=len(order))
            cands = order[lo + 1:hi]
            mapping[k] = cands if cands else "*"
        else:
            mapping[k] = "*"
    (T.kit / "id_mapping.json").write_text(json.dumps(mapping, indent=2, sort_keys=True))
    report = {"n_test_ids": len(evidence), "n_resolved_indices": len(resolved), "ordering": explained[0] if explained else None,
              "monotone_subset": bool(mono),
              "candidate_lists": {k: v for k, v in mapping.items() if isinstance(v, list)},
              "wildcard_indices": [k for k, v in mapping.items() if v == "*"], "evidence": evidence}
    (T.kit / "id_mapping_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "evidence"}, indent=2))


if __name__ == "__main__":
    main()
