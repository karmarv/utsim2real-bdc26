#!/usr/bin/env python
"""Release 10.5 (record docs/decisions/2026-11-14-s10-10.5-final-push.md Section 3): the S8 view-set swap (4 test-time
views -> 12) on a scored system's card, under a class rule fixed before any result. No member, route, fusion set,
IoU, weight or stage changes; only the number of test-time views of members the card already uses.

Every used 4-view member (a `tta` member without `tta_tag`) whose model has 12-view validation outputs gets a 12-view
sibling of the same checkpoint (`tta: flip4+yaw+z+scale`, `tta_tag: tta12`, its own tuned test/postprocess_tta12.yaml).
A class takes the 12-view siblings of all its 4-view members (route and fusion) only if, against the parent:
  (1) its AP on realval A and B pooled gains with paired-bootstrap P(gain) >= 0.9 (scorecard.pooled_gate, 200 draws),
  (2) neither realval A nor realval B drops by more than 0.005 (the pooled rule of docs/decisions/README.md 3.2),
  (3) where the track defines late-A (LUMPI, Measurement4 4800-6399, the frames nearest the test window), its late-A AP
      does not drop.
Classes are scored on the routed outputs of the probe card, which swaps every class at once (each class's routed boxes
come from its own members and stages; a class that receives cross-class copies from a swapped class is reported).

    python common/tools/s10_5_view_swap.py probe  lumpi routed-s10-4-l8 routed-s10-5-l9 --candidate L9
    python common/tools/route_predictions.py validate model-lumpi-track/routed-s10-5-l9
    python common/tools/s10_5_view_swap.py decide lumpi routed-s10-4-l8 routed-s10-5-l9 --candidate L9
`decide` rewrites the card with the passing classes only (exit 0), or leaves the probe card and exits 3 if none passes.
"""
import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import data_path, member_tag, validation_predictions  # noqa: E402
from bdc26 import scorecard as sc  # noqa: E402
from bdc26.config import load_track  # noqa: E402
from route_predictions import used_members  # noqa: E402

REC = "docs/decisions/2026-11-14-s10-10.5-final-push.md"
TAG = "tta12"
VIEWS = "flip4+yaw+z+scale"


def sibling_name(card: dict, n: str) -> str:
    """The 12-view sibling of member n: an existing card member of the same checkpoint with tta_tag tta12, else n's
    name with _tta replaced by _tta12."""
    m = card["members"][n]
    for k, v in card["members"].items():
        if v.get("tta") and v.get("tta_tag") == TAG and v["model"] == m["model"] and v["ckpt"] == m["ckpt"]:
            return k
    return (n[:-4] if n.endswith("_tta") else n) + "_" + TAG


def sibling_def(m: dict) -> dict:
    return {"model": m["model"], "ckpt": m["ckpt"], "tta": VIEWS, "tta_tag": TAG, "postprocess": f"test/postprocess_{TAG}.yaml"}


def swappable(td: Path, card: dict) -> dict:
    """{4-view member: 12-view sibling} for the used members whose model has 12-view outputs on both realval splits."""
    out = {}
    for n in used_members(card):
        m = card["members"][n]
        if not m.get("tta") or m.get("tta_tag"):
            continue
        s = sibling_def(m)
        if all(validation_predictions(td / m["model"], card, sp, tag=member_tag(s)).exists() for sp in ("val", "valB")):
            out[n] = sibling_name(card, n)
    return out


def classes_of(card: dict, sw: dict) -> dict:
    """{class: [4-view members it swaps]} over the route and the fusion sets."""
    out = {}
    for c, n in (card.get("route") or {}).items():
        if n in sw and c not in (card.get("fusion") or {}):
            out.setdefault(c, []).append(n)
    for c, fz in (card.get("fusion") or {}).items():
        hit = [n for n in fz["members"] if n in sw]
        if hit:
            out.setdefault(c, []).extend(hit)
    return out


def swapped_card(parent: dict, sw: dict, classes) -> dict:
    card = copy.deepcopy(parent)
    hit = set()
    for c in classes:
        if c in (card.get("fusion") or {}):
            hit |= {n for n in card["fusion"][c]["members"] if n in sw}
            card["fusion"][c]["members"] = [sw.get(n, n) for n in card["fusion"][c]["members"]]
        if card["route"].get(c) in sw:
            hit.add(card["route"][c])
            card["route"][c] = sw[card["route"][c]]
    for n in sorted(hit):
        card["members"].setdefault(sw[n], sibling_def(parent["members"][n]))
    return card


def write_card(td: Path, parent_name: str, name: str, card: dict, cand: str, status: str, notes: str) -> None:
    dst = td / name
    for sub in ("validation/output", "validation/results", "test/output", "train"):
        (dst / sub).mkdir(parents=True, exist_ok=True)
    for f in ("make_submission.sh", "synthetic_ids.txt"):
        if not (dst / "test" / f).exists():
            shutil.copy2(td / parent_name / "test" / f, dst / "test" / f)
    card.update({"name": name, "strategy": "S10-5", "candidate": cand, "derived_from": parent_name,
                 "status": status, "notes": notes})
    (dst / "model.yaml").write_text(yaml.safe_dump(card, sort_keys=False))


