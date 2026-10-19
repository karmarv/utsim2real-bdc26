# synth-docs: the synth research line (branch `synth-cv`)

> The research toward the CVPR 2027 paper and its follow-ups. It lives on the branch **`synth-cv`** only. Branch `main` holds the challenge entries, the challenge report and nothing else. Start with the plan of record, [`RESEARCH-AGENDA.md`](RESEARCH-AGENDA.md).

## 1. Branches

| Branch | Holds | Rules |
|---|---|---|
| `main` | the challenge line: `common/`, `data-*`, `model-*`, `docs/`, `releases/`, `paper-bigdata2026/` | never contains research; the public code release is exported from it (`synth-paper/README.md` Section 5) |
| `synth-cv` | `main` plus the research line | **adds paths under `synth-*` only**; never edits a file of `main`; takes `main` in by merge; is never merged into `main` before publication; is pushed only to the private `origin` |

Because `synth-cv` only adds `synth-*` paths, `git merge main` on it never conflicts. Check the rule before every commit on `synth-cv`; the command must print nothing:

```bash
git diff --name-only main...synth-cv | grep -v '^synth-'
```

**Working on both.**
- Research: `git checkout synth-cv`.
- Challenge work (final phase, report): `git checkout main`, commit there, then bring it over with `git checkout synth-cv && git merge main`.
- To keep both open at once, add a second working directory next to this one. It shares `$BDC_DATA` (`<repo>/../bdc26-data`), and Python runs from this checkout's `.venv_ut` by its absolute path:

```bash
git worktree add ../utsim2real-bdc26-main main
```

**Pushing** happens in the user's terminal: `git push -u origin synth-cv` (`origin` is private).

## 2. What lives where

| Path | Content |
|---|---|
| [`RESEARCH-AGENDA.md`](RESEARCH-AGENDA.md) | plan of record. Rev. 2: Calibrated Twin Distributions. Rev. 3, Section 13: the refined CVPR paper "Sensor, Scene, Scribe". Also evidence, claims, experiments, compute, work packages, gates and risks |
| [`S3-STRATEGY.md`](S3-STRATEGY.md) | **start here for the plan**: value assessment of every approach, the S3 step sequence (novelty, pros and cons, workflow, complexity, value, gates), the S3-Twin framework and the dated execution plan |
| [`LITERATURE.md`](LITERATURE.md) | references R45-R124 with verification status (R1-R44 stay in `docs/07-LITERATURE.md` on `main`) |
| [`../synth-common/`](../synth-common/README.md) | shared code of the line (package `synthtwin`, tools such as `export_public.py`, pipeline, tests) |
| [`../synth-lumpi-track/`](../synth-lumpi-track/README.md), [`../synth-v2x-track/`](../synth-v2x-track/README.md) | per-track twin parameter spaces (`twin/theta.yaml`), summary statistics and data protocol (`twin/summaries.yaml`), experiment records |
| [`../synth-paper/`](../synth-paper/README.md) | paper sources, and the separation policy between the challenge report and the research papers (what goes where, anonymity, licences, public release) |

## 3. Data use

All work here is academic, non-commercial research (user statement, 2026-10-18): LUMPI (CC BY-NC 3.0), V2X-Real (academic use), TUMTraf-I (CC BY-NC-ND 4.0: never redistribute anything derived from it), and the organizers' UrbanTwin sets. Real data enters the generator only as statistics; no detector is trained on real frames (`synth-common/README.md` Section 3). Licences in detail: `synth-paper/README.md` Section 4.
