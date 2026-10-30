"""Helpers shared by the command-line tools: resolve a model folder, its track and its data paths."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common"))
from bdc26.config import load_track  # noqa: E402


def model_info(model_dir: str | Path):
    """(model_dir, card, track) for model-<track>/<model>."""
    model_dir = Path(model_dir).resolve()
    card = yaml.safe_load((model_dir / "model.yaml").read_text())
    return model_dir, card, load_track(card["track"])


def data_path(track, rel: str) -> Path:
    """Dataset path from a model card entry such as 'pcdet/ut-v1' (relative to $BDC_DATA/<track>) or an absolute path."""
    p = Path(rel)
    return p if p.is_absolute() else track.root / p


def pcdet_root() -> Path:
    root = Path(os.environ.get("PCDET_ROOT", REPO.parent / "bdc26-data" / "third_party" / "OpenPCDet"))
    if not (root / "tools" / "train.py").exists():
        raise FileNotFoundError(f"OpenPCDet not found at {root}; run common/env/setup_bdc_train.sh or set PCDET_ROOT")
    return root


def load_pcdet_cfg(model_dir: Path, data: Path):
    """Load <model>/train/pcdet_model.yaml (with its _BASE_CONFIG_) and point it at `data`."""
    from pcdet.config import cfg, cfg_from_yaml_file

    cwd = os.getcwd()
    os.chdir(model_dir / "train")
    try:
        cfg_from_yaml_file("pcdet_model.yaml", cfg)
    finally:
        os.chdir(cwd)
    cfg.DATA_CONFIG.DATA_PATH = str(data)
    return cfg


def validation_tag(model_dir: Path, card: dict) -> str:
    """Suffix of a model's validation files: 'routed' for a routed model, else the run of local_scores.json
    (<tag>_checkpoint_epoch_N), as written by tune_and_eval.sh."""
    if card.get("members"):
        return "routed"
    import json
    return json.loads((model_dir / "validation" / "results" / "local_scores.json").read_text())["run"]


def member_tag(member: dict) -> str:
    """Validation-file suffix of a routed model's member from its ckpt path (<tag>_checkpoint_epoch_N), plus "_tta"
    for a test-time-augmentation variant (member entry with a `tta` view spec; tune_and_eval.sh --tta writes it), or
    "_<tta_tag>" for a second view set (S8: `tta_tag: tta12`, written by tune_and_eval.sh --tta-tag)."""
    tag = Path(member["ckpt"]).parts[-3] + "_" + Path(member["ckpt"]).stem
    return tag + "_" + member.get("tta_tag", "tta") if member.get("tta") else tag


def validation_predictions(model_dir: Path, card: dict, split: str, tag: str | None = None) -> Path:
    """Post-processed predictions of a model on its real validation split (validation/output/)."""
    data = card["data"]["realval"].replace("/", "_")
    return model_dir / "validation" / "output" / f"{data}_{split}_{tag or validation_tag(model_dir, card)}.json"
