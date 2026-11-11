#!/usr/bin/env python
"""S10 record 15.15.8: for consecutive LUMPI uploads, local per-class deltas on early-A, late-A, B (final routed validation
predictions) against the server per-class delta. Diagnostic only (server per-class numbers are records).

    python common/tools/s10_split_history.py            # prints one json line per pair and class, writes --out
"""
import glob, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common")); sys.path.insert(0, str(REPO / "common/tools"))
from _common import data_path, model_info
from bdc26 import scorecard as sc
L = REPO / "model-lumpi-track"
rows = []
for f in glob.glob(str(L / "*/submissions/*/codabench_*.json")):
    c = json.load(open(f)); s = c.get("scores") or {}
    if "AP_3d_0.5_R40_Person" not in s: continue
    rows.append((Path(f).parents[2].name, Path(f).parent.name, c["codabench_submission_id"], s))
rows.sort(key=lambda r: r[2])
cache = {}
def flags(m):
    if m in cache: return cache[m]
    _, card, track = model_info(L / m)
    rv = card["data"]["realval"]; root = data_path(track, rv); D = rv.replace("/", "_")
    gts = {s_: sc.load_split(root, s_) for s_ in ("val", "valB")}
    p = {s_: L / m / "validation/output" / f"{D}_{s_}_routed.json" for s_ in ("val", "valB")}
    if not all(x.exists() for x in p.values()):
        cache[m] = None; return None
    fl = {s_: sc.flags_for(p[s_], gts[s_], list(track.classes)) for s_ in ("val", "valB")}
    late = sc.late_a_ids(track, list(gts["val"]))
    early = [k for k in gts["val"] if k not in set(late)]
    cache[m] = (fl, {"late": late, "early": early}, rv); return cache[m]
pairs = [("routed-c0", "routed-c1"), ("routed-g22", "routed-c0"), ("routed-g15", "routed-g22"), ("routed-g14", "routed-g15"),
         ("routed-g13", "routed-g14"), ("routed-g12", "routed-g13"), ("routed-g11d", "routed-g12"), ("routed-g11c", "routed-g11d"),
         ("routed-g11b", "routed-g11c"), ("routed-g10", "routed-g11b"), ("routed-g8", "routed-g10"), ("routed-g7", "routed-g8"),
         ("routed-g6", "routed-g7"), ("routed-g15", "routed-g21")]
srv = {}
for m, sub, i, s in rows:
    srv.setdefault(m, (i, s))   # first upload per model folder
srv["routed-c1"] = next((i, s) for m, sub, i, s in rows if m == "routed-c1")
out = []
for a, b in pairs:
    if a not in srv or b not in srv: print("skip (no server record)", a, b); continue
    fa, fb = flags(a), flags(b)
    if not fa or not fb: print("skip (no routed predictions)", a, b); continue
    if fa[2] != fb[2]: print("skip (realval differs)", a, b, fa[2], fb[2]); continue
    for c in ("Person", "Car", "Bicycle", "Truck"):
        res = {}
        for name, s_, sel in (("earlyA", "val", "early"), ("lateA", "val", "late"), ("B", "valB", None)):
            x, y = fa[0][s_][c], fb[0][s_][c]
            if sel:
                x = sc.subset({c: x}, fa[1][sel])[c]; y = sc.subset({c: y}, fa[1][sel])[c]
            ax, ay = sc.ap_from_flags(x, "3d@0.5"), sc.ap_from_flags(y, "3d@0.5")
            res[name] = None if ax is None or ay is None else round(ay - ax, 4)
        sd = srv[b][1].get(f"AP_3d_0.5_R40_{c}"), srv[a][1].get(f"AP_3d_0.5_R40_{c}")
        d = None if None in sd else round(sd[0] - sd[1], 4)
        out.append({"pair": f"{a}->{b}", "ids": f"{srv[a][0]}->{srv[b][0]}", "class": c, **res, "server": d})
        print(json.dumps(out[-1]), flush=True)
OUT = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else None
if OUT:
    json.dump(out, open(OUT, "w"), indent=1)
