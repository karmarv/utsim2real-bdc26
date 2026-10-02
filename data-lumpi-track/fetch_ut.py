#!/usr/bin/env python
"""Download the organizer synthetic dataset for this track (CC0) and extract it under $BDC_DATA/<track>/ut/.

Parts are fetched with parallel HTTP range requests (Dataverse serves about 1.5 MB/s per connection),
MD5-checked against manifests/, then the requested member folders are extracted and the parts deleted.

    python fetch_ut.py                 # pcd + lbl + sem_seg + ins_seg (default: everything G1/G2 need)
    python fetch_ut.py --members pcd lbl
    python fetch_ut.py --check         # count extracted files only
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from bdc26.config import load_track  # noqa: E402
from bdc26.io.ut import check_ut, fetch_ut  # noqa: E402

TRACK = HERE.name.removeprefix("data-")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--members", nargs="+", default=None, help="subset of pcd lbl sem_seg ins_seg")
    ap.add_argument("--workers", type=int, default=24, help="parallel range requests per part")
    ap.add_argument("--keep-zips", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    t = load_track(TRACK)
    members = a.members or t["ut"]["members_default"] + t["ut"]["members_seg"]
    if not a.check:
        fetch_ut(t, members, workers=a.workers, keep_zips=a.keep_zips)
    counts = check_ut(t, members)
    print(counts)
    sys.exit(0 if all(v == t["ut"]["n_frames"] for v in counts.values()) else 1)
