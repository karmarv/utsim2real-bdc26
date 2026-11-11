#!/usr/bin/env python
"""Build the G1 training dataset for Track 2: UT-V2X-Real-IC frames + ray-cast procedural walkers (module M8, first version).

What it adds on top of prepare_ut.py (ut-v1):
  - Walking pedestrians. UT-V2X has riders only, yet "pedestrian" is 62% of the test objects. Each frame gets
    Poisson(--walkers) articulated walkers (common/bdc26/render/pedsim.py) ray-cast with an Ouster OS1-64 at the
    frame origin (the frames are in the IC sensor frame: tilted about 6 deg to the ground, 3.4 m above it):
    64 uniform beams over +/-16.6 deg (OS1-64 spec), --cols columns. Inserted ray-consistently: UT points behind a
    walker are removed (exact ray test from the origin, where the UT sensor also sits) and walker returns
    behind existing geometry are dropped (range image of the frame's points, 3x3 neighbourhood).
  - Density: real frames are resampled by the organizers from the full 64 x 1024 scan to 50k points, so real
    objects keep about 76% of their returns, while UT frames are resampled to 35k of about 69k valid points
    (51%). Walkers are therefore cast with --density-gain 1.5 more columns. Calibrate on legal real
    pedestrians once the starting kit unlocks V2X real labels (compare points-vs-range, as for LUMPI).
  - Placement: free, observed ground (local ground from the frame's points, no structure in the walker's
    column, clear of all boxes) within the range; heading uniform.
  - Annotation box: KITTI-like convention (no legal V2X statistics before the kit): l ~ N(0.80, 0.10),
    w ~ N(0.66, 0.06), h = body height + 4 cm, body height ~ N(1.72, 0.08).
Then the ut-v1 steps (classes -> super-classes, resample to --n-valid points, min points).
With --g2 (engine G2-lite, strategy R3, common/bdc26/render/g2.py): trucks are re-cast at real label sizes (synthetic
median 5.2 x 2.07 m, at most 8.47 m long; real 8.2 x 2.89 m, up to 13 m) from their own convex hull, completed by
exemplar hulls of well-sampled UT trucks when sparse, with the OS1-64, and Poisson(--clutter) unlabeled poles, trees,
bollards, bins and boxes are added (60% of them 1-4 m from real walker positions) as hard negatives for walkers. The
object sampling rate stays the G1 one (bdc26.density.resample_calibrated n_ref).

    python prepare_g1.py --name g1-v1
    python prepare_g1.py --name g1-v4 --walkers 16 --walker v2 --placement prior --fov-mask --density-gain 2.5 --g2   # needs open3d (in .venv_ut)
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
from bdc26.io import v2x  # noqa: E402
from bdc26.pcdet_export import write_card, write_frame, write_splits  # noqa: E402
from bdc26.prep import UTConvertParams, convert_ut_frame  # noqa: E402
from bdc26.render.g1 import LocalGround, WalkerInserter  # noqa: E402
from bdc26.render.pedsim import InsertParams, Sensor  # noqa: E402
from bdc26.render import scene_map as smap, v6  # noqa: E402

T = load_track("v2x-track")
PRIOR = T.gen / "walker_prior_v1.npz"
SIZE_PRIOR = T.gen / "size_prior_g2.npz"
HULL_BANK = T.gen / "hull_bank_g2.npz"
BANK_CLASSES = ("truck",)
DROP = {"clutter": 0.10}   # per-ray drop of re-cast objects (R3 calibration, docs/02-STRATEGY.md Section 8.7.1)
SIZE_FILTERS = {"truck": (5.0, 22.0)}
SCENE_MAP = T.gen / "scene_map_v1.npz"
WALKER_SCALARS = T.gen / "walker_scalars_v6.json"
SIZE_SCALARS = T.gen / "size_scalars_v6.json"
MAP_WEIGHTS = {"curb": 0.30, "open": 0.05, "road": 0.45, "beyond": 0.20}   # S9: as LUMPI (points per walker checked per track)


class MapThenLocalGround:
    """S9: the scene map's ground height where the twin has ground (the map aggregates raw UT frames, so it also
    covers the FOV-masked area near the pole), else the local estimate from the frame's points."""

    def __init__(self, scene):
        self.map, self.local = smap.MapGround(scene, default=None, max_step=1e9), LocalGround(1.5, 8)

    def __call__(self, points, x, y):
        z = self.map.at(x, y)
        return z if z is not None else self.local(points, x, y)


