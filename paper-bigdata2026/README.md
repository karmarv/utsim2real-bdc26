# paper-bigdata2026: the challenge report and the BigData Cup paper

> Scope: the system that produced the challenge entries, strategies S1-S6 (release 6.0) and the final-phase submissions, as recorded in [`docs/01`](../docs/01-CHALLENGE-FACTS.md) to [`docs/07`](../docs/07-LITERATURE.md), the [decision records](../docs/decisions/README.md) and the track READMEs. Every number in the paper comes from a record in this repository; nothing is re-run for the paper.

## 1. Deliverables and dates

| Deliverable | Due | Length and format | Who | Channel |
|---|---|---|---|---|
| Challenge report | **Nov 15, 2026** | 4-8 pages, IEEE two-column | every team | ASK ([`docs/01` Section 10](../docs/01-CHALLENGE-FACTS.md#10-questions-for-the-organizers-email-muhammadshahbazucfedu-on-day-1), question 5) |
| Cup paper (paper track, CyberChair subarea SC04) | camera-ready **Nov 20, 2026** | up to 10 pages including references, IEEE two-column | top 3 per track (invited) | CyberChair |
| Code release for verification | with the paper | a public repository with the detector code and the 6.0 weights | top 3 per track | GitHub (Section 6) |

The final phase closes Sat Nov 14, 16:00 PST, so the report's final-phase numbers arrive less than a day before it is due: draft everything else by **Nov 1**, when the system is frozen at release 6.0 (F1 = the 6.0 zips). Winners are announced Nov 25; IEEE BigData 2026 is Dec 14-17 in Phoenix.

**Questions for the organizers** (send them with question 5 of `docs/01` Section 10): the submission channel and template for the Nov 15 report; whether the report is archival (published in the proceedings) or only a requirement for the prize; whether the Nov 20 camera-ready replaces it or is a separate paper.

## 2. Contributions (what the paper claims)

1. **A rule-compliant synthetic-only pipeline** that ranks first on both tracks (development phase: LUMPI 0.5228, rank 1 of 21; V2X 0.8931, rank 1 of 23; final phase: to add on Nov 15). The real data enters only as statistics for the generator and as labelled validation; no detector sees a real frame in training.
2. **Generator side:** completing the organizers' twins with what they miss (walkers and riders ray-cast with the real sensors, real-size actors, static clutter, calibrated background density and field of view), and realism-frame selection against a legal real proxy. Leaderboard realism from the first upload to S6: LUMPI 0.891 -> 0.932, V2X 0.920 -> 0.933 (the organizers' raw LUMPI frames score about 0.60 on our held-out proxy; `data-lumpi-track/README.md` Section 8).
3. **Detector side:** a routed per-class portfolio of four architectures (PointPillars, CenterPoint, Voxel R-CNN, PV-RCNN++) with test-time augmentation, cross-architecture box fusion, class-wise object scaling, seed bags and per-class post-processing. Measured on the leaderboard: detection +0.121 (V2X) and +0.034 (LUMPI) of combined score since S1.
4. **Validation practice under a 100-frame hidden test:** two disjoint real validation splits (realval-A and realval-B), pre-registered gates and the pooled rule, and bit-exact reproduction of both entries from the released weights.

## 3. Outline and page budget

The 8-page report; the 10-page paper adds Sections 7.3-7.4 and a longer related-work section.

| # | Section | Pages | Content | Sources |
|---|---|---|---|---|
| 1 | Introduction | 0.75 | the task, the two tracks, the combined metric (0.6 detection + 0.4 realism), the four contributions, the headline results | `docs/01` Sections 1-4 |
| 2 | Related work | 0.5 | sim-to-real LiDAR detection, roadside 3D detection, digital twins (UrbanTwin), LiDAR simulation and ray drop, test-time augmentation and box fusion | `docs/07` Sections 6-7 (R1-R44) |
| 3 | Data, splits and rule compliance | 0.75 | the declaration; the forbidden-frame guard and exclusion windows; realval-A/B; the log of real-data use; the rules review | `docs/01` Sections 3 and 9; `docs/decisions/2026-10-14-rules-compliance-review.md`; data READMEs |
| 4 | Synthetic data | 1.5 | engine G1 (walkers, actor scale, density, FOV), engine G2-lite (re-cast real-size actors, riders, clutter), the density prior, realism-frame selection | `docs/03` Section 3; `data-<track>-track/README.md` Section 8; `docs/02` Sections 8.7, 8.9 |
| 5 | Detection | 1.25 | the four architectures and their training; object scaling; TTA; cross-architecture fusion; per-class routing, floors and post-processing; seed bags | `docs/03` Section 4; `model-<track>-track/README.md` Section 7; `docs/02` Sections 8.3-8.6 |
| 6 | Validation and selection | 0.75 | the A/B protocol, the upload gate, the pooled rule (one paragraph), the Van judge; reproduction from the released weights | `docs/decisions/README.md` Section 3; root README Section 6.11 |
| 7 | Results | 1.5 | 7.1 leaderboard progression per step (T1); 7.2 per-class results (T2); 7.3 ablations on realval-B (T3); 7.4 realism by component (T4) | `docs/02` Sections 0 and 8.10; submission register; registries |
| 8 | Limitations and lessons | 0.5 | what did not transfer (LUMPI Bicycle after R3, S5 on LUMPI, GBlobs alone); classes left near zero (Bus, Motorcycle); the cost of a 100-frame test | `docs/02` Section 8.10 |
| | References | 0.5 | | `docs/07` |

## 4. Tables and figures

| ID | What | Source (exists) | To make |
|---|---|---|---|
| T1 | leaderboard progression per step, combined split into detection and realism, both tracks | `docs/02` Section 8.10 (benefits table) | LaTeX table |
| T2 | per-class AP, S1 and S6, both tracks | `docs/02` Section 8.10; `codabench_<id>.json` per submission | LaTeX table |
| T3 | ablations on realval-B, one row per lever, both tracks | `docs/02` Section 0; `model-<track>-track/registry.csv` | LaTeX table |
| T4 | realism R per generator component, held-out proxies | `data-<track>-track/README.md` Section 8 | LaTeX table |
| F1 | pipeline diagram: generator, training, portfolio, gates | `docs/03` Section 2 | drawing |
| F2 | real against synthetic frames, bird's-eye view, one per track | the prepared corpora | a plot script in this folder |
| F3 | per-class gains per step (stacked bars) | T1, T2 | a plot script in this folder |
| F4 | fusion and TTA: static false positives per frame and BEV-3D gap | `docs/02` Section 8.3.1 | a plot script in this folder |

## 5. Layout and build

```
paper-bigdata2026/
├── README.md        this file
├── main.tex         IEEE conference template (IEEEtran), one file per section under sections/
├── sections/        01-intro.tex ... 08-limitations.tex
├── tables/          T1-T4 (.tex), written by make_tables.py from the records
├── figures/         F1-F4, written by make_figures.py (F1 drawn by hand)
├── refs.bib         from docs/07
├── make_tables.py   reads the registries, codabench_<id>.json and the submission register
└── make_figures.py  same sources; matplotlib from .venv_ut
```

The server has no TeX installation: build on Overleaf (IEEE conference template) and keep the sources in this folder, so the tables and figures stay generated from the records. Commit the PDF of each submitted version next to the sources (`report-2026-11-15.pdf`, `camera-ready-2026-11-20.pdf`).

## 6. Checklist

- [ ] Final-phase scores recorded (`codabench_<id>.json`, the register in `docs/decisions/README.md` Section 2) before Section 7 is final.
- [ ] Section 3 matches the declaration and the rules review word for word where it quotes them.
- [ ] Organizers cited as Shahbaz and Agarwal; the UrbanTwin papers and datasets cited with their DOIs; licences acknowledged (LUMPI CC BY-NC 3.0, V2X-Real academic use, UT sets CC0).
- [ ] Every number traceable to a record; development and final-phase numbers labelled as such.
- [ ] Code release (top 3): a new public repository with the detector code and the release-6.0 weights, prepared by the maintainer; the paper links to it, never to this repository (which is private).
- [ ] No em dashes; IEEE reference style; figures readable in grayscale.
