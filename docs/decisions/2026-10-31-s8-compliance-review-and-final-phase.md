# 2026-10-31 rules: compliance review of the S8 entries, and the final-phase plan

**Version.** The final development-phase entries, which are F1 for the final phase:
- LUMPI 1022492: `routed-g11d` / `s8d`, 0.525688, rank 1 of 22;
- V2X 1022246: `routed-g13` / `s8v`, 0.902153, rank 1 of 25.

Release 8.1 holds both zips and their 25 checkpoints. This review extends the [2026-10-26 audit](2026-10-26-rules-compliance-audit.md) and its addenda to everything S8 changed ([S8 record](2026-10-29-s8-last-day-strategy.md)).

**Sources re-read on 2026-10-31, 00:40 UTC, after the development phase closed.**
- **CodaBench 16684 and 16685** through the public API: the six pages (Overview, Evaluation, Data, Submission, Rules, Citations) and the Terms are **byte-identical** to the copies read before the S8 build.
- **Phases.** Development is closed ("Previous"). Final runs 2026-11-01 00:00 UTC to 2026-11-15 00:00 UTC, with 1 submission per day, `hide_score_output: true` and a 1,200 s execution limit. The API's total cap is `None`; the pages say 5.
- **Leaderboard.** `Results`, `submission_rule: Force_Best`.
- **The challenge site** is unchanged since commit `72aa87f` (2026-07-27). It still says "5 total submissions per participant. Development submissions are not carried over: resubmit your best system", and "Every team submits a 4-8 page report".
- **The forums** (16423, 16424) need a login and could not be read from the server. The last FAQ known here is Oct 14.

## 1. Verdict

**Both F1 zips are compliant under the same reading as the 2026-10-26 audit.**
- S8 trained nothing: the 25 checkpoints are byte-identical to release 7.0.
- S8 added no new kind of real-data use, and it touched no forbidden frame or test label.
- The two open items carry over unchanged: the walker label rows in the generator (audit item 4, moderate) and the **disclosure email, still unsent**.
- S8 adds one item to disclose: its test-time post-processing is now heavier (Section 2, item S8-6). It breaks no rule, but an inspector would see it in the predictions, so it belongs in the email.

## 2. What S8 changed, checked against the rules