def map_pose(scene, weights=None):
    w = json.loads(WALKER_SCALARS.read_text())
    return smap.WalkerSampler(scene, smap.WalkerConfig(weights=weights or MAP_WEIGHTS, range_bins=tuple(w["range_bins"]),
                                                       range_share=tuple(w["range_share"]), boxes=tuple(map(tuple, w["boxes"])),
                                                       pc_range=tuple(T.pc_range), range_from=((0.0, 0.0),),
                                                       map_ground=True, max_step=1e9))


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
WALKER_TYPES = ("Pedestrian", "Child", "RoadWorker")      # riders already exist in UT-V2X


def build_prior(margin: float = 2.0) -> Path:
    """Legal V2X-Real walker rows (x, y, yaw, l, w, h) in the agent -1 sensor frame, inside the range (+margin);
    every frame through ForbiddenGuard (logged). Cached in gen/walker_prior_v1.npz."""
    if PRIOR.exists():
        return PRIOR
    g = ForbiddenGuard(T)
    if not g.resolved:
        sys.exit("kit/id_mapping.json missing: run ingest_kit.py and resolve_test_ids.py first")
    agent = T["real"]["agent"]
    ymls = sorted((p.parts[-3], int(p.stem), p) for p in (T.real / "raw").glob(f"*/*/{agent}/*.yaml"))
    allowed = set(g.filter([(sc, f) for sc, f, _ in ymls], purpose="G1 generator: walker placement and box-size prior"))
    x0, y0, _, x1, y1, _ = T.pc_range
    rows = []
    for sc, f, yml in ymls:
        if (sc, f) not in allowed:
            continue
        lab = v2x.labels_in_sensor_frame(v2x.read_yaml(yml), T)
        m = np.isin(lab.obj_types, WALKER_TYPES)
        b = lab.boxes[m]
        b = b[(b[:, 0] > x0 - margin) & (b[:, 0] < x1 + margin) & (b[:, 1] > y0 - margin) & (b[:, 1] < y1 + margin)]
        rows.append(b)
    b = np.concatenate(rows) if rows else np.zeros((0, 7))
    PRIOR.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(PRIOR, xy=b[:, :2], yaw=b[:, 6], lwh=b[:, 3:6], z=b[:, 2],
                        source="legal V2X-Real agent -1 labels, obj_type in Pedestrian/Child/RoadWorker")
    return PRIOR


class PriorPose:
    """Position, heading and l/w/h of a random legal real walker row, jittered (as data-lumpi-track/prepare_g1.py)."""

    def __init__(self, path: Path, jitter_xy: float = 0.4, jitter_yaw: float = 0.2):
        d = np.load(path)
        self.xy, self.yaw, self.lwh, self.z = d["xy"], d["yaw"], d["lwh"], d["z"]
        self.jxy, self.jyaw = jitter_xy, jitter_yaw

    def __call__(self, rng):
        """The real row's box bottom is the ground height: UT-V2X is aligned with the real sensor frame, and the
        FOV-masked UT frame has no ground near the pole to estimate it from (sloped campus: -2 to -7 m)."""
        i = rng.integers(len(self.xy))
        x, y = self.xy[i] + rng.normal(0, self.jxy, 2)
        l, w, h = self.lwh[i] * rng.uniform(0.97, 1.03, 3)
        z_ground = float(self.z[i] - self.lwh[i][2] / 2)
        return float(x), float(y), float(self.yaw[i] + rng.normal(0, self.jyaw)), (float(l), float(w), float(h)), z_ground


def body_from_box_prior(l, w, h, rng):
    """Real annotators' boxes (median 0.71 x 0.72 x 1.73 m): body top 2-14 cm below the box top."""
    return float(np.clip(h - rng.uniform(0.02, 0.14), 1.40, 1.98)), float(np.clip(w - rng.uniform(0.24, 0.34), 0.34, 0.52))


CALIB = T.gen / "os1_64_calib_v1.npz"   # measured on legal unlabeled agent -1 frames: no tilt, rows +16.13..-16.77 deg


def os1_64(cols: float, measured: bool = False) -> Sensor:
    elev = np.load(CALIB)["elev_deg"] if measured else np.linspace(-16.6, 16.6, 64)
    return Sensor(np.eye(4), elev, 360.0 / cols, min_range=0.8, max_range=120.0, name="OS1-64")