def routed(td: Path, name: str, card: dict, split: str) -> dict:
    d = card["data"]["realval"].replace("/", "_")
    return json.loads((td / name / "validation" / "output" / f"{d}_{split}_routed.json").read_text())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["probe", "decide"])
    ap.add_argument("track", choices=["lumpi", "v2x"])
    ap.add_argument("parent")
    ap.add_argument("name")
    ap.add_argument("--candidate", required=True)
    a = ap.parse_args()
    T = load_track(f"{a.track}-track")
    td = T.model_dir
    parent = yaml.safe_load((td / a.parent / "model.yaml").read_text())
    sw = swappable(td, parent)
    cls = classes_of(parent, sw)
    scored = [c for c in cls if c in list(T["classes_with_test_gt"])]
    if a.step == "probe":
        print("swappable:", ", ".join(f"{n} -> {s}" for n, s in sw.items()) or "none")
        print("classes:", ", ".join(f"{c} ({'+'.join(cls[c])})" for c in scored) or "none")
        if not scored:
            return 3
        card = swapped_card(parent, sw, scored)
        write_card(td, a.parent, a.name, card, a.candidate,
                   f"S10-5 {a.candidate} probe: {a.parent} with every 4-view member that has a 12-view sibling swapped "
                   f"({', '.join(scored)}); the class rule decides ({REC})",
                   f"S10-5 {a.candidate} probe ({REC}): validation only; `decide` keeps the passing classes.\n")
        return 0

    new = yaml.safe_load((td / a.name / "model.yaml").read_text())
    root = data_path(T, parent["data"]["realval"])
    gts = {sp: sc.load_split(root, sp) for sp in ("val", "valB")}
    late = sc.late_a_ids(T, list(gts["val"]))
    rec_of = {}                                     # cross-class copies: donor -> receivers
    for b, k in ((parent.get("final_adjust") or {}).get("cross_copies") or {}).items():
        rec_of.setdefault(k["from"], []).append(b)
    look = sorted(set(scored) | {r for c in scored for r in rec_of.get(c, [])})
    fl = {}
    for who, nm, cd in (("inc", a.parent, parent), ("new", a.name, new)):
        for sp in ("val", "valB"):
            p = routed(td, nm, cd, sp)
            fl[(who, sp)] = sc.frame_flags({i: p.get(i, []) for i in gts[sp]}, gts[sp], look)
    rows, keep = {}, []
    for c in look:
        ap_ = {(w, sp): sc.ap_from_flags(fl[(w, sp)][c], "3d@0.5") for w in ("inc", "new") for sp in ("val", "valB")}
        dA = (ap_[("new", "val")] or 0) - (ap_[("inc", "val")] or 0)
        dB = (ap_[("new", "valB")] or 0) - (ap_[("inc", "valB")] or 0)
        pg = sc.pooled_gate({sp: fl[("inc", sp)][c] for sp in ("val", "valB")},
                            {sp: fl[("new", sp)][c] for sp in ("val", "valB")}, c)
        dL = None
        if late:
            li = sc.subset({c: fl[("inc", "val")][c]}, late)[c]
            ln = sc.subset({c: fl[("new", "val")][c]}, late)[c]
            dL = (sc.ap_from_flags(ln, "3d@0.5") or 0) - (sc.ap_from_flags(li, "3d@0.5") or 0)
        ok = bool(pg["ok"] and dA >= -0.005 and dB >= -0.005 and (dL is None or dL >= 0))
        role = "swapped" if c in scored else "receives copies of " + ", ".join(d for d in scored if c in rec_of.get(d, []))
        rows[c] = {"role": role, "members": cls.get(c, []), "delta_A": dA, "delta_B": dB, "delta_lateA": dL,
                   "pooled_delta": pg["delta"], "pooled_p_gain": pg["p_gain"], "rule": "PASS" if ok else "FAIL"}
        if c in scored and ok:
            keep.append(c)
        print(f"{c:10s} {role:28s} A {dA:+.4f}  B {dB:+.4f}  late-A {'' if dL is None else f'{dL:+.4f}'}  pooled "
              f"{(pg['delta'] or 0):+.4f} P {pg['p_gain'] if pg['p_gain'] is not None else float('nan'):.2f}  "
              f"{rows[c]['rule'] if c in scored else ''}", flush=True)
    res = {"parent": a.parent, "rule": "pooled P(gain) >= 0.9, A and B drop <= 0.005, late-A >= 0 (fixed before results)",
           "swaps": sw, "classes": rows, "kept": keep}
    (td / a.name / "validation" / "results" / "view_swap.json").write_text(json.dumps(res, indent=1, default=float))
    if not keep:
        print("no class passes the rule: no system")
        return 3
    card = swapped_card(parent, sw, keep)
    write_card(td, a.parent, a.name, card, a.candidate,
               f"S10-5 {a.candidate}: {a.parent} with 12 test-time views for {', '.join(keep)} (the view-set swap, "
               f"class rule fixed before results) ({REC})",
               f"S10-5 {a.candidate} ({REC}): {a.parent}'s members, route, fusion sets, IoUs, weights and every stage "
               f"unchanged; for {', '.join(keep)} the 4-view members are replaced by their 12-view siblings (same "
               "checkpoints, flip4+yaw+z+scale, their own tuned postprocess). Kept classes passed: pooled realval A+B "
               "P(gain) >= 0.9, neither split down more than 0.005, late-A not down (LUMPI).\n")
    print("kept:", ", ".join(keep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
