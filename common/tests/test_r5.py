"""R5: walker tail copies (route_predictions.apply_tail_copies) and iterative density-prior fitting (density.fit base)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from bdc26 import density  # noqa: E402
from bdc26.evalap import ap_for_class  # noqa: E402
from route_predictions import apply_tail_copies  # noqa: E402


def _toy(seed=0, n_frames=20):
    rng = np.random.default_rng(seed)
    preds, gts = {}, {}
    for k in range(n_frames):
        g = np.column_stack([rng.uniform(-20, 20, (6, 2)), np.full((6, 1), -1.2), np.tile([0.7, 0.7, 1.7, 0.0], (6, 1))])
        b = g.copy()
        b[:, :2] += rng.normal(0, 0.15, (6, 2))                     # walker-like localization noise
        fp = np.column_stack([rng.uniform(-20, 20, (4, 2)), np.full((4, 1), -1.2), np.tile([0.7, 0.7, 1.7, 0.0], (4, 1))])
        boxes = np.vstack([b, fp])
        scores = rng.uniform(0.05, 1.0, len(boxes))
        preds[f"f{k}"] = [{"box": list(x), "score": float(s), "class": "pedestrian"} for x, s in zip(boxes, scores)]
        gts[f"f{k}"] = g
    return preds, gts


def _ap(preds, gts):
    fr = []
    for f, g in gts.items():
        v = [d for d in preds[f] if d["class"] == "pedestrian"]
        fr.append((np.array([d["box"] for d in v]).reshape(-1, 7), np.array([d["score"] for d in v]), g))
    return ap_for_class(fr, 0.5, "3d")["AP_R40"]


def test_tail_copies_rank_below_every_original():
    preds, _ = _toy()
    out = apply_tail_copies(preds, {"pedestrian": {"r": 0.15, "n": 4}})
    orig = [d["score"] for v in preds.values() for d in v]
    new = [d["score"] for f in out for d in out[f][len(preds[f]):]]
    assert len(new) == 4 * len(orig)
    assert max(new) < min(orig)
    for f in preds:                                                   # originals untouched and first
        assert out[f][:len(preds[f])] == preds[f]


def test_tail_copies_never_lower_ap():
    for seed in range(5):
        preds, gts = _toy(seed)
        base = _ap(preds, gts)
        for r in (0.1, 0.15, 0.2):
            assert _ap(apply_tail_copies(preds, {"pedestrian": {"r": r, "n": 4}}), gts) >= base - 1e-12


def test_tail_copies_other_classes_unchanged():
    preds, _ = _toy()
    preds["f0"].append({"box": [0, 0, -1, 4, 2, 1.6, 0], "score": 0.5, "class": "vehicle"})
    out = apply_tail_copies(preds, {"pedestrian": {"r": 0.15, "n": 4}})
    assert sum(d["class"] == "vehicle" for v in out.values() for d in v) == 1


def test_density_fit_base_is_multiplicative():
    rng = np.random.default_rng(0)
    rng_box = (-40, -40, -5, 40, 40, 5)
    real = [np.column_stack([rng.uniform(-40, 40, (5000, 2)), rng.uniform(-3, 0, 5000)]) for _ in range(3)]
    syn = [np.column_stack([rng.uniform(-40, 0, (5000, 2)), rng.uniform(-3, 0, 5000)]) for _ in range(3)]
    p1 = density.fit(real, syn, rng_box, cell=(8, 8, 2.5), alpha=0.1, clip=(0.01, 100))
    p2 = density.fit(real, syn, rng_box, cell=(8, 8, 2.5), alpha=0.1, clip=(0.01, 100), base=p1)
    assert np.allclose(p2.ratio, np.clip(p1.ratio ** 2, 0.01, 100))     # same data twice: ratios multiply
    try:
        density.fit(real, syn, rng_box, cell=(4, 4, 2.5), base=p1)
        raise AssertionError("grid mismatch not detected")
    except ValueError:
        pass