class FovThenWalkers:
    """Mask UT points to the real OS1-64 vertical field of view (UT-V2X emulates a sensor reaching -56 deg, so it
    sees ground under the pole that the real unit never returns), then insert walkers."""

    def __init__(self, inserter, elev_deg, margin: float = 0.27):
        self.ins, self.lo, self.hi = inserter, float(np.min(elev_deg)) - margin, float(np.max(elev_deg)) + margin

    def __call__(self, points, boxes, names, rng):
        p = np.asarray(points, dtype=np.float64)[:, :3]
        el = np.degrees(np.arctan2(p[:, 2], np.hypot(p[:, 0], p[:, 1])))
        fov = (el >= self.lo) & (el <= self.hi)
        out, keep_sub, b, n, st = self.ins(p[fov], boxes, names, rng)
        keep = np.zeros(len(p), dtype=bool)
        keep[np.nonzero(fov)[0][keep_sub]] = True
        st["fov_removed"] = int((~fov).sum())
        return out, keep, b, n, st


class FreeGroundPose:
    """Uniform position in the range annulus; KITTI-like box; body height drawn here and passed via the box."""

    def __init__(self, r_min: float, r_max: float):
        self.r_min, self.r_max = r_min, r_max

    def __call__(self, rng):
        r = np.sqrt(rng.uniform(self.r_min ** 2, self.r_max ** 2))
        a = rng.uniform(-np.pi, np.pi)
        H = float(np.clip(rng.normal(1.72, 0.08), 1.50, 1.95))
        lwh = (float(np.clip(rng.normal(0.80, 0.10), 0.55, 1.1)), float(np.clip(rng.normal(0.66, 0.06), 0.5, 0.85)),
               H + float(np.clip(rng.normal(0.04, 0.02), 0.0, 0.1)))
        return float(r * np.cos(a)), float(r * np.sin(a)), float(rng.uniform(-np.pi, np.pi)), lwh


def body_from_box(l, w, h, rng):
    return float(np.clip(h - 0.04, 1.45, 1.98)), float(np.clip(w - rng.uniform(0.18, 0.26), 0.36, 0.52))


# Walker presets (see data-lumpi-track/prepare_g1.py for the calibration on legal real LUMPI Persons). v2 carries
# the body-shape part of that calibration over (deeper torsos, arm swing, bags, body yaw scatter); a single OS1-64
# has no multi-lidar misregistration, so no per-sensor offsets. Re-check against legal V2X pedestrians after the kit.
WALKERS = {
    "v1": {"style": {}, "insert": {"block_nbr": [1, 1]}, "body_yaw_sigma": 0.0},
    "v2": {"style": {"depth_range": [1.25, 1.7], "arm_swing": 1.3, "backpack_prob": 0.3, "sidebag_prob": 0.25,
                     "front_item_prob": 0.1},
           "insert": {"block_nbr": [1, 1], "range_noise": 0.02}, "body_yaw_sigma": 0.8},
}

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


def make_g2(sensor, ins_params, clutter: float, truck_size: str, drop: dict, v6opt: dict | None = None):
    from bdc26.render.g2 import G2Config, G2Pass, HullBank, size_prior_from_labels
    v6opt = v6opt or {}
    if v6opt.get("size_source") == "quantiles":
        sizes = {"truck": v6.QuantileSizes(json.loads(SIZE_SCALARS.read_text())["truck"]).sample(20000, np.random.default_rng(4321))}
    else:
        sizes = size_prior_from_labels(T.pcdet / "realval-v1", ["val", "valB"], SIZE_FILTERS, cache=SIZE_PRIOR)
    scene = smap.SceneMap.load(SCENE_MAP) if (v6opt.get("clutter_anchors") == "map" or v6opt.get("structure", 0) > 0) else None
    anchors = smap.anchor_points(scene, pc_range=tuple(T.pc_range)) if v6opt.get("clutter_anchors") == "map" else np.load(PRIOR)["xy"]
    sxy, sdir = structure_table(scene) if v6opt.get("structure", 0) > 0 else (None, None)
    cfg = G2Config(recast={"truck": "box"}, resize={"truck": sizes["truck"]} if truck_size == "real" else {},
                   stretch={"truck": {"prob": 0.5, "lengths": sizes["truck"][:, 0]}} if truck_size == "stretch" else {},
                   clutter_mean=clutter, clutter_anchor_xy=anchors, drop=drop, params=ins_params,
                   bank=HullBank.load(HULL_BANK) if HULL_BANK.exists() else None,
                   structure_mean=float(v6opt.get("structure", 0.0)), structure_xy=sxy, structure_dir=sdir,
                   static_anchors=load_static_anchors(v6opt.get("static_anchors")))
    ground = MapThenLocalGround(scene) if scene is not None else LocalGround(1.5, 8)
    return G2Pass([sensor], cfg, ground=ground, pc_range=T.pc_range)


