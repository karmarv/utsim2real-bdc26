"""Submission packaging and validation (spec: docs/01-CHALLENGE-FACTS.md Section 5).

submission.zip
    synthetic/0001.bin ... 0050.bin   raw float32 N x 3 (x, y, z metres), each <= 1.5 MB. Submit N x 3 only:
                                      the server parsed a 150,000-float file as N x 3, so an N x 4 file whose
                                      length is divisible by 3 can be misread.
    predictions.json                  {frame_id: [{"box": [x,y,z,dx,dy,dz,heading], "score": s, "class": c}]}
    declaration.txt                   the verbatim honor statement (declaration.pdf also accepted)
"""
from __future__ import annotations

import hashlib
import json
import math
import time
import zipfile
from pathlib import Path

import numpy as np

from .config import Track
from .frames import in_range_mask, null_mask
from .pcdet_export import git_sha

DECLARATION = ("I confirm that I did not train on any frame listed in forbidden_frames.txt, and that all submitted "
               "detections were produced by a model trained only on synthetic data I generated.")
MAX_BYTES = 1_500_000
MAX_TOTAL_BYTES = 75_000_000      # submission_format.md: total uncompressed size under ~75 MB


def validate(zip_path: Path, track: Track, test_ids: list[str] | None = None) -> tuple[list[str], dict]:
    """Returns (errors, info). An empty error list means the zip matches the published spec."""
    errors, info = [], {}
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        syn = sorted(n for n in names if n.startswith("synthetic/") and n.endswith(".bin"))
        if len(syn) != 50:
            errors.append(f"expected 50 synthetic/*.bin files, found {len(syn)}")
        null_fr, inr_fr, npts = [], [], []
        for n in syn:
            raw = z.read(n)
            if len(raw) > MAX_BYTES:
                errors.append(f"{n}: {len(raw)} bytes > {MAX_BYTES}")
            if len(raw) % 12:
                errors.append(f"{n}: size {len(raw)} is not a multiple of 12 (N x 3 float32)")
                continue
            a = np.frombuffer(raw, dtype=np.float32).reshape(-1, 3)
            if not np.isfinite(a).all():
                errors.append(f"{n}: NaN/Inf values")
            npts.append(len(a))
            null_fr.append(float(null_mask(a).mean()))
            inr_fr.append(float(in_range_mask(a, track.pc_range).mean()))
        total = sum(i.file_size for i in z.infolist())
        if total > MAX_TOTAL_BYTES:
            errors.append(f"uncompressed size {total} bytes > {MAX_TOTAL_BYTES}")
        info["uncompressed_bytes"] = total
        info.update(points_per_frame=[min(npts or [0]), max(npts or [0])],
                    null_fraction=float(np.mean(null_fr or [0])), in_range_fraction=float(np.mean(inr_fr or [0])))
        if "predictions.json" not in names:
            errors.append("predictions.json missing")
        else:
            preds = json.loads(z.read("predictions.json"))
            valid = {c.lower() for c in track.classes}
            if test_ids is not None:
                missing, extra = set(test_ids) - set(preds), set(preds) - set(test_ids)
                if missing:
                    errors.append(f"predictions.json misses {len(missing)} test ids, e.g. {sorted(missing)[:3]}")
                if extra:
                    errors.append(f"predictions.json has {len(extra)} ids that are not test ids, e.g. {sorted(extra)[:3]}")
            nbox, per_class = 0, {}
            for fid, dets in preds.items():
                for d in dets:
                    b = d.get("box", [])
                    if len(b) != 7 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in b):
                        errors.append(f"{fid}: bad box {b}")
                        break
                    if min(b[3:6]) <= 0:
                        errors.append(f"{fid}: non-positive extents {b}")
                        break
                    if str(d.get("class", "")).lower() not in valid:
                        errors.append(f"{fid}: unknown class {d.get('class')!r}")
                        break
                    if not (isinstance(d.get("score"), (int, float)) and math.isfinite(d["score"]) and 0.0 <= d["score"] <= 1.0):
                        errors.append(f"{fid}: score must be a finite number in [0, 1], got {d.get('score')!r}")
                        break
                    nbox += 1
                    per_class[d["class"]] = per_class.get(d["class"], 0) + 1
            info.update(n_boxes=nbox, boxes_per_class=per_class)
        decl = [n for n in names if n in ("declaration.txt", "declaration.pdf")]
        if not decl:
            errors.append("declaration.txt / declaration.pdf missing")
        elif "declaration.txt" in decl and DECLARATION.lower() not in z.read("declaration.txt").decode().lower():
            errors.append("declaration.txt does not contain the verbatim statement")
    return errors, info


def package(out_dir: Path, predictions: dict, synthetic_frames: list[np.ndarray], track: Track,
            meta: dict, team: str = "", test_ids: list[str] | None = None) -> Path:
    """Write submission.zip + manifest.json into out_dir (one folder per CodaBench submission)."""
    if len(synthetic_frames) != 50:
        raise ValueError(f"need exactly 50 synthetic frames, got {len(synthetic_frames)}")
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / "submission.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for i, f in enumerate(synthetic_frames, 1):
            a = np.ascontiguousarray(np.asarray(f)[:, :3], dtype=np.float32)
            if a.nbytes > MAX_BYTES:
                raise ValueError(f"synthetic frame {i}: {a.nbytes} bytes > {MAX_BYTES}; resample to 50k points first")
            z.writestr(f"synthetic/{i:04d}.bin", a.tobytes())
        z.writestr("predictions.json", json.dumps(predictions))
        z.writestr("declaration.txt", f"{DECLARATION}\nTeam: {team}\nDate: {time.strftime('%Y-%m-%d')}\n")
    errors, info = validate(zpath, track, test_ids)
    manifest = {**meta, "track": track.name, "created": time.strftime("%Y-%m-%d %H:%M"), "git_sha": git_sha(),
                "zip_md5": hashlib.md5(zpath.read_bytes()).hexdigest(), "validation_errors": errors, "info": info,
                "codabench_submission_id": None, "leaderboard": None, "local_scores": meta.get("local_scores")}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    if errors:
        raise ValueError(f"invalid submission ({len(errors)} errors), see {out_dir / 'manifest.json'}")
    return zpath
