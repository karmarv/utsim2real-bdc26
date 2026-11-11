#!/usr/bin/env python
"""S10 increment 5b (docs/decisions/2026-11-08-s10-clean-final-plan.md Section 15.6): where the realism EMD of 50
synthetic frames comes from, against LEGAL real proxy frames. Read-only; no generator or frame choice is made here.

    python common/tools/s10_emd_attribution.py v2x model-v2x-track/routed-c0/submissions/2026-11-07_c0/submission.zip \
        --ref pcdet/realism-proxy-4 pcdet/realism-proxy-5 --out $BDC_DATA/logs/s10/realism/v2x_c0.json

For each proxy, with the scorer's own mask, seed and 10,000-point subsamples (bdc26.realism): CD, MMD, EMD, FPD and R;
the exact optimal transport plan (POT ot.emd, Euclidean cost), and W1 = sum(plan * cost) split by the synthetic and
the real points' range band (BEV distance from the origin), height band (z) and BEV 10 m cell, with each band's mass
on both sides. A band holding more synthetic than real mass must send its surplus elsewhere, and the cost of that
move is what EMD measures. Also the means and covariances behind FPD.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parent)]
from bdc26 import realism  # noqa: E402
from _common import load_track  # noqa: E402
from score_realism import load_frames  # noqa: E402

R_BANDS = [0, 5, 10, 15, 20, 25, 30, 40, 60]
Z_BANDS = {"v2x": [-8, -6, -5, -4.5, -4, -3.5, -3, -2, -1, 0, 2], "lumpi": [-5, -2, -1, -0.5, 0, 0.5, 1, 2, 3, 5]}


def bands(v, edges):
    return np.clip(np.digitize(v, edges) - 1, 0, len(edges) - 2)


def split(cost_i, mass_s, mass_r, idx_s, idx_r, n):
    out = []
    for k in range(n):
        out.append({"syn_mass": float(mass_s[idx_s == k].sum()), "real_mass": float(mass_r[idx_r == k].sum()),
                    "W1_from_syn": float(cost_i[idx_s == k].sum())})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track", choices=["v2x", "lumpi"])
    ap.add_argument("syn", help="a submission zip or a folder of 50 synthetic frames")
    ap.add_argument("--ref", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import ot
    t = load_track(a.track)
    syn = load_frames(t, a.syn)
    box = realism.RANGES[t.name]
    report = {"syn": a.syn, "track": a.track, "proxies": {}}
    for ref in a.ref:
        real = load_frames(t, ref)
        rng = np.random.default_rng(1234)
        S_all, R_all = realism.concat_and_mask(syn, box), realism.concat_and_mask(real, box)
        S = realism.subsample(S_all, realism.N_SUBSAMPLE, rng).astype(np.float64)
        R = realism.subsample(R_all, realism.N_SUBSAMPLE, rng).astype(np.float64)
        res = realism.score(syn, real, t.name, exact_emd=True)
        M = cdist(S, R)
        G = ot.emd(np.full(len(S), 1 / len(S)), np.full(len(R), 1 / len(R)), M, numItermax=10_000_000)
        cost_i = (G * M).sum(1)                                   # each synthetic point's share of W1
        j = G.argmax(1)                                           # its main partner
        W1 = float(cost_i.sum())
        rs, rr = np.hypot(S[:, 0], S[:, 1]), np.hypot(R[:, 0], R[:, 1])
        ms, mr = np.full(len(S), 1 / len(S)), np.full(len(R), 1 / len(R))
        zb = Z_BANDS[a.track]
        ent = {"CD": res["CD"], "MMD": res["MMD"], "EMD": res["EMD"], "FPD": res["FPD"], "R": res["R"], "W1": W1,
               "mean_move_m": W1, "move_quantiles_m": {q: float(np.quantile(M[np.arange(len(S)), j], q)) for q in (0.5, 0.75, 0.9, 0.99)},
               "range_bands": {"edges": R_BANDS, "rows": split(cost_i, ms, mr, bands(rs, R_BANDS), bands(rr, R_BANDS), len(R_BANDS) - 1)},
               "z_bands": {"edges": zb, "rows": split(cost_i, ms, mr, bands(S[:, 2], zb), bands(R[:, 2], zb), len(zb) - 1)},
               "fpd_parts": {"mean_syn": S.mean(0).tolist(), "mean_real": R.mean(0).tolist(),
                             "std_syn": S.std(0).tolist(), "std_real": R.std(0).tolist()}}
        cell = lambda P: (np.floor((P[:, 0] + 40) / 10).clip(0, 7) * 8 + np.floor((P[:, 1] + 40) / 10).clip(0, 7)).astype(int)
        cs, cr = cell(S), cell(R)
        cells = [{"cell": int(k), "x0": -40 + 10 * (k // 8), "y0": -40 + 10 * (k % 8), "syn_mass": float(ms[cs == k].sum()),
                  "real_mass": float(mr[cr == k].sum()), "W1_from_syn": float(cost_i[cs == k].sum())} for k in range(64)]
        ent["bev_cells_top"] = sorted(cells, key=lambda c: -abs(c["syn_mass"] - c["real_mass"]))[:12]
        report["proxies"][ref] = ent
        print(ref, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in ent.items() if k in ("CD", "MMD", "EMD", "FPD", "R")}), flush=True)
        print("  range  syn/real mass, W1 share:", " ".join(f"[{e0}-{e1}] {r['syn_mass']:.3f}/{r['real_mass']:.3f} {r['W1_from_syn'] / W1:.2f}"
                                                         for e0, e1, r in zip(R_BANDS, R_BANDS[1:], ent["range_bands"]["rows"])), flush=True)
        print("  z      syn/real mass, W1 share:", " ".join(f"[{e0}-{e1}] {r['syn_mass']:.3f}/{r['real_mass']:.3f} {r['W1_from_syn'] / W1:.2f}"
                                                         for e0, e1, r in zip(zb, zb[1:], ent["z_bands"]["rows"])), flush=True)
        print("  moves (m) median/75/90/99:", ent["move_quantiles_m"], " means syn", np.round(S.mean(0), 2), "real", np.round(R.mean(0), 2),
              " std syn", np.round(S.std(0), 2), "real", np.round(R.std(0), 2), flush=True)
    Path(a.out).write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
