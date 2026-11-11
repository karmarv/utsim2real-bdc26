#!/usr/bin/env python
"""Build the G1 training dataset for Track 1: UT-LUMPI frames + ray-cast procedural Persons (module M8, first version).

What it adds on top of prepare_ut.py (ut-v1):
  - Persons. UT-LUMPI has none, yet Person is 1/7 of the score. Each frame gets Poisson(--persons) walkers
    (articulated ellipsoid bodies, common/bdc26/render/pedsim.py), ray-cast with the five Measurement4 lidars
    as described in meta.json (pose, per-beam elevation table, azimuth step; the UT frames were simulated with
    the same rig: beam residual median 0.03 deg). Inserted ray-consistently BEFORE the actor scale fix: frame
    points behind a walker are removed (per sensor, exact ray test) and walker returns behind existing geometry
    are dropped (per-sensor range image).
  - Placement and annotation box from legal real Person labels (Measurement4 frames < 6400, through
    ForbiddenGuard; Rules: real label statistics for generator parameters are allowed): each walker copies the
    position, heading and l/w/h of a random real Person row, with jitter. The body is fitted inside that box.
  - Class map: UT Van -> Van (--van-as car to keep ut-v1's Van -> Car). Legal M4 id 6 ("Van") boxes have van
    dimensions (median 4.84 x 1.99 x 1.95 m vs car 4.48 x 1.99 x 1.70 m).
Then the ut-v1 steps: actor scale fix 1/0.78, mask to range, resample to 50,000 points, min points.
With --g2 (engine G2-lite, strategy R3, common/bdc26/render/g2.py), after the scale fix: Car, Van, Truck and Bus are
re-cast from their own convex hull (mirrored; completed by exemplar hulls of well-sampled UT actors when sparse) with
the five lidars (the scale fix leaves UT Cars at 0.44x the real density in the same place), Truck, Bus, Bicycle and
Motorcycle take real label sizes, Bicycle and Motorcycle become two-wheelers with seated riders (UT ones: 0.25-0.52x),
per-class ray dropout (DROP) matches the real points per box in the same place, and Poisson(--clutter) unlabeled
poles, trees, bollards, bins and boxes are added (60% of them 1-4 m from real walker positions) as hard negatives.
The object sampling rate stays the G1 one (bdc26.density.resample_calibrated n_ref).

    python prepare_g1.py --name g1-v1
    python prepare_g1.py --name g1-smoke --frames 40 --stride 250 --workers 8
    python prepare_g1.py --name g1-v4 --walker v2 --density-prior gen/density_prior_v1.npz --g2     # needs open3d (in .venv_ut)

S9 engine v6 (docs/decisions/2026-11-02-s9-clean-twin-plan.md), every option off by default so older versions rebuild:
  --placement map      walkers from the twin's own scene map (gen/scene_map_v1.npz, bdc26.render.scene_map) with the box
                       mixture and range histogram of gen/walker_scalars_v6.json (scalars; no label row is read)
  --clutter-anchors map  clutter anchors at the map's curbside cells instead of real walker positions
  --size-source quantiles  G2 real sizes from 19 quantiles per dimension (gen/size_scalars_v6.json) instead of label rows
  --class-rule size    the LUMPI vehicle convention by size (bdc26.render.v6.lumpi_class_rule: transporters are Truck)
  --structure N        Poisson(N) map-placed hedges, fences, walls, bushes, shelters, kiosks (G2, unlabeled)
  --ground-bowl F      the 5-constant ground surface of F (bdc26.render.v6.GroundBowl) added to every point and box
    python prepare_g1.py --name g1-v6 --walker v2 --g2 --placement map --clutter-anchors map --size-source quantiles \
        --class-rule size --structure 30 --ground-bowl gen/ground_bowl_v1.json --density-prior gen/density_prior_v6.npz
"""
import argparse
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from bdc26.config import load_track  # noqa: E402
from bdc26.guard import ForbiddenGuard  # noqa: E402
from bdc26.io import lumpi  # noqa: E402
from bdc26.pcdet_export import write_card, write_frame, write_splits  # noqa: E402
from bdc26.prep import UTConvertParams, convert_ut_frame  # noqa: E402
from bdc26.render.g1 import FlatGround, WalkerInserter  # noqa: E402
from bdc26.render.pedsim import InsertParams, Sensor  # noqa: E402
from bdc26.render import scene_map as smap, v6  # noqa: E402

