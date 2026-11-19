# V2X-Real track paper (IEEE BigData 2026 Cup, CyberChair SC04)

Status 2026-11-18 21:00 CST, revision 5b (your Word edit applied: Fig. 5 after the "Qualitative cases" paragraph): **ready for upload.** 8 pages (limit 10 incl. references), IEEE two-column, US letter, CyberChair letter template (`template/ieee-conference-template-letter.docx`, identical to the file from the camera-ready instructions page). Every page checked: full-width figures at the page tops, no table or figure split across columns or pages, no overlaps, no column gap above 0.45 in, last page balanced.

## Files

| File | What it is |
|---|---|
| `paper_v2x.md` | single source of the paper |
| `Vishwakarma_BigDataCup2026_V2X-Real.pdf` | **upload this PDF** (layout verified page by page; fonts embedded) |
| `Vishwakarma_BigDataCup2026_V2X-Real.docx` | Word version in the IEEE template, for edits; if you export from Word instead, check that the full-width figures still sit at the page tops |
| `arxiv/` | arXiv PDF and `ARXIV_METADATA.md` (abstract 236 words, 1,517 characters) |
| `figures/` | Fig. 1 pipeline, Fig. 4 validation vs test, Fig. 5 approach gains (all by `../tools/make_paper_figures.py`); Figs. 2, 3, 6 from the repo |
| `build_docx.py` | builder (writes the real title and author into the file properties, so the PDF metadata is correct): repo version plus `--footer`, `--out`, display equations (`$$ ... | (n)`), non-breaking hyphen (U+2011, keeps "V2X-Real" on one line) and a balanced last page |

## arXiv (submitted 2026-11-18, about 21:55 CST)

- Submission **submit/8394854**, status "submitted" (in moderation); the arXiv identifier (2611.xxxxx) is assigned when it is announced
- License: arXiv non-exclusive; primary cs.CV, cross-lists cs.LG and cs.RO; ACM class I.4.8; I.2.10; metadata as in `arxiv/ARXIV_METADATA.md`
- After announcement: send the arXiv link to the organizers; after the IEEE proceedings appear, add the journal-ref and DOI

## Title (revision 4: middle ground after the review)

**Pedestrian Synthesis and Detector Fusion for Synthetic-Only Roadside LiDAR Detection on V2X-Real** (12 words, 3 title lines)

| # | Proposal | Note |
|---|---|---|
| **1 (used)** | **Pedestrian Synthesis and Detector Fusion for Synthetic-Only Roadside LiDAR Detection on V2X-Real** | names the two largest levers in plain terms: ray-cast walkers that create the pedestrian class (62% of the test boxes) and the fused detector portfolio (+0.0645), then the setting and the track; no subtitle |
| 2 | Raycasting the Digital Twin: Walkers, Sensor Fidelity and Annotation Conventions for Synthetic-Only Roadside LiDAR Detection on V2X-Real | revision 3; longer, and the subtitle reads as a claim about annotation conventions that the paper only shows as consistent with the data |
| 3 | Raycast, Fuse, Follow the Labels: Synthetic-Only Roadside LiDAR Detection on V2X-Real | catchier, less searchable |

Pairs with the LUMPI title ("Digital Twin Augmentation and Classwise Detector Fusion for Synthetic-Only Multi-LiDAR Detection on LUMPI").

## Changes in revision 5 (final check against the organizers' Nov 17 guidelines)

