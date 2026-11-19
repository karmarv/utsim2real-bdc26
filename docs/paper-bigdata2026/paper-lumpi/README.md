# LUMPI track paper (IEEE BigData 2026 Cup, CyberChair SC04)

Status 2026-11-18 19:45 CST, revision 5 (organizer-guideline fixes; no rank claim): **ready for upload.** 9 pages (limit 10 incl. references), IEEE two-column, US letter, CyberChair letter template (`template/ieee-conference-template-letter.docx`, identical to the file from the camera-ready instructions page). Every page checked: full-width figures at the page tops, no table or figure split across columns or pages, no overlaps, no column gap above 0.50 in, last page balanced.

Ranked entry: **CodaBench 1053789** (0.5430, mAP 0.198, realism 0.934), marked as the leaderboard entry in "My Submissions"; the organizers confirmed on Nov 18 that 1053789 is the entry on record (their "1052645" was a typo).

## Files

| File | What it is |
|---|---|
| `paper_lumpi.md` | single source of the paper |
| `Vishwakarma_BigDataCup2026_LUMPI.pdf` | **upload this PDF** (layout verified page by page; fonts embedded) |
| `Vishwakarma_BigDataCup2026_LUMPI.docx` | Word version in the IEEE template, for edits; if you export from Word instead, check that the full-width figures still sit at the page tops |
| `arxiv/` | arXiv PDF and `ARXIV_METADATA.md` (abstract 248 words, 1,558 characters) |
| `figures/` | Fig. 1 pipeline, Fig. 4 validation vs test, Fig. 6 approach gains (all by `../tools/make_paper_figures.py`); Figs. 2, 3, 5 from the repo |
| `build_docx.py` | builder (writes the real title and author into the file properties, so the PDF metadata is correct): repo version plus `--footer`, `--out`, display equations, non-breaking hyphen (U+2011) and a balanced last page |

## arXiv (submitted 2026-11-18, about 21:55 CST)

- Submission **submit/8395481**, status "submitted" (in moderation); the arXiv identifier (2611.xxxxx) is assigned when it is announced
- License: arXiv non-exclusive; primary cs.CV, cross-lists cs.LG and cs.RO; ACM class I.4.8; I.2.10; metadata as in `arxiv/ARXIV_METADATA.md`
- After announcement: send the arXiv link to the organizers; after the IEEE proceedings appear, add the journal-ref and DOI

## Title (revision 4: middle ground after the review)

**Digital Twin Augmentation and Classwise Detector Fusion for Synthetic-Only Multi-LiDAR Detection on LUMPI** (13 words, 3 title lines)

| # | Proposal | Note |
|---|---|---|
| **1 (used)** | **Digital Twin Augmentation and Classwise Detector Fusion for Synthetic-Only Multi-LiDAR Detection on LUMPI** | names the two measured levers (the label-free twin completion and the per-class routed, fused ensemble) in plain terms, then the setting and the track; no subtitle |
| 2 | Ensembling Detectors over a Completed Digital Twin: Scale, Density and Label Conventions for Synthetic-Only Multi-LiDAR Detection on LUMPI | revision 3; longer, and the subtitle reads as a claim about label conventions that the paper only shows as consistent with the data |
| 3 | Rescale, Recast, Ensemble: Completing the Digital Twin for Synthetic-Only Multi-LiDAR Detection on LUMPI | catchier, less searchable |

Pairs with the V2X-Real title ("Pedestrian Synthesis and Detector Fusion for Synthetic-Only Roadside LiDAR Detection on V2X-Real").

## Changes in revision 5 (final check against the organizers' Nov 17 guidelines)

