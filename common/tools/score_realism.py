#!/usr/bin/env python
"""Local realism proxy for 50 synthetic frames (a submission zip or a folder) against LEGAL real frames.

    python common/tools/score_realism.py --track v2x --syn model-v2x-track/<model>/submissions/<id>/submission.zip \
        --ref pcdet/realism-proxy-1 [--ref pcdet/realism-proxy-2 ...] [--map 0.45] [--no-exact]
--ref folders contain points/*.npy of legal real frames (data-<track>/prepare_realval.py writes proxy sets).
Never point --ref at the starting kit (its frames are forbidden). Reports each metric, the normalized terms,
R, and the spread across reference sets (the proxy's own noise).
"""
import argparse
import json
import zipfile
from pathlib import Path

import numpy as np

from _common import data_path, load_track
from bdc26 import realism


def load_frames(track, spec: str) -> list[np.ndarray]:
    p = Path(spec)
    if p.suffix == ".zip":
        with zipfile.ZipFile(p) as z:
            return [np.frombuffer(z.read(n), dtype=np.float32).reshape(-1, 3)
                    for n in sorted(z.namelist()) if n.startswith("synthetic/") and n.endswith(".bin")]
    root = data_path(track, spec)
    files = sorted((root / "points").glob("*.npy")) if (root / "points").exists() else sorted(root.glob("*.bin"))
    return [np.load(f)[:, :3] if f.suffix == ".npy" else np.fromfile(f, np.float32).reshape(-1, 3) for f in files][:50]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--track", required=True)
    ap.add_argument("--syn", required=True)
    ap.add_argument("--ref", action="append", required=True)
    ap.add_argument("--map", type=float, default=None)
    ap.add_argument("--no-exact", action="store_true")
    a = ap.parse_args()
    t = load_track(a.track)
    if any("kit" in Path(r).parts for r in a.ref):
        raise SystemExit("refusing to score against starting-kit frames (forbidden)")
    syn = load_frames(t, a.syn)
    results = [realism.score(syn, load_frames(t, r), t.name, exact_emd=not a.no_exact) for r in a.ref]
    for r, res in zip(a.ref, results):
        print(r, json.dumps({k: (round(v, 5) if isinstance(v, float) else v) for k, v in res.items()}))
    Rs = [res["R"] for res in results]
    print(f"R mean {np.mean(Rs):.4f} (spread {np.ptp(Rs):.4f} over {len(Rs)} reference sets)")
    if a.map is not None:
        print(f"combined estimate {realism.combined(a.map, float(np.mean(Rs))):.4f}")


if __name__ == "__main__":
    main()
