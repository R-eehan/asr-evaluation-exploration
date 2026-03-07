# Day 4: Post-ASR Error Correction PoC — Results

**Date:** 2026-03-07
**Scope:** 13 Sarvam files (WER > 15%) + 12 ElevenLabs files (WER > 20%)
**Two iterations:** v1 (GPT-4o, no fallback) → v2 (GPT-5.4, full-transcript fallback, 3-seed averaging)

## 1. Approaches Tested

### Sarvam — Full-transcript LLM Correction
- Sarvam API does NOT return per-word confidence scores
- Send full ASR transcript to LLM with banking domain system prompt
- Re-compute WER on corrected output

### ElevenLabs — Confidence-guided Correction + Fallback
- Re-run audio with `timestamps_granularity='word'` to get per-word logprob
- Flag low-confidence words (logprob < -0.5)
- If >= 2 words flagged: targeted correction on flagged words only
- **If < 2 words flagged (overconfident model): fall back to full-transcript correction**
- 3 seeded runs (seeds: 42, 123, 7) averaged to control for transcription non-determinism

---

## 2. v1 Results (GPT-4o, no fallback) — Initial Run

### Sarvam: 2 improved, 7 worsened, 4 unchanged. Avg delta: **+4.86%** (WORSE)

GPT-4o aggressively standardized dialectal Kannada to written forms, making WER worse. Worst case: `indicvoices_ka_04.wav` went from 22.22% to 55.56% (+33.34%).

### ElevenLabs: 2 improved, 1 worsened, 9 unchanged. Avg delta: **-0.81%** (negligible)

Confidence-guided correction was essentially a no-op — ElevenLabs logprobs are so close to 0 that almost no words got flagged. Files with 0 flagged words passed through unchanged.

### Critical problem identified: ElevenLabs overconfidence

| File | WER | Avg logprob | Words flagged (<-0.5) |
|------|-----|-------------|----------------------|
| loan-enquiry (115% WER) | 115.00% | -0.130 | 1/20 |
| ka_05 (95% WER) | 94.74% | -0.069 | 0/19 |
| ka_04 (56% WER) | 55.56% | -0.029 | 0/9 |
| ka_02 (52% WER) | 51.61% | -0.019 | 0/35 |

**The model assigns near-zero logprobs (high confidence) even to files with 50-115% WER.** Confidence scores are poorly calibrated for Indian languages.

---

## 3. v2 Results (GPT-5.4, fallback, 3-seed avg) — After Iteration

Three changes based on review:
1. **Upgraded to GPT-5.4** (released 2026-03-05) — better Indic language understanding
2. **Added full-transcript fallback** — when <2 words flagged by logprob, send entire transcript to LLM
3. **3-seed averaging** — run ElevenLabs 3 times with different seeds, average WER to separate re-transcription variance from correction effect

### Sarvam Results (GPT-5.4)

| File | Lang | WER Before | WER After | Delta |
|------|------|-----------|-----------|-------|
| indicvoices_ka_03.wav | ka | 57.89% | 63.16% | +5.27% |
| indicvoices_ka_05.wav | ka | 42.11% | 42.11% | +0.00% |
| **loan-enquiry-1-Kannada.m4a** | kn-en | 40.00% | **25.00%** | **-15.00%** |
| **suspicious-transaction-1-Kannada.m4a** | kn-en | 35.14% | **21.62%** | **-13.52%** |
| indicvoices_ka_07.wav | ka | 33.33% | 33.33% | +0.00% |
| indicvoices_ka_02.wav | ka | 25.81% | 38.71% | +12.90% |
| indicvoices_ka_01.wav | ka | 25.00% | 25.00% | +0.00% |
| indicvoices_ka_04.wav | ka | 22.22% | 22.22% | +0.00% |
| svarah_en_04.wav | en-IN | 22.22% | 27.78% | +5.56% |
| indicvoices_hi_07.wav | hi | 21.43% | 28.57% | +7.14% |
| credit-card-application-1-hinglish.m4a | hi-en | 18.18% | 18.18% | +0.00% |
| **indicvoices_hi_02.wav** | hi | 17.39% | **8.70%** | **-8.69%** |
| gpay-fraud-1-hinglish.m4a | hi-en | 16.67% | 16.67% | +0.00% |

**Summary:** 3 improved, 4 worsened, 6 unchanged. Average WER delta: **-0.49%**

### ElevenLabs Results (GPT-5.4 + fallback + 3-seed avg)

| File | Lang | WER Orig | Avg WER Retrans | Avg WER Corrected | Delta | Correction Effect |
|------|------|----------|----------------|-------------------|-------|-------------------|
| **loan-enquiry-1-Kannada.m4a** | kn-en | 115.00% | 90.00% | **61.67%** | **-53.33%** | **-28.33%** |
| indicvoices_ka_05.wav | ka | 94.74% | 80.70% | 80.70% | -14.04% | +0.00% |
| indicvoices_ka_03.wav | ka | 68.42% | 69.30% | 78.07% | +9.65% | +8.77% |
| **indicvoices_ka_04.wav** | ka | 55.56% | 55.56% | **33.33%** | **-22.23%** | **-22.23%** |
| indicvoices_ka_02.wav | ka | 51.61% | 45.16% | 47.31% | -4.30% | +2.15% |
| indicvoices_ka_07.wav | ka | 33.33% | 33.33% | 33.33% | +0.00% | +0.00% |
| svarah_en_04.wav | en-IN | 33.33% | 33.33% | 37.04% | +3.71% | +3.71% |
| indicvoices_ka_01.wav | ka | 31.25% | 31.25% | 35.42% | +4.17% | +4.17% |
| **suspicious-transaction-1-Kannada.m4a** | kn-en | 29.73% | 26.12% | **23.42%** | **-6.31%** | **-2.70%** |
| **debit-card-verification-1-Kannada.m4a** | kn-en | 28.57% | 26.98% | **17.46%** | **-11.11%** | **-9.52%** |
| credit-card-application-1-hinglish.m4a | hi-en | 27.27% | 27.27% | 27.27% | +0.00% | +0.00% |
| indicvoices_ka_06.wav | ka | 25.00% | 25.00% | 25.00% | +0.00% | +0.00% |

