# arXiv submission metadata (LUMPI paper)

Paste these fields into the arXiv submission form (https://arxiv.org/submit). Plain ASCII, as arXiv requires.

## Title
Digital Twin Augmentation and Classwise Detector Fusion for Synthetic-Only Multi-LiDAR Detection on LUMPI

## Authors
Rahul Vishwakarma (Hitachi America, Ltd. R&D)

## Abstract (1558 characters, 248 words; arXiv limit 1,920 characters; do not include the word "Abstract")
A digital twin of a roadside site can label LiDAR frames for free, but a detector trained on its frames must still transfer to the real sensors. We study this on the LUMPI track of the UCF UrbanTwin Sim2Real LiDAR Challenge: five merged lidars at an urban intersection, seven classes, a detector trained on synthetic data only, and 50 submitted synthetic frames scored for realism. Against legal real statistics, the released twin renders actors at 0.78 times their real size, has no pedestrians, gives cars and bicycles half and a quarter of the real points, and misses a third of the real static structure. We complete it without copying any real label: actors at real scale, ray-cast walkers placed on the twin's own scene map, vehicles re-cast at real size and density, seated riders and unlabeled clutter. An ensemble of thirteen detectors from five families, trained from scratch on these frames, is routed per class and fused over test-time views and generator-draw bags; label-free size steps and low-score copies ranked below the original boxes follow. Every change passed a validation gate fixed in advance. The ranked entry, our best submission ranked by the organizers, scores 0.5430 (3D mAP 0.198 at IoU 0.5, realism 0.934). Fusion was the largest single gain, and placing walkers on the twin's map raised Person AP for every architecture. The remaining error is class confusion between vehicle types, consistent with the real labels' size conventions and provenance and with our class mapping. Code: https://github.com/karmarv/utsim2real-bdc26.

## Comments
9 pages, 6 figures, 7 tables. Submitted to the IEEE BigData 2026 Cup proceedings (UCF UrbanTwin Sim2Real LiDAR Challenge, LUMPI track). Companion paper on the V2X-Real track. Code: https://github.com/karmarv/utsim2real-bdc26 

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
`Vishwakarma_BigDataCup2026_LUMPI_arXiv.pdf`: one PDF made from the Word document (not from TeX), which arXiv accepts as a PDF-only submission; fonts
embedded, US letter, no JavaScript. If you regenerate it in Word, use File > Save As > PDF ("Best for electronic
distribution and accessibility"), not "Print to PDF", and check that the full-width figures stay at the page tops.

## Before you submit
1. Internal approval for external publication, if your organization requires it.
2. arXiv account; a first submission to cs.CV may need an endorsement (arXiv says so during submission).
3. Same content as the CyberChair PDF (no IEEE copyright line on the first page before acceptance).
4. After acceptance: replace the arXiv version with the accepted manuscript carrying the IEEE notice in the first-page
   footer (build command in the folder README), then add the DOI as journal-ref.
5. Email the arXiv link to the organizers (their request of 2026-11-17).
