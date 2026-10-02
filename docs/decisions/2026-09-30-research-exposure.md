# 2026-09-30 Research-phase exposure to real labels that may include forbidden frames

**Context.** On 2026-09-30, while the plan was being researched and before `forbidden_frames.txt` was on disk, an automated research assistant working for the entrant:

1. downloaded LUMPI `Label/Measurement4/Label.csv` (all 8,120 labeled frames) to learn the label format, and computed per-class counts and median box sizes over the whole measurement. Measurement4 frames 006497-008109 contain all 100 forbidden LUMPI frames, so those aggregates include forbidden-frame labels (at most about 1.2% of rows);
2. opened two V2X-Real **test-split** frames (`2023-04-03-18-19-32_13_0/{-1,-2,1}/000100` and `2023-03-17-16-12-12_3_0/{-1,-2,1}/000050`) to learn the file format. Whether either is a forbidden frame is unknown until the challenge's V2X scenario-index mapping is resolved (M1 step 4);
3. computed V2X class statistics on a strided sample of the V2X-Real **train** split. Whether the challenge's forbidden V2X frames come from that split is also unknown;
4. later the same day, while building the data-preparation code, the V2X-Real train-split frame `2023-04-03-18-19-32_13_1/-1/000040` (point cloud and labels, from item 3's sample) was used once to check the label-to-sensor-frame box conversion (points inside boxes). Since then all unit and integration tests use synthetic fixtures only.

No model was trained, validated or tuned, no generator parameter was set, and no submission was made.

**Containment.**
- The raw LUMPI `Label.csv` and the two V2X test frames were deleted the same day.
- No label statistic from items 1-3 is used to set any parameter in the plan. The docs state class *semantics* (for example that riders count as V2X pedestrians, from the official class map) but take every numeric size, count or distribution from M5.2 on guarded legal frames only.
- The only aggregate test-set numbers used are the per-class GT counts that the organizers' scoring program prints publicly on every detailed-results page, used as a class-map sanity check.

**Decision.**
- Keep a written record (this file) and repeat it in the integrity section of the challenge report.
- After M1 step 4, check the two V2X frames above against the resolved forbidden list and append the result here.
- Optional: mention the incident to the organizers in the Section 10 email of `01-CHALLENGE-FACTS.md`, so that the honor declaration is made with full disclosure. The entrant decides.

**Follow-up result (2026-10-02, after `resolve_test_ids.py`).** The starting kit's 50 test IDs resolve 26 scenario indices, all of them V2X-Real **train**-split scenes, at strictly increasing positions of the sorted train-scene list (the challenge indexes a sorted subset of train scenes). The 6 indices that occur only among the realism-reference IDs (17, 18, 19, 25, 26, 31; 11 forbidden IDs) are bounded by their resolved neighbours to 1-3 candidate train scenes each; the guard blocks their frames (+/- 20) in every candidate (`kit/id_mapping.json`, `kit/id_mapping_report.json`).
- Item 2, `2023-04-03-18-19-32_13_0/000100` and `2023-03-17-16-12-12_3_0/000050` (V2X-Real test split): no forbidden frame in these scenes; **not forbidden** (allowed by the guard).
- Item 4, `2023-04-03-18-19-32_13_1/000040` (train split, scenario index 2): **16 frames (1.6 s) after the forbidden frame `2_000024`** in the same scene, inside our +/- 20 self-exclusion window. It is not itself a forbidden frame; it was used once on 2026-09-30 to check the label-to-sensor box conversion, and nothing was trained, validated or tuned on it.
- Any parameter traced back to items 1-3? **No.**

Recommendation: mention item 4 in the organizer email (near-neighbour of a forbidden frame, format check only) together with the LUMPI aggregate in item 1, so the declaration is made with full disclosure. The entrant decides.
