#!/usr/bin/env python
"""Scaffold a new model folder in a track, copying configs (never outputs) from an existing model.

    python common/tools/new_model.py v2x centerpoint-g1 --from pointpillars-ut
Creates model-<track>/<name>/{model.yaml, train/, validation/results/, test/, submissions/} and copies
train/*.yaml, train/*.sh, test/postprocess.yaml and validation/*.sh. Edit model.yaml (data, architecture,
status) and train/pcdet_model.yaml afterwards, and add the model to the "Models" table of the track doc.
"""
import argparse
import shutil

import yaml

from _common import REPO, load_track


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track")
    ap.add_argument("name")
    ap.add_argument("--from", dest="src", default="pointpillars-ut")
    a = ap.parse_args()
    t = load_track(a.track)
    src, dst = t.model_dir / a.src, t.model_dir / a.name
    if dst.exists():
        raise SystemExit(f"{dst} exists")
    for sub in ("train", "validation/results", "test", "submissions"):
        (dst / sub).mkdir(parents=True)
    for pattern in ("train/*.yaml", "train/*.sh", "test/*.yaml", "test/*.sh", "validation/*.sh"):
        for f in src.glob(pattern):
            shutil.copy2(f, dst / f.relative_to(src))
    card = yaml.safe_load((src / "model.yaml").read_text())
    card.update(name=a.name, status="planned", derived_from=a.src)
    (dst / "model.yaml").write_text(yaml.safe_dump(card, sort_keys=False))
    print(f"created {dst.relative_to(REPO)}")


if __name__ == "__main__":
    main()
