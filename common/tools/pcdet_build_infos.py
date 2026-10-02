#!/usr/bin/env python
"""Create OpenPCDet infos (custom_infos_{train,val}.pkl) and the GT-sampling database for a dataset folder.

    python common/tools/pcdet_build_infos.py model-v2x-track/pointpillars-ut            # data from model.yaml
    python common/tools/pcdet_build_infos.py model-v2x-track/pointpillars-ut --data pcdet/smoke-v2x
The dataset folder must follow bdc26.pcdet_export (points/, labels/, ImageSets/{train,val}.txt).
Class names come from the model config, so boxes of other classes are ignored.
"""
import argparse
import pickle

from _common import data_path, load_pcdet_cfg, model_info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir")
    ap.add_argument("--data", default=None, help="dataset (default: model.yaml data.train)")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    data = data_path(track, a.data or card["data"]["train"])
    cfg = load_pcdet_cfg(model_dir, data)

    from pcdet.utils import common_utils

    from bdc26.detect.pcdet_dataset import BDCDataset

    ds = BDCDataset(dataset_cfg=cfg.DATA_CONFIG, class_names=cfg.CLASS_NAMES, root_path=data, training=False,
                    logger=common_utils.create_logger())
    nfeat = len(cfg.DATA_CONFIG.POINT_FEATURE_ENCODING.src_feature_list)
    for split in ("train", "val"):
        ds.set_split(split)
        infos = ds.get_infos(cfg.CLASS_NAMES, num_workers=a.workers, has_label=True, num_features=nfeat)
        for info in infos:                                   # keep only the model's classes
            m = [n in cfg.CLASS_NAMES for n in info["annos"]["name"]]
            info["annos"]["name"], info["annos"]["gt_boxes_lidar"] = info["annos"]["name"][m], info["annos"]["gt_boxes_lidar"][m]
        with open(data / f"custom_infos_{split}.pkl", "wb") as f:
            pickle.dump(infos, f)
        print(f"{split}: {len(infos)} frames -> {data / f'custom_infos_{split}.pkl'}")
    ds.set_split("train")
    ds.create_groundtruth_database(data / "custom_infos_train.pkl", split="train")
    # OpenPCDet's GT sampler crashes ("need at least one array to stack") when a sampled class has no
    # database entry left after filter_by_min_points: report that here instead of mid-training.
    db = pickle.load(open(data / "custom_dbinfos_train.pkl", "rb"))
    # The sampler also indexes db[c] for EVERY model class; classes without training data (for example Person
    # before engine G1 adds them) need an empty entry.
    missing = [c for c in cfg.CLASS_NAMES if c not in db]
    if missing:
        db.update({c: [] for c in missing})
        with open(data / "custom_dbinfos_train.pkl", "wb") as f:
            pickle.dump(db, f)
        print(f"classes without GT-database entries (empty lists added): {missing}")
    for aug in cfg.DATA_CONFIG.DATA_AUGMENTOR.AUG_CONFIG_LIST:
        if aug.NAME != "gt_sampling":
            continue
        mins = dict(x.split(":") for x in aug.PREPARE.get("filter_by_min_points", []))
        for grp in aug.SAMPLE_GROUPS:
            c = grp.split(":")[0]
            n = sum(e["num_points_in_gt"] >= int(mins.get(c, 0)) for e in db.get(c, []))
            print(f"gt_sampling {c}: {n} entries with >= {mins.get(c, 0)} points")
            if n == 0:
                raise SystemExit(f"class {c} has no GT-database entry with >= {mins.get(c, 0)} points: lower "
                                 f"filter_by_min_points or drop {c} from SAMPLE_GROUPS in pcdet_dataset.yaml")


if __name__ == "__main__":
    main()
