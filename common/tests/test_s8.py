"""S8: the scale views of the 12-view TTA set (bdc26.detect.tta), the tail copies with a score threshold, the view-set
swap candidates (route_predictions.variant_candidates) and the tta_tag member suffix (_common.member_tag)."""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common" / "tools"))
sys.path.insert(0, str(REPO / "common"))

from _common import member_tag  # noqa: E402
from bdc26.detect import tta  # noqa: E402
from route_predictions import apply_tail_copies, variant_candidates  # noqa: E402

CK = "train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth"


def test_twelve_views_extend_the_eight_and_invert_exactly():
    v8, v12 = tta.parse("flip4+yaw+z"), tta.parse("flip4+yaw+z+scale")
    assert v12[:8] == v8 and len(v12) == 12
    assert {v.scale for v in v12[8:]} == {0.95, 1.05}
    rng = np.random.default_rng(0)
    b = np.c_[rng.uniform(-30, 30, (40, 3)), rng.uniform(0.5, 5, (40, 3)), rng.uniform(-np.pi, np.pi, 40)]
    for v in v12:
        back = tta.inverse_boxes(tta.forward_boxes(b, v), v)
        assert np.abs(back[:, :6] - b[:, :6]).max() < 1e-9
        dh = np.abs((back[:, 6] - b[:, 6] + np.pi) % (2 * np.pi) - np.pi).max()
        assert min(dh, abs(dh - np.pi)) < 1e-9
        p = np.c_[b[:, :3], np.zeros(40)].astype(np.float32)          # points move with the box centres
        assert np.abs(tta.forward_points(p, v)[:, :3] - tta.forward_boxes(b, v)[:, :3]).max() < 1e-3


def test_tail_copies_threshold_copies_only_high_boxes_and_stays_below_all():
    preds = {"f": [{"box": [0, 0, 0, 1, 1, 1, 0], "score": s, "class": "Person"} for s in (0.9, 0.5, 0.1, 0.02)]
             + [{"box": [5, 5, 0, 4, 2, 1.5, 0], "score": 0.3, "class": "Car"}]}
    out = apply_tail_copies(preds, {"Person": {"r": 0.2, "n": 4, "min_score": 0.4}})["f"]
    copies = out[len(preds["f"]):]
    assert len(copies) == 8 and all(d["class"] == "Person" for d in copies)          # 2 boxes >= 0.4, 4 copies each
    assert max(d["score"] for d in copies) < 0.02                                     # below every original Person box
    assert out[:len(preds["f"])] == preds["f"]
    assert len(apply_tail_copies(preds, {"Person": {"r": 0.2, "n": 4}})["f"]) == 5 + 16   # no threshold: every box


def test_variant_swap_replaces_tta_members_by_their_tagged_siblings():
    t8, t12 = {"tta": "flip4+yaw+z"}, {"tta": "flip4+yaw+z+scale", "tta_tag": "tta12"}
    card = {"members": {"a": {"model": "ma", "ckpt": CK}, "a_tta": {"model": "ma", "ckpt": CK, **t8},
                        "a_tta12": {"model": "ma", "ckpt": CK, **t12}, "b_tta": {"model": "mb", "ckpt": CK, **t8},
                        "c_tta": {"model": "mc", "ckpt": CK, **t8}, "c_tta12": {"model": "mc", "ckpt": CK, **t12}}}
    prior = {"Car": {"members": ["a_tta", "b_tta"], "iou": 0.7},       # a swapped, b has no sibling
             "Van": {"members": ["a", "c_tta"], "iou": 0.5},           # the plain member stays plain
             "Truck": {"members": ["b_tta", "a"], "iou": 0.3}}         # nothing to swap: no candidate
    got = variant_candidates(card, prior, ["Car", "Van", "Truck", "Person"], "tta12")
    assert got == {"Car": ("a_tta12", "b_tta"), "Van": ("a", "c_tta12")}


def test_member_tag_of_a_tagged_variant():
    assert member_tag({"ckpt": CK}) == "run1_checkpoint_epoch_40"
    assert member_tag({"ckpt": CK, "tta": "flip4+yaw+z"}) == "run1_checkpoint_epoch_40_tta"
    assert member_tag({"ckpt": CK, "tta": "flip4+yaw+z+scale", "tta_tag": "tta12"}) == "run1_checkpoint_epoch_40_tta12"