| # | S8 change | Clause | Check | Risk | Action |
|---|---|---|---|---|---|
| S8-1 | No training; the same 25 checkpoints as 7.0 (`releases/8.1/weights.json`, md5-equal) | "Any 3D object detector ... trained on your synthetic data only"; declaration | the detectors are exactly the S7.6 ones, from scratch on our synthetic corpora | none new (audit items 4 and 19 carry over) | none |
| S8-2 | 12-view TTA (flips, ±5° yaw, ±0.25 m height, **global scale 0.95/1.05**) at inference | Allowed: any detector; augmentation is inference-side here | the views transform the test cloud and map the boxes back; nothing is learned from the test frames | none | disclose (S8-6) |
| S8-3 | Post-processing tuned per 12-view variant on realval-A, reported on B; fusion swaps and searches; the final check with the train-split condition | Allowed: "train split ... for hyperparameter selection"; FAQ: real frames "to judge and select models" | the same frames and the same kind of scalar knobs as S3-S7 (audit item 5). Every S8 gate reported the train-split result (audit rule a): LUMPI realval-A, V2X train-split frames | none-remote (LUMPI M5-6 still open, Q2) | none |
| S8-4 | Tail-copy threshold t (0.274, then 0.0841) and the Bus radius, chosen on realval-A | as S8-3; audit rule e (constants) | t is a constant quantile of our own realval-A scores; the radius is a grid choice on A | none | none |
| S8-5 | Test frames: inference, the V2X sparse point counts at inference, official kit checks; **kit-time measurements and box counts of our own predictions** | Terms 3: test clouds "strictly for generating challenge submissions"; audit rule c: no statistic of the test frames | the kit check scores against realval labels placed under the test IDs (`check_submission.py`), never test GT. Kit times and box counts are cost measurements of our outputs, used only to meet our 400 s server-cost rule; no accuracy number of the test frames is involved | remote | state in the report: kit-time fits used the test clouds for cost only |
| S8-6 | **Hedges in the predictions.** Low-score duplicates (tail copies), each shifted 0.2 m (LUMPI Person, 4 per box for boxes scored >= 0.0841), 1.0 m (LUMPI Bus, 4 per box) or 0.15 m (V2X pedestrian), scored below every original box of the class. Score floors at 0.01. LUMPI predictions grow 23,270 -> 37,396 boxes. | Rules: none against it. Disqualification: "predictions whose distribution implies access to held-out ground truth" | a copy can only match a GT box that no original matched, so it uses the R40 interpolation, not test information. The rings of duplicates are visible to anyone who inspects the predictions. In use since R5 (Oct 15), in every entry since then | **low** (no rule touched; a reviewer could read it as metric engineering) | **disclose in the email (new item (h))** and in the report, with the proof that copies cannot lower AP and their measured share of the gain |
| S8-7 | Realism frames | Forbidden: probing the realism reference; FAQ: the 50 frames must be synthetic | byte-identical to the S7.6 (and S6/R5) frames in both zips; generator outputs chosen on legal proxies | remote (audit item 10) | none |
| S8-8 | Leaderboard use on Oct 30 | audit rule d; allowed: "resubmit your best system" | S8, S8.2 and S8.3 were pre-registered before their results. Every class decision came from local gates, not leaderboard per-class numbers. S8.3 was designed after `s8c` was scored, but chose its classes by realval-B localization loss and kit time; Car was never a candidate. The uploads and the F1 choice pick among complete systems by their combined score, which the site invites | remote | none |
| S8-9 | Upload counts | 5 per day, 100 total, one account | Oct 30: LUMPI 3 (1022250, 1022399, 1022492), V2X 1 (1022246); totals LUMPI 11, V2X 12 | none | none |
| S8-10 | Format and declaration | Submission page; FAQ | 50 frames of 50,000 x 3 float32 (600,000 bytes each); predictions validated by `check_submission.py --official` (LUMPI 361 s, V2X 128 s, both under 1,200 s); the declaration is the required statement verbatim, then `Team: KarmaRV` and the date | remote | optional: ask whether team and date suffice as the signature (Q5) |
| S8-11 | Repository and release contents | Terms 3; dataset licences (V2X-Real academic only, LUMPI CC BY-NC 3.0) | git tracks no point cloud, prior, label, kit file, forbidden-frame list or ID map. Release 8.0/8.1 assets are synthetic-trained checkpoints and our scored zips | remote | keep the repository private until the release excludes anything real-derived; the licence sign-off for a corporate entrant stays the entrant's (audit item 16) |

## 3. The email: revised Appendix A (send before the final phase opens)

Send Appendix A of the [2026-10-26 audit](2026-10-26-rules-compliance-audit.md) with these changes, best as a reply in the 2026-08-26 LOI thread.

In part 1, after (g), add:

> (h) **Test-time processing.** Every submitted box comes from our synthetic-trained detectors, processed as follows:
> - test-time augmentation over 8-12 views (flips, ±5° yaw, ±0.25 m height, global scale 0.95/1.05);
> - weighted box fusion across views, random seeds and detectors;
> - per-class score floors;
> - a minimum number of points per predicted box (V2X);
> - for walkers and buses, low-score duplicates of a detection shifted by 0.15-1.0 m, ranked below every original detection of their class.
>
> The duplicates can only add a match for a detection that is slightly misplaced; they cannot lower average precision. All settings are chosen on our validation frames. No test frame is used for anything but inference and checking the file before upload.

In part 2, keep Q1-Q4. Q3 (best or last final submission) is now the one that shapes the final-phase plan. Add:

> Q5. Our declaration.txt holds the required statement verbatim, followed by our team name and the date. Is that the signature you expect, or should we add a line with the entrant's name?

