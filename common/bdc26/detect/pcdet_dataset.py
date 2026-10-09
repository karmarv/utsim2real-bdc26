"""OpenPCDet glue: a CustomDataset subclass for canonical frames, registered without editing OpenPCDet.

Differences from `pcdet.datasets.custom.CustomDataset`:
  - get_lidar: float32 xyz, (0,0,0) null returns stripped (they are Ouster no-returns at the sensor origin);
  - get_label: tolerant parser for "x y z dx dy dz heading Class" lines (empty files allowed);
  - evaluation: the challenge-style evaluator (bdc26.evalap) instead of the KITTI path, which ignores Van
    when scoring Car, uses 0.25 IoU for small classes, has only 6 class slots and needs a GPU.
Use `register()` before OpenPCDet builds its dataloader (common/tools/pcdet_train.py does this) and set
`DATASET: 'BDCDataset'` in the dataset YAML.
"""
from __future__ import annotations

import numpy as np

from pathlib import Path

try:
    import pcdet.datasets.custom.custom_dataset as _cd
    from pcdet.datasets.custom.custom_dataset import CustomDataset
except ImportError as e:  # pragma: no cover - only importable inside the bdc-train env
    raise ImportError("bdc26.detect.pcdet_dataset needs OpenPCDet (common/env/setup_bdc_train.sh)") from e

_cd.Path = Path   # OpenPCDet bug: custom_dataset.py imports Path only under __main__ (breaks create_groundtruth_database)

from ..evalap import evaluate
from ..frames import strip_nulls


class BDCDataset(CustomDataset):
    def get_lidar(self, idx):
        pts = np.load(self.root_path / "points" / f"{idx}.npy").astype(np.float32, copy=False)
        return np.ascontiguousarray(strip_nulls(pts)[:, : len(self.point_feature_encoder.src_feature_list)])

    def get_label(self, idx):
        path = self.root_path / "labels" / f"{idx}.txt"
        rows = [l.split() for l in path.read_text().splitlines() if l.strip()]
        if not rows:
            return np.zeros((0, 7), dtype=np.float32), np.array([], dtype=str)
        boxes = np.array([[float(v) for v in r[:7]] for r in rows], dtype=np.float32)
        return boxes, np.array([r[7] for r in rows])

    def evaluation(self, det_annos, class_names, **kwargs):
        if not self.custom_infos or "annos" not in self.custom_infos[0]:
            return "no ground truth", {}
        preds, gts = {}, {}
        for info, det in zip(self.custom_infos, det_annos):
            fid = info["point_cloud"]["lidar_idx"]
            gts[fid] = (info["annos"]["gt_boxes_lidar"], info["annos"]["name"])
            preds[fid] = [{"box": b.tolist(), "score": float(s), "class": str(n)}
                          for b, s, n in zip(det["boxes_lidar"], det["score"], det["name"])]
        res = evaluate(preds, gts, list(class_names))
        lines = [f"mAP_3d_0.5_R40 {res['mAP_3d_0.5_R40']:.4f}  mAP_bev_0.5_R40 {res['mAP_bev_0.5_R40']:.4f}"]
        flat = {"mAP_3d_0.5_R40": res["mAP_3d_0.5_R40"], "mAP_bev_0.5_R40": res["mAP_bev_0.5_R40"]}
        for c, v in res["per_class"].items():
            ap = v["3d@0.5"]
            lines.append(f"  {c:12s} " + ("n/a (no GT)" if ap is None else f"AP3D@0.5 {ap['AP_R40']:.4f}  n_gt {ap['n_gt']}"))
            if ap is not None:
                flat[f"{c}_3d_0.5_R40"] = ap["AP_R40"]
        return "\n".join(lines), flat


def register() -> None:
    """Register BDCDataset with OpenPCDet and apply the runtime fixes of bdc26.detect.pcdet_patches."""
    import pcdet.datasets as D
    D.__all__["BDCDataset"] = BDCDataset
    from . import pcdet_patches
    pcdet_patches.apply()
