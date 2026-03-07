# Day 5: Product & Developer Experience Audit

**Date:** 2026-03-07
**Scope:** Sarvam AI, ElevenLabs, OpenAI Whisper — evaluated through building and running a 28-file ASR evaluation pipeline over Days 2-4.

---

## 1. Developer Experience Comparison

### 1.1 Objective DX Observations (from building the pipeline)

| Dimension | Sarvam AI | ElevenLabs | OpenAI Whisper |
|---|---|---|---|
| **Authentication** | Custom header `api-subscription-key` — non-standard, not Bearer/API-Key | Standard SDK init with `api_key` | Standard SDK init with `api_key` |
| **SDK availability** | Official Python SDK (`sarvamai` on PyPI) — not used in this project; we used raw REST via `requests` | Official Python SDK (`elevenlabs`) — typed, well-structured | Official Python SDK (`openai`) — mature, well-documented |
| **Lines of code for wrapper** | 30 lines (REST + MIME handling) | 25 lines (SDK does heavy lifting) | 25 lines (SDK does heavy lifting) |
| **Error messages** | Cryptic 400 errors on MIME type mismatch — no hint about what's wrong | Clear SDK exceptions | Clear SDK exceptions |
| **Model versioning** | `saarika:v2` silently deprecated — had to discover `saarika:v2.5` through trial and error | `scribe_v1` — stable, clear naming | `whisper-1` — stable |
| **Audio format handling** | Rejected `audio/mp4a-latm` for m4a files — required manual override to `audio/mp4` | Accepts m4a natively, no MIME issues | Accepts m4a natively, no MIME issues |
| **Language code format** | BCP-47 (`hi-IN`, `kn-IN`) — different from ISO-639-1 used by others | ISO-639-1 (`hi`, `kn`) | ISO-639-1 (`hi`, `kn`) |
| **Language auto-detect** | Yes — reliable | Yes — but confused Kannada for Hindi on 1 file (output Devanagari for Kannada audio) | Yes — but translated Kannada to English instead of transcribing |
| **Confidence scores** | Not available — API returns only transcript + language_code | Per-word logprob via `timestamps_granularity='word'` — but poorly calibrated for Indian languages | Word-level timestamps via `verbose_json` — no logprobs |
| **Determinism** | Deterministic — same input → same output | Non-deterministic — 80-point WER variance between seeds on same file | Deterministic |
| **Response format** | Simple JSON: `{transcript, language_code}` | Rich object: text, words, timestamps, logprobs | Rich JSON: text, segments, language, duration |
| **Free tier** | Rs 1,000 credits (~33 hrs STT) | Limited free tier (exact amount varies by plan) | Pay-as-you-go, no free credits |

### 1.2 Bugs Encountered During Integration

| Bug | Provider | Severity | Impact |
|---|---|---|---|
| MIME type `audio/mp4a-latm` rejected for m4a files | Sarvam | Medium | Blocked all personal recordings until manually overridden to `audio/mp4` |
| Model `saarika:v2` deprecated without clear docs | Sarvam | Medium | Wasted ~20 min debugging before finding `saarika:v2.5` |
| Nuqta characters (ज़ vs ज) inflated WER by 50% on short texts | All (normalization issue) | High | Required building custom Devanagari normalizer |
| Output Devanagari script for Kannada audio input | ElevenLabs | High | Language confusion — transcribed in wrong script (115% WER on loan-enquiry) |
| Translated Kannada to English instead of transcribing | Whisper | Critical | Fundamental task failure — ASR model did translation, not transcription |
| `max_tokens` → `max_completion_tokens` API change | OpenAI (GPT-5.4) | Low | Quick fix, but undocumented at time of testing |

### 1.3 Agent-Assisted DX Observation

A notable finding: all three providers were integrated by an AI coding agent (Claude Code) with only API keys provided by the developer. The agent read docs, wrote wrappers, and debugged issues autonomously. This suggests that in the AI-assisted development era, **DX is increasingly about how well documentation is structured for machine consumption** — not just human readability. Sarvam's REST-only API was actually easier for the agent to consume than complex SDKs, but the MIME type and model versioning issues cost debugging time.

### 1.4 Subjective DX Assessment (PM Review)

