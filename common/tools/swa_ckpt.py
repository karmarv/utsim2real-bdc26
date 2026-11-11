#!/usr/bin/env python
"""S10 lever D1 (docs/decisions/2026-11-08-s10-clean-final-plan.md): weight averaging of a member's last checkpoints
(SWA over the tail of its one-cycle schedule; Izmailov et al. 2018, SWAD for domain generalization, Cha et al. 2021).

    python common/tools/swa_ckpt.py model-v2x-track/voxelrcnn-ros-g1v6 --first 31 --last 40

Creates the sibling member folder <family>-swa-<corpus> (e.g. voxelrcnn-ros-swa-g1v6) with the parent's configs
(common/tools/new_model.py) and writes its train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth: every float
tensor of model_state is the mean over the epochs (the batch-norm running statistics too: no re-estimation in this
probe), integer tensors are taken from the last epoch, the optimizer state is dropped. The file name keeps the
tooling's epoch-40 convention; the card records what it is. Only synthetic-trained weights are averaged (no data).
"""
import argparse
import subprocess
import sys
from pathlib import Path

import torch
import yaml


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("parent")
    ap.add_argument("--first", type=int, default=31)
    ap.add_argument("--last", type=int, default=40)
    a = ap.parse_args()
    parent = Path(a.parent)
    track = parent.parent.name.replace("model-", "").replace("-track", "")
    fam, corpus = parent.name.rsplit("-", 1)
    name = f"{fam}-swa-{corpus}"
    dst = parent.parent / name
    ck = parent / "train/output/pcdet_model/run1/ckpt"
    files = [ck / f"checkpoint_epoch_{e}.pth" for e in range(a.first, a.last + 1)]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        raise SystemExit(f"missing checkpoints: {missing}")
    if dst.exists():
        raise SystemExit(f"{dst} exists")
    acc, last = None, None
    for f in files:
        st = torch.load(f, map_location="cpu")
        ms = st["model_state"]
        if acc is None:
            acc = {k: v.double().clone() if v.is_floating_point() else v.clone() for k, v in ms.items()}
        else:
            for k, v in ms.items():
                if v.is_floating_point():
                    acc[k] += v.double()
        last = st
    n = len(files)
    avg = {k: (v / n).to(last["model_state"][k].dtype) if v.is_floating_point() else last["model_state"][k]
           for k, v in acc.items()}
    subprocess.run([sys.executable, str(Path(__file__).with_name("new_model.py")), track, name, "--from", parent.name],
                   check=True, capture_output=True)
    out = dst / "train/output/pcdet_model/run1/ckpt"
    out.mkdir(parents=True)
    torch.save({"epoch": last["epoch"], "it": last["it"], "model_state": avg, "optimizer_state": None,
                "version": last["version"], "swa": {"parent": parent.name, "epochs": [a.first, a.last]}},
               out / "checkpoint_epoch_40.pth")
    c = yaml.safe_load((parent / "model.yaml").read_text())
    c.update({"name": name, "strategy": "S10", "derived_from": parent.name, "module": "M9 (engine v6) / S10 lever D1",
              "status": f"S10 D1 probe: weight average of {parent.name} epochs {a.first}-{a.last} (no training)",
              "notes": (f"S10 lever D1 (docs/decisions/2026-11-08-s10-clean-final-plan.md): mean of the {n} checkpoints "
                        f"{a.first}-{a.last} of {parent.name} (common/tools/swa_ckpt.py), batch-norm statistics averaged "
                        "too; same corpus as the parent. Enters a portfolio only after the S6 member check against "
                        "its parent (S10 rule 4).\n")})
    (dst / "model.yaml").write_text(yaml.safe_dump(c, sort_keys=False))
    print(f"wrote {out / 'checkpoint_epoch_40.pth'} ({n} checkpoints averaged)")


if __name__ == "__main__":
    main()
