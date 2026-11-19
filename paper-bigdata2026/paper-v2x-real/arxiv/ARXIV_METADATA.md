# arXiv submission metadata (V2X-Real paper)

Paste these fields into the arXiv submission form (https://arxiv.org/submit). Plain ASCII, as arXiv requires.

## Title
Pedestrian Synthesis and Detector Fusion for Synthetic-Only Roadside LiDAR Detection on V2X-Real

## Authors
Rahul Vishwakarma (Hitachi America, Ltd. R&D)

## Abstract (1517 characters, 236 words; arXiv limit 1,920 characters; do not include the word "Abstract")
Roadside LiDAR perception needs site-specific 3D labels that are slow to produce. Digital twins promise them for free, but only if a detector trained on simulated frames transfers to the real sensor. We study this on the V2X-Real track of the UCF UrbanTwin Sim2Real LiDAR Challenge, where the detector is trained on synthetic data only and 50 submitted synthetic frames are scored for realism. Against legal real statistics, the released twin has no walkers although pedestrians are 62% of the test objects, renders trucks 3 m too short, and emulates a denser, wider sensor than the real Ouster OS1-64. We raycast what is missing without copying any real label: articulated walkers placed on the twin's own scene map and trucks at real size, both ray-cast with the measured beam table and field of view, plus unlabeled static clutter. Voxel R-CNN and DSVT-Pillar detectors trained from scratch on five generator draws are fused per class over test-time views and draw bags, and label-free post-processing encodes the annotators' conventions. Every change had to pass a validation gate fixed in advance. The ranked entry, our best submission ranked by the organizers, scores 0.8944 (3D mAP 0.605 at IoU 0.5, realism 0.941). Ablations show that test-time views, bags and fusion carry the largest detection gains, that the convention stages add detection without retraining, and that retraining on a realism-calibrated corpus raised realism by 0.011 but cost 0.059 mAP. Code: https://github.com/karmarv/utsim2real-bdc26.

## Comments
8 pages, 6 figures, 6 tables. Submitted to the IEEE BigData 2026 Cup proceedings (UCF UrbanTwin Sim2Real LiDAR Challenge, V2X-Real track). Companion paper on the LUMPI track. Code: https://github.com/karmarv/utsim2real-bdc26 

## Categories
- Primary: cs.CV (Computer Vision and Pattern Recognition)
- Cross-list: cs.LG (Machine Learning), cs.RO (Robotics)

## ACM class (optional)
I.4.8; I.2.10

## License
arXiv.org perpetual, non-exclusive license (the default). It stays compatible with the IEEE copyright transfer of the
camera-ready version; avoid CC BY for a paper that IEEE will publish.

## Report-no / Journal-ref / DOI
Leave empty now. After the IEEE proceedings appear, add the journal-ref and the IEEE DOI with arXiv's journal-ref
facility (no new version needed).

## File to upload
`Vishwakarma_BigDataCup2026_V2X-Real_arXiv.pdf`: one PDF made from the Word document (not from TeX), which arXiv accepts as a PDF-only submission; fonts
embedded, US letter, no JavaScript. If you regenerate it in Word, use File > Save As > PDF ("Best for electronic
distribution and accessibility"), not "Print to PDF", and check that the full-width figures stay at the page tops.

## Before you submit
1. Internal approval for external publication, if your organization requires it.
2. arXiv account; a first submission to cs.CV may need an endorsement (arXiv says so during submission).
3. Same content as the CyberChair PDF (no IEEE copyright line on the first page before acceptance).
4. After acceptance: replace the arXiv version with the accepted manuscript carrying the IEEE notice in the first-page
   footer (build command in the folder README), then add the DOI as journal-ref.
5. Email the arXiv link to the organizers (their request of 2026-11-17).
