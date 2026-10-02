#!/usr/bin/env python
"""Download real V2X-Real infrastructure data (agent -1, the Ouster OS1-64) from the UCLA box shares.

LICENCE: V2X-Real code is under the UCLA Academic Software License and the project page says "All Rights
Reserved". Get written clearance for your organization first; --accept-licence records that you have it.

Two phases keep forbidden-frame labels off disk:
  1. --points : agent -1 point clouds (.bin) of the chosen shares. Needed by resolve_test_ids.py.
  2. --labels : agent -1 labels (.yaml) ONLY for frames the ForbiddenGuard allows (needs kit/id_mapping.json).

    python fetch_real.py --accept-licence --points                  # all shares (about 7 GB of agent -1 bins)
    python resolve_test_ids.py                                      # -> $BDC_DATA/v2x-track/kit/id_mapping.json
    python fetch_real.py --accept-licence --labels --stride 1
Files land in $BDC_DATA/v2x-track/real/raw/<split>/<scenario>/-1/<frame>.{bin,yaml} (same paths as in the zips).
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from bdc26.config import load_track  # noqa: E402
from bdc26.guard import ForbiddenGuard  # noqa: E402
from bdc26.io import fetch  # noqa: E402

T = load_track("v2x-track")


def open_share(share: str):
    res = fetch.static_resolver(T["real"]["box_static"] + T["real"]["shares"][share])
    size = fetch.remote_size(res)
    return (lambda: fetch.open_zip([(res, size)], buffer=1 << 20)), size


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--accept-licence", action="store_true", required=True)
    ap.add_argument("--points", action="store_true")
    ap.add_argument("--labels", action="store_true")
    ap.add_argument("--shares", nargs="+", default=list(T["real"]["shares"]))
    ap.add_argument("--stride", type=int, default=1, help="labels: every k-th allowed frame")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    if not (a.points or a.labels):
        ap.error("choose --points and/or --labels")
    agent = T["real"]["agent"]
    out = T.real / "raw"
    guard = ForbiddenGuard(T) if a.labels else None
    if a.labels and not guard.resolved:
        sys.exit("kit/id_mapping.json missing: run ingest_kit.py and resolve_test_ids.py first")
    for share in a.shares:
        zopen, size = open_share(share)
        names = zopen().namelist()
        # test.zip / val.zip members are "<split>/<scenario>/<agent>/<frame>"; train1-4.zip members have no
        # split folder ("<scenario>/<agent>/<frame>"), so they are written under raw/train/.
        split = share.rstrip("0123456789")
        prefixed = any(n.startswith(split + "/") for n in names)
        depth = 3 if prefixed else 2
        dest = out if prefixed else out / split
        mine = [n for n in names if n.count("/") == depth and n.split("/")[depth - 1] == agent]
        if a.points:
            bins = [n for n in mine if n.endswith(".bin")]
            print(f"[{share}] {len(bins)} agent {agent} point clouds ({size / 1e9:.1f} GB zip) -> {dest}")
            fetch.extract_members(zopen, bins, dest, workers=a.workers)
        if a.labels:
            ymls = sorted(n for n in mine if n.endswith(".yaml"))[:: a.stride]
            keys = [(n.split("/")[depth - 2], int(Path(n).stem)) for n in ymls]
            allowed = set(guard.filter(keys, purpose=f"download labels ({share})"))
            ymls = [n for n, k in zip(ymls, keys) if k in allowed]
            print(f"[{share}] {len(ymls)} allowed label files of {len(keys)}")
            fetch.extract_members(zopen, ymls, dest, workers=a.workers)


if __name__ == "__main__":
    main()
