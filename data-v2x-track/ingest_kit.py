#!/usr/bin/env python
"""Unpack the CodaBench starting kit for this track into $BDC_DATA/<track>/kit and print a format report.

Download it first (login required): CodaBench competition -> Files tab -> starting_kit.
    python ingest_kit.py ~/Downloads/starting_kit.zip
The 50 detection-test frames are forbidden frames: this script reads them only for format checks.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from bdc26.config import load_track  # noqa: E402
from bdc26.io.kit import ingest  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path, help="starting kit zip or unpacked folder")
    rep = ingest(load_track(HERE.name.removeprefix("data-")), ap.parse_args().source)
    print(json.dumps({k: v for k, v in rep.items() if k != "files"}, indent=2, default=str))
