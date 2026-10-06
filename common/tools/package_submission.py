#!/usr/bin/env python
"""Package one CodaBench submission into model-<track>/<model>/submissions/<date>_<tag>/.

    python common/tools/package_submission.py model-v2x-track/pointpillars-ut --tag first \
        --pred model-v2x-track/pointpillars-ut/test/output/predictions.json --synthetic pcdet/ut-v1 --team "<team>"
Synthetic frames: 50 frames from --synthetic (split --syn-split), chosen by --syn-list (one id per line, e.g. the
output of the M12 frame selector) or at random with --seed. They are written as float32 N x 3 as stored
(V2X realism frames must already contain their (0,0,0) null returns). The folder receives submission.zip
(gitignored), manifest.json and synthetic_ids.txt (tracked); a registry row is appended.
Upload the zip by hand, then record the CodaBench id and scores with --record.
"""
import argparse
import os
import json
import time
from pathlib import Path

import numpy as np

from _common import data_path, model_info
from bdc26 import registry, submit


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--pred")
    ap.add_argument("--synthetic")
    ap.add_argument("--syn-split", default="train")
    ap.add_argument("--syn-list", default=None)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--nulls", type=float, default=None,
                    help="(0,0,0) share of each synthetic frame (default track.yaml resample.null_fraction; V2X 0.31)")
    ap.add_argument("--team", default=os.environ.get("BDC_TEAM", ""), help="team name in declaration.txt (default $BDC_TEAM)")
    ap.add_argument("--ckpt", default="")
    ap.add_argument("--local-scores", default=None, help="json with local realism/AP estimates to store in the manifest")
    ap.add_argument("--record", nargs=2, metavar=("CODABENCH_ID", "LEADERBOARD_JSON"), default=None,
                    help="after upload: store the CodaBench id and a json of leaderboard numbers in the manifest")
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)

    if a.record:
        sub_dir = sorted((model_dir / "submissions").glob(f"*_{a.tag}"))[-1]
        man = json.loads((sub_dir / "manifest.json").read_text())
        lb = json.loads(Path(a.record[1]).read_text())
        lb = lb.get("scores", lb)                     # a codabench_<id>.json record or a bare scores dict
        man["codabench_submission_id"], man["leaderboard"] = a.record[0], lb
        (sub_dir / "manifest.json").write_text(json.dumps(man, indent=2))
        per_class = {k.removeprefix("AP_3d_0.5_R40_"): v for k, v in lb.items() if k.startswith("AP_3d_0.5_R40_")}
        registry.append(track, kind="leaderboard", model=card["name"], run=a.tag, codabench_id=a.record[0],
                        metric_source="codabench", leaderboard_combined=lb.get("score_combined", ""),
                        realism_R=lb.get("score_realism", ""), per_class=json.dumps(per_class) if per_class else "",
                        **{"mAP_3d_0.5_R40": lb.get("mAP_3d_0.5_R40", "")})
        print(f"recorded {a.record[0]} in {sub_dir}")
        return

    from bdc26.io.kit import test_ids
    preds = json.loads(Path(a.pred).read_text())
    ids = test_ids(track)
    syn_root = data_path(track, a.synthetic)
    pool = (Path(a.syn_list).read_text().split() if a.syn_list
            else (syn_root / "ImageSets" / f"{a.syn_split}.txt").read_text().split())
    chosen = pool[:50] if a.syn_list else sorted(np.random.default_rng(a.seed).choice(pool, 50, replace=False).tolist())
    frames = [np.load(syn_root / "points" / f"{i}.npy") for i in chosen]
    null_frac = a.nulls if a.nulls is not None else float(track["resample"].get("null_fraction", 0.0))
    if null_frac > 0:
        from bdc26.frames import with_nulls
        rng = np.random.default_rng(a.seed)
        frames = [with_nulls(f, null_frac, int(track["resample"]["n_points"]), rng) for f in frames]
    out = model_dir / "submissions" / f"{time.strftime('%Y-%m-%d')}_{a.tag}"
    meta = {"model": card["name"], "ckpt": a.ckpt, "predictions": str(Path(a.pred).resolve()),
            "synthetic_source": a.synthetic, "synthetic_selection": a.syn_list or f"random seed {a.seed} from split {a.syn_split}",
            "null_fraction": null_frac,
            "local_scores": json.loads(Path(a.local_scores).read_text()) if a.local_scores else None}
    z = submit.package(out, {i: preds.get(i, []) for i in ids}, frames, track, meta, team=a.team, test_ids=ids)
    (out / "synthetic_ids.txt").write_text("\n".join(chosen) + "\n")
    registry.append(track, kind="submission", model=card["name"], run=a.tag, data_version=a.synthetic,
                    config=str(out.relative_to(model_dir)), notes="packaged, not yet uploaded")
    print(f"ready: {z}  (upload on CodaBench {track['codabench_id']}, then --record)")


if __name__ == "__main__":
    main()
