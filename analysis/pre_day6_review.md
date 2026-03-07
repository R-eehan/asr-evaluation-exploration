# Pre-Day-6 Review: Agent Team Findings & Corrections

**Date:** 2026-03-07
**Process:** Two-agent parallel review (Critique Agent + Domain Expert Agent), synthesized by lead agent, verified with data.

---

## Critical Finding: Script Mismatch Bias (C1)

### What was wrong

ElevenLabs scribe_v2 outputs English loanwords in Latin script ("credit card") while ground truth uses native script ("क्रेडिट कार्ड"). Our WER normalizer didn't transliterate across scripts, systematically inflating ElevenLabs' code-mixed WER.

### Verification

Spot-checked 3 code-mixed files — ElevenLabs had 31-65% Latin characters in output; Sarvam and Whisper had 0-6%.

### Impact on WER (Code-Mixed Files Only)


| Provider   | Model             | Raw WER | Script-Normalized WER | Delta        |
| ---------- | ----------------- | ------- | --------------------- | ------------ |
| Sarvam     | saaras:v3         | 20.06%  | 20.06%                | 0.00pp       |
| ElevenLabs | scribe_v2         | 56.61%  | **17.01%**            | **-39.60pp** |
| Whisper    | gpt-4o-transcribe | 20.55%  | 19.90%                | -0.65pp      |


After normalization, ElevenLabs goes from worst to best on code-mixed content.

### scribe_v1 had no script bias

scribe_v1 output everything in native script (0.00pp normalization delta). scribe_v2 changed behavior to output English words in Latin. The "scribe_v2 regression" (25.24% → 32.23% overall WER) was partially a format change, not a quality drop.

### scribe_v1 → scribe_v2 (script-normalized, code-mixed)


| File                           | scribe_v1 | scribe_v2 | Delta   |
| ------------------------------ | --------- | --------- | ------- |
| credit-card (hi-en)            | 27.3%     | 13.6%     | -13.6pp |
| gpay-fraud (hi-en)             | 16.7%     | 12.5%     | -4.2pp  |
| loan-enquiry (kn-en)           | 115.0%    | 35.0%     | -80.0pp |
| suspicious-transaction (kn-en) | 29.7%     | 10.8%     | -18.9pp |


scribe_v2 is substantially better after removing script bias.

---

## Entity Accuracy (New Metric)

Banking-specific entity accuracy across 7 code-mixed personal recordings, 41 entities (amounts, card types, banking terms, names).

### Latest Models


| Provider                  | Entity Accuracy  |
| ------------------------- | ---------------- |
| ElevenLabs scribe_v2      | **41/41 (100%)** |
| Sarvam saaras:v3          | 40/41 (97.6%)    |
| Whisper gpt-4o-transcribe | 34/41 (82.9%)    |


### Legacy Models


| Provider             | Entity Accuracy |
| -------------------- | --------------- |
| ElevenLabs scribe_v1 | 29/41 (70.7%)   |
| Sarvam saarika:v2.5  | 37/41 (90.2%)   |
| Whisper whisper-1    | 22/41 (53.7%)   |


### Improvement: Legacy → Latest


| Provider   | Delta   |
| ---------- | ------- |
| ElevenLabs | +29.3pp |
| Whisper    | +29.2pp |
| Sarvam     | +7.4pp  |


Sarvam was already high; ElevenLabs and Whisper closed the gap dramatically.

---

## Corrections for Day 6 Report

### Must fix

1. **Present code-mixed WER in three layers:** Raw WER, script-normalized WER, and entity accuracy. Frame as "which metric matters depends on deployment context."
2. **Retract "ElevenLabs struggles with code-mixed" claim.** Replace with: "ElevenLabs achieves 17.01% script-normalized WER but outputs English words in Latin script, a gap for native-script-required deployments."
3. **Retract "scribe_v2 regression" claim.** Replace with nuanced finding: scribe_v2 changed script output behavior; actual transcription quality improved.
4. **Update pricing table** to use latest model WER numbers (currently uses legacy).
5. **Fix latency claim:** "3.5x faster" uses legacy numbers. With latest models, Sarvam is 1.36x faster (0.84s vs 1.14s).

### Should address

1. **Acknowledge non-banking public data:** Most IndicVoices clips are about cooking, sports, shopping — not banking. Personal recordings are the true banking-specific test data.
2. **Acknowledge code-mixed = personal recordings confound (C2):** Can't separate code-mixing effects from recording source effects.
3. **Acknowledge sample size limitations more prominently:** n=7 per language, n=3 for kn-en. Add per-finding sample sizes.
4. **Note S5 (noisy environment) was dropped** and why.
5. **Add Google Cloud STT** as acknowledged missing competitor with explanation for exclusion.
6. **Fix section numbering:** Day 5 Section 5 uses 4.x numbering.
7. **Acknowledge Sarvam SDK exists** — DX comparison used raw REST; SDK would likely have avoided MIME bug.

### Add to report

1. **Whatfix → speech AI bridge paragraph** — connect element detection experience to speech evaluation methodology.
2. **"What I don't know" section** — intellectual honesty about streaming, diarization, noise, production speech AI.
3. **Voice of India benchmark reference** — position project findings as extending the public benchmark.
4. **Quantify the Kannada opportunity** — 60M speakers, major banks, specific WER target.

---

## 2x2 Correction Matrix (Updated Interpretation)

The correction matrix insight is strengthened by the script discovery:


|                           | Base Quality               | Correction Delta        | Interpretation                  |
| ------------------------- | -------------------------- | ----------------------- | ------------------------------- |
| Sarvam (both versions)    | High                       | +0.76% / +0.92% (worse) | Too good to correct             |
| ElevenLabs scribe_v1      | Medium                     | -5.10%                  | Genuine errors correctable      |
| ElevenLabs scribe_v2      | High (after normalization) | -0.09%                  | Too good to correct             |
| Whisper whisper-1         | Low                        | -15.28%                 | Lots to correct                 |
| Whisper gpt-4o-transcribe | Medium-high                | +0.00%                  | Model upgrade = free correction |


The PM insight holds: **correction benefit is inversely proportional to base model quality.** The scribe_v2 correction delta (-0.09%) now makes perfect sense — the base model was already accurate.

---

## Agent Review Strengths (what's already strong)

1. The 2x2 correction matrix and "model quality > post-processing" insight
2. ElevenLabs overconfidence finding (logprobs poorly calibrated for Indian languages)
3. Cost-per-accurate-transcript framing
4. Personal recordings as original test data
5. CER vs WER insight for Indian languages
6. Sarvam-specific awareness (customers, Edge, sovereign positioning)

---

## Post-Day-6 Quality Gate

After the Day 6 report is fully drafted, run one final review agent on the complete report as a pre-submission quality check. This is the right place for a second review pass — review the finished artifact, not intermediate corrections. The agent should verify:

- All 16 corrections/additions from this review are addressed
- Numbers in the report match the raw data
- The script normalization narrative is presented clearly (both raw + normalized WER)
- The framing is "opportunities not criticisms" throughout
- No remaining definitive language where caveats are needed (sample size, confounds)

---

## Files Generated

- `src/metrics/script_normalize.py` — Script normalization module
- `src/recompute_codemixed_wer.py` — Re-computation runner
- `data/results/script_normalized_wer.json` — Full results with entity accuracy