## 4. The final phase: mechanics and plan

**Mechanics** (re-read 2026-10-31):

| Item | Value | Consequence |
|---|---|---|
| Window | 2026-11-01 00:00 UTC (**Sat Oct 31, 19:00 CDT**) to 2026-11-15 00:00 UTC (**Sat Nov 14, 18:00 CST**; DST ends Nov 1) | 14 UTC days; the daily limit resets at 00:00 UTC (CodaBench) |
| Budget | 1 per day, 5 in total (pages; the API shows no total cap, so self-enforce 5) | at most 5 attempts per track |
| Scores | hidden until the close | no feedback: a final upload cannot confirm anything |
| Rule | `Force_Best` on the single Results leaderboard | the best final submission most likely counts; unconfirmed until Q3 is answered |
| Test data | the same test and reference data as the development phase | a development-scored zip scores the same again |
| Carry-over | none | F1 must be uploaded in the final phase |
| Limit | 1,200 s execution | our zips take 128-368 s locally |

**Plan, robust to Q3 either way.**

| Slot | When | LUMPI | V2X | Why |
|---|---|---|---|---|
| **F1** | Nov 1 (from Sat Oct 31, 19:00 CDT) | `lumpi_s8d_submission.zip` (1022492, 0.525688), the exact scored zip | `v2x_s8v_submission.zip` (1022246, 0.902153) | the best confirmed systems; under either rule this secures the development score |
| F2-F4 | Nov 6-12, one per day, only if a candidate passes every gate | a candidate (below) | a candidate, only if one exists | under `Force_Best` an unconfirmed candidate has no downside, apart from a slot |
| **F5** | Nov 13 (one day of slack before the close) | **the F1 zip again**, unless Q3 is answered "best counts" | the same | if the last submission counts, this keeps the confirmed score; if the best counts, it is harmless |

Fallbacks, all in releases 8.0 and 8.1 with IDENTICAL reproduction scripts: LUMPI `s8c` (1022399), then `s8b` (1022250); V2X `s7s` (1014682).

**Where improvements can still come from**, ranked by value, risk and fit to a final phase without feedback:
1. **Compliance first.** If the organizers rule against audit item 4 (walker label rows) or item 19 (frame statistics), contingency C1 or C2 of the 2026-10-26 audit replaces any score work. C1 means train-split-only priors; C2 means walkers placed from non-label sources. Either costs 1-2 days of 8 GPUs per track, then the F2-F4 slots carry the rebuilt entries. **This is why the email should go out now:** a ruling after about Nov 5 leaves little room.
2. **LUMPI realism (WP1 of the S8 record).** Our server EMD is 1.30 against 1.10 for both LUMPI challengers. R carries 0.4 of the score, and realism measured on the legal held-out proxies has transferred reliably since R3.
   - An EMD drop of 0.2 is about +0.01 R, or **+0.004 combined**. That is twice everything S8 bought on LUMPI.
   - It needs generator content (ground and background structure), a new frame selection on proxies 1-3, and the held-out check on proxies 4-5.
   - A new zip combines the new frames with the F1 predictions.
   - **The gate:** held-out R +0.005 or more on both proxies, no detection change, and the kit check.
3. **More views for the walker members** (a 20-view set: the 12 views plus ±5° yaw on the flips). S8 showed that view count helps LUMPI Person and V2X pedestrian, and that the gain transferred.
   - It costs a few GPU-hours per member, then the S8 swap and gates.
   - Expected about +0.001 on LUMPI. Valid only through the same pre-registered gates.
4. **Not recommended.** Relaxing the 400 s kit rule to buy more copies:
   - the local gains are +0.0002-0.0005;
   - the server time varies;
   - a timed-out final submission wastes one of five hidden slots.

   Also not recommended: unfreezing LUMPI Bicycle, Motorcycle or Bus, and any change chosen from development-phase per-class numbers (audit rules c and d still hold).

