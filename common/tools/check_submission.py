#!/usr/bin/env python
"""Pre-upload check of a CodaBench submission zip, done the way the server does it.

    python common/tools/check_submission.py --track lumpi model-lumpi-track/routed-g1/submissions/<date>_<tag>/submission.zip
    python common/tools/check_submission.py --track v2x <zip> --set-team KarmaRV      # rewrite the team line in place
    python common/tools/check_submission.py --track v2x <zip> --official               # + run the kit's scorer locally

1. Structure: exactly synthetic/*.bin (50 files), predictions.json and declaration.txt|pdf at the zip ROOT. A zip
   made by re-compressing an unzipped folder (macOS Finder "Compress", Windows "Send to") puts everything under
   <folder>/ and adds __MACOSX/ or .DS_Store entries; the scorer then finds no declaration / synthetic/ and the
   submission fails.
2. Content: bdc26.submit.validate (sizes, N x 3 float32, finite values, test IDs exactly, boxes, classes, score
   in [0, 1], declaration statement and a non-empty "Team:" line, total size).
3. --set-team NAME: rewrites only declaration.txt (other members are copied byte-for-byte), re-validates, and
   updates manifest.json next to the zip (team, zip_md5, validation).
4. --official: runs the starting kit's local_eval.py (the server's scoring_program) on the zip with a local
   reference built from LEGAL real data: realism-proxy-4 frames as the realism reference and realval-v1 labels
   (every 7th val frame) placed under the test IDs as a stand-in detection GT, so the detection loops do a
   realistic amount of work (the kit's dummy GT has no boxes and runs 6x faster than the server will). Runs
   under the server's execution budget (1,200 s) and reports validity, realism, wall time and peak memory. The
   stand-in AP is meaningless (those labels belong to other frames); only validity and cost matter.
"""
import argparse
import hashlib
import json
import resource
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import numpy as np

from _common import load_track
from bdc26 import submit
from bdc26.io.kit import test_ids
from bdc26.pcdet_export import read_labels_txt

BUDGET_S = 1200


def set_team(zip_path: Path, team: str) -> None:
    tmp = zip_path.with_suffix(".tmp.zip")
    with zipfile.ZipFile(zip_path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "declaration.txt":
                lines = data.decode("utf-8", errors="replace").splitlines()
                lines = [l for l in lines if not l.lower().startswith("team:")]
                at = next((k + 1 for k, l in enumerate(lines) if submit.DECLARATION.lower() in l.lower()), len(lines))
                lines.insert(at, f"Team: {team}")
                data = ("\n".join(lines) + "\n").encode("utf-8")
            zout.writestr(info.filename, data)
    tmp.replace(zip_path)


def update_manifest(zip_path: Path, team: str | None, errors: list, info: dict) -> None:
    man = zip_path.parent / "manifest.json"
    if not man.exists():
        return
    m = json.loads(man.read_text())
    if team is not None:
        m["team"] = team
    m["zip_md5"] = hashlib.md5(zip_path.read_bytes()).hexdigest()
    m["validation_errors"], m["info"] = errors, info
    m.setdefault("history", []).append({"time": time.strftime("%Y-%m-%d %H:%M"), "action": f"check_submission (team={team})"})
    man.write_text(json.dumps(m, indent=2))


def official(track, zip_path: Path) -> dict:
    kit = track.kit
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        ref = td / "reference"
        (ref / "realism_reference").mkdir(parents=True)
        cfg = json.loads((kit / "reference_data_dummy" / "config.json").read_text())
        cfg["n_realism_frames"] = 50
        (ref / "config.json").write_text(json.dumps(cfg))
        val = (track.pcdet / "realval-v1" / "ImageSets" / "val.txt").read_text().split()[::7]
        gt = {}
        for fid, vid in zip(cfg["detection_test_frame_ids"], val):
            b, nm = read_labels_txt(track.pcdet / "realval-v1" / "labels" / f"{vid}.txt")
            gt[fid] = [{"box": [float(x) for x in bb], "class": str(c)} for bb, c in zip(np.asarray(b).reshape(-1, 7), nm)]
        (ref / "detection_gt.json").write_text(json.dumps(gt))
        proxy = sorted((track.pcdet / "realism-proxy-4" / "points").glob("*.npy"))[:50]
        if len(proxy) < 50:
            raise SystemExit("need pcdet/realism-proxy-4 (data-<track>/prepare_realval.py) for a local realism reference")
        for i, f in enumerate(proxy, 1):
            np.load(f)[:, :3].astype(np.float32).tofile(ref / "realism_reference" / f"{i:04d}.bin")
        work = td / "kit"
        shutil.copytree(kit / "scoring_program", work / "scoring_program")
        shutil.copy(kit / "local_eval.py", work / "local_eval.py")
        t0 = time.time()
        try:
            p = subprocess.run([sys.executable, "local_eval.py", str(zip_path.resolve()), str(ref)], cwd=work,
                               capture_output=True, text=True, timeout=BUDGET_S)
        except subprocess.TimeoutExpired:
            return {"valid": False, "error": f"exceeded the server's {BUDGET_S} s execution limit locally"}
        wall = time.time() - t0
        peak_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
        scores = json.loads((work / "scores.json").read_text()) if (work / "scores.json").exists() else {}
        return {"valid": bool(scores.get("valid_submission")), "error": scores.get("error_message"),
                "stand_in_gt_boxes": sum(len(v) for v in gt.values()),
                "score_realism": scores.get("score_realism"), "CD": scores.get("CD"), "MMD": scores.get("MMD"),
                "EMD": scores.get("EMD"), "FPD": scores.get("FPD"), "wall_s": round(wall, 1), "peak_rss_mb": round(peak_mb),
                "budget_s": BUDGET_S, "returncode": p.returncode, "stderr_tail": p.stderr[-800:] if p.returncode else ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("zip", type=Path)
    ap.add_argument("--track", required=True)
    ap.add_argument("--set-team", default=None)
    ap.add_argument("--official", action="store_true")
    a = ap.parse_args()
    t = load_track(a.track)
    if a.set_team:
        set_team(a.zip, a.set_team)
    with zipfile.ZipFile(a.zip) as z:
        roots = sorted({n.split("/")[0] + ("/" if "/" in n else "") for n in z.namelist()})
    errors, info = submit.validate(a.zip, t, test_ids(t))
    info["zip_roots"] = roots
    if a.set_team or (a.zip.parent / "manifest.json").exists():
        update_manifest(a.zip, a.set_team, errors, info)
    print(json.dumps({"zip": str(a.zip), "roots": roots, "errors": errors,
                      **{k: info.get(k) for k in ("team", "n_boxes", "points_per_frame", "null_fraction", "uncompressed_bytes")}}, indent=2))
    if a.official:
        res = official(t, a.zip)
        print(json.dumps({"official_local_eval": res}, indent=2))
        if not res["valid"]:
            errors.append(f"official scorer: {res.get('error')}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
