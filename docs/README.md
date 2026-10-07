# Documentation index

> Plan, design and approach documents for the UrbanTwin Sim2Real 2026 entry (IEEE BigData Cup 2026, both tracks). The developer guide that walks through setup, data, training, validation, inference and submission is the [root README](../README.md); each track documents its data and models inside its own folders.

## Where to read what

| You want to | Read |
|---|---|
| Run the pipeline end to end | [root `README.md`](../README.md) Sections 4-7; evaluation, packaging, integrity and contributing per track: [`model-lumpi-track/README.md`](../model-lumpi-track/README.md), [`model-v2x-track/README.md`](../model-v2x-track/README.md) Sections 10-12 |
| See the named strategies and their CodaBench results | [root `README.md`](../README.md) Sections 8-9; details in [`02-STRATEGY.md`](02-STRATEGY.md#8-strategy-routes-after-s1) Section 8 |
| Know the rules, the exact scoring and the submission spec | [`01-CHALLENGE-FACTS.md`](01-CHALLENGE-FACTS.md) |
| Know where the points are and what to build next | [`02-STRATEGY.md`](02-STRATEGY.md) |
| Understand the system design and the code map | [`03-ARCHITECTURE.md`](03-ARCHITECTURE.md) |
| Build or extend a module (goal, location, steps, acceptance tests) | [`04-IMPLEMENTATION-GUIDE.md`](04-IMPLEMENTATION-GUIDE.md) |
| Plan the days to the final phase and the submission budget | [`05-SCHEDULE-AND-RUNBOOK.md`](05-SCHEDULE-AND-RUNBOOK.md) |
| Learn the concepts, beginner to state of the art | [`06-LEARNING-PATH.md`](06-LEARNING-PATH.md) |
| Find papers, code and licences | [`07-LITERATURE.md`](07-LITERATURE.md) |
| See why something was decided | [`decisions/`](decisions) |
| Read the organizers' papers | [`reference/papers/`](reference/papers) |

## Track documents (inside the track folders)

| Track | Data and generator | Models (approaches, selected model, lifecycle, results) | One model |
|---|---|---|---|
| 1 LUMPI (CodaBench 16684) | [`data-lumpi-track/README.md`](../data-lumpi-track/README.md) | [`model-lumpi-track/README.md`](../model-lumpi-track/README.md) | `model-lumpi-track/<model>/README.md` |
| 2 V2X-Real (CodaBench 16685) | [`data-v2x-track/README.md`](../data-v2x-track/README.md) | [`model-v2x-track/README.md`](../model-v2x-track/README.md) | `model-v2x-track/<model>/README.md` |

## Decision records

| Record | Subject |
|---|---|
| [`2026-09-30-plan-review.md`](decisions/2026-09-30-plan-review.md) | review of the earlier plan set and what replaced it |
| [`2026-09-30-research-exposure.md`](decisions/2026-09-30-research-exposure.md) | real data touched during research before the guard existed, and the 2026-10-02 follow-up check |
| [`2026-09-30-real-data-download.md`](decisions/2026-09-30-real-data-download.md) | downloading real LUMPI and V2X-Real on the entrant's instruction; what is used how |
| [`2026-09-30-g1-generator.md`](decisions/2026-09-30-g1-generator.md) | engine G1: walkers, Van mapping, calibrated background density (gray area, disclosed), walker v2 |
| [`2026-10-06-codabench-submission-failures.md`](decisions/2026-10-06-codabench-submission-failures.md) | first uploads (957399 Failed, 957439 stuck) were hand-edited copies; team set by the packager; pre-upload checker |

New records follow the template in [`decisions/README.md`](decisions/README.md): one dated file per decision, organizer answer, legal answer or gate outcome.
