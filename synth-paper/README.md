# synth-paper: papers of the synth research line (private until publication)

> Plan of record: [`synth-docs/RESEARCH-AGENDA.md`](../synth-docs/RESEARCH-AGENDA.md) (method, experiments, gates). This folder holds the paper sources and the **separation policy**: what each publication may contain, how the research stays out of the challenge report and the public code release, and the anonymity rules of the review.

## 1. The publications

| | Challenge report | BigData Cup paper | CVPR 2027 main paper | Paper 2 (evaluation science, agenda Section 12) |
|---|---|---|---|---|
| Due | Nov 15, 2026 | camera-ready Nov 20, 2026 (top 3, invited) | registration Nov 10, paper **Nov 16 AoE**, supplementary Nov 23 | NeurIPS 2027 (Evaluations and Datasets), about May 2027 |
| Review | none (organizers) | Cup chairs | double-blind, OpenReview | double-blind |
| Length | 4-8 pages | up to 10 pages with references | 8 pages + references + supplementary | per venue |
| Contribution | the S1-S6 system and its results | same, longer | Sensor, Scene, Scribe (agenda Section 13.2; CTD of Sections 4-6 as the inference engine) | statistics of small-test leaderboards and realism metrics |
| Folder | [`paper-bigdata2026/`](../paper-bigdata2026/README.md) (public) | same | `synth-paper/cvpr2027/` | `synth-paper/paper2/` |

Author: Rahul Vishwakarma, OpenReview profile **RahulVishwakarma1**.

## 2. Separation policy: what goes where

The BigData papers report the **system that was submitted**; the CVPR paper reports a **new method with new experiments**. The two must not overlap in method or results, so the CVPR paper is not a dual submission of the challenge work and the challenge work does not pre-publish the CVPR novelty.

| Content | BigData report and Cup paper | CVPR 2027 | Reason |
|---|---|---|---|
| S1-S6 recipes, portfolio, routing, fusion, seed bags | full | one baseline row ("an engineered detector portfolio"), cited as anonymized concurrent work | it is the BigData contribution |
| Leaderboard and hidden-test numbers, ranks, CodaBench IDs | full | **no** (they identify the authors through the challenge) | anonymity; the challenge must not be mentioned |
| Label conventions | the fixes as engineering: actor scale 1/0.78, size and z post-processing, Van mapping, rider boxes | the scribe model, regimes per recording, the sensor-scene-scribe decomposition (agenda Section 13.2) | the scribe is the CVPR headline |
| Generator engines G1 and G2-lite, density prior, frame selection | full | the simulator substrate, one paragraph, neutral wording, anonymized citation | shared tool, not a CVPR claim |
| realval-A/B splits | described as the validation protocol | own description as the evaluation protocol, with realval-B as the held-out test | the protocol is not a contribution of either paper |
| Pooled rule, realism-metric noise, leaderboard variance | one paragraph each, as practice, no analysis | no | reserved for paper 2 |
| Twin posterior inference, summaries, misspecification pipeline (C1-C2) | **no** | core | CVPR novelty |
| Distribution ensembles against seed ensembles (C3) | seed bags only, as practice | core | CVPR novelty |
| Paired multi-render consistency (C4), failure-driven repair (C5) | **no** | core | CVPR novelty |
| Third site (UT-TUMTraf-I against real TUMTraf-I) | no | core | new data, new experiment |
| Code | public repository of the detector line (Section 5) | anonymized repository for review; public with the camera-ready | |

**Wording guard for the BigData papers.** No sentence may announce or describe follow-up work on inferring the twin, posterior or likelihood-free calibration, multi-render consistency or a third site. "Future work" says only "better twins and fewer hand-set parameters". Run the leak scan of Section 5 on the paper source too:

```bash
grep -n -i -E "posterior|likelihood-free|simulation-based inference|multi-render|consistency loss|TUMTraf|twin distribution|misspecif|scribe|annotator (twin|model)|labell?ing policy|regime|decompos" paper-bigdata2026/sections/*.tex
```

## 3. Anonymity and dual-submission rules (CVPR 2027)

