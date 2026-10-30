#!/usr/bin/env python
"""Reproduce a scored submission of a routed model: the exact weights, a test-run script, and checks against the zip.

    python common/tools/reproduce_submission.py model-lumpi-track/routed-g7 --tag r5                 # re-merge check
    python common/tools/reproduce_submission.py model-lumpi-track/routed-g7 --tag r5 --write-script  # test/reproduce_r5.sh
    python common/tools/reproduce_submission.py model-lumpi-track/routed-g7 --tag r5 --markdown      # block for the record
    python common/tools/reproduce_submission.py model-lumpi-track/routed-g7 --tag r5 --compare <predictions.json>

The scored zip is the file in submissions/*_<tag>/ whose md5 equals the manifest's (the upload copy). Re-merge check:
the saved per-member test predictions (test/output/predictions_<member>.json) merged with the committed model.yaml
(route, calibration, fusion, score floors, tail copies) must give the zip's predictions.json exactly. The script
test/reproduce_<tag>.sh re-runs the test inference of every used member from its checkpoint (paths and md5 below),
merges, compares with the zip, repackages the same 50 frames into test/output/repro-<tag>/ (git-ignored; no upload
copy, no registry row), runs the official kit scorer and compares predictions and frames with the scored zip. The comparison is exact (boxes and scores to 1e-4). On a GPU no other job uses, inference is bit-identical
(S1 PointPillars, and on 2026-10-16 all seven V2X R5 members including Voxel R-CNN and PV-RCNN++: maximum difference
0.0). A run sharing its GPU with a training job differed slightly (one PV-RCNN++ member: median 1e-5, 99th percentile
0.04 m and 0.0014 in score; most likely the cuDNN algorithm choice under load), so the boxes are also matched per frame
and class (Hungarian on centers, within 0.5 m) and the run is "equivalent" when no box with score above 0.3 is
unmatched and 99% of the matched boxes agree within 0.1 m and 0.01 in score. Run reproductions on an idle GPU. Checkpoints are not in git; their md5s are
written to validation/results/reproduce_<tag>.json so a later run can prove the same weights were used.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import yaml

from _common import REPO, member_tag, model_info
from route_predictions import frame_points, merge_card, used_members

TTA_PP = "test/postprocess_tta.yaml"


def md5(path: Path, cache: dict) -> str | None:
    key = str(path)
    if key in cache:
        return cache[key]
    if not path.exists():
        return None
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    cache[key] = h.hexdigest()
    return cache[key]


def scored_zip(model_dir: Path, tag: str) -> tuple[Path, dict]:
    subs = sorted(model_dir.glob(f"submissions/*_{tag}"))
    if not subs:
        raise SystemExit(f"no submissions/*_{tag} in {model_dir}")
    sub = subs[0]
    man = json.loads((sub / "manifest.json").read_text())
    want = (man.get("upload_file") or {}).get("md5") or man.get("zip_md5")
    cache: dict = {}
    for z in sorted(sub.glob("*.zip"), key=lambda z: z.name == "submission.zip"):   # the committed upload copy first
        if md5(z, cache) == want:
            return z, man
    raise SystemExit(f"no zip in {sub} has the manifest md5 {want}")


def members_inventory(model_dir: Path, card: dict, cache: dict) -> list[dict]:
    rows = []
    for key in used_members(card):
        m = card["members"][key]
        md = model_dir.parent / m["model"]
        mcard = yaml.safe_load((md / "model.yaml").read_text())
        tta = m.get("tta")
        variant = (m.get("tta_tag") or "tta") if tta else "plain"            # S8: tta12 for the 12-view variant
        if mcard.get("type") == "bag":
            seeds = []
            for s in mcard["members"]:
                ck = model_dir.parent / s / "train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth"
                seeds.append({"model": f"{model_dir.parent.name}/{s}", "ckpt": str(ck.relative_to(REPO)), "md5": md5(ck, cache),
                              "postprocess": f"{model_dir.parent.name}/{s}/" + (f"test/postprocess_{variant}.yaml" if tta else "test/postprocess.yaml")})
            rows.append({"key": key, "model": f"{model_dir.parent.name}/{m['model']}", "bag": seeds, "tta": tta, "variant": variant,
                         "iou": mcard["iou"]})
            continue
        ck = md / m["ckpt"]
        pp = m.get("postprocess", TTA_PP) if tta else "test/postprocess.yaml"
        rows.append({"key": key, "model": f"{model_dir.parent.name}/{m['model']}", "ckpt": str(ck.relative_to(REPO)),
                     "md5": md5(ck, cache), "exists": ck.exists(), "tta": tta, "postprocess": f"{model_dir.parent.name}/{m['model']}/{pp}"})
    return rows


def compare(pred_a: dict, pred_b: dict, tol: float = 1e-4) -> dict:
    keys_equal = set(pred_a) == set(pred_b)
    n_a = sum(len(v) for v in pred_a.values()); n_b = sum(len(v) for v in pred_b.values())
    worst, frames_diff = 0.0, 0
    for f in pred_a:
        A = sorted((d["class"], round(d["score"], 6), *d["box"]) for d in pred_a.get(f, []))
        B = sorted((d["class"], round(d["score"], 6), *d["box"]) for d in pred_b.get(f, []))
        if len(A) != len(B) or any(x[0] != y[0] for x, y in zip(A, B)):
            frames_diff += 1; continue
        d = max((abs(u - v) for x, y in zip(A, B) for u, v in zip(x[1:], y[1:])), default=0.0)
        worst = max(worst, d)
        frames_diff += d > tol
    return {"frames_equal_keys": keys_equal, "boxes": [n_a, n_b], "frames_differing": frames_diff, "max_abs_diff": worst,
            "identical_within_tol": keys_equal and n_a == n_b and frames_diff == 0}


def match_compare(pred_a: dict, pred_b: dict, gate: float = 0.5, hi: float = 0.3) -> dict:
    """GPU-nondeterminism check: match the boxes of each frame and class by center (Hungarian, within `gate` m)."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    dc, ds, unmatched_hi, unmatched = [], [], 0, 0
    for f in set(pred_a) | set(pred_b):
        A_, B_ = pred_a.get(f, []), pred_b.get(f, [])
        for c in {d["class"] for d in A_} | {d["class"] for d in B_}:
            A = [d for d in A_ if d["class"] == c]
            B = [d for d in B_ if d["class"] == c]
            mA, mB = set(), set()
            if A and B:
                D = np.linalg.norm(np.array([d["box"][:3] for d in A])[:, None] - np.array([d["box"][:3] for d in B])[None], axis=2)
                for x, y in zip(*linear_sum_assignment(D)):
                    if D[x, y] < gate:
                        mA.add(x); mB.add(y)
                        dc.append(float(D[x, y])); ds.append(abs(A[x]["score"] - B[y]["score"]))
            rest = [d["score"] for k, d in enumerate(A) if k not in mA] + [d["score"] for k, d in enumerate(B) if k not in mB]
            unmatched += len(rest)
            unmatched_hi += sum(sc_ > hi for sc_ in rest)
    p99c = float(np.percentile(dc, 99)) if dc else 0.0
    p99s = float(np.percentile(ds, 99)) if ds else 0.0
    return {"matched": len(dc), "unmatched": unmatched, f"unmatched_score_above_{hi}": unmatched_hi,
            "center_diff_p99_m": p99c, "score_diff_p99": p99s, "center_diff_median_m": float(np.median(dc)) if dc else 0.0,
            "equivalent": unmatched_hi == 0 and p99c < 0.1 and p99s < 0.01}


