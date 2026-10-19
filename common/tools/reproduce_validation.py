#!/usr/bin/env python
"""Reproduce the real-validation numbers of a packaged version from its checkpoints (no saved predictions needed).

    python common/tools/reproduce_validation.py model-lumpi-track/routed-g8 --tag s6 --write-script   # test/reproduce_s6_validation.sh
    python common/tools/reproduce_validation.py model-lumpi-track/routed-g8 --tag s6 --jobs           # one inference command per line
    python common/tools/reproduce_validation.py model-lumpi-track/routed-g8 --tag s6 --score          # fuse, merge, evaluate, compare

Every used member (for a bag: every seed) predicts realval-A (split val) and realval-B (split valB) with its epoch-40
checkpoint and its committed post-processing file, exactly as validation/tune_and_eval.sh wrote the predictions the
portfolio was selected on, into <model>/validation/output/repro_<tag>/. --score fuses each bag from those seed
predictions (bag_predictions.fuse_files), merges the routed model with the committed model.yaml
(route_predictions.merge_card: route, calibration, fusion, score floors, tail copies, S7 sparse stage), evaluates with the official
metric and compares the per-class AP on realval-A, realval-B and late-A with validation/results/scorecard.json:
IDENTICAL within 1e-4 per class, EQUIVALENT within 1e-3 per class and 5e-4 per split mAP (the last digits of GPU
inference: a member whose recorded predictions were written on a GPU shared with a training job differs by about 1e-3
in score and a few cm in position; S6 close-out: 41 of 48 member files bit-identical, the rest within 4e-4 AP per
class), else DIFFERENT. On a machine that has the recorded member predictions, each reproduced file is also compared
with its recorded one. Writes validation/results/reproduce_<tag>_validation.json.
Needs the prepared real validation data ($BDC_DATA/<track>/pcdet/realval-v1; data-<track>/README.md), which is
licensed and not redistributed, and the checkpoints (git-ignored; common/tools/release_weights.py fetch).
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

from _common import REPO, data_path, model_info

CK = "train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth"
TTA_PP = "test/postprocess_tta.yaml"


def plan(model_dir: Path, card: dict) -> tuple[list[dict], dict]:
    """Inference jobs (one per detector view: model folder, TTA, post-processing) and, per used member, how its
    predictions are made from them ({"job": id} or {"bag": [ids], "iou": ...})."""
    from route_predictions import used_members
    jobs, how = {}, {}

    def job(model: str, ckpt: str, tta, pp: str) -> str:
        jid = f"{model}{'_tta' if tta else ''}"
        if jid in jobs and (jobs[jid]["ckpt"], jobs[jid]["postprocess"]) != (ckpt, pp):
            jid += f"__{len(jobs)}"
        jobs.setdefault(jid, {"id": jid, "model": model, "ckpt": ckpt, "tta": tta, "postprocess": pp})
        return jid

    for key in sorted(used_members(card)):
        m = card["members"][key]
        tta = m.get("tta")
        mc = yaml.safe_load((model_dir.parent / m["model"] / "model.yaml").read_text())
        if mc.get("type") == "bag":
            how[key] = {"bag": [job(s, CK, tta, TTA_PP if tta else "test/postprocess.yaml") for s in mc["members"]], "iou": mc["iou"]}
        else:
            how[key] = {"job": job(m["model"], m["ckpt"], tta, m.get("postprocess", TTA_PP) if tta else "test/postprocess.yaml")}
    return list(jobs.values()), how


def commands(model_dir: Path, card: dict, tag: str) -> list[str]:
    jobs, _ = plan(model_dir, card)
    data = card["data"]["realval"]
    out = (model_dir / "validation" / "output" / f"repro_{tag}").relative_to(REPO)
    cmds = []
    for j in jobs:
        md = (model_dir.parent / j["model"]).relative_to(REPO)
        for split in ("val", "valB"):
            c = (f"python common/tools/pcdet_predict.py {md} --ckpt {md}/{j['ckpt']} --frames {data} --split {split} "
                 f"--postprocess {md}/{j['postprocess']}" + (f" --tta {j['tta']}" if j["tta"] else "") + f" --out {out}/{j['id']}_{split}.json")
            cmds.append(c)
    return cmds


def score(model_dir: Path, card: dict, track, tag: str) -> dict:
    from bdc26 import scorecard as sc
    from bdc26.evalap import evaluate
    from bag_predictions import fuse_files
    from route_predictions import frame_points, merge_card
    jobs, how = plan(model_dir, card)
    d = model_dir / "validation" / "output" / f"repro_{tag}"
    root = data_path(track, card["data"]["realval"])
    gts = {s: sc.load_split(root, s) for s in ("val", "valB")}
    late = set(sc.late_a_ids(track, list(gts["val"])))
    cwg = list(track["classes_with_test_gt"])
    missing = [f"{j['id']}_{s}.json" for j in jobs for s in ("val", "valB") if not (d / f"{j['id']}_{s}.json").exists()]
    if missing:
        raise SystemExit(f"missing predictions in {d}: {missing} (run the inference commands first: --jobs or the script)")
    res = {}
    for split in ("val", "valB"):
        preds = {}
        for key, h in how.items():
            if "bag" in h:
                preds[key] = fuse_files([d / f"{j}_{split}.json" for j in h["bag"]], h["iou"])
            else:
                preds[key] = json.loads((d / f"{h['job']}_{split}.json").read_text())
        routed = merge_card(card, preds, frame_points(track, card["data"]["realval"]))
        (d / f"routed_{split}.json").write_text(json.dumps(routed))
        g = gts[split]
        pc = evaluate({i: routed.get(i, []) for i in g}, g, track.classes)["per_class"]
        res[split] = {c: (pc[c]["3d@0.5"]["AP_R40"] if pc[c]["3d@0.5"] else None) for c in pc}
        if split == "val" and late:
            gl = {i: v for i, v in g.items() if i in late}
            pl = evaluate({i: routed.get(i, []) for i in gl}, gl, track.classes)["per_class"]
            res["lateA"] = {c: (pl[c]["3d@0.5"]["AP_R40"] if pl[c]["3d@0.5"] else None) for c in pl}
    ref = json.loads((model_dir / "validation" / "results" / "scorecard.json").read_text())
    rows, worst = [], 0.0
    for c in cwg:
        for k, name in (("val", "A"), ("valB", "B"), ("lateA", "lateA")):
            new, old = (res.get(k) or {}).get(c), ref["per_class"][c].get(name)
            if new is None or old is None:
                continue
            worst = max(worst, abs(new - old))
            rows.append({"class": c, "split": name, "reproduced": new, "recorded": old, "diff": new - old})
    mean = lambda r: sum(r[c] for c in cwg if r.get(c) is not None) / max(len([c for c in cwg if r.get(c) is not None]), 1)
    from _common import member_tag
    from reproduce_submission import compare
    D = card["data"]["realval"].replace("/", "_")
    files = {}                                       # each reproduced member file against its recorded one, when present
    for j in jobs:
        for split in ("val", "valB"):
            orig = model_dir.parent / j["model"] / "validation" / "output" / f"{D}_{split}_{member_tag({'ckpt': j['ckpt'], 'tta': j['tta']})}.json"
            if orig.exists():
                files[f"{j['id']}_{split}"] = compare(json.loads((d / f"{j['id']}_{split}.json").read_text()), json.loads(orig.read_text()))["identical_within_tol"]
    out = {"model": card["name"], "tag": tag, "predictions": str(d.relative_to(REPO)), "jobs": jobs,
           "A_mAP": mean(res["val"]), "B_mAP": mean(res["valB"]), "lateA_mAP": mean(res["lateA"]) if "lateA" in res else None,
           "recorded": {k: ref.get(k) for k in ("A_mAP", "B_mAP", "lateA_mAP")}, "per_class": rows, "max_abs_diff": worst,
           "member_files_identical_to_recorded": files}
    split_diff = max(abs(out[k] - ref[k]) for k in ("A_mAP", "B_mAP", "lateA_mAP") if out.get(k) is not None and ref.get(k) is not None)
    out["max_split_mAP_diff"] = split_diff
    out["verdict"] = "IDENTICAL" if worst < 1e-4 else "EQUIVALENT" if worst < 1e-3 and split_diff < 5e-4 else "DIFFERENT"
    (model_dir / "validation" / "results" / f"reproduce_{tag}_validation.json").write_text(json.dumps(out, indent=2))
    print(f"{card['name']} {tag}: A {out['A_mAP']:.4f} (recorded {ref.get('A_mAP'):.4f}), B {out['B_mAP']:.4f} (recorded {ref.get('B_mAP'):.4f})"
          + (f", late-A {out['lateA_mAP']:.4f} (recorded {ref.get('lateA_mAP'):.4f})" if out["lateA_mAP"] is not None else "")
          + f"; max per-class difference {worst:.2e}: {out['verdict']}")
    if files:
        diff = [k for k, v in files.items() if not v]
        print(f"  member files: {len(files) - len(diff)} of {len(files)} bit-identical to the recorded predictions"
              + (f"; last-digit differences in {', '.join(diff)}" if diff else ""))
    return out


def write_script(model_dir: Path, card: dict, tag: str) -> Path:
    rel = model_dir.relative_to(REPO)
    d = (model_dir / "validation" / "output" / f"repro_{tag}").relative_to(REPO)
    lines = ["#!/usr/bin/env bash",
             f"# Reproduce the real-validation numbers of '{tag}' ({rel}) from the checkpoints: realval-A/B inference of every used",
             "# member with its committed post-processing, bag fusion, merge with model.yaml, official metric, comparison with",
             "# validation/results/scorecard.json. Needs the prepared real validation data and the checkpoints. Generated by",
             "# common/tools/reproduce_validation.py. Run on an idle GPU:",
             f"#   CUDA_VISIBLE_DEVICES=0 bash {rel}/test/reproduce_{tag}_validation.sh",
             "# The inference commands are independent: `python common/tools/reproduce_validation.py " + f"{rel} --tag {tag} --jobs`",
             "# prints them, one per line, for running several GPUs at once.",
             "set -euo pipefail", 'cd "$(dirname "${BASH_SOURCE[0]}")/../../.."      # the repository root (portable)',
             "source common/env/activate.sh", f"mkdir -p {d}"]
    for c in commands(model_dir, card, tag):
        out = c.rsplit("--out ", 1)[1]
        lines.append(f"[ -s {out} ] || {c}")
    lines.append(f"python common/tools/reproduce_validation.py {rel} --tag {tag} --score")
    p = model_dir / "test" / f"reproduce_{tag}_validation.sh"
    p.write_text("\n".join(lines) + "\n")
    p.chmod(0o755)
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--write-script", action="store_true")
    ap.add_argument("--jobs", action="store_true", help="print the inference commands, one per line (run from the repository root)")
    ap.add_argument("--score", action="store_true")
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    if a.write_script:
        print("wrote", write_script(model_dir, card, a.tag))
    if a.jobs:
        d = (model_dir / "validation" / "output" / f"repro_{a.tag}").relative_to(REPO)
        for c in commands(model_dir, card, a.tag):
            print(f"mkdir -p {d} && {c}")
    if a.score:
        r = score(model_dir, card, track, a.tag)
        sys.exit(0 if r["verdict"] != "DIFFERENT" else 1)


if __name__ == "__main__":
    main()
