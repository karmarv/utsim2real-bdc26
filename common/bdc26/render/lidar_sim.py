"""Minimal spinning-LiDAR simulator on Open3D RaycastingScene (Embree, CPU).

Features: arbitrary per-beam elevation table, per-beam azimuth offsets, sensor pose
(4x4 world_T_sensor), max/min range, Gaussian range noise, per-ray drop probability
(constant or a callable of range/incidence), and returns hit points + geometry
(instance) ids + triangle ids + incidence cosine. Static scene and dynamic actors are
kept in separate RaycastingScenes so the big static BVH is built once; per frame only
the small actor BVH is rebuilt, and the nearer hit wins.
"""
import numpy as np
import open3d as o3d

INVALID = o3d.t.geometry.RaycastingScene.INVALID_ID


def make_ray_dirs(elev_deg, n_az, az_offset_deg=None, az_fov=(0.0, 360.0)):
    """Unit ray directions in the SENSOR frame, shape (n_beams*n_az, 3), beam-major.

    elev_deg      : (B,) arbitrary per-beam elevation angles (non-uniform allowed)
    n_az          : columns per revolution (e.g. 512/1024/2048 for Ouster)
    az_offset_deg : (B,) per-beam azimuth offsets (Ouster beam_azimuth_angles,
                    Velodyne rotCorrection); None -> zeros
    """
    elev = np.deg2rad(np.asarray(elev_deg, np.float64))[:, None]           # (B,1)
    az0 = np.deg2rad(np.linspace(az_fov[0], az_fov[1], n_az, endpoint=False))[None, :]
    off = np.zeros_like(elev) if az_offset_deg is None else np.deg2rad(np.asarray(az_offset_deg))[:, None]
    az = az0 + off                                                          # (B,A)
    ce = np.cos(elev)
    d = np.stack([ce * np.cos(az), ce * np.sin(az), np.broadcast_to(np.sin(elev), az.shape)], -1)
    return d.reshape(-1, 3).astype(np.float32)


class LidarSim:
    def __init__(self, static_meshes, nthreads=0):
        """static_meshes: list of (V (n,3) float32, F (m,3) uint32) in WORLD frame."""
        self.nthreads = nthreads
        self.static = o3d.t.geometry.RaycastingScene(nthreads=nthreads)
        self.static_ids = [self.static.add_triangles(o3d.core.Tensor(V.astype(np.float32)),
                                                     o3d.core.Tensor(F.astype(np.uint32)))
                           for V, F in static_meshes]

    @staticmethod
    def build_actor_scene(actors, nthreads=0):
        """actors: list of (V_world, F). Returns (scene, geometry_id -> actor_index)."""
        sc = o3d.t.geometry.RaycastingScene(nthreads=nthreads)
        gid2idx = {}
        for i, (V, F) in enumerate(actors):
            g = sc.add_triangles(o3d.core.Tensor(V.astype(np.float32)), o3d.core.Tensor(F.astype(np.uint32)))
            gid2idx[g] = i
        return sc, gid2idx

    def scan(self, dirs_sensor, world_T_sensor, actor_scene=None, max_range=120.0, min_range=0.5,
             range_noise_std=0.01, drop_prob=0.0, rng=None):
        """Returns dict: xyz_sensor (N,3), xyz_world, range, is_actor, geom_id, prim_id, cos_inc."""
        rng = np.random.default_rng() if rng is None else rng
        R, t = world_T_sensor[:3, :3], world_T_sensor[:3, 3]
        d_w = (dirs_sensor @ R.T).astype(np.float32)
        rays = np.concatenate([np.broadcast_to(t.astype(np.float32), d_w.shape), d_w], 1)
        rt = o3d.core.Tensor(rays)
        rs = self.static.cast_rays(rt, nthreads=self.nthreads)
        t_s = rs['t_hit'].numpy()
        gid = rs['geometry_ids'].numpy().astype(np.int64)
        pid = rs['primitive_ids'].numpy().astype(np.int64)
        nrm = rs['primitive_normals'].numpy()
        is_actor = np.zeros(len(t_s), bool)
        if actor_scene is not None:
            ra = actor_scene.cast_rays(rt, nthreads=self.nthreads)
            t_a = ra['t_hit'].numpy()
            closer = t_a < t_s
            t_s = np.where(closer, t_a, t_s)
            gid = np.where(closer, ra['geometry_ids'].numpy().astype(np.int64), gid)
            pid = np.where(closer, ra['primitive_ids'].numpy().astype(np.int64), pid)
            nrm = np.where(closer[:, None], ra['primitive_normals'].numpy(), nrm)
            is_actor = closer
        valid = np.isfinite(t_s) & (t_s <= max_range) & (t_s >= min_range)
        cos_inc = np.abs(np.einsum('ij,ij->i', nrm, d_w))                   # |n.d| (d is unit)
        # per-ray drop: constant, or callable(range, cos_inc) -> prob
        p = drop_prob(t_s, cos_inc) if callable(drop_prob) else drop_prob
        valid &= rng.random(len(t_s)) >= p
        r = t_s[valid] + rng.normal(0.0, range_noise_std, valid.sum()).astype(np.float32)
        xyz_s = dirs_sensor[valid] * r[:, None]
        return dict(xyz_sensor=xyz_s.astype(np.float32), xyz_world=(xyz_s @ R.T + t).astype(np.float32),
                    range=r, is_actor=is_actor[valid], geom_id=gid[valid], prim_id=pid[valid],
                    cos_inc=cos_inc[valid])


# Example beam tables -----------------------------------------------------------
def uniform_table(n, up, lo):
    return np.linspace(up, lo, n)


def os1_128_like():
    # Placeholder: real Ouster tables come from the sensor's metadata JSON
    # (beam_altitude_angles, beam_azimuth_angles). Use those for the real twin.
    elev = np.linspace(22.5, -22.5, 128)
    az_off = np.tile([4.2, 1.4, -1.4, -4.2], 32)   # staggered like OS1 (illustrative only)
    return elev, az_off
