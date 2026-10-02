"""Shared code for both tracks of the UCF UrbanTwin Sim2Real LiDAR Challenge (IEEE BigData Cup 2026).

Module map (see docs/03-ARCHITECTURE.md): config (track configs, data root), io (fetch, readers),
guard (forbidden-frame guard), frames (masking, resampling), boxes (box geometry), classmap,
pcdet_export (OpenPCDet custom datasets), evalap (challenge AP), realism (CD/MMD/EMD/FPD),
submit (validator, packager), registry (experiment log), render (raycaster), detect (OpenPCDet glue).
"""
__version__ = "0.1.0"
