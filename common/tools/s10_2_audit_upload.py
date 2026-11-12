#!/usr/bin/env python
"""Release 10.2: audit an upload copy against the rules, byte by byte (record 2026-11-12-s10-10.2-clean-final-push.md).

    python common/tools/s10_2_audit_upload.py model-lumpi-track/routed-c2r/submissions/2026-11-12_s10-2-l1 \
        [--same-frames-as model-lumpi-track/routed-c0/submissions/2026-11-07_c0/lumpi_s10_submission.zip]

Checks, each printed as PASS or FAIL:
  1. the zip's md5 is the manifest's upload md5 (the file that was uploaded);
  2. the zip holds only synthetic/0001-0050.bin, predictions.json and declaration.txt, the declaration is verbatim with a
     team name, and the kit-format validation passes;
  3. rules 1 and 1b (clean_check.py) on the model, and the model card's realism frames are the manifest's corpus;
  4. every frame comes from that corpus: frame k is the corpus frame synthetic_ids[k], byte-identical (no nulls) or,
     with nulls, every non-null point is a point of the corpus frame and the null share is the manifest's;
  5. where each frame id sits in the corpus splits (train is the data the detectors trained on);
  6. optional: the 50 frames are byte-identical to another upload's (the same realism frames).
Exit code 1 if any check fails. Reads no test frame and no real frame: only the zip, the manifest and the corpus.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import REPO, data_path, model_info  # noqa: E402
from bdc26 import submit  # noqa: E402


def frames_of(z: zipfile.ZipFile) -> list:
    names = sorted(x for x in z.namelist() if x.startswith("synthetic/") and x.endswith(".bin"))
    return names, [np.frombuffer(z.read(x), dtype=np.float32).reshape(-1, 3) for x in names]


def rows(a: np.ndarray) -> np.ndarray:
    a = np.ascontiguousarray(a.astype(np.float32))
    return a.view(np.dtype((np.void, a.dtype.itemsize * a.shape[1]))).ravel()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sub_dir")
    ap.add_argument("--same-frames-as", default=None, help="another upload zip whose 50 frames must be byte-identical")
    a = ap.parse_args()
    sd = Path(a.sub_dir).resolve()
    model_dir = sd.parent.parent
    _, card, track = model_info(model_dir)
    man = json.loads((sd / "manifest.json").read_text())
    up = sd / man["upload_file"]["name"]
    res = []

    def check(name, ok, detail=""):
        res.append(ok)
        print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + detail if detail else ''}")

    md5 = hashlib.md5(up.read_bytes()).hexdigest()
    check("1 uploaded file", md5 == man["upload_file"]["md5"] == man["zip_md5"], f"{up.name} md5 {md5}")

    with zipfile.ZipFile(up) as z:
        names = set(z.namelist())
        want = {f"synthetic/{i:04d}.bin" for i in range(1, 51)} | {"predictions.json", "declaration.txt"}
        decl = z.read("declaration.txt").decode() if "declaration.txt" in names else ""
        team = next((l.split(":", 1)[1].strip() for l in decl.splitlines() if l.lower().startswith("team:")), "")
        errors, info = submit.validate(up, track)
        check("2 zip contents", names == want and submit.DECLARATION in decl and bool(team) and not errors,
              f"{len(names)} entries, declaration verbatim, team '{team}', kit-format errors {errors or 'none'}")
        fnames, frames = frames_of(z)

    cc = subprocess.run([sys.executable, str(REPO / "common/tools/clean_check.py"), str(model_dir)], capture_output=True, text=True)
    last = [l for l in cc.stdout.splitlines() if l.startswith(("FRAMES", "PASS", "FAIL", "NOTE"))]
    corpus = man["synthetic_source"]
    check("3 rules 1 and 1b", cc.returncode == 0 and card.get("realism_frames") == corpus, " | ".join(last))

    ids = (sd / "synthetic_ids.txt").read_text().split()
    root = Path(data_path(track, corpus))
    nf = float(man.get("null_fraction") or 0.0)
    bad, detail = [], []
    for k, (fid, f) in enumerate(zip(ids, frames)):
        c = np.load(root / "points" / f"{fid}.npy")[:, :3].astype(np.float32)
        if nf == 0:
            if not (f.shape == c.shape and np.array_equal(f, c)):
                bad.append(fid)
        else:
            nul = np.all(f == 0, axis=1)
            ok = abs(nul.mean() - nf) < 2.0 / len(f) and np.isin(rows(f[~nul]), rows(c[~np.all(c == 0, axis=1)])).all()
            if not ok:
                bad.append(fid)
    how = "byte-identical to the corpus frames" if nf == 0 else f"non-null points all from the corpus frames, null share {nf}"
    check("4 frames from the corpus", len(ids) == len(frames) == 50 and not bad,
          f"{corpus}, 50 ids, {how}" + (f"; mismatched {bad[:5]}" if bad else ""))

    splits = {p.stem: set(p.read_text().split()) for p in (root / "ImageSets").glob("*.txt")}
    where = {s: sum(i in v for i in ids) for s, v in splits.items()}
    check("5 frame ids in the corpus splits", any(where.values()), json.dumps(where))

    if a.same_frames_as:
        with zipfile.ZipFile(a.same_frames_as) as z:
            _, other = frames_of(z)
        same = len(other) == len(frames) and all(np.array_equal(x, y) for x, y in zip(frames, other))
        check("6 the same frames as", same, Path(a.same_frames_as).resolve().relative_to(REPO).as_posix())
    print(f"{'AUDIT PASS' if all(res) else 'AUDIT FAIL'} {sd.relative_to(REPO)}")
    return 0 if all(res) else 1


if __name__ == "__main__":
    sys.exit(main())
