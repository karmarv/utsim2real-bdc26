"""GBlobs voxel encoders (strategy S5, docs/02-STRATEGY.md Section 8.5).

GBlobs (Malic et al., CVPR 2025, R27) feeds a detector the local shape of the point cloud instead of absolute point
coordinates: per voxel, the offset of the points' mean from the voxel centre (3 values) and the 3 x 3 sample
covariance of the points (9 values), 12 values in place of MeanVFE's mean xyz. The network then cannot shortcut
through absolute position, and position reaches it only through the sparse grid itself.

- GBlobsVFE: the published form, ported from the authors' OpenPCDet code (github.com/malicd/GBlobs,
  pcdet/models/backbones_3d/vfe/gblobs_vfe.py, BSD-3; notice below): the covariance of the voxel's own points.
- GBlobsCellVFE (bdc26 adaptation): the covariance over the aligned cell of CELL_FACTOR voxels that contains the
  voxel. On our frames at the 0.1 x 0.1 x 0.25 m grid, 80-83% of the voxels hold one point and 13-15% two (S5
  review), so the voxel covariance is undefined for about 95% of them, the paper's own failure case on nuScenes;
  cells of 4 x 4 x 2 voxels (0.4 x 0.4 x 0.5 m) put 65-74% of the points in cells with at least 3 points. The fine
  offset stays per voxel. Points are centred on their cell before the sums, so float32 keeps the precision a raw
  E[pp^T] - mu mu^T at 40 m would lose.

Both use xyz only (the first 3 point features) and output 12 values. Registered into OpenPCDet's VFE registry by
bdc26.detect.pcdet_dataset.register(), so third_party/OpenPCDet stays unmodified.

BSD 3-Clause License, Copyright (c) 2025, Dusan Malic (for the GBlobsVFE computation ported here):
Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
following conditions are met: 1. Redistributions of source code must retain the above copyright notice, this list of
conditions and the following disclaimer. 2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation and/or other materials provided with the
distribution. 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or
promote products derived from this software without specific prior written permission. THIS SOFTWARE IS PROVIDED BY
THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
from __future__ import annotations

import torch
import torch.nn as nn


def _valid_mask(voxels: torch.Tensor, num_points: torch.Tensor) -> torch.Tensor:
    """(V, P, 1) float mask of the filled point slots (by count: a real point at the origin is not padding)."""
    P = voxels.shape[1]
    return (torch.arange(P, device=voxels.device)[None, :] < num_points[:, None]).unsqueeze(-1).to(voxels.dtype)


def voxel_centres(coords: torch.Tensor, voxel_size, pc_range) -> torch.Tensor:
    """(V, 4) [b, z, y, x] voxel indices -> (V, 3) xyz centres (as OpenPCDet's get_voxel_centers)."""
    vs = torch.as_tensor(voxel_size, dtype=torch.float32, device=coords.device)
    lo = torch.as_tensor(pc_range[0:3], dtype=torch.float32, device=coords.device)
    return (coords[:, [3, 2, 1]].float() + 0.5) * vs + lo


def gblobs_voxel(voxels, num_points, coords, voxel_size, pc_range, relative=True) -> torch.Tensor:
    """Published GBlobs: [mean - voxel centre (or mean), voxel sample covariance (9)] per voxel."""
    m = _valid_mask(voxels, num_points)
    xyz = voxels[..., :3]
    n = num_points.clamp(min=1).to(voxels.dtype)[:, None]
    mean = (xyz * m).sum(1) / n
    d = (xyz - mean[:, None, :]) * m
    cov = torch.einsum("vpa,vpb->vab", d, d) / (n - 1.0).clamp(min=1.0)[:, :, None]
    pos = mean - voxel_centres(coords, voxel_size, pc_range) if relative else mean
    return torch.cat([pos, cov.reshape(-1, 9)], dim=1)


def gblobs_cell(voxels, num_points, coords, voxel_size, pc_range, factor=(4, 4, 2), relative=True) -> torch.Tensor:
    """bdc26 GBlobs: [mean - voxel centre, sample covariance of all points in the voxel's cell (9)] per voxel.
    factor: cell size in voxels along x, y, z (aligned to the voxel grid)."""
    m = _valid_mask(voxels, num_points)
    xyz = voxels[..., :3]
    n = num_points.clamp(min=1).to(voxels.dtype)[:, None]
    mean = (xyz * m).sum(1) / n
    pos = mean - voxel_centres(coords, voxel_size, pc_range) if relative else mean
    fx, fy, fz = (int(f) for f in factor)
    cell = torch.stack([coords[:, 0], coords[:, 1] // fz, coords[:, 2] // fy, coords[:, 3] // fx], dim=1)
    _, inv = torch.unique(cell, dim=0, return_inverse=True)
    f = torch.tensor([fx, fy, fz], dtype=torch.float32, device=voxels.device)
    vs = torch.as_tensor(voxel_size, dtype=torch.float32, device=voxels.device)
    lo = torch.as_tensor(pc_range[0:3], dtype=torch.float32, device=voxels.device)
    centre = (cell[:, [3, 2, 1]].float() * f + f / 2.0) * vs + lo                     # cell centre, per voxel
    q = (xyz - centre[:, None, :]) * m                                                  # centred on the cell
    K = int(inv.max()) + 1
    s1 = torch.zeros(K, 3, device=voxels.device, dtype=voxels.dtype).index_add_(0, inv, q.sum(1))
    s2 = torch.zeros(K, 3, 3, device=voxels.device, dtype=voxels.dtype).index_add_(0, inv, torch.einsum("vpa,vpb->vab", q, q))
    cnt = torch.zeros(K, device=voxels.device, dtype=voxels.dtype).index_add_(0, inv, num_points.to(voxels.dtype))
    mu = s1 / cnt.clamp(min=1.0)[:, None]
    cov = (s2 - cnt[:, None, None] * mu[:, :, None] * mu[:, None, :]) / (cnt - 1.0).clamp(min=1.0)[:, None, None]
    cov = torch.where(cnt[:, None, None] >= 2, cov, torch.zeros_like(cov))
    return torch.cat([pos, cov[inv].reshape(-1, 9)], dim=1)


class _GBlobsBase(nn.Module):
    def __init__(self, model_cfg, num_point_features, voxel_size=None, point_cloud_range=None, **kwargs):
        super().__init__()
        self.model_cfg = model_cfg
        self.num_point_features = num_point_features
        self.voxel_size = list(voxel_size)
        self.point_cloud_range = list(point_cloud_range)
        self.relative = bool(model_cfg.get("RELATIVE_DISTANCE", True))

    def get_output_feature_dim(self):
        return 12

    def forward(self, batch_dict, **kwargs):
        batch_dict["voxel_features"] = self.encode(batch_dict["voxels"], batch_dict["voxel_num_points"],
                                                   batch_dict["voxel_coords"]).contiguous()
        return batch_dict


class GBlobsVFE(_GBlobsBase):
    """The published GBlobs encoder (voxel-level covariance)."""

    def encode(self, voxels, num_points, coords):
        return gblobs_voxel(voxels, num_points, coords, self.voxel_size, self.point_cloud_range, self.relative)


class GBlobsCellVFE(_GBlobsBase):
    """GBlobs with the covariance over the aligned cell of CELL_FACTOR voxels (default 4 x 4 x 2)."""

    def __init__(self, model_cfg, num_point_features, **kwargs):
        super().__init__(model_cfg, num_point_features, **kwargs)
        self.factor = tuple(model_cfg.get("CELL_FACTOR", [4, 4, 2]))

    def encode(self, voxels, num_points, coords):
        return gblobs_cell(voxels, num_points, coords, self.voxel_size, self.point_cloud_range, self.factor, self.relative)


def register() -> None:
    from pcdet.models.backbones_3d import vfe
    vfe.__all__["GBlobsVFE"] = GBlobsVFE
    vfe.__all__["GBlobsCellVFE"] = GBlobsCellVFE