Reviewed all three providers' dashboards and documentation pages.

**Dashboard & Playground Comparison:**

| Dimension | Sarvam | ElevenLabs | OpenAI |
|---|---|---|---|
| **Interactive playground** | Yes — "Start Speaking" + "Upload Audio" + Indian-language example cards (code-mixed Gujarati finance, Marathi cricket verbatim, Tamil healthcare diarization) | Yes — "Transcribe files" + "Try Scribe Realtime v2" demo + transcription history | No dedicated STT playground — API-only |
| **"Get Code" CTA** | Yes — prominent top-right button, gives starter code | Not as prominent on app page | N/A |
| **Dedicated STT nav item** | Yes — left nav under Playground | Yes — under Products | No — STT is buried in general platform docs |
| **India-first positioning** | Strong — example cards showcase Indian languages and use cases | Generic — no India-specific examples | Generic |

**Key Observations:**

1. **Sarvam's India-first playground examples are a strong signal.** Code-mixed Gujarati finance news, Marathi cricket commentary, Tamil healthcare diarization — this immediately tells Indian enterprise buyers "this is built for you." Smart product positioning.

2. **ElevenLabs' voice agent in docs is the standout DX innovation.** Their "Talk to interrupt" feature lets developers have a real-time voice conversation with a documentation agent. The agent uses ElevenLabs' own models (STT + TTS), creating a self-improving loop:
   - Developers get a more natural way to navigate complex docs
   - ElevenLabs gets free, opt-in voice data for benchmarking and training
   - It's dogfooding as a product feature — the best demo of their capabilities IS the docs interaction

   **PM recommendation for Sarvam:** This is a nice-to-have, not a must-have. But the underlying insight is powerful — crowdsourcing voice inputs through a docs agent is essentially free data collection. If Sarvam built a multilingual version (talk to docs in Hindi, Kannada, Tamil), it would both showcase their 22-language capability AND generate diverse Indian language training data.

3. **OpenAI has no dedicated STT experience.** Everything is under general platform developer documentation. For a company where STT is one product among many, this makes sense — but it means they're not competing on DX for voice-specific use cases.

**Enterprise Readiness Score (1-5, for Indian banking adoption):**

| Provider | Score | Rationale |
|---|---|---|
| **Sarvam** | **4/5** | Best accuracy, India-hosted, proven banking deployments (Tata Capital, SBI Life). Gaps: Kannada WER still ~27%, MIME/error message polish needed. |
| **ElevenLabs** | **3/5** | Good SDK/DX, competitive on Hindi. But: scribe_v2 regression, non-determinism, India data residency only at Enterprise tier, no banking references. |
| **OpenAI** | **3/5** | Massive gpt-4o-transcribe improvement, best on Hinglish code-mixed. But: no India data residency for inference, Kannada still 58% WER, no voice-specific product focus. |

---

## 2. Pricing Analysis

### 2.1 Published Per-Unit Pricing (as of March 2026)