| Area | Change |
|---|---|
| Guideline 1 (no lists of experiments outside the final entry) | Table VII "Alternatives that did not pass their gates" removed; Section VI-D renamed "Realism-calibrated training corpus" and cut to two sentences (it explains why the entry keeps the uncalibrated corpus); contribution bullet now says "ablations" |
| Rank | no placement anywhere in the paper or the arXiv comments; abstract and introduction say "our best submission ranked by the organizers" (the CodaBench board shows a different raw order than the organizers' notification, and the website posts winners on Nov 25) |
| Prior work | "an earlier edition ... run under different rules, test data and scorer settings" replaced by "the ECCV 2026 DriveX edition of this challenge" (all four cited reports verified on arXiv as DriveX entries) |
| Layout | 8 pages, 6 tables, gaps at most 0.50 in, 0 overlaps |
| Your Word edit (5b) | Fig. 5 moved below the "Qualitative cases" paragraph, as in your edited .docx; the source now has the same order and the .docx/.pdf were rebuilt from it, so the figure keeps the template's centered image and "figure caption" style (pasted in Word it became Body Text, whose 0.95-line spacing made LibreOffice draw the image over the text above it); the wide Fig. 6 anchor sits after Fig. 5 and still prints at the top of page 6 |

## Changes in revision 4 (from the external review; scope: factual fixes only)

| Area | Change |
|---|---|
| Title | middle-ground title above; companion reference [10] updated to the LUMPI title |
| Real-data paragraph | detector weights optimized only on synthetic point clouds and annotations; the 100 forbidden frames excluded from training, generator calibration, validation and model selection; the 50 released test clouds used only for inference with the frozen pipeline; organizer clarifications dated November 9 and 12, 2026 |
| Pedestrian labels | "lower bound" replaced by "a suspected annotation-coverage gap that may affect measured pedestrian AP on B" |
| Test-time views | the 12 views listed |
| Ensemble | seven checkpoints spelled out (Voxel R-CNN on five generator draws, one Voxel R-CNN rosf, one DSVT-Pillar) |
| System gate | 1,000 resamples of whole scene parts |
| Copies | described as low-confidence alternative hypotheses; the original ranking is unchanged |
| Truck route | +0.0073 truck AP and +0.0012 pedestrian AP (+0.0024 combined, about +0.0021 from trucks), recomputed from the score files |
| Realism | gap of about 0.008 to the empirical real-against-real reference; the unsupported "a re-rendered twin cannot" claim removed |
| Wording | IoU 0.5 called demanding for a 0.7 m pedestrian box; conclusion no longer guarantees transfer |
| Related work | one neutral sentence on earlier-edition solutions by method only, no scores [29], [30]; references renumbered by first citation (38) |
| Layout | Table III, Fig. 4, Fig. 5 and Table VI re-placed so every column fills; last-page columns balanced |

Deferred (named in the review, out of scope for a factual-fix round; candidates for future work or a journal version): an audit of the pedestrian annotation coverage, controlled same-seed comparisons per lever, a split of the range-mapping and background effects, near/far recall, inference cost.

## Organizer guideline check (2026-11-17)

- [x] Ranked entry only (CodaBench 1051825: 0.8944, mAP 0.605, realism 0.941); no submission IDs in text or figures
- [x] Paper structure with an ablation section; short tables
- [x] Real-data paragraph (uses, calibration and fit frames, choice of the 50 frames, no forbidden frame, withdrawn label-placed walkers)
- [x] No list of experiments outside the final entry (the "did not pass their gates" table was removed in revision 5)
- [x] No other teams' results and no rank or placement claim: the paper calls the ranked entry "our best submission ranked by the organizers"; ECCV 2026 DriveX-edition reports cited by method only, without scores
- [x] Public code link in the abstract and the reproducibility paragraph
- [x] Organizers' papers and datasets cited in their form

## Build and layout tools

```bash
python3 build_docx.py --pdf                                        # submission version
python3 ../tools/check_paper.py paper_v2x.md                       # abstract length, citation order, link and ID checks
python3 ../tools/renumber_refs.py paper_v2x.md                     # renumber references by first citation
python3 ../tools/place.py . paper_v2x.md --report                  # page gaps and overlaps of the current source
python3 ../tools/place.py . paper_v2x.md "TABLE III" after "Each member runs"   # move a float, rebuild, report
python3 build_docx.py --footer "<IEEE copyright line from CyberChair>" --out camera_ready.docx --pdf
```

After any text edit, run `place.py --report`: a column gap above about 0.5 in means a float should move.

## Camera-ready notes (Nov 20; from the review, verify on the CyberChair instructions page)

- IEEE PDF eXpress check with the conference ID given there (the review quotes 70701X; unverified)
- figures at 300 dpi or more; up to 2 extra pages at a fee
- add the IEEE copyright line with `--footer`, then the copyright form

## CyberChair fields

- Title: as above
- Author: Rahul Vishwakarma, Hitachi America, Ltd. R&D, Santa Clara, CA, USA
- Keywords: LiDAR 3D object detection, sim-to-real transfer, digital twin, synthetic data, roadside perception, V2X-Real
- Abstract: copy from `arxiv/ARXIV_METADATA.md`