**Competitive position.**
- **LUMPI** leads by +0.0139 (Raj Patil 0.5118). We are ahead on detection by 0.022 mAP (+0.019 combined) and behind on realism by 0.010 R (-0.004).
- **V2X** leads by +0.090.
- A challenger can improve in the final phase without anyone seeing it. LUMPI realism is the one lever where both challengers are ahead, so WP1 is also the main defence.

## 5. After the final phase

| When | Item | Notes |
|---|---|---|
| each final upload | record like a development one | `codabench_<id>.json` (status, file, time; the score stays hidden until the close), the register, track README Section 9, root README Section 9 |
| Nov 15 | **the 4-8 page report** (every team) | source: `paper-bigdata2026/README.md` Sections 3-4, the decision records and the progression tracker. Include: where the 50 frames came from (FAQ), every real-data use of Section 3 and audit items 4 and 19, the test-time processing of S8-6, and the integrity practice (guard, pre-registration, train-split gates). Channel and template: Q4 |
| Nov 20 | camera-ready, "final report and solutions"; top-3 per track "must be ready to release code for verification" | prepare a verification bundle from release 8.1: code, the weights and the reproduction scripts (IDENTICAL from the release assets). It contains no real data, no kit file and no real-derived prior; the scripts that rebuild the priors from the public datasets go instead (V2X-Real is "All Rights Reserved") |
| Nov 25 | winners | |
| Dec 14-17 | IEEE BigData 2026, Phoenix (paper track for the top 3: up to 10 pages) | |

## 6. Next steps (the entrant's actions first)

1. **Send the email** (Section 3: Appendix A plus (h) and Q5), ideally before Sat Oct 31, 19:00 CDT. Record the reply verbatim in the 2026-10-26 audit.
2. **Re-read both forums** (login needed) for organizer posts after Oct 14. Before F1, re-read the Rules and Terms (the audit's Terms 7 note: terms may change before Nov 1).
3. **F1 on Nov 1:** upload `lumpi_s8d_submission.zip` and `v2x_s8v_submission.zip` unchanged (md5 `d5bd41769788c902b6e49095236aafd6` and `b9c82e3de0c37babf146549eeedabbf6`), then record both.
4. **Nov 1-7:** WP1 LUMPI realism, plus the 20-view walker probe if GPUs are free. Contingency C1/C2 takes priority if the ruling requires it.
5. **Nov 6-12:** F2-F4 only for versions that pass every gate.
6. **Nov 13:** F5 = the F1 zips again, unless Q3 says the best counts.
7. **Nov 15:** the report; Nov 20 the verification bundle.

**Decision.** The F1 zips stand. Nothing in S8 needs a withdrawal or a rebuild. The disclosure email, extended with (h), is the one open action, and it is time-critical.

## Addendum 2026-11-02: development extended, final phase moved

- **Dates (CodaBench API, 2026-11-02 01:25 UTC).** The organizers extended the development phase to 2026-11-06 04:59 UTC, at 10 submissions per day, because CodaBench was down from about Oct 21 to Oct 26. The final phase now runs:
  - LUMPI: 2026-11-06 05:00 to 11-16 04:59 UTC;
  - V2X: 2026-11-06 05:00 to 11-15 04:59 UTC.

  Each track allows 1 per day, 5 in total, with hidden scores and `Force_Best`. Uploads made since Nov 1 went to the development phase.
- **The plan of Section 4 moves with the dates.** F1 = the best confirmed development zip per track, on Nov 6 (UTC). F2-F4 follow the same gates. F5 = the F1 zips again on the last full day (LUMPI Nov 15, V2X Nov 14), unless Q3 is answered "best counts".
- **Organizer reply (2026-10-31)** to the entrant's email of 2026-10-30, which carried the declaration only: the declaration is received, and "no further action is needed"; including it in the zip is optional (our zips include it). This answers Q5. The disclosure items (a)-(h) and Q1-Q4 remain unsent.
- **The S9 plan** for the extra development days is [2026-11-02-s9-clean-twin-plan.md](2026-11-02-s9-clean-twin-plan.md).