| Area | Change |
|---|---|
| Guideline 1 (no lists of experiments outside the final entry) | Table VIII "Alternatives that did not pass their gates" removed; Section VI-D renamed "Lessons for the gates" and cut to two sentences (class-gate pooling; re-cast corpus raised realism but lowered detection); TransFusion-L and SE-SSD references dropped (only cited in that table): 38 references |
| Rank | no placement anywhere in the paper or the arXiv comments; abstract and introduction say "our best submission ranked by the organizers" (the CodaBench board shows a different raw order than the organizers' notification, and the website posts winners on Nov 25) |
| Prior work | "an earlier edition ... run under different rules, test data and scorer settings" replaced by "the ECCV 2026 DriveX edition of this challenge" (all four cited reports verified on arXiv as DriveX entries) |
| Layout | 9 pages, 7 tables, gaps at most 0.50 in, 0 overlaps |

## Changes in revision 4 (from the external review; scope: factual fixes only)

| Area | Change |
|---|---|
| Title | middle-ground title above; companion reference [10] updated to the V2X-Real title |
| Real-data paragraph | detector weights optimized only on synthetic point clouds and annotations; the 100 forbidden frames excluded from training, generator calibration, validation and model selection; the 50 released test clouds used only for inference with the frozen pipeline |
| Late-A split | frames 4800-6395, ending about 100 frames before the first test frame (6497) |
| Scale argument | 0.78^3 = 0.47 IoU stated for a concentric, aligned box |
| Test-time views | the 12 views listed (identity, 3 flips, yaw ±5°, height ±0.25 m, scales 0.95/1.05 on identity and x-y flip) |
| Copies | described as low-ranked alternative hypotheses; the original ranking is unchanged |
| System gate | 1,000 resamples of whole windows |
| Results | unscored 3D mAP at IoU 0.7 (0.102) stated |
| Realism | 44% of the excess transport in the near-ground band; gap of about 0.006 to the empirical real-against-real reference (not called an upper bound) |
| Causal wording | label findings stated as "consistent with" the label conventions and our class thresholds (37.5% of real vans kept); "suspected annotation or taxonomy inconsistencies"; conclusion no longer guarantees transfer |
| Table V | caption defines localization, ranking and misses, and recall at IoU 0.5 |
| Related work | one neutral sentence on earlier-edition solutions by method only, no scores [29], [30]; references renumbered by first citation (40) |
| Layout | Tables II, IV, VIII and Fig. 6 moved so every column fills; last-page columns balanced |

Deferred (named in the review, out of scope for a factual-fix round; candidates for future work or a journal version): a label audit with corrected annotations, controlled same-seed comparisons per lever, a split of the range-mapping and background effects, near/far recall, inference cost.

## Organizer guideline check (2026-11-17)

- [x] Ranked entry only (CodaBench 1053789: 0.5430, mAP 0.198, realism 0.934); no submission IDs in text or figures
- [x] Paper structure with an ablation section; short tables
- [x] Real-data paragraph (uses, calibration and fit frames, choice of the 50 frames, no forbidden frame, withdrawn label-placed walkers and frames-only calibration)
- [x] No list of experiments outside the final entry (the "did not pass their gates" table was removed in revision 5)
- [x] No other teams' results and no rank or placement claim: the paper calls the ranked entry "our best submission ranked by the organizers"; ECCV 2026 DriveX-edition reports cited by method only, without scores
- [x] Public code link in the abstract and the reproducibility paragraph
- [x] Organizers' papers and datasets cited in their form

## Build and layout tools

```bash
python3 build_docx.py --pdf                                        # submission version
python3 ../tools/check_paper.py paper_lumpi.md                     # abstract length, citation order, link and ID checks
python3 ../tools/renumber_refs.py paper_lumpi.md                   # renumber references by first citation
python3 ../tools/place.py . paper_lumpi.md --report                # page gaps and overlaps of the current source
python3 build_docx.py --footer "<IEEE copyright line from CyberChair>" --out camera_ready.docx --pdf
```

## Camera-ready notes (Nov 20; from the review, verify on the CyberChair instructions page)

- IEEE PDF eXpress check with the conference ID given there (the review quotes 70701X; unverified)
- figures at 300 dpi or more; up to 2 extra pages at a fee
- add the IEEE copyright line with `--footer`, then the copyright form

## CyberChair fields

- Title: as above
- Author: Rahul Vishwakarma, Hitachi America, Ltd. R&D, Santa Clara, CA, USA
- Keywords: LiDAR 3D object detection, sim-to-real transfer, digital twin, synthetic data, roadside perception, LUMPI
- Abstract: copy from `arxiv/ARXIV_METADATA.md`