def write_script(model_dir: Path, card: dict, track, tag: str, rows: list[dict], man: dict, zpath: Path) -> Path:
    rel = model_dir.relative_to(REPO)
    t = track.name.replace("-track", "")
    sub = zpath.parent
    lines = ["#!/usr/bin/env bash",
             f"# Reproduce {card.get('strategy', '')} {track.name} submission '{tag}' ({rel}): test-frame inference with the exact",
             "# checkpoints, merge with the committed model.yaml, compare with the scored zip, repackage the same 50 frames, kit check.",
             f"# Generated by common/tools/reproduce_submission.py; scored zip {zpath.relative_to(REPO)} (md5 {man.get('zip_md5')}).",
             "# Usage: CUDA_VISIBLE_DEVICES=0 bash " + str(rel / "test" / f"reproduce_{tag}.sh"),
             "set -euo pipefail", 'cd "$(dirname "${BASH_SOURCE[0]}")/../../.."      # the repository root (portable)',
             "source common/env/activate.sh",
             f"OUT={rel}/test/output/repro_{tag}", "mkdir -p $OUT"]
    preds = []
    for r in rows:
        if "bag" in r:
            lines.append(f"# member {r['key']}: seed bag {r['model']} ({len(r['bag'])} seeds, TTA {r['tta'] or 'off'}); seeds: " +
                         ", ".join(f"{s['ckpt']} (md5 {s['md5']})" for s in r["bag"]))
            lines.append(f"python common/tools/bag_predictions.py {r['model'].replace(model_dir.parent.name, 'model-' + t + '-track', 1)} "
                         f"--kit --variant {r['variant']} --refresh --cache-dir $OUT/bag_{r['key']} "
                         f"--out $OUT/predictions_{r['key']}.json")
        else:
            md = r["model"]
            lines.append(f"# member {r['key']}: {md}, checkpoint md5 {r['md5']}")
            cmd = f"python common/tools/pcdet_predict.py {md} --ckpt {r['ckpt']} --frames kit --postprocess {r['postprocess']}"
            if r["tta"]:
                cmd += f" --tta {r['tta']}"
            lines.append(cmd + f" --out $OUT/predictions_{r['key']}.json")
        preds.append(f"--pred {r['key']}=$OUT/predictions_{r['key']}.json")
    lines.append(f"python common/tools/route_predictions.py merge {rel} {' '.join(preds)} --out $OUT/predictions.json")
    lines.append(f"python common/tools/reproduce_submission.py {rel} --tag {tag} --compare $OUT/predictions.json")
    syn = man.get("synthetic_source") or card.get("realism_frames")
    ids = (sub / "synthetic_ids.txt").relative_to(REPO)
    lines += ["# the 50 realism frames: from the synthetic corpus when it is present (a check that it still gives the scored frames),",
              "# else from the scored zip itself (a fresh clone has no corpus; the zip is in git)",
              f"if [ -d \"$BDC_DATA/{track.name}/{syn}/points\" ]; then SYN=(--syn-split val --syn-list {ids}); "
              f"else SYN=(--syn-zip {zpath.relative_to(REPO)} --syn-list {ids}); fi",
              f"python common/tools/package_submission.py {rel} --tag repro-{tag} --pred $OUT/predictions.json --synthetic {syn} "
              f"\"${{SYN[@]}}\" --team ${{BDC_TEAM:-KarmaRV}} --ckpt 'reproduction of {tag}' --reproduction",
              f"Z={rel}/test/output/repro-{tag}/submission.zip",
              f"python common/tools/check_submission.py --track {t} $Z --official",
              f"python common/tools/reproduce_submission.py {rel} --tag {tag} --compare-zip $Z     # predictions and frames against the scored zip"]
    out = model_dir / "test" / f"reproduce_{tag}.sh"
    out.write_text("\n".join(lines) + "\n")
    out.chmod(0o755)
    return out


