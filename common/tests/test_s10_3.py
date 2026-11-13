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


@pytest.mark.parametrize("track,new,parent", [("lumpi", "routed-s10-3-l3", "routed-c0"), ("lumpi", "routed-s10-3-l6", "routed-c0"),
                                              ("v2x", "routed-s10-3-v3", "routed-c1a"), ("v2x", "routed-s10-3-v3x", "routed-c2r")])
def test_recipe_cards_keep_the_parents_knobs_and_retrain_every_member(track, new, parent):
    from route_predictions import used_members
    d = REPO / f"model-{track}-track"
    if not (d / new / "model.yaml").exists():
        pytest.skip(f"{new} not made")
    n, p = (yaml.safe_load((d / x / "model.yaml").read_text()) for x in (new, parent))
    if new.endswith("l6"):                           # L6 = L3 + P: L3's knobs (copies fit included), not C0's tail copies
        n3 = yaml.safe_load((d / "routed-s10-3-l3" / "model.yaml").read_text())
        assert all(n.get(k) == n3.get(k) for k in KNOBS if k != "tail_copies") and n["members"] == n3["members"]
        assert n["final_adjust"] == yaml.safe_load((d / "routed-s10-2-l5" / "model.yaml").read_text())["final_adjust"]
        return
    assert all(n.get(k) == p.get(k) for k in KNOBS if not (track == "lumpi" and k == "tail_copies"))
    assert used_members(n) == used_members(p)
    suf = "n1" if track == "lumpi" else "aw"
    frames = n["realism_frames"]
    assert frames == f"pcdet/g1-v6{suf}" and n["data"]["train"] == frames
    for m in used_members(n):
        mc = yaml.safe_load((d / n["members"][m]["model"] / "model.yaml").read_text())
        seeds = mc["members"] if mc.get("type") == "bag" else [n["members"][m]["model"]]
        for s in seeds:
            sc = yaml.safe_load((d / s / "model.yaml").read_text())
            assert sc["data"]["train"].endswith(suf) and sc["realism_frames"] == frames, s
    assert (d / new / "test" / "synthetic_ids.txt").read_text() == (d / parent / "test" / "synthetic_ids.txt").read_text()
