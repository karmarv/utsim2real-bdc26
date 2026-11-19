# Documentation index

> Plan, design and approach documents for the UrbanTwin Sim2Real 2026 entry (IEEE BigData Cup 2026, both tracks). The developer guide that walks through setup, data, training, validation, inference and submission is [`DEVELOPMENT.md`](../DEVELOPMENT.md); each track documents its data and models inside its own folders.

## Where to read what

| You want to | Read |
|---|---|
| Run the pipeline end to end | [`DEVELOPMENT.md`](../DEVELOPMENT.md) Sections 4-7; evaluation, packaging, integrity and contributing per track: [`model-lumpi-track/DEVELOPMENT.md`](../model-lumpi-track/DEVELOPMENT.md), [`model-v2x-track/DEVELOPMENT.md`](../model-v2x-track/DEVELOPMENT.md) Sections 10-12 |
| See the named strategies and their CodaBench results | [`DEVELOPMENT.md`](../DEVELOPMENT.md) Sections 8-9; details in [`02-STRATEGY.md`](02-STRATEGY.md#8-strategy-routes-after-s1) Section 8 |
| Know the rules, the exact scoring and the submission spec | [`01-CHALLENGE-FACTS.md`](01-CHALLENGE-FACTS.md) |
| Know where the points are and what to build next | [`02-STRATEGY.md`](02-STRATEGY.md) |
| Understand the system design and the code map | [`03-ARCHITECTURE.md`](03-ARCHITECTURE.md) |
| Build or extend a module (goal, location, steps, acceptance tests) | [`04-IMPLEMENTATION-GUIDE.md`](04-IMPLEMENTATION-GUIDE.md) |
| Plan the days to the final phase and the submission budget | [`05-SCHEDULE-AND-RUNBOOK.md`](05-SCHEDULE-AND-RUNBOOK.md) |
| Learn the concepts, beginner to state of the art | [`06-LEARNING-PATH.md`](06-LEARNING-PATH.md) |
| Find papers, code and licences | [`07-LITERATURE.md`](07-LITERATURE.md) |
| See every submission, its gate result and why it was decided; the gates, the progression tracker and the calendar | [`decisions/README.md`](decisions/README.md) |
| Find the files of a released leaderboard entry | [`RELEASES.md`](../RELEASES.md) |
| Read the organizers' papers | [`reference/papers/`](reference/papers) |
| Read our papers and the final challenge reports (both tracks) | [`paper-bigdata2026/`](paper-bigdata2026): [`paper-v2x-real/`](paper-bigdata2026/paper-v2x-real), [`paper-lumpi/`](paper-bigdata2026/paper-lumpi), [`final-report/`](paper-bigdata2026/final-report) |
| See the final entries and how to reproduce them | [root `README.md`](../README.md) |

## Track documents (inside the track folders)

| Track | Data and generator | Models (approaches, selected model, lifecycle, results) | One model |
|---|---|---|---|
| 1 LUMPI (CodaBench 16684) | [`data-lumpi-track/README.md`](../data-lumpi-track/README.md) | [`model-lumpi-track/DEVELOPMENT.md`](../model-lumpi-track/DEVELOPMENT.md) | `model-lumpi-track/<model>/README.md` |
| 2 V2X-Real (CodaBench 16685) | [`data-v2x-track/README.md`](../data-v2x-track/README.md) | [`model-v2x-track/DEVELOPMENT.md`](../model-v2x-track/DEVELOPMENT.md) | `model-v2x-track/<model>/README.md` |

## Decision records

The index of dated records (one per decision-ready version, named `YYYY-MM-DD-<strategy or scope>-<topic>.md`), the submission register, the evaluation protocol and gates, the progression tracker and the calendar are in [`decisions/README.md`](decisions/README.md).
