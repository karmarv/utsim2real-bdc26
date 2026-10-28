"""S7 final revisions (docs/decisions/2026-10-26-s7-final-revisions.md): the final check per class against the entry
(rule 5) and the upload-gate projection (rule 6), shared by common/pipeline/s7f_portfolio.sh and s7g_amend.sh.

    python common/tools/s7_check.py check <track> <model_dir> <entry_dir>        # prints one line per class, then FROZEN ...
    python common/tools/s7_check.py projection <track> <model_dir> <entry_dir>

check reads the final validation predictions of both models (validation/output/<data>_<split>_routed.json). A class is
kept when the pooled A+B gain has paired-bootstrap P(gain) >= 0.9, neither split drops by more than 0.005 and the
train-split frames alone do not lose (audit rule a: V2X the V2X-Real train split of A and B pooled, LUMPI realval-A);
LUMPI Van by its S6 judge (late-A gain >= 0.01 at P >= 0.9); LUMPI Bicycle, Motorcycle and Bus are frozen (S6 rule 4).
Writes <model_dir>/validation/results/final_check.json.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import data_path, load_track  # noqa: E402
from bdc26 import scorecard as sc  # noqa: E402

FROZEN = {"lumpi": {"Bicycle", "Motorcycle", "Bus"}}


def check(t: str, m: Path, ref: Path, n_boot: int = 200, seed: int = 0) -> tuple[dict, list]:
    tr = load_track(t)
    root = data_path(tr, "pcdet/realval-v1")
    cls = list(tr["classes_with_test_gt"])
    gts = {s: sc.load_split(root, s) for s in ("val", "valB")}
    p = lambda d, s: Path(d, "validation", "output", f"pcdet_realval-v1_{s}_routed.json")
    fl = {(k, s): sc.flags_for(p(d, s), gts[s], cls, cache=False) for k, d in (("inc", ref), ("new", m)) for s in gts}
    train = None
    if t == "v2x":                                      # frame ids are <scene>__<frame>; the scene folders sit under their split
        raw = data_path(tr, "real/raw")
        split_of = {x.name: s.name for s in raw.iterdir() for x in s.iterdir()}
        train = {s: [i for i in gts[s] if split_of[i.split("__")[0]] == "train"] for s in gts}
    late = sc.late_a_ids(tr, list(gts["val"]))
    res, fail = {}, []
    for c in cls:
        if c in FROZEN.get(t, ()):
            res[c] = {"kept": False, "note": "frozen (S6 rule 4)"}
            fail.append(c)
            continue
        ap = {(k, s): sc.ap_from_flags(fl[(k, s)][c], "3d@0.5") for k in ("inc", "new") for s in gts}
        dA, dB = ap[("new", "val")] - ap[("inc", "val")], ap[("new", "valB")] - ap[("inc", "valB")]
        if t == "lumpi" and c == "Van":                 # the S6 judge: late-A gain >= 0.01 at P >= 0.9; the train split is A
            b = sc.paired_bootstrap({c: sc.subset(fl[("inc", "val")], late)[c]}, {c: sc.subset(fl[("new", "val")], late)[c]},
                                    [c], n_boot, seed)[c]
            ok = b["p_gain"] is not None and b["delta"] >= 0.01 and b["p_gain"] >= 0.9 and dA >= 0
            res[c] = {"dA": dA, "late_A_delta": b["delta"], "p_gain": b["p_gain"], "kept": ok}
        else:
            pg = sc.pooled_gate({s: fl[("inc", s)][c] for s in gts}, {s: fl[("new", s)][c] for s in gts}, c, n_boot, seed)
            if train is not None:
                dtr = sc.pooled_gate({s: sc.subset(fl[("inc", s)], train[s])[c] for s in gts},
                                     {s: sc.subset(fl[("new", s)], train[s])[c] for s in gts}, c, n_boot, seed)["delta"]
            else:
                dtr = dA
            ok = pg["ok"] and dA >= -0.005 and dB >= -0.005 and dtr is not None and dtr >= 0
            res[c] = {"dA": dA, "dB": dB, "pooled_delta": pg["delta"], "p_gain": pg["p_gain"], "train_split_delta": dtr, "kept": ok}
        if not ok:
            fail.append(c)
    Path(m, "validation", "results", "final_check.json").write_text(json.dumps({"vs": Path(ref).name, "classes": res}, indent=2))
    return res, fail


def projection(t: str, m: Path, ref: Path) -> dict:
    """Rule 6: 0.6 x the mean of the A and B mAP gains x 0.6 / 0.7 (Unknown excluded; LUMPI Van read from realval-A,
    its judging split, on both sides)."""
    n, r = (json.loads(Path(d, "validation", "results", "local_scores.json").read_text()) for d in (m, ref))

    def mAP(s, split):
        pc = dict(s[f"realval_{split}_per_class"])
        if t == "lumpi" and split == "B":
            pc["Van"] = s["realval_A_per_class"]["Van"]
        cs = [c for c, v in pc.items() if v is not None and c != "Unknown"]
        return sum(pc[c] for c in cs) / len(cs)

    dA, dB = mAP(n, "A") - mAP(r, "A"), mAP(n, "B") - mAP(r, "B")
    p = 0.6 * (dA + dB) / 2 * 0.6 / 0.7
    return {"dA": dA, "dB": dB, "combined": p, "passed": p >= 0.003}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["check", "projection"])
    ap.add_argument("track")
    ap.add_argument("model_dir")
    ap.add_argument("entry_dir")
    a = ap.parse_args()
    if a.mode == "check":
        res, fail = check(a.track, Path(a.model_dir), Path(a.entry_dir))
        for c, r in res.items():
            print(c, json.dumps(r))
        print("FROZEN", " ".join(fail))
    else:
        p = projection(a.track, Path(a.model_dir), Path(a.entry_dir))
        print(f"dA {p['dA']:+.4f} dB {p['dB']:+.4f} combined {p['combined']:+.4f} (bar +0.003: {'passed' if p['passed'] else 'not met'})")


if __name__ == "__main__":
    main()