T = load_track("lumpi-track")
PRIOR = T.gen / "person_prior_m4.npz"
SIZE_PRIOR = T.gen / "size_prior_g2.npz"
HULL_BANK = T.gen / "hull_bank_g2.npz"
BANK_CLASSES = ("Car", "Van", "Truck", "Bus")
DROP = {"Car": [0.14, 0.02, 15.0, 25.0], "Van": 0.43, "Truck": 0.20, "Bus": 0.70, "clutter": 0.10}   # per-ray drop of re-cast objects (R3 calibration, docs/02-STRATEGY.md Section 8.7.1)
SIZE_FILTERS = {"Bus": (8.0, 20.0), "Truck": (5.0, 22.0), "Bicycle": (1.4, 2.8), "Motorcycle": (1.5, 3.0)}
SCENE_MAP = T.gen / "scene_map_v1.npz"
WALKER_SCALARS = T.gen / "walker_scalars_v6.json"
SIZE_SCALARS = T.gen / "size_scalars_v6.json"
MAP_WEIGHTS = {"curb": 0.30, "open": 0.05, "road": 0.45, "beyond": 0.20}   # walker area shares: points per walker (median 45 road, 30 curb, 22 open, 25 beyond on 40 frames) against real 42
V6 = {}                                                                    # per-worker v6 state (class rule, bowl)


def map_pose(scene, weights=None):
    w = json.loads(WALKER_SCALARS.read_text())
    return smap.WalkerSampler(scene, smap.WalkerConfig(weights=weights or MAP_WEIGHTS, range_bins=tuple(w["range_bins"]),
                                                       range_share=tuple(w["range_share"]), boxes=tuple(map(tuple, w["boxes"])),
                                                       pc_range=tuple(T.pc_range),
                                                       range_from=tuple(map(tuple, w.get("range_from", [[0.0, 0.0]]))),
                                                       map_ground=True))


def structure_table(scene):
    xy, _ = smap.structure_points(scene, pc_range=tuple(T.pc_range))
    dirs = np.full(len(xy), np.nan)
    i, j = scene.index(xy[:, 0], xy[:, 1])
    for k in range(len(xy)):
        d = scene.axial_dir_near(int(i[k]), int(j[k]), radius=12)
        if d is not None:
            dirs[k] = np.arctan2(d[1], d[0])
    return xy, dirs


def build_hull_bank(params, val_from: int, stride: int = 90) -> Path:
    """Exemplar hulls of well-sampled re-cast actors from training-range UT frames (G2 completion of sparse actors); cached."""
    if HULL_BANK.exists():
        return HULL_BANK
    from bdc26.render.g2 import HullBank
    bank = HullBank(BANK_CLASSES, min_points=800)
    for i in range(0, min(val_from, T["ut"]["n_frames"]), stride):
        convert_ut_frame(T, i, params, post_inserter=bank)
    bank.save(HULL_BANK)
    print("hull bank", bank.summary())
    return HULL_BANK


def g2_drop_table(override_json=None) -> dict:
    return dict(DROP, **(json.loads(override_json) if override_json else {}))


def build_prior(margin: float = 2.0) -> Path:
    """Legal Measurement4 Person rows (x, y, yaw, l, w, h) inside the range (+margin); cached."""
    if PRIOR.exists():
        return PRIOR
    g = ForbiddenGuard.for_track(T)
    lab = lumpi.read_labels_guarded(T.real / "labels" / "Measurement4_Label.guarded.csv", "Measurement4", g,
                                    purpose="G1 generator: Person placement and box-size prior")
    b = lab.boxes[lab.class_id == 0]
    x0, y0, _, x1, y1, _ = T.pc_range
    m = (b[:, 0] > x0 - margin) & (b[:, 0] < x1 + margin) & (b[:, 1] > y0 - margin) & (b[:, 1] < y1 + margin)
    b = b[m]
    PRIOR.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(PRIOR, xy=b[:, :2], yaw=b[:, 6], lwh=b[:, 3:6], source="legal M4 labels, class id 0")
    return PRIOR