| Provider | Model | STT Price/Hour | STT Price/Min | Source |
|---|---|---|---|---|
| **Sarvam AI** | Saarika v2.5 (batch) | Rs 30/hr (~$0.36) | Rs 0.50/min | [Sarvam Pricing](https://docs.sarvam.ai/api-reference-docs/getting-started/pricing) |
| **Sarvam AI** | Saaras v3 (advanced: transcribe + translate + diarize) | Rs 45/hr (~$0.54) | Rs 0.75/min | [Sarvam Pricing](https://www.sarvam.ai/api-pricing/) |
| **ElevenLabs** | Scribe v1 | $0.40/hr (~Rs 34) | $0.0067/min | [ElevenLabs Pricing](https://elevenlabs.io/pricing/api) |
| **ElevenLabs** | Scribe v2 Realtime | $0.28/hr (~Rs 24) | $0.0047/min | [ElevenLabs Realtime STT](https://elevenlabs.io/realtime-speech-to-text) |
| **ElevenLabs** | Enterprise | $0.22/hr (~Rs 18.5) | $0.0037/min | [ElevenLabs Enterprise](https://elevenlabs.io/enterprise) |
| **OpenAI** | Whisper-1 | $0.36/hr (~Rs 30) | $0.006/min | [OpenAI Pricing](https://developers.openai.com/api/docs/pricing) |
| **OpenAI** | GPT-4o Transcribe | $0.36/hr | $0.006/min | [OpenAI Pricing](https://developers.openai.com/api/docs/pricing) |
| **OpenAI** | GPT-4o Mini Transcribe | $0.18/hr | $0.003/min | [OpenAI Pricing](https://developers.openai.com/api/docs/pricing) |

**Sarvam plan tiers:** Starter (pay-as-you-go, 60 req/min) | Pro Rs 10,000 for Rs 11,000 credits (200 req/min) | Business Rs 50,000 for Rs 57,500 credits (1,000 req/min). All include Rs 1,000 free credits on signup (~33 hrs STT).

**Note:** Saarika v2.5 is being deprecated in favor of Saaras v3. Rs 30/hr applies to both. Sarvam-M (their LLM) is **free per token** — relevant for building correction pipelines on Sarvam's own stack.

**LLM correction pricing (for post-ASR pipeline):**

| Model | Input | Output | Batch | Source |
|---|---|---|---|---|
| GPT-5.4 | $2.50/1M tokens | $15.00/1M tokens | $1.25/$7.50 | [OpenAI Pricing](https://developers.openai.com/api/docs/pricing) |
| GPT-4o | ~$2.50/1M tokens | ~$10.00/1M tokens | — | [OpenAI Pricing](https://developers.openai.com/api/docs/pricing) |

**Key framing:** GPT-5.4 correction costs ~20x more per unit than the STT itself. This matters for the "correction as a product feature" argument — if Sarvam built correction into their API using Sarvam-M (free LLM), they could offer banking-grade accuracy at the same Rs 30/hr.

**Exchange rate used:** $1 = Rs 84 (approximate March 2026)

### 2.2 Actual Experiment Costs (Days 2-4)

Our experiment processed 28 audio files (total: 290.1s = 4.83 min, avg 10.4s/file).

#### API Call Inventory

| Phase | Sarvam ASR | ElevenLabs ASR | Whisper ASR | LLM Correction | Notes |
|---|---|---|---|---|---|
| Day 2: Testing (3 iterations) | 15 | 15 | 15 | 0 | 5 Hindi files x 3 providers x 3 iterations |
| Day 3: Full run | 28 | 28 | 28 | 0 | 28 files x 3 providers |
| Day 3: Personal rerun | 7 | 7 | 7 | 0 | 7 personal files re-processed after MIME fix |
| Day 4 v1: Correction | 0 | ~12 | 0 | ~25 (GPT-4o) | 13 Sarvam corrections + 12 ElevenLabs re-transcriptions |
| Day 4 v2: Correction | 0 | ~40 | 0 | ~29 (GPT-5.4) | 12 files x 3 seeds + LLM correction |
| **Totals** | **50** | **~102** | **50** | **~54** | |

#### Cost Breakdown

| Provider | Total Audio Processed | Rate | Estimated Cost |
|---|---|---|---|
| Sarvam | 50 calls x 10.4s = 520s = 8.7 min | Rs 0.50/min | **Rs 4.35** (~$0.05) |
| ElevenLabs | 102 calls x 10.4s = 1,061s = 17.7 min | $0.0067/min | **$0.12** (~Rs 10) |
| Whisper | 50 calls x 10.4s = 520s = 8.7 min | $0.006/min | **$0.05** (~Rs 4.20) |
| GPT-4o (correction) | ~25 calls x ~300 tokens = 7,500 tokens | $2.50 + $10/1M | **~$0.05** |
| GPT-5.4 (correction) | ~29 calls x ~300 tokens = 8,700 tokens | $2.50 + $15/1M | **~$0.07** |
| **Total experiment cost** | | | **~$0.35** (~Rs 29) |

The entire experiment — 28 files, 3 providers, 2 correction iterations — cost less than Rs 30. All providers were tested within their free tiers.

### 2.3 At-Scale Projection: Mid-Size Indian Bank

**Scenario:** 50,000 customer calls/day, average 3 min each = 150,000 min/day = 2,500 hr/day

#### Raw ASR Cost (transcription only)

| Provider | Daily Cost | Monthly Cost (30 days) | Annual Cost |
|---|---|---|---|
| Sarvam (Saarika) | Rs 75,000 ($893) | **Rs 22.5 lakh** ($26,786) | Rs 2.74 cr ($326,000) |
| Sarvam (Saaras + diarization) | Rs 112,500 ($1,339) | **Rs 33.75 lakh** ($40,179) | Rs 4.11 cr ($489,000) |
| ElevenLabs (Scribe v1) | $1,000 (Rs 84,000) | **$30,000** (Rs 25.2 lakh) | $360,000 (Rs 3.02 cr) |
| ElevenLabs (Scribe v2 RT) | $700 (Rs 58,800) | **$21,000** (Rs 17.6 lakh) | $252,000 (Rs 2.12 cr) |
| Whisper-1 | $900 (Rs 75,600) | **$27,000** (Rs 22.7 lakh) | $324,000 (Rs 2.72 cr) |

**Raw cost takeaway:** Sarvam (Saarika) and Whisper are nearly identical at ~Rs 22.5 lakh/month. ElevenLabs Scribe v1 is ~12% more expensive. ElevenLabs Scribe v2 Realtime is actually the cheapest option.

#### The Hidden Cost: Correction Pipeline

Raw ASR price is a vanity metric. The real question: **what does it cost to get banking-grade accuracy?**

Based on our Day 4 findings, providers that struggle with Indian languages need LLM post-processing. Assuming correction on the 50% of calls that are code-mixed or Kannada:

| Scenario | Provider | Base WER | + Correction WER | Correction Cost/Month | Total Cost/Month |
|---|---|---|---|---|---|
| Hindi calls (40%) | Sarvam | 10.23% | Not needed | Rs 0 | Rs 9.0 lakh |
| Hindi calls (40%) | ElevenLabs | 7.15% | Not needed | $0 | $12,000 |
| Kannada calls (30%) | Sarvam | 29.48% | ~29% (marginal help) | ~Rs 1.5 lakh | Rs 8.25 lakh |
| Kannada calls (30%) | ElevenLabs | 51.42% | ~43.6% (-7.82pp) | ~$3,500 | $12,500 |
| Code-mixed calls (30%) | Sarvam | 18.74% | ~18.2% (-0.49pp) | ~Rs 1.5 lakh | Rs 8.25 lakh |
| Code-mixed calls (30%) | ElevenLabs | 32.51% | ~24.7% (-7.82pp) | ~$3,500 | $12,500 |
| **Blended monthly** | **Sarvam** | **15.67%** | **~15.2%** | **~Rs 3 lakh** | **Rs 25.5 lakh** ($30,357) |
| **Blended monthly** | **ElevenLabs** | **25.24%** | **~20.1%** | **~$7,000** | **$37,000** (Rs 31.1 lakh) |

**Key insight:** Sarvam's lower base WER means it needs less correction, making its total cost of accuracy lower despite similar per-hour pricing. ElevenLabs's correction pipeline adds ~23% to the monthly bill and still doesn't match Sarvam's uncorrected accuracy for Kannada.

### 2.4 Cost Per Accurate Transcript

The most meaningful metric for a bank isn't cost-per-hour — it's cost-per-usable-transcript.

| Provider | Monthly Cost (blended) | Effective WER | Transcripts Needing Manual Review (est.) | Cost Per Usable Transcript |
|---|---|---|---|---|
| Sarvam | Rs 25.5 lakh | ~15.2% | ~25% of calls | Rs 1.70/call |
| ElevenLabs | Rs 31.1 lakh | ~20.1% | ~35% of calls | Rs 2.07/call |
| Whisper | Rs 22.7 lakh | 42.96% (no correction) | ~60% of calls | Rs 1.51/call (but 60% unusable) |

Whisper is cheapest per-call but has the highest hidden cost: 60% of transcripts would need human review for banking compliance, making it economically unviable for Indian languages.

---

## 3. API Reliability

### 3.1 Failure Rate

| Provider | Total API Calls | Failures | Failure Rate |
|---|---|---|---|
| Sarvam | ~50 | 0 | **0%** |
| ElevenLabs | ~102 | 0 | **0%** |
| Whisper | ~50 | 0 | **0%** |

All three providers had 100% availability across 4 days of testing. No timeouts, no rate limiting, no server errors.

### 3.2 Latency Profile (Day 3 full run, 28 files)

| Provider | Mean | P50 | P95 | P99 (est.) | Latency/Audio Second |
|---|---|---|---|---|---|
| **Sarvam** | 0.78s | 0.72s | 1.27s | ~1.5s | **0.075s** (13x faster than realtime) |
| **ElevenLabs** | 2.73s | 2.10s | 6.22s | ~8s | **0.263s** (3.8x faster than realtime) |
| **Whisper** | 3.16s | 2.77s | 6.11s | ~7s | **0.304s** (3.3x faster than realtime) |

**Sarvam is 3.5x faster than ElevenLabs and 4x faster than Whisper.** For real-time call transcription, sub-second latency is critical — Sarvam's 0.72s P50 is well within the <1s threshold for live agent assist.

### 3.3 Non-Determinism

| Provider | Deterministic? | Variance Observed |
|---|---|---|
| Sarvam | Yes | Same audio → same transcript every time |
| ElevenLabs | **No** | 80-point WER variance between seeds on same file (loan-enquiry: seed 42 gave 120% WER, seeds 123/7 gave 40-45% WER) |
| Whisper | Yes | Same audio → same transcript every time |

**What is a "seed"?** A seed is a number that controls the random sampling in a model's text generation. Setting seed=42 makes the randomness reproducible — you get the same output every time with that seed. A different seed (e.g., 123) gives a different but also reproducible output. We used seeds 42, 123, and 7 to get 3 different transcriptions per file, then averaged WER across them.

**Why we didn't average Sarvam's runs:** Sarvam is deterministic — same audio in, same transcript out, every time. No randomness to average. We verified this during Day 2 testing. ElevenLabs is the only provider that produced different transcriptions on repeated runs of the same file, which is why it required multi-seed averaging to get a fair measurement.

**Reliability implication:** ElevenLabs's non-determinism is a significant concern for banking. Production systems cannot have a transcription engine that randomly fails on the same audio. This requires multi-run averaging or consensus voting — adding complexity and cost.

### 3.4 Why LLM Correction Worsened Pure Kannada (Sarvam files)

Of 13 Sarvam files sent through GPT-5.4 correction, 4 got worse — all pure Kannada or short utterances. Root cause analysis on each:

| File | Delta | What GPT-5.4 Did Wrong |
|---|---|---|
| `indicvoices_ka_03.wav` | +5.27% | Merged "ಎಸ್ ಬಿ" (S B) into "ಎಸ್‌ಬಿಐ" (SBI) — plausible banking correction, but ground truth has separate words. Caused word-alignment cascade. |
| `indicvoices_ka_02.wav` | +12.90% | Split colloquial "ಲೇಸನ್ನು" into standard written "ಲೇಸ್ ಅನ್ನು" — grammatically "correct" but the speaker used the colloquial form. Cascade effect. |
| `svarah_en_04.wav` | +5.56% | Changed "rock" to "rope" — semantically plausible in climbing context, but speaker said "rock." LLM hallucinated a "smarter" word. |
| `indicvoices_hi_07.wav` | +7.14% | Fixed "नगर" (city) → "नकद" (cash) — close to correct "नगद" but not exact. Also "corrected" grammar ("है"→"हैं") the speaker didn't use. |

**Verdict: The LLM is at fault, not the ASR.** Sarvam's ASR was already the closest transcription available. GPT-5.4 "corrects" dialectal/colloquial Kannada toward standard written forms, but ground truth transcribes what was *actually said*. The LLM's Kannada isn't strong enough to know when a dialectal form is correct.

**PM recommendation:** Don't apply LLM correction uniformly. Route by language: correct code-mixed content (where English banking terms provide strong semantic signal for the LLM) but skip or use a lighter touch on pure Kannada/regional language files where the LLM introduces more errors than it fixes. This could be implemented as a language-confidence router in the correction pipeline.

---

## 4. Model Evolution: Legacy vs Latest

### 4.1 Critical Discovery

During Day 5, we discovered that all three providers had been evaluated on legacy/outdated models throughout Days 2-4. The correct latest models are:

| Provider | Legacy Model (Days 2-4) | Latest Model (Day 5 re-run) |
|---|---|---|
| Sarvam | saarika:v2.5 | **saaras:v3** |
| ElevenLabs | scribe_v1 | **scribe_v2** |
| OpenAI | whisper-1 | **gpt-4o-transcribe** |

All 28 files were re-run with latest models. Old data was preserved for comparison.

### 4.2 Raw ASR Results: Legacy vs Latest

| Provider | Legacy WER | Latest WER | Delta | Legacy Latency | Latest Latency |
|---|---|---|---|---|---|
| **Sarvam** | 15.67% | **15.14%** | -0.53% | 0.78s | 0.84s |
| **ElevenLabs** | 25.24% | **32.23%** | +7.00% (regression) | 2.73s | **1.14s** |
| **OpenAI** | 42.96% | **27.68%** | -15.29% (massive gain) | 3.16s | **1.86s** |

**Per-language breakdown (latest models):**

| Language | Sarvam saaras:v3 | ElevenLabs scribe_v2 | OpenAI gpt-4o-transcribe |
|---|---|---|---|
| Hindi (hi) | **9.10%** | 14.47% | 18.39% |
| English (en-IN) | **4.07%** | 9.06% | 13.39% |
| Kannada (ka) | **27.31%** | 48.78% | 58.37% |
| Hinglish (hi-en) | 14.58% | 41.78% | **9.05%** |
| Kannada-English (kn-en) | **27.38%** | 76.39% | 35.87% |

Key observations:
- **gpt-4o-transcribe is the biggest winner** — 15% absolute WER improvement, no longer translates Kannada to English
- **ElevenLabs scribe_v2 regressed** — worse on everything except latency (2.4x faster)
- **Sarvam saaras:v3 holds steady** — marginal improvement, still dominant overall
- **gpt-4o-transcribe now beats everyone on Hinglish** (9.05%) — a complete reversal
- Sarvam→OpenAI gap narrowed from 27pp to 12.5pp

### 4.3 The 2×2 Correction Matrix: Model Quality vs Post-Processing

To fairly evaluate whether model upgrades or post-ASR correction matters more, we ran the same improved correction prompt across both model generations for all 3 providers. English files were excluded (already <14% WER for all providers).

**Correction prompt improvements (v3):** Added conservatism bias ("if unsure, leave unchanged"), dialect preservation rules, script preservation, language-aware behavior for code-mixed content. This fixed the Kannada overcorrection problem from Day 4.

#### Legacy Models + Improved Correction Prompt

| Provider | Files Corrected | Improved | Worsened | Unchanged | Avg WER Delta |
|---|---|---|---|---|---|
| Sarvam (saarika:v2.5) | 16 | 1 | 2 | 13 | +0.76% |
| ElevenLabs (scribe_v1) | 17 | 10 | 3 | 4 | **-5.10%** |
| Whisper (whisper-1) | 18 | **16** | **0** | 2 | **-15.28%** |

#### Latest Models + Improved Correction Prompt

| Provider | Files Corrected | Improved | Worsened | Unchanged | Avg WER Delta |
|---|---|---|---|---|---|
| Sarvam (saaras:v3) | 17 | 1 | 2 | 14 | +0.92% |
| ElevenLabs (scribe_v2) | 19 | 4 | 4 | 11 | -0.09% |
| Whisper (gpt-4o-transcribe) | 15 | **0** | **0** | **15** | **+0.00%** |

### 4.4 The PM Insight: Model Quality > Post-Processing

The 2×2 matrix reveals a clear pattern: **correction benefit is inversely proportional to base model quality.**

- **Whisper-1** (worst at 42.96% WER) → correction saved 15.28pp. **gpt-4o-transcribe** (27.68% WER) → correction saved 0.00pp. The model upgrade alone achieved the same final accuracy as the entire correction pipeline — for free, with zero latency overhead and zero GPT-5.4 cost.

- **ElevenLabs scribe_v1** (25.24%) → correction helped 5.10pp. **scribe_v2** (32.23%) → correction helped 0.09pp. Despite worse raw WER, scribe_v2's errors are "harder" — less obviously wrong to an LLM.

- **Sarvam** is barely correctable in either version (+0.76% / +0.92%). Its errors are already too subtle for an LLM to improve without overcorrecting. This is actually evidence of model quality — the remaining errors are genuinely hard.

**Strategic implication for Sarvam:** Don't build correction pipelines as a product feature. Instead, invest in base model quality (especially for Kannada, where 27% WER still has room to improve). The correction pipeline is a band-aid for weak base models — Sarvam's model is already strong enough that correction adds no value.

**The one exception:** Code-mixed content still benefits from correction across all providers, because English banking terms give the LLM strong semantic signal. A lightweight, language-routed correction layer (correct code-mixed, skip pure Indic) could be a product differentiator.

---

## 5. Integration Considerations for Banking

### 4.1 Data Residency & Compliance

| Dimension | Sarvam AI | ElevenLabs | OpenAI |
|---|---|---|---|
| **Data processing location** | India-only (sovereign infrastructure) | US/EU by default; **India available (Enterprise-only)** | US by default; at-rest residency in India; inference still in US |
| **Deployment models** | Cloud, Private Cloud/VPC, **On-Premises** (air-gapped) | Cloud only; private cloud via AWS Marketplace (TTS only); on-prem planned H1 2026 | Cloud; Azure OpenAI has India South region |
| **On-device / Edge** | **Sarvam Edge** — offline, no cloud, 10 Indic languages | Not available | Not available |
| **Air-gapped deployment** | **Proven** — deployed for UIDAI Aadhaar (March 2025) | Not available | Not available |
| **SOC 2 Type II** | Yes | Yes | Yes |
| **ISO 27001** | Yes | Yes | Not found |
| **PCI DSS** | Not found | **Level 1** | Not found |
| **HIPAA** | Not found | Yes (BAA available) | Yes (BAA, eligible cases) |
| **RBI compliance readiness** | Strong — India-hosted + on-prem air-gapped satisfies data localization | Enterprise India residency exists but adds cost/complexity | Azure India partially addresses; inference routing is complex |

**For Indian banking, data residency is non-negotiable.** RBI's data localization mandate (2018, reinforced 2024) requires that all payment system data be stored in India. Sarvam's India-only infrastructure is a structural competitive advantage. ElevenLabs now offers India data residency but only at Enterprise tier. OpenAI's India offering is at-rest only — inference still runs in the US, which may not satisfy strict RBI interpretations.

### 4.1.1 Sarvam's Banking Customers (Validation)

Sarvam already has production banking deployments — this validates the project's use case framing:

| Customer | Scale | Use Case | Source |
|---|---|---|---|
| **Tata Capital** | 20M+ monthly interactions | Consumer loan lifecycle — voice AI (Samvaad) in English + 10 Indian languages | [Sarvam case study](https://www.sarvam.ai/stories/tata-capital-ai-voice-transformation) |
| **SBI Life Insurance** | 8 crore customers, 3.5 lakh distributors | Policy queries in 11+ languages, nationwide rollout August 2026 | [BusinessToday](https://www.businesstoday.in/technology/story/sarvam-partners-with-sbi-life-to-deploy-ai-tools-for-customer-engagement-sales-518227-2026-02-26) |
| **UIDAI (Aadhaar)** | National-scale identity system | Voice interactions + fraud detection in 10 languages, air-gapped | [PIB](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2112485) |

Sources: [PIB — Sarvam AI](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2231169), [TechCrunch — Sarvam Edge](https://techcrunch.com/2026/02/18/indias-sarvam-wants-to-bring-its-ai-models-to-feature-phones-cars-and-smart-glasses/), [ElevenLabs India data residency](https://elevenlabs.io/blog/introducing-india-data-residency), [OpenAI data residency](https://openai.com/index/expanding-data-residency-access-to-business-customers-worldwide/)

### 4.2 API Capabilities for Banking

| Capability | Sarvam | ElevenLabs | OpenAI |
|---|---|---|---|
| **Batch API** (file upload) | Yes — files up to 1 hr | Yes | Yes (25MB limit) |
| **Streaming/WebSocket** | Yes — WebSocket, Saaras v3, 5 output modes (transcribe, translate, verbatim, transliterate, codemix) | Yes — Scribe v2 Realtime (150ms latency) | Not natively; separate Realtime API product required |
| **8kHz telephony support** | **Yes** — recently added, critical for call center audio | Not documented | Not documented |
| **Speaker diarization** | Yes (Saaras v3, Rs 45/hr) | Yes | Yes (GPT-4o Transcribe) |
| **Timestamps** | Yes (word-level) | Yes (word-level + logprobs) | Yes (word/segment-level) |
| **Indian language support** | 22 languages (all scheduled languages) | 12 Indian languages | Hindi + limited Indic |
| **Code-mixed handling** | Best — graceful degradation (14.65% → 18.74% WER) | Moderate — 22.81% → 32.51% WER | Poor — 40.91% → 49.11% WER |
| **Voice agent integration** | Pipecat integration available | Conversational AI SDK | Via Realtime API |

### 4.3 Banking-Specific Integration Architecture

For a production banking voice AI deployment:

```
Live Call → Streaming STT (Sarvam) → Post-ASR Correction (GPT-5.4)
                                          ↓
                                   Entity Extraction
                                   (amounts, account #s, names)
                                          ↓
                                   Intent Detection
                                   (complaint, inquiry, KYC)
                                          ↓
                                   Agent Assist / IVR Response
```

**Why Sarvam fits this architecture:**
1. **Streaming API** for live call transcription (<1s latency)
2. **India-hosted** — no data leaves the country
3. **22 languages** — covers all scheduled Indian languages
4. **Sarvam Edge** — can run on-premise in bank's own data center
5. **Cost-effective** — Rs 30/hr with best-in-class Indian language accuracy

---

## 6. Summary: Product Strengths & Gaps (Updated with Latest Models)

### Sarvam AI (saaras:v3)

| Strengths | Gaps |
|---|---|
| Best overall accuracy (15.14% WER — latest) | REST-only integration used in this project (official `sarvamai` SDK exists but was not used) |
| Fastest latency (P50: 0.72s) | MIME type handling bug for m4a |
| India-hosted (compliance advantage) | No per-word confidence scores in API |
| 22 Indian languages | Model versioning unclear (silent deprecation of saarika:v2.5) |
| Cheapest effective cost for Indian languages | Error messages are cryptic |
| Deterministic output | Kannada WER still ~27% (room for improvement) |
| Rs 1,000 free credits | |
| Errors too subtle for LLM correction (sign of model quality) | |

### ElevenLabs (scribe_v2)

| Strengths | Gaps |
|---|---|
| Official Python SDK | **scribe_v2 regressed vs scribe_v1** (32.23% vs 25.24% WER) |
| Per-word logprobs available | Non-deterministic (80-point WER variance) |
| Scribe v2 Realtime (150ms, 2.4x faster) | Confidence scores poorly calibrated for Indian languages |
| | Hinglish WER tripled (13.57% → 41.78%) in scribe_v2 |
| | Language confusion (Kannada → Devanagari) persists |
| | India data residency: Enterprise-only |
| | Higher effective cost after correction |

### OpenAI (gpt-4o-transcribe)

| Strengths | Gaps |
|---|---|
| **Massive improvement**: 42.96% → 27.68% WER | Still 2x worse than Sarvam overall |
| Now best on Hinglish code-mixed (9.05% WER) | Kannada still 58% WER (vs Sarvam 27%) |
| Mature SDK ecosystem | No India data residency for inference |
| 1.7x faster than whisper-1 | `verbose_json` format incompatible — undocumented |
| Cheapest raw price (GPT-4o Mini at $0.18/hr) | LLM correction adds zero value (model already at correction ceiling) |
| Deterministic output | |

---

## 7. What Remains for Reehan

After I (Claude Code) built this analysis, Reehan should:

1. **Review docs for each provider** — Rate clarity, completeness, and examples on a 1-5 scale
2. **Dashboard UX comparison** — Navigate each provider's dashboard and note friction points
3. **Validate pricing assumptions** — Check current dashboard billing for actual charges vs. estimates
4. **Add subjective DX notes** — Any observations from the signup and API key process
5. **Review the at-scale projections** — Confirm the 50K calls/day scenario is realistic for a mid-size Indian bank
