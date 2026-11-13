#!/usr/bin/env python
"""S10-2 (release 10.2): member folders that retrain an existing member on a calibrated corpus, with the parent's
configs and training recipe unchanged (docs/decisions/2026-11-12-s10-10.2-clean-final-push.md Sections 4-5).
Each new folder is `<parent with its corpus suffix replaced>`; its card names the parent, the corpus, the candidate
(L3, L4 or V3) and the realism frames, so rules 1 and 1b can check the shipped system.

    python common/tools/s10_2_members.py lumpi L3 pvrcnnpp-ros-g1v6:g1-v6n1 voxelrcnn-rosf-g1v6j:g1-v6jn1 ...
    python common/tools/s10_2_members.py lumpi L3q pvrcnnpp-ros-g1v6:g1-v6pq --frames pcdet/g1-v6pq \
        --record docs/decisions/2026-11-13-s10-10.3-final-system.md        # 10.3: the re-cast-only corpus
Prints one `track:member` line per new folder (the train queue format).
"""
import argparse
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bdc26.config import load_track  # noqa: E402

REC = "docs/decisions/2026-11-12-s10-10.2-clean-final-push.md"
FRAMES = {"lumpi": "pcdet/g1-v6n1", "v2x": "pcdet/g1-v6aw"}


def new_name(parent: str, src_corpus: str, corpus: str) -> str:
    """parent name with the source corpus tag (g1v6, g1v6d2, g1v6j) replaced by the new one (g1v6n1, ...)."""
    s, c = src_corpus.split("/")[-1].replace("-", ""), corpus.split("/")[-1].replace("-", "")
    if not parent.endswith(s):
        raise SystemExit(f"{parent}: does not end with its corpus tag {s}")
    return parent[: -len(s)] + c


def make(track: str, cand: str, parent: str, corpus: str, frames: str = None, rec: str = REC) -> str:
    T = load_track(f"{track}-track")
    src = T.model_dir / parent
    card = yaml.safe_load((src / "model.yaml").read_text())
    name = new_name(parent, card["data"]["train"], corpus)
    dst = T.model_dir / name
    if dst.exists():
        raise SystemExit(f"{dst} exists")
    subprocess.run([sys.executable, str(Path(__file__).with_name("new_model.py")), track, name, "--from", parent],
                   check=True, capture_output=True, text=True)
    d = yaml.safe_load((dst / "model.yaml").read_text())
    d.update({
        "name": name, "strategy": "S10-3" if rec != REC else "S10-2", "derived_from": parent, "candidate": cand,
        "module": "M9 (engine v6) / S10-2 lever " + ("B" if track == "lumpi" else "V3"),
        "status": f"{'S10-3' if rec != REC else 'S10-2'} {cand}: {parent} retrained from scratch on the calibrated corpus pcdet/{corpus} (same configs, seed and epochs)",
        "notes": (f"{cand} ({rec}): the parent's recipe on the calibrated generator, as the organizers' "
                  "answer of 2026-11-12 allows (the calibration in the training data, the detector retrained on it, the 50 "
                  f"frames from that data). Realism frames {frames or FRAMES[track]}.\n"),
        "realism_frames": frames or FRAMES[track],
    })
    d["data"]["train"] = f"pcdet/{corpus}"
    (dst / "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
    return f"{track}:{name}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track", choices=["lumpi", "v2x"])
    ap.add_argument("candidate", choices=["L3", "L4", "V3", "L3q"])
    ap.add_argument("pairs", nargs="+", help="parent:corpus")
    ap.add_argument("--frames", default=None, help="realism frames corpus (default: the S10-2 corpus of the track)")
    ap.add_argument("--record", default=REC, help="decision record named in the cards")
    a = ap.parse_args()
    for p in a.pairs:
        parent, corpus = p.split(":")
        print(make(a.track, a.candidate, parent, corpus, a.frames, a.record))


if __name__ == "__main__":
    main()