def m4_sensors() -> list[Sensor]:
    sess = lumpi.read_sessions(T.real / "raw" / "meta.json", T, experiment=4)
    names = T["real"]["sessions_m4"]
    return [Sensor(s.extrinsic_local, s.elevation_deg, s.horizontal_resolution, name=names.get(sid, str(sid)))
            for sid, s in sorted(sess.items())]


class PriorPose:
    def __init__(self, path: Path, jitter_xy: float, jitter_yaw: float):
        d = np.load(path)
        self.xy, self.yaw, self.lwh = d["xy"], d["yaw"], d["lwh"]
        self.jxy, self.jyaw = jitter_xy, jitter_yaw

    def __call__(self, rng):
        i = rng.integers(len(self.xy))
        x, y = self.xy[i] + rng.normal(0, self.jxy, 2)
        l, w, h = self.lwh[i] * rng.uniform(0.97, 1.03, 3)
        return float(x), float(y), float(self.yaw[i] + rng.normal(0, self.jyaw)), (float(l), float(w), float(h))


# Walker presets. v1: the first walker. v2: calibrated on legal real Persons (realval-A, 20-200 points):
#   torso-band (0.3-1.6 m) horizontal std along / across the heading: real 0.125 / 0.123 m, v1 0.068 / 0.132,
#   v2 0.116 / 0.121 (deeper torsos, stronger arm swing, bags, body yaw scatter 0.8 rad about the box heading);
#   head band (1.5-1.8 m) share: real 12.7%, v1 8.7% (v2 puts the body top 2-14 cm below the box top, v1 6-20 cm);
#   per-sensor misregistration / capture-time offsets of the five unsynchronised lidars (4 cm) and 3 cm range noise.
WALKERS = {
    "v1": {"style": {}, "insert": {}, "body_yaw_sigma": 0.0, "height_margin": [0.06, 0.20]},
    "v2": {"style": {"depth_range": [1.25, 1.7], "arm_swing": 1.3, "backpack_prob": 0.3, "sidebag_prob": 0.25,
                     "front_item_prob": 0.1},
           "insert": {"range_noise": 0.03, "sensor_jitter_xy": 0.04, "sensor_jitter_z": 0.01},
           "body_yaw_sigma": 0.8, "height_margin": [0.02, 0.14]},
}


class BodyFromBox:
    def __init__(self, height_margin):
        self.lo, self.hi = height_margin

    def __call__(self, l, w, h, rng):
        return (float(np.clip(h - rng.uniform(self.lo, self.hi), 1.45, 1.98)),
                float(np.clip(w - rng.uniform(0.24, 0.34), 0.36, 0.52)))


_INS = None
_G2 = None


def load_static_anchors(path):
    """S10 R1 anchors [(x, y, yaw, l, w, h)] from common/tools/s10_static_anchors.py, or None; a calibrated file
    (--calibrate) adds each block's kept share of returns as a 7th value."""
    if not path:
        return None
    d = json.loads(Path(path).read_text())
    return [tuple(float(v) for v in (a["x"], a["y"], a["yaw"], a["l"], a["w"], a["h"]))
            + ((float(a["keep"]),) if "keep" in a else ()) for a in d["anchors"]]


