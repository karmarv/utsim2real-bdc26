#!/usr/bin/env python
"""S10-2 gate G-R (docs/decisions/2026-11-12-s10-10.2-clean-final-push.md Section 7): held-out realism of a candidate
50-frame set against a base set, on judge sets that no fit used, at two scorer seeds (exact EMD, the kit's protocol).
Judges are unlabelled legal real proxies; the kit's realism_reference and the test frames are never read.

    python common/tools/s10_2_gate_r.py lumpi --base zip:<scored zip> --cand corpus:pcdet/g1-v6n1 --ids <50 ids> \
        [--cand dir:<folder of 0001.bin ...>] --judges realism-proxy-4 realism-proxy-5 ... --seeds 1234 99
Prints one line per (candidate, judge, seed) and a summary per candidate: mean dR, the lowest dR, wins, mean dEMD,
the largest CD; writes the rows as JSON with --out.
"""
import argparse
import json
import sys
import zipfile
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import data_path  # noqa: E402
from bdc26 import realism  # noqa: E402
from bdc26.config import load_track  # noqa: E402


def frames(spec: str, T, ids: list) -> list:
    kind, ref = spec.split(":", 1)
    if kind == "zip":
        with zipfile.ZipFile(ref) as zf:
            names = sorted(x for x in zf.namelist() if x.startswith("synthetic/") and x.endswith(".bin"))
            return [np.frombuffer(zf.read(x), dtype=np.float32).reshape(-1, 3).copy() for x in names]
    if kind == "corpus":
        root = data_path(T, ref)
        return [np.load(root / "points" / f"{i}.npy")[:, :3].astype(np.float32) for i in sorted(ids)]
    if kind == "dir":
        return [np.fromfile(f, dtype=np.float32).reshape(-1, 3) for f in sorted(Path(ref).glob("*.bin"))]
    raise SystemExit(f"unknown frame spec {spec}")


def judge(T, name: str) -> list:
    if "kit" in name or "realism_reference" in name or "test" in name:
        raise SystemExit(f"{name}: never a judge")
    return [np.load(f)[:, :3].astype(np.float32) for f in sorted((T.root / "pcdet" / name / "points").glob("*.npy"))]


_T = _J = _S = None


def _init(track, judges, sets):
    global _T, _J, _S
    _T = load_track(track)
    _J = {j: judge(_T, j) for j in judges}
    _S = sets


def _score(job):
    name, j, seed = job
    r = realism.score(_S[name], _J[j], _T.name.split("-")[0], exact_emd=True, seed=seed)
    return {"set": name, "judge": j, "seed": seed, **{k: float(r[k]) for k in ("CD", "MMD", "EMD", "FPD", "R")}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track")
    ap.add_argument("--base", required=True)
    ap.add_argument("--cand", action="append", required=True)
    ap.add_argument("--ids", required=True)
    ap.add_argument("--judges", nargs="+", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, default=[1234, 99])
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    T = load_track(a.track)
    ids = Path(a.ids).read_text().split()
    sets = {"base": frames(a.base, T, ids), **{c: frames(c, T, ids) for c in a.cand}}
    for k, v in sets.items():
        if len(v) != 50:
            raise SystemExit(f"{k}: {len(v)} frames, not 50")
    jobs = [(s, j, seed) for s in sets for j in a.judges for seed in a.seeds]
    with Pool(min(a.workers, len(jobs)), initializer=_init, initargs=(a.track, a.judges, sets)) as pool:
        rows = pool.map(_score, jobs)
    by = {(r["set"], r["judge"], r["seed"]): r for r in rows}
    for c in a.cand:
        d = [(by[(c, j, s)]["R"] - by[("base", j, s)]["R"], by[(c, j, s)]["EMD"] - by[("base", j, s)]["EMD"])
             for j in a.judges for s in a.seeds]
        for (j, s), (dr, de) in zip([(j, s) for j in a.judges for s in a.seeds], d):
            print(f"{c} {j} seed {s}: dR {dr:+.4f} dEMD {de:+.3f} (R {by[(c, j, s)]['R']:.4f}, base {by[('base', j, s)]['R']:.4f})")
        dr = np.array([x for x, _ in d])
        print(f"SUMMARY {c}: mean dR {dr.mean():+.4f}, lowest {dr.min():+.4f}, wins {(dr > 0).sum()}/{len(dr)}, "
              f"mean dEMD {np.mean([y for _, y in d]):+.3f}, max CD {max(by[(c, j, s)]['CD'] for j in a.judges for s in a.seeds):.3f}, "
              f"MMD worse {sum(by[(c, j, s)]['MMD'] > by[('base', j, s)]['MMD'] for j in a.judges for s in a.seeds)}, "
              f"FPD worse {sum(by[(c, j, s)]['FPD'] > by[('base', j, s)]['FPD'] for j in a.judges for s in a.seeds)}")
    if a.out:
        Path(a.out).write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
