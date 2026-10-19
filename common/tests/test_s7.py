"""S7: per-box point counts (bdc26.boxes.count_points_per_box), the sparse-box demotion stage
(route_predictions.apply_sparse_demotion and its place in merge_card) and the label visibility rule
(common/tools/filter_labels.py)."""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common" / "tools"))
sys.path.insert(0, str(REPO / "common"))

from bdc26.boxes import count_points_in_boxes, count_points_per_box  # noqa: E402
from route_predictions import apply_sparse_demotion, box_point_counts, merge_card  # noqa: E402


def _cloud(centres_counts, seed=0):
    """Points: n points uniformly inside a 0.6 x 0.6 x 1.6 m column at each centre, plus null returns."""
    rng = np.random.default_rng(seed)
    pts = [np.zeros((50, 3))]                                     # (0,0,0) nulls are not measurements
    for (x, y), n in centres_counts:
        pts.append(np.column_stack([rng.uniform(x - 0.25, x + 0.25, n), rng.uniform(y - 0.25, y + 0.25, n),
                                    rng.uniform(-1.7, -0.3, n)]))
    return np.vstack(pts)


def _ped(x, y, s):
    return {"box": [x, y, -1.0, 0.7, 0.7, 1.75, 0.0], "score": s, "class": "pedestrian"}


def test_count_per_box_counts_overlapping_boxes_independently():
    p = _cloud([((10.0, 5.0), 12)])
    b = np.array([[10.0, 5.0, -1.0, 0.7, 0.7, 1.75, 0.0], [10.05, 5.0, -1.0, 0.7, 0.7, 1.75, 0.3]])
    assert count_points_per_box(p, b).tolist() == [12, 12]
    assert count_points_in_boxes(p, b).tolist() == [12, 0]       # the label counter gives each point to one box only


def test_count_per_box_drops_nulls():
    b = np.array([[0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0]])          # a box around the sensor origin
    assert count_points_per_box(np.zeros((20, 3)), b).tolist() == [0]
    assert count_points_per_box(np.zeros((20, 3)), b, drop_null=False).tolist() == [20]


def _frames():
    pts = {"f1": _cloud([((10.0, 5.0), 12), ((30.0, -4.0), 3)]), "f2": _cloud([((-20.0, 8.0), 8), ((35.0, 20.0), 1)], seed=1)}
    preds = {"f1": [_ped(10.0, 5.0, 0.9), _ped(30.0, -4.0, 0.95),
                    {"box": [12.0, 0.0, -1.0, 4.5, 1.9, 1.6, 0.0], "score": 0.5, "class": "vehicle"}],
             "f2": [_ped(-20.0, 8.0, 0.4), _ped(35.0, 20.0, 0.8)]}
    return pts, preds


def test_sparse_demotion_ranks_below_every_other_box_and_deletes_nothing():
    pts, preds = _frames()
    out = apply_sparse_demotion(preds, {"pedestrian": 6}, lambda f: pts[f])
    assert [len(v) for v in out.values()] == [len(v) for v in preds.values()]
    kept = [d["score"] for f in out for d, d0 in zip(out[f], preds[f]) if d["class"] == "pedestrian" and d["score"] == d0["score"]]
    demoted = [d["score"] for f in out for d, d0 in zip(out[f], preds[f]) if d["class"] == "pedestrian" and d["score"] != d0["score"]]
    assert sorted(kept) == [0.4, 0.9] and len(demoted) == 2            # 3-point and 1-point boxes demoted
    assert max(demoted) < min(kept)
    assert demoted[0] > demoted[1]                                     # their order among themselves is kept (0.95 > 0.8)
    assert out["f1"][2] == preds["f1"][2]                              # other classes untouched
    assert preds["f1"][1]["score"] == 0.95                             # input not modified


def test_sparse_demotion_needs_points_and_is_a_noop_without_spec():
    pts, preds = _frames()
    assert apply_sparse_demotion(preds, None) is preds
    with pytest.raises(ValueError):
        apply_sparse_demotion(preds, {"pedestrian": 6})
    counts = box_point_counts(preds, {"pedestrian"}, lambda f: pts[f])
    assert counts["f1"].tolist() == [12, 3, -1]
    assert apply_sparse_demotion(preds, {"pedestrian": 6}, counts=counts) == apply_sparse_demotion(preds, {"pedestrian": 6}, lambda f: pts[f])


def test_merge_card_applies_the_stage_last():
    pts, preds = _frames()
    card = {"route": {"pedestrian": "m", "vehicle": "m"}, "tail_copies": {"pedestrian": {"r": 0.15, "n": 4}},
            "sparse_demotion": {"pedestrian": 6}}
    out = merge_card(card, {"m": preds}, lambda f: pts[f])
    ped = [d for v in out.values() for d in v if d["class"] == "pedestrian"]
    assert len(ped) == 4 * 5                                            # originals + 4 copies each, nothing deleted
    dense = {(round(d["box"][0], 3), round(d["box"][1], 3)): d["score"] for d in ped}
    assert dense[(10.0, 5.0)] == 0.9 and dense[(-20.0, 8.0)] == 0.4
    assert max(d["score"] for d in ped if (round(d["box"][0]), round(d["box"][1])) in ((30, -4), (35, 20))) \
        < min(d["score"] for d in ped if (round(d["box"][0]), round(d["box"][1])) in ((10, 5), (-20, 8)))
    with pytest.raises(ValueError):
        merge_card(card, {"m": preds})


def test_filter_labels_keeps_frames_and_drops_sparse_labels(tmp_path, monkeypatch):
    src = tmp_path / "v2x-track" / "pcdet" / "src"
    for d in ("points", "labels", "ImageSets"):
        (src / d).mkdir(parents=True)
    np.save(src / "points" / "000001.npy", _cloud([((10.0, 5.0), 12), ((30.0, -4.0), 3)]).astype(np.float32))
    (src / "labels" / "000001.txt").write_text("10.0 5.0 -1.0 0.7 0.7 1.75 0.0 pedestrian\n30.0 -4.0 -1.0 0.7 0.7 1.75 0.0 pedestrian\n"
                                               "12.0 0.0 -1.0 4.5 1.9 1.6 0.0 vehicle\n")
    (src / "ImageSets" / "train.txt").write_text("000001\n")
    (src / "ImageSets" / "val.txt").write_text("")
    r = subprocess.run([sys.executable, str(REPO / "common/tools/filter_labels.py"), "--track", "v2x", "--src", str(src),
                        "--dst", str(src.parent / "dst"), "--min-points", "pedestrian=6", "--workers", "1"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    dst = src.parent / "dst"
    lines = (dst / "labels" / "000001.txt").read_text().splitlines()
    assert len(lines) == 2 and lines[0].endswith("pedestrian") and lines[1].endswith("vehicle")   # vehicle has no rule
    assert (dst / "points").is_symlink()
    card = yaml.safe_load((dst / "dataset.yaml").read_text())
    assert card["label_rule"]["min_points_per_box"] == {"pedestrian": 6} and card["label_rule_removed"] == {"pedestrian": 1}