def init(walkers, cols, gain, walker="v1", placement="free", fov=False, g2=False, clutter=30.0, truck_size="real",
         g2_drop=None, v6opt=None):
    global _INS, _G2
    v6opt = v6opt or {}
    w = WALKERS[walker]
    if placement == "map":
        pose = map_pose(smap.SceneMap.load(SCENE_MAP), json.loads(v6opt["map_weights"]) if v6opt.get("map_weights") else None)
        body, ground = body_from_box_prior, LocalGround(1.5, 8)
    elif placement == "prior":
        pose, body, ground = PriorPose(PRIOR), body_from_box_prior, LocalGround(1.5, 8)
    else:
        pose, body, ground = FreeGroundPose(2.0, 40.0), body_from_box, LocalGround(1.5, 8)
    sensor = os1_64(cols * gain, measured=fov)
    _INS = WalkerInserter([sensor], pose, n_mean=walkers, ground=ground,
                          pc_range=T.pc_range, class_name="pedestrian", body_from_box=body,
                          params=InsertParams(**{k: tuple(v) if isinstance(v, list) else v for k, v in w["insert"].items()}),
                          min_dist_xy=2.0 if placement == "free" else 0.8, walker_style=w["style"],
                          body_yaw_sigma=w["body_yaw_sigma"])
    if fov:
        _INS = FovThenWalkers(_INS, sensor.elev_deg)
    if g2:
        ins = {k: tuple(v) if isinstance(v, list) else v for k, v in w["insert"].items()}
        _G2 = make_g2(sensor, InsertParams(**ins), clutter, truck_size, g2_drop_table(g2_drop), v6opt)


