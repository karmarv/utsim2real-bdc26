#!/usr/bin/env python
"""Train an OpenPCDet model whose configs live in model-<track>/<model>/train/.

    python common/tools/pcdet_train.py model-v2x-track/pointpillars-ut --extra_tag run1
    torchrun --nproc_per_node=4 common/tools/pcdet_train.py model-v2x-track/pointpillars-ut --launcher pytorch --extra_tag run1
    ... --data pcdet/smoke-v2x --epochs 1                 # override the dataset from model.yaml; any train.py flag passes through
    ... --fix_random_seed --seed 1666                     # another fixed seed (OpenPCDet hard-codes 666; seed runs, R5)

Registers BDCDataset, points OpenPCDet's ROOT_DIR at <model>/train so outputs land in
<model>/train/output/pcdet_model/<extra_tag>/ (ckpt/, train_*.log, tensorboard/, eval/), injects the
dataset path with --set, then runs OpenPCDet's tools/train.py unchanged.
"""
import os
import runpy
import sys
from pathlib import Path

from _common import data_path, model_info, pcdet_root

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        sys.exit(__doc__)
    model_dir, card, track = model_info(sys.argv[1])
    rest = sys.argv[2:]
    data_rel = card["data"]["train"]
    if "--data" in rest:
        i = rest.index("--data")
        data_rel = rest[i + 1]
        rest = rest[:i] + rest[i + 2:]
    seed = None
    if "--seed" in rest:
        i = rest.index("--seed")
        seed = int(rest[i + 1])
        rest = rest[:i] + rest[i + 2:]
        if "--fix_random_seed" not in rest:
            sys.exit("--seed needs --fix_random_seed")
    data = data_path(track, data_rel)
    if not (data / "custom_infos_train.pkl").exists():
        sys.exit(f"{data} has no infos: run common/tools/pcdet_build_infos.py {model_dir} --data {data_rel}")

    tools = pcdet_root() / "tools"
    sys.path.insert(0, str(tools))
    from bdc26.detect.pcdet_dataset import register

    register()
    from pcdet.config import cfg

    if seed is not None:
        # OpenPCDet's train.py seeds with 666 (+ rank) and its dataloader workers with 666 (+ worker id); shift both
        from pcdet.utils import common_utils

        base_set, base_worker, shift = common_utils.set_random_seed, common_utils.worker_init_fn, seed - 666

        def set_random_seed(s):
            base_set(int(s) + shift)

        def worker_init_fn(worker_id, seed=666):          # the dataloader binds seed= by keyword
            base_worker(worker_id, None if seed is None else int(seed) + shift)

        common_utils.set_random_seed, common_utils.worker_init_fn = set_random_seed, worker_init_fn
        print(f"pcdet_train: fixed seed {seed} (instead of 666)", flush=True)

    cfg.ROOT_DIR = model_dir / "train"
    os.chdir(model_dir / "train")
    injected = ["DATA_CONFIG.DATA_PATH", str(data)]
    if "--set" in rest:
        i = rest.index("--set")
        rest = rest[: i + 1] + injected + rest[i + 1:]
    else:
        rest = rest + ["--set"] + injected
    sys.argv = [str(tools / "train.py"), "--cfg_file", "pcdet_model.yaml"] + rest
    runpy.run_path(str(tools / "train.py"), run_name="__main__")
