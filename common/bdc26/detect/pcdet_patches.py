"""Runtime fixes for OpenPCDet (233f849), applied by bdc26.detect.pcdet_dataset.register() so third_party stays unmodified.

CenterHead.assign_targets label corruption (found 2026-10-09 while training the S2 CenterPoint members):
inside the loop over head groups, `temp_box = cur_gt_boxes[idx]` is a view of the caller's gt_boxes, and
`temp_box[-1] = cur_class_names.index(name) + 1` overwrites the class label in place with the head-local index.
Later head groups therefore see relabeled boxes. With head groups in CLASS_NAMES order this is harmless (a
relabeled box can only fall into an earlier head), which is why OpenPCDet's own configs are unaffected; with any
other grouping, a class trains a later head. Example (V2X, CLASS_NAMES [vehicle, pedestrian, truck], heads
[[pedestrian], [vehicle], [truck]]): every pedestrian becomes label 1 = vehicle after the first head, so the
vehicle head learned pedestrians (realval: about 96 pedestrian-sized "vehicle" boxes per frame at score >= 0.5).
The fix runs the original method once per head group on a fresh copy of gt_boxes; outputs are identical to the
original wherever the original was correct.

Two-stage score blend (added 2026-10-10 for the S4 Voxel R-CNN members, docs/02-STRATEGY.md Section 8.4): at test
time VoxelRCNNHead (and PVRCNNHead) replaces the stage-1 heat-map score of each proposal with its stage-2 IoU-quality score alone. With
ROI_HEAD.SCORE_BLEND_ALPHA = a set, the final score becomes stage1^a x stage2^(1-a) (a = 0: mainline; a = 0.5: the
geometric mean of CenterPoint's two-stage variant; a list sets one a per class in CLASS_NAMES order); padded proposals (stage-1 score 0) get score 0 instead of an IoU
prediction for an empty box. Training is unchanged.
"""
from __future__ import annotations

_APPLIED = False


def blend_scores(roi_scores, rcnn_logits, alpha, roi_labels=None):
    """(B, N) stage-1 scores and (B, N, 1) stage-2 logits -> (B, N, 1) probabilities stage1^a x stage2^(1-a).
    alpha: one value, or one per class in CLASS_NAMES order (indexed by the 1-based stage-1 roi_labels): the IoU
    head is class-agnostic and trained mostly on the frequent classes, so the best blend differs per class."""
    import torch
    p2 = torch.sigmoid(rcnn_logits.reshape(roi_scores.shape))
    p1 = roi_scores.clamp(min=0.0)
    if isinstance(alpha, (list, tuple)):
        table = torch.tensor([float(x) for x in alpha], dtype=p2.dtype, device=p2.device)
        a = table[(roi_labels.long() - 1).clamp(min=0, max=len(alpha) - 1)]
    else:
        a = torch.full_like(p2, float(alpha))
    p = torch.exp(a * torch.log(p1.clamp(min=1e-12)) + (1.0 - a) * torch.log(p2.clamp(min=1e-12)))
    return torch.where(roi_scores > 0, p, torch.zeros_like(p)).unsqueeze(-1)


def _patch_two_stage_scores() -> None:
    from pcdet.models.roi_heads.pvrcnn_head import PVRCNNHead
    from pcdet.models.roi_heads.voxelrcnn_head import VoxelRCNNHead

    for head in (VoxelRCNNHead, PVRCNNHead):
        original = head.forward

        def forward(self, batch_dict, _original=original):
            out = _original(self, batch_dict)
            alpha = self.model_cfg.get("SCORE_BLEND_ALPHA", None)
            if not self.training and alpha is not None and not batch_dict.get("cls_preds_normalized", False):
                alpha = list(alpha) if isinstance(alpha, (list, tuple)) else float(alpha)
                batch_dict["batch_cls_preds"] = blend_scores(batch_dict["roi_scores"], batch_dict["batch_cls_preds"], alpha,
                                                             batch_dict.get("roi_labels"))
                batch_dict["cls_preds_normalized"] = True
            return out

        forward.__doc__ = "bdc26 score blend: " + (original.__doc__ or "")
        head.forward = forward


class _TorchScatter:
    """S9 DSVT arm: the two torch_scatter calls of OpenPCDet's dynamic VFEs (scatter_mean and scatter_max(...)[0], index
    along dim 0) in plain torch 2.1 (Tensor.scatter_reduce), so DSVT needs no extra package (one pinned environment)."""

    @staticmethod
    def _reduce(src, index, reduce, dim=0):
        import torch
        assert dim == 0
        n = int(index.max()) + 1 if index.numel() else 0
        out = torch.zeros((n,) + tuple(src.shape[1:]), dtype=src.dtype, device=src.device)
        idx = index.long().view(-1, *([1] * (src.dim() - 1))).expand_as(src)
        return out.scatter_reduce(0, idx, src, reduce=reduce, include_self=False)

    @classmethod
    def scatter_mean(cls, src, index, dim=0):
        return cls._reduce(src, index, "mean", dim)

    @classmethod
    def scatter_max(cls, src, index, dim=0):
        return cls._reduce(src, index, "amax", dim), None     # callers read [0] only


def _patch_torch_scatter() -> None:
    import importlib
    for name in ("dynamic_voxel_vfe", "dynamic_pillar_vfe", "dynamic_mean_vfe"):
        mod = importlib.import_module(f"pcdet.models.backbones_3d.vfe.{name}")
        if not hasattr(mod, "torch_scatter"):
            mod.torch_scatter = _TorchScatter


def apply() -> None:
    global _APPLIED
    if _APPLIED:
        return
    _patch_two_stage_scores()
    _patch_torch_scatter()
    from pcdet.models.dense_heads.center_head import CenterHead

    original = CenterHead.assign_targets

    def assign_targets(self, gt_boxes, feature_map_size=None, **kwargs):
        heads = self.class_names_each_head
        out = None
        try:
            for cur in heads:
                self.class_names_each_head = [cur]
                r = original(self, gt_boxes.clone(), feature_map_size=feature_map_size, **kwargs)
                if out is None:
                    out = {k: list(v) for k, v in r.items()}
                else:
                    for k, v in r.items():
                        out[k].extend(v)
        finally:
            self.class_names_each_head = heads
        return out

    assign_targets.__doc__ = "bdc26 fix: " + (original.__doc__ or "")
    CenterHead.assign_targets = assign_targets

    # S9 (VoxelNeXt members): VoxelNeXtHead.assign_targets has the same in-place relabeling; same fix, one call per head
    from pcdet.models.dense_heads.voxelnext_head import VoxelNeXtHead

    original_vn = VoxelNeXtHead.assign_targets

    def assign_targets_vn(self, gt_boxes, *args, **kwargs):
        heads = self.class_names_each_head
        out = None
        try:
            for cur in heads:
                self.class_names_each_head = [cur]
                r = original_vn(self, gt_boxes.clone(), *args, **kwargs)
                if out is None:
                    out = {k: list(v) for k, v in r.items()}
                else:
                    for k, v in r.items():
                        out[k].extend(v)
        finally:
            self.class_names_each_head = heads
        return out

    assign_targets_vn.__doc__ = "bdc26 fix: " + (original_vn.__doc__ or "")
    VoxelNeXtHead.assign_targets = assign_targets_vn
    _APPLIED = True
