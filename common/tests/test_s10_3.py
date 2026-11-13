"""Release 10.3: the recipe systems (common/tools/s10_3_recipe.py) on the retrained members."""
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common"))
sys.path.insert(0, str(REPO / "common" / "tools"))

KNOBS = ("route", "fusion", "calibration", "budget", "tail_copies", "final_copies", "sparse_demotion", "overhead_demotion",
         "point_rescore", "size_calibration")


def test_sibling_names():
    from s10_3_recipe import sibling
    assert sibling("voxelrcnn-rosf-g1v6", "n1") == "voxelrcnn-rosf-g1v6n1"
    assert sibling("pvrcnnpp-ros-g1v6j", "n1") == "pvrcnnpp-ros-g1v6jn1"
    assert sibling("pointpillars-ros-g1v6d2", "n1") == "pointpillars-ros-g1v6d2n1"
    assert sibling("bag-voxelrcnn-rosf-g1v6x", "n1") == "bag-voxelrcnn-rosf-g1v6n1x"
    assert sibling("bag-voxelrcnn-ros-g1v6x5", "aw") == "bag-voxelrcnn-ros-g1v6awx5"
    with pytest.raises(SystemExit):
        sibling("pointpillars-ut", "n1")


@pytest.mark.parametrize("track,new,parent,suf", [("lumpi", "routed-s10-3-l3", "routed-c0", "n1"),
                                                  ("lumpi", "routed-s10-3-l6", "routed-c0", "n1"),
                                                  ("lumpi", "routed-s10-3-l3q", "routed-c0", "pq"),   # record Section 10
                                                  ("lumpi", "routed-s10-3-l6q", "routed-c0", "pq"),
                                                  ("v2x", "routed-s10-3-v3", "routed-c1a", "aw"),
                                                  ("v2x", "routed-s10-3-v3x", "routed-c2r", "aw")])
def test_recipe_cards_keep_the_parents_knobs_and_retrain_every_member(track, new, parent, suf):
    from route_predictions import used_members
    d = REPO / f"model-{track}-track"
    if not (d / new / "model.yaml").exists():
        pytest.skip(f"{new} not made")
    n, p = (yaml.safe_load((d / x / "model.yaml").read_text()) for x in (new, parent))
    if new.endswith(("l6", "l6q")):                  # L6 = L3 + P: L3's knobs (copies fit included), not C0's tail copies
        n3 = yaml.safe_load((d / new.replace("-l6", "-l3") / "model.yaml").read_text())
        assert all(n.get(k) == n3.get(k) for k in KNOBS if k != "tail_copies") and n["members"] == n3["members"]
        assert n["final_adjust"] == yaml.safe_load((d / "routed-s10-2-l5" / "model.yaml").read_text())["final_adjust"]
        return
    assert all(n.get(k) == p.get(k) for k in KNOBS if not (track == "lumpi" and k == "tail_copies"))
    assert used_members(n) == used_members(p)
    frames = n["realism_frames"]
    assert frames == f"pcdet/g1-v6{suf}" and n["data"]["train"] == frames
    for m in used_members(n):
        mc = yaml.safe_load((d / n["members"][m]["model"] / "model.yaml").read_text())
        seeds = mc["members"] if mc.get("type") == "bag" else [n["members"][m]["model"]]
        for s in seeds:
            sc = yaml.safe_load((d / s / "model.yaml").read_text())
            assert sc["data"]["train"].endswith(suf) and sc["realism_frames"] == frames, s
    assert (d / new / "test" / "synthetic_ids.txt").read_text() == (d / parent / "test" / "synthetic_ids.txt").read_text()


def test_partial_swap_keeps_every_other_member_and_the_frames(tmp_path, monkeypatch):
    """L7 (record Section 12): --only replaces just the named single models; bags, frames and corpus stay the parent's."""
    import s10_3_recipe
    d = REPO / "model-lumpi-track"
    if not (d / "voxelrcnn-rosf-g1v6pq" / "model.yaml").exists():
        pytest.skip("re-cast members not made")
    card = yaml.safe_load((d / "routed-c0" / "model.yaml").read_text())
    mapping, bags, missing = s10_3_recipe.plan(d, card, "pq", {"voxelrcnn-rosf-g1v6", "voxelrcnn-rosn-g1v6"})
    assert not bags and not missing
    changed = {p: s for p, s in mapping.items() if p != s}
    assert changed == {"voxelrcnn-rosf-g1v6": "voxelrcnn-rosf-g1v6pq", "voxelrcnn-rosn-g1v6": "voxelrcnn-rosn-g1v6pq"}
    with pytest.raises(SystemExit):
        s10_3_recipe.plan(d, card, "pq", {"bag-voxelrcnn-rosf-g1v6x"})
