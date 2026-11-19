"""S6: seed bags (bag_predictions), class freezing (freeze_classes), reproduction check (reproduce_submission.compare),
the pipeline's queue files (common/pipeline/common.sh) and the integrity of every bag folder."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common" / "tools"))

from bag_predictions import fuse_files  # noqa: E402
from reproduce_submission import compare, match_compare  # noqa: E402
from route_predictions import member_weights  # noqa: E402

IOU = {"default": 0.5, "Car": 0.7}


def _dets(seed=0, n_frames=6, n=5):
    rng = np.random.default_rng(seed)
    out = {}
    for k in range(n_frames):
        b = np.column_stack([rng.uniform(-30, 30, (n, 2)), np.full((n, 1), -1.0), np.tile([4.2, 1.8, 1.5], (n, 1)),
                             rng.uniform(-3, 3, (n, 1))])
        out[f"{k:06d}"] = [{"box": [float(v) for v in x], "score": float(s), "class": "Car"}
                           for x, s in zip(b, rng.uniform(0.1, 1.0, n))]
    return out


def _canon(pred):
    return {f: sorted((d["class"], round(d["score"], 6), *[round(v, 6) for v in d["box"]]) for d in v) for f, v in pred.items()}


def test_bag_of_identical_seeds_is_the_seed(tmp_path):
    p = _dets()
    f = tmp_path / "seed.json"
    f.write_text(json.dumps(p))
    assert _canon(fuse_files([f, f, f], IOU)) == _canon(p)


def test_bag_demotes_a_box_only_one_seed_finds(tmp_path):
    p = _dets(n_frames=1)
    lone = {"box": [80.0, 80.0, -1.0, 4.2, 1.8, 1.5, 0.0], "score": 0.9, "class": "Car"}
    files = []
    for k in range(3):
        q = json.loads(json.dumps(p))
        if k == 0:
            q["000000"].append(lone)
        files.append(tmp_path / f"s{k}.json")
        files[-1].write_text(json.dumps(q))
    fused = fuse_files(files, IOU)["000000"]
    far = [d for d in fused if d["box"][0] > 70]
    assert len(far) == 1 and abs(far[0]["score"] - 0.9 / 3) < 1e-6     # soft vote: averaged over all three seeds
    assert len(fused) == len(p["000000"]) + 1


def test_compare_tolerates_gpu_jitter_only():
    a = _dets(1)
    b = json.loads(json.dumps(a))
    assert compare(a, b)["identical_within_tol"]
    b["000002"][0]["box"][0] += 5e-5
    assert compare(a, b)["identical_within_tol"]
    b["000002"][0]["box"][0] += 1e-2
    r = compare(a, b)
    assert not r["identical_within_tol"] and r["frames_differing"] == 1
    c = json.loads(json.dumps(a))
    c["000003"].pop()
    assert not compare(a, c)["identical_within_tol"]



def test_match_compare_accepts_gpu_jitter_and_rejects_a_moved_box():
    rng = np.random.default_rng(3)
    a = _dets(2)
    b = json.loads(json.dumps(a))
    for v in b.values():
        for d in v:
            d["box"] = [x + float(rng.normal(0, 1e-4)) for x in d["box"]]
            d["score"] += float(rng.normal(0, 1e-5))
    b["000001"].append({"box": [50.0, 50.0, -1.0, 4.2, 1.8, 1.5, 0.0], "score": 0.05, "class": "Car"})   # low-score extra
    assert match_compare(a, b)["equivalent"]
    b["000004"][0]["box"][0] += 2.0                                                                    # a real change
    b["000004"][0]["score"] = 0.9
    assert not match_compare(a, b)["equivalent"]


def test_match_compare_names_a_fusion_merge_split():
    """One fused Truck box in one run against two unfused ones in the other (an IoU across the fusion threshold): not
    equivalent under the strict rule, and listed as a merge/split; a lone extra box is not."""
    from reproduce_submission import differ_label
    a = {"007209": [{"box": [23.53, 35.33, -0.53, 11.41, 2.87, 3.22, -2.33], "score": 0.45, "class": "Truck"}]}
    b = {"007209": [{"box": [23.98, 35.82, -0.54, 11.77, 3.0, 3.2, -2.33], "score": 0.24, "class": "Truck"},
                    {"box": [22.58, 34.34, -0.54, 10.16, 2.73, 3.23, -2.32], "score": 0.21, "class": "Truck"}]}
    b["007209"][0]["box"][0] += 0.6                    # beyond the 0.5 m match gate, inside the fused box's footprint
    m = match_compare(a, b)
    assert not m["equivalent"] and m["unmatched_above_0.3"][0]["merge_split_with"]
    assert m["unmatched_above_hi_all_merge_split"]
    assert "merge/split" in differ_label({"gpu_nondeterminism_check": m})
    lone = {"007209": a["007209"] + [{"box": [-20.0, 5.0, -0.5, 9.0, 2.8, 3.2, 0.0], "score": 0.6, "class": "Truck"}]}
    m2 = match_compare(lone, a)
    assert not m2["equivalent"] and not m2["unmatched_above_hi_all_merge_split"]
    assert differ_label({"gpu_nondeterminism_check": m2}) == "DIFFERENT"


def _routed(path: Path, route_car: str, members: dict, fusion=None):
    path.mkdir(parents=True)
    card = {"name": path.name, "members": members, "route": {"Car": route_car, "Van": route_car},
            "calibration": {"Car": {"dz": 0.1}}, "fusion": fusion, "budget": {"Car": 0.05}}
    (path / "model.yaml").write_text(yaml.safe_dump(card, sort_keys=False))


def test_freeze_copies_the_reference_class(tmp_path):
    m = {"a": {"model": "x", "ckpt": "c"}, "b": {"model": "y", "ckpt": "c"}}
    _routed(tmp_path / "ref", "a", m, fusion={"Car": {"members": ["a", "b"], "iou": 0.5}})
    _routed(tmp_path / "new", "b", m)
    tool = REPO / "common" / "tools" / "freeze_classes.py"
    subprocess.run([sys.executable, str(tool), str(tmp_path / "new"), "--from", str(tmp_path / "ref"), "Car"], check=True,
                   capture_output=True)
    card = yaml.safe_load((tmp_path / "new" / "model.yaml").read_text())
    assert card["route"] == {"Car": "a", "Van": "b"}                 # only the frozen class changes
    assert card["fusion"]["Car"] == {"members": ["a", "b"], "iou": 0.5}


def test_freeze_refuses_a_changed_member(tmp_path):
    _routed(tmp_path / "ref", "a", {"a": {"model": "x", "ckpt": "c"}})
    _routed(tmp_path / "new", "a", {"a": {"model": "x", "ckpt": "c", "tta": "flip4+yaw+z"}})
    tool = REPO / "common" / "tools" / "freeze_classes.py"
    r = subprocess.run([sys.executable, str(tool), str(tmp_path / "new"), "--from", str(tmp_path / "ref"), "Car"],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "differs" in r.stderr


def test_queue_pops_every_job_once_under_concurrency(tmp_path):
    q = tmp_path / "q.txt"
    q.write_text("".join(f"job{k}\n" for k in range(40)))
    script = (f"source {REPO}/common/pipeline/common.sh; RUN={tmp_path}; "
              f"for w in 1 2 3 4; do (while j=$(qpop {q}); [ -n \"$j\" ]; do echo $j >> {tmp_path}/out_$w; done) & done; wait")
    subprocess.run(["bash", "-c", script], check=True)
    got = sorted(line for w in range(1, 5) if (tmp_path / f"out_{w}").exists() for line in (tmp_path / f"out_{w}").read_text().split())
    assert got == sorted(f"job{k}" for k in range(40)) and q.read_text() == ""


@pytest.mark.parametrize("bag", sorted(REPO.glob("model-*-track/bag-*")), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_bag_folders_are_seeds_of_one_configuration(bag):
    card = yaml.safe_load((bag / "model.yaml").read_text())
    assert card["type"] == "bag" and len(card["members"]) >= 2 and "default" in card["iou"]
    cfgs = set()
    corpora = {c.strip() for c in str(card["data"]["train"]).split("+")}   # S7 draw bags list each generator draw
    for m in card["members"]:
        md = bag.parent / m
        mc = yaml.safe_load((md / "model.yaml").read_text())
        assert mc["data"]["train"] in corpora, m
        text = (md / "train" / "pcdet_model.yaml").read_text()
        # the per-member score blend is an inference knob chosen after training; everything else must be equal
        cfgs.add("\n".join(line for line in text.splitlines() if "SCORE_BLEND_ALPHA" not in line))
    assert len(cfgs) == 1, f"{bag.name}: members differ in their training configuration"


def test_bag_and_its_seed_share_weights(tmp_path):
    for m, card in (("seed-a", {"name": "seed-a"}), ("seed-b", {"name": "seed-b"}), ("other", {"name": "other"}),
                    ("bag-x", {"name": "bag-x", "type": "bag", "members": ["seed-a", "seed-b"], "iou": {"default": 0.5}})):
        (tmp_path / m).mkdir()
        (tmp_path / m / "model.yaml").write_text(yaml.safe_dump(card))
    ck = "train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth"
    card = {"members": {"a": {"model": "seed-a", "ckpt": ck}, "a_tta": {"model": "seed-a", "ckpt": ck, "tta": "flip4+yaw+z"},
                        "o": {"model": "other", "ckpt": ck},
                        "bag_tta": {"model": "bag-x", "ckpt": "train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth", "tta": "flip4+yaw+z"}}}
    W = {n: member_weights(tmp_path / "routed", card, n) for n in card["members"]}
    ok = lambda *ns: len(set().union(*(W[n] for n in ns))) == sum(len(W[n]) for n in ns)
    assert not ok("a", "a_tta") and not ok("bag_tta", "a") and ok("bag_tta", "o") and ok("a", "o")


def test_github_slug_from_remote_urls():
    from _github import slug_from_url
    assert slug_from_url("https://github.com/karmarv/utsim2real-bdc26.git") == "karmarv/utsim2real-bdc26"
    assert slug_from_url("git@github.com:karmarv/utsim2real-bdc26.git\n") == "karmarv/utsim2real-bdc26"
    assert slug_from_url("https://github.com/karmarv/utsim2real-bdc26") == "karmarv/utsim2real-bdc26"


def test_validation_plan_expands_bags_into_seed_jobs(tmp_path):
    from reproduce_validation import plan
    for m, card in (("seed-a", {"name": "seed-a"}), ("seed-b", {"name": "seed-b"}), ("other", {"name": "other"}),
                    ("bag-x", {"name": "bag-x", "type": "bag", "members": ["seed-a", "seed-b"], "iou": {"default": 0.5}})):
        (tmp_path / m).mkdir()
        (tmp_path / m / "model.yaml").write_text(yaml.safe_dump(card))
    ck = "train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth"
    card = {"route": {"Car": "o", "Van": "o"}, "fusion": {"Car": {"members": ["bag_tta", "o"], "iou": 0.7}},
            "members": {"o": {"model": "other", "ckpt": ck},
                        "bag_tta": {"model": "bag-x", "ckpt": "train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth", "tta": "flip4+yaw+z"}}}
    jobs, how = plan(tmp_path / "routed", card)
    assert sorted(j["id"] for j in jobs) == ["other", "seed-a_tta", "seed-b_tta"]
    assert how["bag_tta"] == {"bag": ["seed-a_tta", "seed-b_tta"], "iou": {"default": 0.5}} and how["o"] == {"job": "other"}
    assert all(j["postprocess"] == "test/postprocess_tta.yaml" for j in jobs if j["tta"])


@pytest.mark.skipif(not (REPO / "releases").exists(), reason="no release manifests")
@pytest.mark.parametrize("manifest", sorted(REPO.glob("releases/*/weights.json")), ids=lambda p: p.parent.name)
def test_release_manifest_is_consistent(manifest):
    m = json.loads(manifest.read_text())
    names = [a["name"] for a in m["assets"]]
    assert len(names) == len(set(names))
    for v in m["versions"]:
        z = next(a for a in m["assets"] if a["path"] == v["submission_zip"])
        assert z["md5"] == v["zip_md5"]                                  # the asset is the scored upload copy
        man = json.loads((REPO / v["submission_zip"]).parent.joinpath("manifest.json").read_text())
        assert man["upload_file"]["md5"] == v["zip_md5"] and str(man.get("codabench_submission_id")) == str(v["codabench_id"])
        for c in v["checkpoints"]:
            a = next(a for a in m["assets"] if a["name"] == c)
            assert a["path"].endswith("train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth") and v["version"] in a["used_by"]
        assert (REPO / v["reproduce_test"]).exists() and (REPO / v["reproduce_validation"]).exists()