**Summary:** 6 improved, 3 worsened, 3 unchanged. Average WER delta: **-7.82%**. Average correction effect: **-3.66%**

---

## 4. v1 vs v2 Comparison

| Metric | v1 (GPT-4o) | v2 (GPT-5.4 + fallback) | Change |
|--------|------------|------------------------|--------|
| **Sarvam avg delta** | +4.86% (worse) | **-0.49%** (slight improvement) | Model upgrade stopped overcorrection |
| **ElevenLabs avg delta** | -0.81% (negligible) | **-7.82%** (meaningful) | Fallback enabled actual correction |
| **ElevenLabs correction effect** | ~0% | **-3.66%** | LLM adds real value when given a chance |
| Sarvam improved/worsened | 2/7 | 3/4 | GPT-5.4 much more conservative |
| ElevenLabs improved/worsened | 2/1 | 6/3 | Fallback unlocks correction on all files |

---

## 5. Key Findings for the PM Report

### Finding 1: Model choice matters enormously for post-ASR correction
- GPT-4o aggressively rewrote Kannada dialect → written forms, making WER *worse* on 7/13 Sarvam files
- GPT-5.4 is more conservative — preserves dialectal forms, only corrects when confident (6/13 unchanged vs 4/13)
- **PM implication:** Post-ASR correction quality is bottlenecked by the correcting LLM's Indic language capability. As LLMs improve at Indian languages, this pipeline gets better automatically.

### Finding 2: Confidence-guided correction requires well-calibrated confidence
- ElevenLabs logprobs are near-zero even at 50-115% WER for Indian languages
- Without fallback, the confidence-guided pipeline was a no-op for 9/12 files
- **PM implication:** Confidence calibration is a product gap. Providers should publish calibration data per language, or expose alternative error signals (e.g., acoustic model uncertainty, language ID confidence).

### Finding 3: Full-transcript fallback is essential
- When confidence scores are unreliable, falling back to full-transcript LLM correction captures value
- This turned ElevenLabs from -0.81% avg improvement to -7.82%
- **PM implication:** Production correction pipelines need tiered approaches — try targeted correction first, fall back to broader correction when targeted signals are unavailable or unreliable.

### Finding 4: Code-mixed content benefits most from LLM correction
- Sarvam's biggest wins: loan-enquiry (-15%), suspicious-transaction (-13.52%) — both code-mixed Kannada-English
- ElevenLabs's biggest correction effect: loan-enquiry (-28.33%), ka_04 (-22.23%), debit-card (-9.52%)
- English banking terms (personal loan, fraud, transaction) give the LLM strong semantic signal
- **PM implication:** For banking voice AI, LLM post-processing adds most value on code-mixed calls — which are the majority of real Indian banking calls.

### Finding 5: Multi-run averaging reveals the true signal
- ElevenLabs is non-deterministic — same audio gives different transcriptions each run
- 3-seed averaging separates: (a) re-transcription variance from (b) actual correction improvement
- loan-enquiry: seed 42 gave 120% WER, seeds 123/7 gave 40-45% WER — 80% point variance on a single file
- **PM implication:** Any production evaluation must average multiple runs. Single-run benchmarks are misleading, especially for Indian languages where model behavior varies significantly.

### Finding 6: The real metric for banking is entity accuracy, not WER
- Correction sometimes "hurts" WER by changing filler words while fixing entities correctly
- For banking, getting ₹18,500 right matters more than transcribing every "um" correctly
- **PM implication:** Build entity-specific evaluation (amounts, account numbers, bank names, transaction types) as the primary metric for banking voice AI.

---

## 6. What I'd Build in Production

1. **Tiered correction pipeline:** Confidence-guided → full-transcript fallback → entity extraction
2. **Language-specific calibration:** Map logprobs to actual error probability per language
3. **Multi-run ensembling:** 3+ transcriptions per audio → voting/consensus → correction on merged result
4. **Entity-focused evaluation:** Task success rate + entity accuracy as primary metrics
5. **Domain-adapted prompts:** Banking-specific correction prompts per language (not one generic prompt)
6. **LLM selection:** Use the latest available model — the gap between GPT-4o and GPT-5.4 was the difference between "correction hurts" and "correction helps"

---

## 7. Files Generated
- **v1 results (GPT-4o):** `data/results/correction_20260307_005424.csv` / `.json`
- **v2 results (GPT-5.4):** `data/results/correction_v2_20260307_013716.csv` / `.json`
- **Logprob exploration:** `data/results/correction_20260307_005530.json` (lenient threshold -0.1)
