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
"""
from __future__ import annotations

_APPLIED = False


def apply() -> None:
    global _APPLIED
    if _APPLIED:
        return
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
    _APPLIED = True
