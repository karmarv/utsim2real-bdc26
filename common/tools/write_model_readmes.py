#!/usr/bin/env python
"""Write (or refresh) model-<track>/<model>/README.md from the model's own files.

    python common/tools/write_model_readmes.py            # every model of both tracks
    python common/tools/write_model_readmes.py lumpi      # one track

Sources: model.yaml (card), train/pcdet_model.yaml (classes, epochs, batch), test/postprocess.yaml (selected
post-processing), validation/results/local_scores.json (latest real-validation result), test/synthetic_ids.txt
(chosen realism frames) and routed members. The track README (model-<track>/README.md) holds the narrative.
"""
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]


def fmt(v):
    return "-" if v is None else f"{v:.3f}"


def model_readme(track_dir: Path, mdir: Path) -> str:
    card = yaml.safe_load((mdir / "model.yaml").read_text())
    name, track = card["name"], card["track"]
    rel = f"{track_dir.name}/{mdir.name}"
    routed = "members" in card
    lines = [f"# `{name}` ({track})", "",
             f"> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).", ""]
    lines += ["| | |", "|---|---|",
              f"| Module | {card.get('module', '-')} |",
              f"| Architecture | {card.get('architecture', '-')} |",
              f"| Training data | `{card.get('data', {}).get('train', '-')}` |" if not routed else
              f"| Members | " + ", ".join(f"`{k}` = [`{v['model']}`](../{v['model']}) (`{v['ckpt']}`" + (f", TTA `{v['tta']}`" if v.get("tta") else "") + ")"
                                          for k, v in card["members"].items()) + " |",
              f"| Real validation | `{card.get('data', {}).get('realval', '-')}` (split `val` = realval-A, `valB` = realval-B) |",
              f"| Realism frames | `{card.get('realism_frames', '-')}`" + (" (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt))" if (mdir / "test/synthetic_ids.txt").exists() else " (random 50 of the val split until selected)") + " |",
              f"| Status | {card.get('status', '-')} |", ""]
    if card.get("notes"):
        lines += [str(card["notes"]).strip(), ""]
    if routed and card.get("route"):
        lines += ["## Route (class -> member)", "", "| " + " | ".join(card["route"]) + " |", "|" + "---|" * len(card["route"]),
                  "| " + " | ".join(card["route"].values()) + " |", ""]
        sel = card.get("route_selection")
        if sel:
            lines += [f"Rule: {sel.get('rule')}.", ""]
        if card.get("calibration"):
            lines += ["Range-dependent z calibration of the routed classes (z += z0 + z_per_m x range): "
                      + ", ".join(f"{c} ({v['z0']}, {v['z_per_m']})" for c, v in card["calibration"].items()) + ".", ""]
    if routed and card.get("fusion"):
        lines += ["## Fusion (classes replaced by the fused members, `route_predictions.py fuse`)", "",
                  "| Class | Members | Weights | BEV IoU | Member z calibration |", "|---|---|---|---|---|"]
        for c, fz in card["fusion"].items():
            cal = ", ".join(f"{n} ({v['z0']}, {v['z_per_m']})" for n, v in (fz.get("calibration") or {}).items()) or "-"
            lines.append(f"| {c} | {' + '.join(fz['members'])} | {fz.get('weights', '-')} | {fz['iou']} | {cal} |")
        lines.append("")
    if routed and card.get("budget"):
        lines += ["## Score floors (server-cost budget, `route_predictions.py budget`)", "",
                  "| " + " | ".join(card["budget"]) + " |", "|" + "---|" * len(card["budget"]),
                  "| " + " | ".join(str(v) for v in card["budget"].values()) + " |", ""]
    lines += ["## Commands", "", "From the repository root after `source common/env/activate.sh`:", "", "```bash"]
    if not routed:
        lines += [f"CUDA_VISIBLE_DEVICES=0,1,2,3 bash {rel}/train/train.sh 4 run1 --fix_random_seed --workers 6      # train",
                  f"CUDA_VISIBLE_DEVICES=0 bash {rel}/validation/tune_and_eval.sh {rel}/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune",
                  f"CUDA_VISIBLE_DEVICES=0 bash {rel}/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only",
                  f"CUDA_VISIBLE_DEVICES=0 bash {rel}/test/predict.sh <ckpt>                                       # predict the 50 kit frames",
                  f"CUDA_VISIBLE_DEVICES=0 bash {rel}/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score"]
    else:
        lines += [f"python common/tools/route_predictions.py select {rel}" + (" --rule joint --calibrated" if card.get("fusion") else "")
                  + "                                  # choose the route"]
        if card.get("fusion"):
            big = max([len(fz["members"]) for fz in card["fusion"].values()] + [3 if str(card.get("strategy", "")) >= "S4" else 2])  # S4 on: triples searched
            lines += [f"python common/tools/route_predictions.py fuse {rel}" + (f" --max-members {big}" if big > 2 else "")
                      + "                                    # per-class fusion (class gate)"]
        if card.get("budget"):
            lines += [f"python common/tools/route_predictions.py budget {rel}                                  # per-class score floors"]
        lines += [f"CUDA_VISIBLE_DEVICES=0 bash {rel}/test/make_submission.sh <tag> [team]                        # zip + validation + local score"]
    lines += ["```", ""]
    cfg = mdir / "train/pcdet_model.yaml"
    if cfg.exists():
        c = yaml.safe_load(cfg.read_text())
        opt = c.get("OPTIMIZATION", {})
        lines += ["## Configuration", "",
                  f"- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): "
                  f"classes {c.get('CLASS_NAMES')}, {opt.get('NUM_EPOCHS')} epochs, batch {opt.get('BATCH_SIZE_PER_GPU')} per GPU, "
                  f"{opt.get('OPTIMIZER')} LR {opt.get('LR')}.", ""]
    pp = mdir / "test/postprocess.yaml"
    if pp.exists():
        d = yaml.safe_load(pp.read_text())
        sel = d.get("selected_on")
        lines += ["## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))", "",
                  ("Selected by `tune_postprocess.py` on " + sel + "." if sel else "Starting values (not yet tuned on real validation)."), "",
                  "| Class | Settings |", "|---|---|"]
        for c, v in (d.get("classes") or {}).items():
            lines.append(f"| {c} | " + (", ".join(f"{k} {v2}" for k, v2 in v.items()) if v else "defaults") + " |")
        if d.get("hedge"):
            lines.append("| hedges | " + "; ".join(f"{s} -> " + ", ".join(f"{t} x{f}" for t, f in (pairs if isinstance(pairs[0], list) else [pairs]))
                                                    for s, pairs in d["hedge"].items()) + " |")
        lines.append("")
    ls = mdir / "validation/results/local_scores.json"
    if ls.exists():
        d = json.loads(ls.read_text())
        A, B = d.get("realval_A_per_class", {}), d.get("realval_B_per_class", {})
        cls = [c for c in A if A.get(c) is not None or B.get(c) is not None]
        lines += ["## Latest real-validation result (official metric, 3D AP@0.5 R40)", "",
                  f"Checkpoint: `{Path(d.get('ckpt', '-')).name if d.get('ckpt') else d.get('run', '-')}`.", "",
                  "| Split | mAP (classes with test GT) | " + " | ".join(cls) + " |", "|---|---|" + "---|" * len(cls),
                  f"| realval-A | **{fmt(d.get('realval_A_mAP_3d_0.5_R40'))}** | " + " | ".join(fmt(A.get(c)) for c in cls) + " |",
                  f"| realval-B | {fmt(d.get('realval_B_mAP_3d_0.5_R40'))} | " + " | ".join(fmt(B.get(c)) for c in cls) + " |", ""]
        if d.get("realism_R_heldout"):
            r = {k: v for k, v in d["realism_R_heldout"].items() if k.startswith("pcdet/")}
            lines += [f"Realism on held-out legal proxies: " + ", ".join(f"{k.split('/')[-1]} R {v}" for k, v in r.items()) + "."]
        if d.get("combined_estimate"):
            lines += [f"Combined estimate: " + ", ".join(f"{k} {v}" for k, v in d["combined_estimate"].items()) + "."]
        lines.append("")
    subs = sorted((mdir / "submissions").glob("*_*/manifest.json"))
    if subs:
        lines += ["## Submissions", "", "| Folder | CodaBench id | Leaderboard |", "|---|---|---|"]
        for m in subs:
            man = json.loads(m.read_text())
            lb = man.get("leaderboard") or {}
            lbs = (f"combined {lb['score_combined']:.4f}, mAP {lb['mAP_3d_0.5_R40']:.4f}, R {lb['score_realism']:.4f}"
                   if "score_combined" in lb else "-")
            lines.append(f"| `{m.parent.name}` | {man.get('codabench_submission_id') or '-'} | {lbs} |")
        lines.append("")
    return "\n".join(lines)


def main():
    tracks = [a for a in sys.argv[1:]] or ["lumpi", "v2x"]
    for t in tracks:
        td = REPO / f"model-{t}-track"
        for mdir in sorted(p for p in td.iterdir() if (p / "model.yaml").exists()):
            (mdir / "README.md").write_text(model_readme(td, mdir))
            print("wrote", mdir.relative_to(REPO) / "README.md")


if __name__ == "__main__":
    main()