def make_g2(ins_params, clutter: float, truck_size: str, drop: dict, v6opt: dict | None = None):
    from bdc26.render.g2 import G2Config, G2Pass, HullBank, size_prior_from_labels
    v6opt = v6opt or {}
    if v6opt.get("size_source") == "quantiles":
        spec = json.loads(SIZE_SCALARS.read_text())
        rng = np.random.default_rng(4321)
        sizes = {c: v6.QuantileSizes(spec[c]).sample(20000, rng) for c in SIZE_FILTERS}
    else:
        sizes = size_prior_from_labels(T.pcdet / "realval-v1", ["val", "valB"], SIZE_FILTERS, cache=SIZE_PRIOR)
    scene = smap.SceneMap.load(SCENE_MAP) if (v6opt.get("clutter_anchors") == "map" or v6opt.get("structure", 0) > 0) else None
    anchors = smap.anchor_points(scene, pc_range=tuple(T.pc_range)) if v6opt.get("clutter_anchors") == "map" else np.load(PRIOR)["xy"]
    sxy, sdir = structure_table(scene) if v6opt.get("structure", 0) > 0 else (None, None)
    cfg = G2Config(recast={"Car": "car", "Van": "box", "Truck": "box", "Bus": "box"},
                   resize={"Bus": sizes["Bus"], "Bicycle": sizes["Bicycle"], "Motorcycle": sizes["Motorcycle"],
                           **({"Truck": sizes["Truck"]} if truck_size == "real" else {})},
                   stretch={"Truck": {"prob": 0.5, "lengths": sizes["Truck"][:, 0]}} if truck_size == "stretch" else {},
                   riders={"Bicycle": "bicycle", "Motorcycle": "motorcycle"},
                   clutter_mean=clutter, clutter_anchor_xy=anchors, drop=drop, params=ins_params,
                   bank=HullBank.load(HULL_BANK) if HULL_BANK.exists() else None,
                   structure_mean=float(v6opt.get("structure", 0.0)), structure_xy=sxy, structure_dir=sdir,
                   static_anchors=load_static_anchors(v6opt.get("static_anchors")))
    ground = (smap.MapGround(scene, default=T["ut"]["ground_z"]) if scene is not None
              else FlatGround(T["ut"]["ground_z"]))                       # S9: clutter and structures on the map's ground
    return G2Pass(m4_sensors(), cfg, ground=ground, pc_range=T.pc_range)


def init(persons, jitter_xy, jitter_yaw, walker="v1", style_json=None, insert_json=None, body_yaw_sigma=None,
         g2=False, clutter=30.0, truck_size="real", g2_drop=None, v6opt=None):
    global _INS, _G2
    v6opt = v6opt or {}
    w = WALKERS[walker]
    style = dict(w["style"], **(json.loads(style_json) if style_json else {}))
    ins = dict(w["insert"], **(json.loads(insert_json) if insert_json else {}))
    pose = (map_pose(smap.SceneMap.load(SCENE_MAP), json.loads(v6opt["map_weights"]) if v6opt.get("map_weights") else None)
            if v6opt.get("placement") == "map" else PriorPose(PRIOR, jitter_xy, jitter_yaw))
    V6.clear()
    V6["class_rule"] = v6opt.get("class_rule") == "size"
    V6["bowl"] = v6.GroundBowl.load(T.root / v6opt["ground_bowl"]) if v6opt.get("ground_bowl") else None
    _INS = WalkerInserter(m4_sensors(), pose, n_mean=persons,
                          ground=FlatGround(T["ut"]["ground_z"]), pc_range=T.pc_range, params=InsertParams(**ins),
                          walker_style=style, body_yaw_sigma=w["body_yaw_sigma"] if body_yaw_sigma is None else body_yaw_sigma,
                          body_from_box=BodyFromBox(w["height_margin"]))
    _G2 = make_g2(InsertParams(**ins), clutter, truck_size, g2_drop_table(g2_drop), v6opt) if g2 else None