def work(args):
    idx, out, params = args
    pts, boxes, names, st = convert_ut_frame(T, idx, params, inserter=_INS, post_inserter=_G2)
    write_frame(out, f"{idx:06d}", pts, boxes, names)
    return st


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="g1-v1")
    ap.add_argument("--walkers", type=float, default=12.0)
    ap.add_argument("--walker", default="v1", choices=sorted(WALKERS), help="walker preset (see WALKERS)")
    ap.add_argument("--fov-mask", action="store_true",
                    help="mask UT points to the measured OS1-64 field of view and cast walkers with its beam table (g1-v3)")
    ap.add_argument("--placement", default="free", choices=["free", "prior", "map"],
                    help="free: uniform free ground, KITTI-like boxes (g1-v1/v2); prior: legal real walker rows (g1-v3); "
                         "map: the twin's own scene map with scalar box and range statistics (S9, gen/walker_scalars_v6.json)")
    ap.add_argument("--clutter-anchors", default="prior", choices=["prior", "map"], help="S9: G2 clutter anchor source")
    ap.add_argument("--size-source", default="rows", choices=["rows", "quantiles"], help="S9: G2 truck size source")
    ap.add_argument("--structure", type=float, default=0.0, help="S9: mean map-placed structures per frame (G2)")
    ap.add_argument("--static-anchors", default=None, help="S10 R1 (allowed by the organizers' answer to question (c), 2026-11-10; "
                    "the clean check fails such a corpus unless BDC_ALLOW_R1=1): static-block anchors JSON (s10_static_anchors.py)")
    ap.add_argument("--map-weights", default=None, help="S9: JSON walker area shares (scene_map.WalkerConfig.weights)")
    ap.add_argument("--cols", type=int, default=T["real"]["sensor"]["cols"])
    ap.add_argument("--density-gain", type=float, default=1.5)
    ap.add_argument("--n-valid", type=int, default=T["resample"]["n_valid_points"])
    ap.add_argument("--min-points", type=int, default=1)
    ap.add_argument("--frames", type=int, default=T["ut"]["n_frames"])
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--density-prior", default=None, help="bdc26.density prior relative to $BDC_DATA/<track> (calibrated background)")
    ap.add_argument("--val-from", type=int, default=9000)
    ap.add_argument("--workers", type=int, default=48)
    ap.add_argument("--seed", type=int, default=1234, help="generator seed (UTConvertParams.seed); S7.4/S7.5 draws use other seeds")
    ap.add_argument("--g2", action="store_true", help="engine G2-lite pass (R3): re-cast and lengthen trucks, clutter")
    ap.add_argument("--clutter", type=float, default=30.0, help="G2: mean unlabeled static objects per frame")
    ap.add_argument("--truck-size", default="real", choices=["real", "stretch"],
                    help="G2: trucks take real label sizes (real: also the real width, 2.89 vs 2.07 m), or half of them are "
                         "lengthened to a real length (stretch)")
    ap.add_argument("--g2-drop", default=None, help='G2: JSON overrides of DROP, e.g. {"Car": 0.2}')
    a = ap.parse_args()
    v6opt = {"placement": a.placement, "map_weights": a.map_weights, "clutter_anchors": a.clutter_anchors,
             "size_source": a.size_source, "structure": a.structure, "static_anchors": a.static_anchors}
    out = T.pcdet / a.name
    if a.placement == "prior":
        build_prior()
    params = UTConvertParams(n_points=a.n_valid, scale_fix=T["ut"]["actor_scale_fix"], min_points=a.min_points,
                             density_prior=str(T.root / a.density_prior) if a.density_prior else None, seed=a.seed)
    frames = list(range(0, T["ut"]["n_frames"], a.stride))[: a.frames]
    if a.g2:
        build_hull_bank(params, a.val_from)
    with Pool(a.workers, initializer=init, initargs=(a.walkers, a.cols, a.density_gain, a.walker, a.placement, a.fov_mask,
                                                     a.g2, a.clutter, a.truck_size, a.g2_drop, v6opt)) as pool:
        stats = pool.map(work, [(i, out, params) for i in frames], chunksize=4)
    ids = [f"{i:06d}" for i in frames]
    write_splits(out, {"train": [i for i in ids if int(i) < a.val_from], "val": [i for i in ids if int(i) >= a.val_from]})
    counts = {}
    for s in stats:
        for k, v in s.items():
            if k.startswith("n_") and k not in ("n_boxes", "n_dropped_empty", "n_walkers"):
                counts[k[2:]] = counts.get(k[2:], 0) + v
    write_card(out, {"track": T.name, "source": "UT-V2X-Real-IC (doi:10.7910/DVN/N6N4UR, CC0) + G1 procedural walkers",
                     "engine": "G1 (UT + ray-cast walkers, OS1-64 spec at the frame origin)" + (" + G2-lite (trucks re-cast and lengthened, static clutter)" if a.g2 else ""),
                     "params": {**{k: v for k, v in vars(params).items() if k != "class_map"}, "walkers": a.walkers,
                                "cols": a.cols, "density_gain": a.density_gain, "walker": a.walker, "placement": a.placement,
                                "fov_mask": a.fov_mask, "g2": a.g2, "clutter": a.clutter if a.g2 else 0.0,
                                "truck_size": a.truck_size if a.g2 else None,
                                "g2_drop": g2_drop_table(a.g2_drop) if a.g2 else None, "v6": v6opt},
                     "class_map": T["ut"]["class_map"],
                     "real_data_use": "; ".join(u for u in (     # every real-derived generator input (FAQ review 2026-10-27)
                         "legal V2X-Real walker label rows (placement, box sizes; gen/walker_prior_v1.npz)" if a.placement == "prior" else "",
                         "walker box mixture and range histogram as scalars (gen/walker_scalars_v6.json); placement on the twin's own scene map" if a.placement == "map" else "",
                         ("legal V2X-Real walker positions as clutter anchors" if a.clutter_anchors == "prior" else "clutter anchors at map curbside cells") if a.g2 else "",
                         "OS1-64 beam table measured on legal unlabeled frames (gen/os1_64_calib_v1.npz)" if a.fov_mask else "",
                         "S10 R1 static-block anchors from unlabelled legal real frames (allowed: organizers' answer to question (c), 2026-11-10)" if a.static_anchors else "",
                         ("19 size quantiles per dimension of legal realval truck labels (gen/size_scalars_v6.json)" if a.size_source == "quantiles"
                          else "legal realval truck label sizes (gen/size_prior_g2.npz)") if a.g2 and a.truck_size == "real" else "",
                         "background density prior from legal unlabeled realval-A frames disjoint from the realism proxies"
                         f" ({Path(a.density_prior).name})" if a.density_prior else "") if u)
                         or "none (sensor spec and KITTI-like box convention)",
                     "g2_stats": {k: float(np.mean([s.get(k, 0) for s in stats])) for k in ("g2_recast", "g2_resized", "g2_grown", "g2_completed", "g2_clutter", "g2_structures", "g2_hits_median", "g2_occluded_removed")} if a.g2 else None,
                     "mean_boxes_per_frame": sum(s["n_boxes"] for s in stats) / max(len(stats), 1),
                     "mean_walkers_per_frame": sum(s.get("n_walkers", 0) for s in stats) / max(len(stats), 1),
                     "walker_hits_median_raw": float(np.median([s.get("walker_hits_median", 0) for s in stats])),
                     "dropped_empty_boxes": sum(s["n_dropped_empty"] for s in stats), "boxes_per_class_out": counts})
    print(f"wrote {len(ids)} frames to {out}")
    print(json.dumps(counts))