- **No challenge, no identity.** The submission does not mention the challenge, its leaderboard, team names, CodaBench, the GitHub account or the employer (agenda Section 10). Results are on realval-B and the third site only.
- **Concurrent work.** CVPR treats workshop papers longer than four pages as publications, so an archival BigData report or Cup paper (4-10 pages) counts as concurrent work. Follow the CVPR rule for concurrent submissions: cite it anonymously in the third person ("[X] describes an engineered portfolio ..."), state in the paper why the CVPR paper differs (Section 2), and put an anonymized copy in the supplementary (`synth-paper/anonymized/`).
- **Ask the organizers before Nov 10** whether the report is archival, and whether the Cup paper appears in the IEEE BigData proceedings (IEEE Xplore). Either answer is compatible with the policy above; it only changes whether the anonymized copy goes into the supplementary.
- **Code for review.** An anonymized snapshot of `synth-*` (no author names, no repository URL, no `$BDC_DATA` paths with user names), as a supplementary zip or an anonymous mirror.
- **Preprints and social media.** Check the CVPR 2027 policy (preprints, embargo) before posting anything; until then, nothing about the method leaves this repository.
- **OpenReview (before Nov 10).** Profile RahulVishwakarma1: current affiliation with the institutional e-mail, DBLP link, conflicts of interest (co-workers, advisors, recent co-authors), expertise keywords. Check the CVPR 2027 author guidelines for a reviewing obligation and the policy on LLM use.

## 4. Data licences for the papers

**Use statement (user, 2026-10-18):** all work in this repository is academic, non-commercial research, which is within every licence below. No derived asset is used commercially; product use at Hitachi will be built on a separate open-source stack, not on this branch.

| Data | Licence | Use in the papers |
|---|---|---|
| UT-LUMPI, UT-V2X-Real-IC, UT-TUMTraf-I (organizers' synthetic sets; Dataverse DOI 10.7910/DVN/D21HNZ for UT-TUMTraf-I) | CC0 for the first two; UT-TUMTraf-I: record at download (WP5) | training substrate, figures |
| LUMPI | CC BY-NC 3.0 | evaluation and generator statistics; attribution |
| V2X-Real | academic use only | evaluation and generator statistics; no redistribution |
| TUMTraf-I (Zimmer et al., ITSC 2023, arXiv 2306.09266; two Ouster OS1-64 gen 2 on a 7 m gantry, 4,800 labelled frames, test labels unpublished) | **CC BY-NC-ND 4.0** (dev-kit README and paper; dev-kit code MIT) | evaluation and generator statistics; cite the paper; **NoDerivatives: never redistribute converted or class-mapped labels, modified scans or a twin built from its geometry** (keep them under `$BDC_DATA`, never in git or a release); publishing AP numbers is fine; record the licence text in `synth-tumtraf-track/README.md` at download |
| SMPL / SMPL-X, AMASS (if used for walker assets) | non-commercial research licences | allowed for academic research; register before download; never in a public release |

## 5. Public code release (challenge, top 3) without the research line

The repository is **private** and stays private. Branch `main` holds the challenge line only; branch `synth-cv` adds the research, under `synth-*` paths only ([`synth-docs/README.md`](../synth-docs/README.md)). The challenge's code release is a **new public repository** made from an export of `main` (a plain tree, no history):

```bash
.venv_ut/bin/python synth-common/tools/export_public.py --ref main --out ../bdc26-public --public-repo <owner>/<public-name>
```

The export drops any `synth-*` path and any Markdown line naming the research line (both empty for `main`; a safety net), rewrites the private repository name in the weight manifests and links, and refuses to finish (exit 1) if its leak scan finds a research name. Then, in the user's terminal:
1. create the public repository on GitHub;
2. `git init` and push from the export folder;
3. from that clone, publish the weights (`common/tools/release_weights.py publish`, token at the hidden prompt);
4. check `fetch` and `verify` in a fresh clone.

Never push `synth-cv` anywhere but the private `origin`, never merge it into `main` before publication, and never make the repository public.

## 6. Layout

```
synth-paper/
├── README.md        this file: publications, separation policy, anonymity, licences, export
├── cvpr2027/        main.tex (CVPR 2027 template), sections/, tables/, figures/, supp/; tables and figures generated from
│                    synth-<track>-track/experiments/*/results.json by make_tables.py and make_figures.py
├── anonymized/      anonymized copy of the BigData report or paper, for the CVPR supplementary
└── paper2/          evaluation-science paper (after the CVPR submission)
```

The timeline and the go/no-go gates (G1 Oct 21, G2 Oct 26, G3 Nov 2) are in agenda Section 9; the writing starts at G3 at the latest.