def markdown(model_dir: Path, card: dict, track, tag: str, rows: list[dict], man: dict, zpath: Path, check: dict) -> str:
    rel = model_dir.relative_to(REPO)
    out = [f"**Reproduce ({track.name.replace('-track', '').upper() if 'v2x' in track.name else 'LUMPI'}, `{rel}`, tag `{tag}`).** "
           f"{'Scored' if man.get('codabench_submission_id') else 'Packaged'} zip `{zpath.relative_to(REPO)}` (md5 `{man.get('zip_md5')}`, CodaBench {man.get('codabench_submission_id') or 'not yet uploaded'}); "
           f"realism frames `{man.get('synthetic_source')}` listed in `{(zpath.parent / 'synthetic_ids.txt').relative_to(REPO)}`. "
           f"Re-merge of the saved member predictions: {'identical' if check['identical_within_tol'] else 'DIFFERENT'} "
           f"({check['boxes'][0]} boxes).", "",
           "| Member | Model folder | Weights (epoch 40) | md5 | Release asset | TTA | Post-processing |", "|---|---|---|---|---|---|---|"]
    assets, version = {}, None                       # checkpoints published as release assets (releases/<tag>/weights.json)
    for mf in sorted(REPO.glob("releases/*/weights.json")):
        m = json.loads(mf.read_text())
        for a in m["assets"]:
            assets.setdefault(a["path"], f"{m['tag']}: `{a['name']}`")
        for v in m["versions"]:
            if v["model"] == str(rel) and v["submission_zip"] == str(zpath.relative_to(REPO)):
                version = (m["tag"], v["version"])
    for r in rows:
        for s in (r["bag"] if "bag" in r else [r]):
            key = f"`{r['key']}`" + (" (bag)" if "bag" in r else "")
            out.append(f"| {key} | `{s['model']}` | `{s['ckpt']}` | `{(s['md5'] or 'missing')[:12]}` | {assets.get(s['ckpt'], '-')} | "
                       f"{r['tta'] or '-'} | `{s['postprocess']}` |")
    out += ["", "```bash"]
    if version:
        out.append(f"python common/tools/release_weights.py fetch --tag {version[0]} --version {version[1]}   # the weights above, md5-verified")
    out += [f"CUDA_VISIBLE_DEVICES=0 bash {rel}/test/reproduce_{tag}.sh     # inference with these weights, merge, compare, repackage, kit check"]
    if (model_dir / "test" / f"reproduce_{tag}_validation.sh").exists():
        out.append(f"CUDA_VISIBLE_DEVICES=0 bash {rel}/test/reproduce_{tag}_validation.sh   # realval-A/B from the weights against the recorded scorecard")
    out += [f"python common/tools/reproduce_submission.py {rel} --tag {tag}   # quick check: re-merge the saved member predictions", "```"]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--write-script", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--compare", default=None, help="a predictions.json to compare with the scored zip")
    ap.add_argument("--compare-zip", default=None, help="a repackaged zip: compare its predictions and its 50 frames with the scored zip")
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    zpath, man = scored_zip(model_dir, a.tag)
    with zipfile.ZipFile(zpath) as z:
        scored = json.loads(z.read("predictions.json"))
    if a.compare_zip:
        import hashlib
        with zipfile.ZipFile(a.compare_zip) as z2, zipfile.ZipFile(zpath) as z1:
            new = json.loads(z2.read("predictions.json"))
            fr = lambda z: [hashlib.md5(z.read(n)).hexdigest() for n in sorted(z.namelist()) if n.startswith("synthetic/")]
            frames_equal = fr(z1) == fr(z2)
        res = compare(new, scored)
        if not res["identical_within_tol"]:
            res["gpu_nondeterminism_check"] = match_compare(new, scored)
        res["synthetic_frames_identical"] = frames_equal
        print(json.dumps(res, indent=2))
        ok = (res["identical_within_tol"] or res["gpu_nondeterminism_check"]["equivalent"]) and frames_equal
        print("reproduction:", ("IDENTICAL" if res["identical_within_tol"] else "EQUIVALENT (GPU nondeterminism: run it on an idle GPU for an exact match)")
              if ok else "DIFFERENT", f"(scored zip {zpath.relative_to(REPO)}; frames {'identical' if frames_equal else 'DIFFERENT'})")
        raise SystemExit(0 if ok else 1)
    if a.compare:
        new = json.loads(Path(a.compare).read_text())
        res = compare(new, scored)
        if not res["identical_within_tol"]:
            res["gpu_nondeterminism_check"] = match_compare(new, scored)
        print(json.dumps(res, indent=2))
        ok = res["identical_within_tol"] or res["gpu_nondeterminism_check"]["equivalent"]
        print("reproduction:", "IDENTICAL" if res["identical_within_tol"] else
              "EQUIVALENT (GPU nondeterminism: run it on an idle GPU for an exact match)" if ok else "DIFFERENT")
        raise SystemExit(0 if ok else 1)
    cache_path = model_dir / "validation" / "results" / f"reproduce_{a.tag}.json"
    cache = json.loads(cache_path.read_text()).get("md5_cache", {}) if cache_path.exists() else {}
    rows = members_inventory(model_dir, card, cache)
    saved = {}
    for r in rows:
        f = model_dir / "test" / "output" / f"predictions_{r['key']}.json"
        saved[r["key"]] = json.loads(f.read_text()) if f.exists() else None
    if any(v is None for v in saved.values()):
        check = {"identical_within_tol": False, "boxes": [0, 0], "note": "saved member predictions missing: " +
                 ", ".join(k for k, v in saved.items() if v is None)}
    else:
        check = compare(merge_card(card, saved, frame_points(track, "kit")), scored, tol=1e-9)
    res = {"model": card["name"], "tag": a.tag, "scored_zip": str(zpath.relative_to(REPO)), "zip_md5": man.get("zip_md5"),
           "codabench": man.get("codabench_submission_id"), "remerge_check": check, "members": rows, "md5_cache": cache}
    cache_path.write_text(json.dumps(res, indent=2))
    print(f"{card['name']} {a.tag}: re-merge {'identical' if check['identical_within_tol'] else 'DIFFERENT'} {check}")
    missing = [r["key"] for r in rows if "bag" not in r and not r.get("exists")]
    if missing:
        print("MISSING checkpoints:", missing)
    if a.write_script:
        print("wrote", write_script(model_dir, card, track, a.tag, rows, man, zpath))
    if a.markdown:
        print(markdown(model_dir, card, track, a.tag, rows, man, zpath, check))


if __name__ == "__main__":
    main()