def work(args):
    idx, out, params = args
    pts, boxes, names, st = convert_ut_frame(T, idx, params, inserter=_INS, post_inserter=_G2)
    if V6.get("class_rule"):
        before = np.asarray(names, dtype=object)
        names = v6.lumpi_class_rule(boxes, names)
        for k in [k for k in st if k.startswith("n_") and k not in ("n_boxes", "n_dropped_empty", "n_walkers")]:
            del st[k]
        for c in set(names):
            st[f"n_{c}"] = int((names == c).sum())
        st["relabeled"] = int((before != names).sum())
    if V6.get("bowl") is not None:
        pts, boxes = V6["bowl"].apply(pts, boxes)
    write_frame(out, f"{idx:06d}", pts, boxes, names)
    return st


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="g1-v1")
    ap.add_argument("--persons", type=float, default=16.0, help="mean walkers per frame (legal M4: 17.4 in range)")
    ap.add_argument("--jitter-xy", type=float, default=0.4)
    ap.add_argument("--jitter-yaw", type=float, default=0.2)
    ap.add_argument("--van-as", default="Van", choices=["Van", "Car"])
    ap.add_argument("--walker", default="v1", choices=sorted(WALKERS), help="walker preset (see WALKERS)")
    ap.add_argument("--walker-style", default=None, help="JSON overrides of pedsim.human keywords")
    ap.add_argument("--insert-params", default=None, help="JSON overrides of pedsim.InsertParams")
    ap.add_argument("--body-yaw-sigma", type=float, default=None)
    ap.add_argument("--scale-fix", type=float, default=T["ut"]["actor_scale_fix"])
    ap.add_argument("--n-points", type=int, default=T.n_points)
    ap.add_argument("--min-points", type=int, default=1)
    ap.add_argument("--frames", type=int, default=T["ut"]["n_frames"])
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--density-prior", default=None, help="bdc26.density prior relative to $BDC_DATA/<track> (calibrated background)")
    ap.add_argument("--val-from", type=int, default=9000)
    ap.add_argument("--workers", type=int, default=48)
    ap.add_argument("--seed", type=int, default=1234, help="generator seed (UTConvertParams.seed); S7.4/S7.5 draws use other seeds")
    ap.add_argument("--g2", action="store_true", help="engine G2-lite pass (R3): re-cast actors, riders, clutter")
    ap.add_argument("--clutter", type=float, default=30.0, help="G2: mean unlabeled static objects per frame")
    ap.add_argument("--truck-size", default="real", choices=["real", "stretch"],
                    help="G2: Trucks take real label sizes (real), or half of them are lengthened to a real length (stretch: "
                         "only 8%% grow, since a real sample must be longer and the space free)")
    ap.add_argument("--g2-drop", default=None, help='G2: JSON overrides of DROP, e.g. {"Car": 0.2}')
    ap.add_argument("--placement", default="prior", choices=["prior", "map"], help="S9: walker placement source")
    ap.add_argument("--clutter-anchors", default="prior", choices=["prior", "map"], help="S9: G2 clutter anchor source")
    ap.add_argument("--size-source", default="rows", choices=["rows", "quantiles"], help="S9: G2 real-size source")
    ap.add_argument("--class-rule", default="none", choices=["none", "size"], help="S9: LUMPI vehicle convention by size")
    ap.add_argument("--structure", type=float, default=0.0, help="S9: mean map-placed structures per frame (G2)")
    ap.add_argument("--static-anchors", default=None, help="S10 R1 (allowed by the organizers' answer to question (c), 2026-11-10; "
                    "the clean check fails such a corpus unless BDC_ALLOW_R1=1): static-block anchors JSON (s10_static_anchors.py)")
    ap.add_argument("--ground-bowl", default=None, help="S9: ground surface JSON relative to $BDC_DATA/<track>")
    ap.add_argument("--map-weights", default=None, help='S9: JSON walker area shares, e.g. {"curb": 0.3, "open": 0.3, "road": 0.05, "beyond": 0.35}')
    a = ap.parse_args()
    v6opt = {"placement": a.placement, "map_weights": a.map_weights, "clutter_anchors": a.clutter_anchors, "size_source": a.size_source,
             "class_rule": a.class_rule, "structure": a.structure, "ground_bowl": a.ground_bowl,
             "static_anchors": a.static_anchors}
    build_prior()
    cmap = dict(T["ut"]["class_map"], Van=a.van_as)
    out = T.pcdet / a.name
    params = UTConvertParams(n_points=a.n_points, scale_fix=a.scale_fix, min_points=a.min_points, class_map=cmap,
                             density_prior=str(T.root / a.density_prior) if a.density_prior else None, seed=a.seed)
    frames = list(range(0, T["ut"]["n_frames"], a.stride))[: a.frames]
    if a.g2:
        build_hull_bank(params, a.val_from)
    with Pool(a.workers, initializer=init, initargs=(a.persons, a.jitter_xy, a.jitter_yaw, a.walker, a.walker_style,
                                                     a.insert_params, a.body_yaw_sigma, a.g2, a.clutter, a.truck_size,
                                                     a.g2_drop, v6opt)) as pool:
        stats = pool.map(work, [(i, out, params) for i in frames], chunksize=4)
    ids = [f"{i:06d}" for i in frames]
    write_splits(out, {"train": [i for i in ids if int(i) < a.val_from], "val": [i for i in ids if int(i) >= a.val_from]})
    counts = {}
    for s in stats:
        for k, v in s.items():
            if k.startswith("n_") and k not in ("n_boxes", "n_dropped_empty", "n_walkers"):
                counts[k[2:]] = counts.get(k[2:], 0) + v
    write_card(out, {"track": T.name, "source": "UT-LUMPI (doi:10.7910/DVN/D9SSWD, CC0) + G1 procedural walkers",
                     "engine": "G1 (UT + ray-cast walkers, Measurement4 rig from meta.json)" + (" + G2-lite (actors re-cast at real size, riders, static clutter)" if a.g2 else ""),
                     "params": {**{k: v for k, v in vars(params).items() if k != "class_map"}, "persons": a.persons,
                                "jitter_xy": a.jitter_xy, "jitter_yaw": a.jitter_yaw, "walker": a.walker,
                                "walker_style": a.walker_style, "insert_params": a.insert_params,
                                "body_yaw_sigma": a.body_yaw_sigma, "g2": a.g2, "clutter": a.clutter if a.g2 else 0.0,
                                "truck_size": a.truck_size if a.g2 else None,
                                "g2_drop": g2_drop_table(a.g2_drop) if a.g2 else None, "v6": v6opt},
                     "class_map": cmap, "person_prior": str(PRIOR.relative_to(T.root)),
                     "real_data_use": "Measurement4 sensor metadata" + ("; S10 R1 static-block anchors from unlabelled legal real frames (allowed: organizers' answer to question (c), 2026-11-10)" if a.static_anchors else "")
                                      + ("; walker box mixture and range histogram as scalars (gen/walker_scalars_v6.json); placement on the twin's own scene map"
                                         if a.placement == "map" else "; legal M4 Person label rows (placement, box sizes)")
                                      + ("; clutter anchors at map curbside cells" if a.g2 and a.clutter_anchors == "map" else
                                         ("; legal M4 Person positions as clutter anchors" if a.g2 else ""))
                                      + (("; 19 size quantiles per dimension of legal realval Bus, Truck, Bicycle, Motorcycle labels (gen/size_scalars_v6.json)"
                                          if a.size_source == "quantiles" else
                                          "; legal realval label sizes of Bus, Truck, Bicycle, Motorcycle (gen/size_prior_g2.npz)") if a.g2 else "")
                                      + ("; vehicle class convention as four size thresholds from legal realval-A labels" if a.class_rule == "size" else "")
                                      + (f"; ground surface (5 constants) fitted on legal unlabeled realval-A frames disjoint from the realism proxies ({a.ground_bowl})" if a.ground_bowl else "")
                                      + ("; background density prior from legal unlabeled realval-A frames disjoint from the "
                                         "realism proxies (docs/decisions/2026-09-30-s1-g1-generator.md)" if a.density_prior else ""),
                     "g2_stats": {k: float(np.mean([s.get(k, 0) for s in stats])) for k in ("g2_recast", "g2_riders", "g2_resized", "g2_grown", "g2_completed", "g2_clutter", "g2_structures", "g2_hits_median", "g2_occluded_removed")} if a.g2 else None,
                     "relabeled_per_frame": float(np.mean([s.get("relabeled", 0) for s in stats])),
                     "mean_boxes_per_frame": sum(s["n_boxes"] for s in stats) / max(len(stats), 1),
                     "mean_walkers_per_frame": sum(s.get("n_walkers", 0) for s in stats) / max(len(stats), 1),
                     "walker_hits_median_raw": float(np.median([s.get("walker_hits_median", 0) for s in stats])),
                     "dropped_empty_boxes": sum(s["n_dropped_empty"] for s in stats), "boxes_per_class_out": counts})
    print(f"wrote {len(ids)} frames to {out}")
    print(json.dumps(counts))
