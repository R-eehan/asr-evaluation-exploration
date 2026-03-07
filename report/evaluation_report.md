# Voice AI for Indian banking: a product evaluation

**Reehan Ahmed** | March 2026 | [GitHub Repository](https://github.com/reehan-ahmed/sarvam-speech-eval)

## Executive summary

India's banking sector processes over [10 million customer complaints annually](https://rootle.ai/blog/voice-ai-for-indian-call-centers/), increasingly through voice channels where customers naturally code-mix (switch between languages mid-sentence), blending Hindi-English or Kannada-English. I evaluated three speech-to-text providers (Sarvam AI saaras:v3, ElevenLabs scribe_v2, and OpenAI gpt-4o-transcribe) across 28 audio files spanning 5 languages, including 7 original code-mixed banking recordings I created as test data.

There's no single winner: **which provider is "best" depends entirely on which metric you optimize for.** Sarvam leads on overall WER (15.14%), Whisper leads on Hinglish code-mixed (9.05% WER), and ElevenLabs leads on banking entity accuracy (41/41, 100%), but only after accounting for a script mismatch bias that inflated its raw code-mixed WER by 40 percentage points. A post-ASR correction proof-of-concept revealed that **model quality matters more than post-processing**: upgrading from whisper-1 to gpt-4o-transcribe delivered the same WER improvement as an entire LLM correction pipeline, for free.

For Sarvam, the opportunity is clear: dominant Indian language accuracy, India-hosted infrastructure, and proven banking deployments ([Tata Capital](https://www.sarvam.ai/stories/tata-capital-ai-voice-transformation), [SBI Life](https://www.businesstoday.in/technology/story/sarvam-partners-with-sbi-life-to-deploy-ai-tools-for-customer-engagement-sales-518227-2026-02-26)) position it well. But Kannada WER at 27% and the absence of per-word confidence scores are specific gaps worth closing.

## 1. The enterprise problem

Indian banking is the largest concrete voice AI opportunity in the country:

- **Scale:** [95 Indian banks received 10M+ complaints in FY23-24](https://rootle.ai/blog/voice-ai-for-indian-call-centers/). RBI is actively pushing AI adoption for customer service.
- **Market:** India's call center AI market is projected to grow from $103.8M (2024) to $452.5M by 2030. The voice assistant market is on a [35.7% CAGR trajectory toward $957M by 2030](https://www.nextmsc.com/news/india-voice-assistant-market).
- **The code-mixing reality:** Real Indian banking calls are not monolingual. A customer in Bangalore might say: "ನಮಸ್ಕಾರ sir, ನಿಮ್ personal loan enquiry ಬಗ್ಗೆ call ಮಾಡ್ತಾ ಇದೀನಿ" (namaskara sir, nim personal loan enquiry bagge call madta idini). Any speech AI system that can't handle this is solving the wrong problem.
- **Compliance pressure:** RBI's data localization mandate requires payment system data to stay in India, making the choice of speech AI provider a compliance decision, not just a technical one.

The [Voice of India benchmark](https://smestreet.in/technology/global-speech-ai-struggles-to-understand-india-new-national-benchmark-voice-of-india-reveals-11110091) (February 2026) confirmed what practitioners already knew: global speech AI models struggle with Indian languages. Indo-Aryan languages (Hindi, Bengali) achieve ~5-6% WER, but Dravidian languages (Tamil, Telugu, Kannada) sit at ~15-20% WER, a gap that directly impacts banking coverage in South India.

My work on element detection at Whatfix, iteratively improving Finder algorithm accuracy from 15% failure to under 2%, taught me that domain-specific evaluation is the foundation of model improvement. I applied the same thinking here: start from the enterprise problem, build a measurement framework, and let the data tell the story.

## 2. Methodology

### 2.1 Test data (n=28)


| Source                                                                           | Files | Languages                         | Content                                                                                                                                     |
| -------------------------------------------------------------------------------- | ----- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **[IndicVoices](https://ai4bharat.iitm.ac.in/datasets/indicvoices)** (AI4Bharat) | 14    | Hindi (7), Kannada (7)            | Diverse topics: cooking, sports, shopping, complaints. Not banking-specific.                                                                |
| **[Svarah](https://huggingface.co/datasets/ai4bharat/Svarah)** (AI4Bharat)       | 7     | Indian English                    | Indian-accented English queries including banking scenarios                                                                                 |
| **Personal recordings**                                                          | 7     | Hinglish (4), Kannada-English (3) | Original code-mixed banking conversations I recorded: credit card applications, GPay fraud reports, loan enquiries, suspicious transactions |


**Important caveats:**

- **Sample size is small.** n=7 per language, n=3 for Kannada-English. These results are directional, not statistically significant. Per-finding sample sizes are noted throughout.
- **Public data is not banking-specific.** Most IndicVoices clips cover everyday topics. The 7 personal recordings are the true banking-domain test data. Results on public data show general Indian language capability, not banking-specific performance.
- **Code-mixed = personal recordings (confound caveat 2).** All code-mixed files are personal recordings and all personal recordings are code-mixed. I can't fully separate the effect of code-mixing from recording source/quality differences.
- **S5 (noisy environment) was dropped.** The original plan included a noisy environment scenario. I cut it to focus evaluation time on the higher-signal language and code-mixing dimensions.
- **Google Cloud STT was not tested.** Google offers competitive Indian language ASR but was excluded to keep the evaluation focused on three providers with distinct positioning (sovereign Indian AI, global speech specialist, general AI platform).

### 2.2 Providers evaluated


| Provider       | Model (latest)    | Model (legacy) | Indian languages             |
| -------------- | ----------------- | -------------- | ---------------------------- |
| **Sarvam AI**  | saaras:v3         | saarika:v2.5   | 22 (all scheduled languages) |
| **ElevenLabs** | scribe_v2         | scribe_v1      | 12 Indian languages          |
| **OpenAI**     | gpt-4o-transcribe | whisper-1      | Hindi + limited Indic        |


All providers were tested with both legacy and latest models. Legacy model results were preserved for comparison; **latest model results** are the primary numbers used throughout this report.

### 2.3 Metrics


| Metric                         | What it measures                                                              | Why it matters                                                                                                                                      |
| ------------------------------ | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **WER (Word Error Rate)**      | Word-level transcription accuracy                                             | Standard benchmark; but misleading for Indian Dravidian languages where one wrong character can flip an entire word                                 |
| **CER (Character Error Rate)** | Character-level accuracy                                                      | Better signal for Indian languages: a 29% WER in Kannada with only 11% CER means errors are minor character differences, not complete word failures |
| **Script-normalized WER**      | WER after transliterating Latin script English loanwords to native script     | Essential for fair comparison when providers output English words in different scripts (see Section 3.4)                                            |
| **Entity accuracy**            | Did the model correctly capture banking entities: amounts, card types, terms? | The metric that actually matters for banking: getting "₹18,500" and "credit card" right is more important than transcribing every filler word       |
| **Latency**                    | API response time (p50, p95)                                                  | Sub-second latency is required for live call transcription and agent assist                                                                         |


**Normalization:** All WER/CER computations use a custom Indic normalizer that handles Unicode NFC, nuqta stripping (ज़→ज, za→ja), chandrabindu→anusvara (ँ→ं, chandrabindu→anusvara), and punctuation removal. Without this, character-level script variations **inflate WER by up to 50%** on short texts.

## 3. ASR results

### 3.1 Overall performance (latest models, n=28)


| Provider       | Model             | Mean WER   | Mean CER | Mean latency |
| -------------- | ----------------- | ---------- | -------- | ------------ |
| **Sarvam**     | saaras:v3         | **15.14%** | 6.67%    | **0.84s**    |
| **OpenAI**     | gpt-4o-transcribe | 27.68%     | 14.61%   | 1.86s        |
| **ElevenLabs** | scribe_v2         | 32.23%     | 20.76%   | 1.14s        |


Sarvam leads on raw WER by a wide margin, especially on Indian languages. But the overall numbers hide an important story. Before diving into the per-language breakdown, it's worth seeing how much the competitive picture changed in a single model generation.

### 3.2 How much changed in one model generation

Each provider released a new model during or just before this evaluation. The deltas are striking:


| Provider   | Legacy model (WER)     | Latest model (WER)                       | WER delta    | Latency delta |
| ---------- | ---------------------- | ---------------------------------------- | ------------ | ------------- |
| Sarvam     | saarika:v2.5 (15.67%)  | saaras:v3 (15.14%)                       | -0.53pp      | +0.06s        |
| ElevenLabs | scribe_v1 (25.24%)     | scribe_v2 (32.23% raw / ~22% normalized) | See 3.5      | **-1.59s**    |
| OpenAI     | whisper-1 (42.96%)     | gpt-4o-transcribe (27.68%)               | **-15.29pp** | **-1.31s**    |


- **OpenAI** made the largest leap. whisper-1 translated Kannada to English instead of transcribing it (105% WER on one file). gpt-4o-transcribe fixes this entirely and now beats all providers on Hinglish.
- **ElevenLabs** traded latency for a script format change: 2.4x faster with scribe_v2, but outputs English words in Latin script instead of native script. This makes its raw WER look worse, but actual quality improved (more on this in Section 3.5).
- **Sarvam** was already strong and stayed strong. Marginal improvement, suggesting saarika:v2.5 was already well-optimized.

The Sarvam-to-OpenAI gap narrowed from 27pp to 12.5pp. If this trajectory continues, OpenAI could close the gap within 1-2 more model generations on monolingual Indian languages, though Sarvam's advantage on Kannada (27% vs 58%) remains substantial.

This context matters for the rest of the results: when I reference "legacy" vs "latest" models, these are the jumps we're talking about.

### 3.3 Per-language breakdown (latest models)


| Language                | n   | Sarvam saaras:v3 | ElevenLabs scribe_v2 | Whisper gpt-4o-transcribe |
| ----------------------- | --- | ---------------- | -------------------- | ------------------------- |
| Hindi (hi)              | 7   | **9.10%**        | 14.47%               | 18.39%                    |
| Indian English (en-IN)  | 7   | **4.07%**        | 9.06%                | 13.39%                    |
| Kannada (ka)            | 7   | **27.31%**       | 48.78%               | 58.37%                    |
| Hinglish (hi-en)        | 4   | 14.58%           | 41.78%               | **9.05%**                 |
| Kannada-English (kn-en) | 3   | **27.38%**       | 76.39%               | 35.87%                    |


Three patterns emerge:

1. **Sarvam dominates monolingual Indian languages.** Best on Hindi, English, Kannada, and Kannada-English. The gap is especially large on Kannada: Sarvam's 27% WER versus Whisper's 58% WER.
2. **Whisper wins Hinglish code-mixed (9.05%).** A complete reversal from legacy whisper-1, which scored 24.3% on the same files. gpt-4o-transcribe is the biggest single-generation improvement across all providers tested.
3. **ElevenLabs' code-mixed numbers look terrible, but this is misleading.** The 41.78% Hinglish and 76.39% Kannada-English WER are largely artifacts of a script mismatch bias, not transcription quality.

### 3.4 The script mismatch discovery

ElevenLabs scribe_v2 outputs English loanwords in Latin script ("credit card") while the ground truth and other providers use native script ("क्रेडिट कार्ड" / credit card). Our WER normalizer didn't transliterate across scripts, systematically inflating ElevenLabs' code-mixed WER.

Spot-checking confirmed the pattern: ElevenLabs output contained 31-65% Latin characters on code-mixed files; Sarvam and Whisper had 0-6%.

**Code-mixed WER presented in three layers (n=7 personal recordings):**


| Provider                  | Raw WER | Script-normalized WER | Entity accuracy  |
| ------------------------- | ------- | --------------------- | ---------------- |
| Sarvam saaras:v3          | 20.06%  | 20.06%                | 40/41 (97.6%)    |
| ElevenLabs scribe_v2      | 56.61%  | **17.01%**            | **41/41 (100%)** |
| Whisper gpt-4o-transcribe | 20.55%  | 19.90%                | 34/41 (82.9%)    |


Entity accuracy also improved across model generations (from the legacy models in Section 3.2 to their latest versions): ElevenLabs jumped from 70.7% to 100% (+29.3pp), Whisper from 53.7% to 82.9% (+29.2pp), and Sarvam from 90.2% to 97.6% (+7.4pp). Model upgrades are the strongest lever for banking accuracy.

After script normalization, ElevenLabs goes from **worst to best on code-mixed content**. It captures every single banking entity correctly (amounts, card types, transaction terms, city names) across all 7 recordings. The "which metric matters" question is a deployment decision:

- **Native-script-required deployments** (compliance forms, Indic language displays): ElevenLabs' Latin script output is a gap. Raw WER is the relevant metric.
- **Entity extraction pipelines** (intent detection, routing, agent assist): Entity accuracy is what matters. ElevenLabs' 100% entity accuracy is the strongest result.
- **Downstream NLP in any script**: Script-normalized WER is the fair comparison. ElevenLabs' 17.01% leads all providers.

### 3.5 The "scribe_v2 regression", a correction

Early runs showed scribe_v2 performing worse than scribe_v1 on raw WER (32% vs 25%). This looked like a regression. It wasn't.

scribe_v1 output everything in native script (0.00pp normalization delta), while scribe_v2 changed behavior to output English words in Latin script. On code-mixed files with script normalization applied:


| File                           | scribe_v1 WER | scribe_v2 WER (normalized) | Delta   |
| ------------------------------ | ------------- | -------------------------- | ------- |
| credit-card (hi-en)            | 27.3%         | 13.6%                      | -13.6pp |
| gpay-fraud (hi-en)             | 16.7%         | 12.5%                      | -4.2pp  |
| loan-enquiry (kn-en)           | 115.0%        | 35.0%                      | -80.0pp |
| suspicious-transaction (kn-en) | 29.7%         | 10.8%                      | -18.9pp |


scribe_v2 is substantially better after accounting for the script format change. The "regression" was a format change, not a quality drop.

### 3.6 CER vs WER: why WER alone is misleading for Indian languages


| Language        | Sarvam WER | Sarvam CER | Ratio |
| --------------- | ---------- | ---------- | ----- |
| Hindi           | 9.10%      | 3.52%      | 2.6x  |
| Kannada         | 27.31%     | 12.97%     | 2.1x  |
| Kannada-English | 27.38%     | 9.97%      | 2.7x  |


Kannada's 27% WER sounds alarming, but the 13% CER tells a different story. The errors are minor character differences: dialectal forms like "ಅದರಲ್ಲಿ" (adaralli) vs "ಅದ್ರಲ್ಲಿ" (adralli), not complete word failures. For banking applications, most of these minor variations don't affect entity extraction or intent detection. **CER should be the primary quality signal** for agglutinative Indian languages.

## 4. When the numbers are bad, what can you actually do?

The ASR results raised an obvious PM question: when transcription quality is poor on certain languages, what levers do you have? Unlike LLMs, where you can iterate on a system prompt to improve output, ASR models are black boxes. Audio goes in, text comes out. That leaves two options: (1) upgrade to a better model, or (2) post-process the output with an LLM. I tested both.

### 4.1 The experiment

I built a proof-of-concept post-ASR correction pipeline targeting the worst-performing files:

- **Sarvam files:** Full-transcript LLM correction (Sarvam's API doesn't return per-word confidence scores, so targeted correction wasn't possible)
- **ElevenLabs files:** Confidence-guided correction using per-word logprobs, with full-transcript fallback when confidence scores were unreliable
- **Correction LLM:** GPT-5.4 with a banking domain system prompt

**Why ElevenLabs needed 3-seed averaging:** ElevenLabs is non-deterministic: the same audio file produces different transcriptions on repeated runs. On one Kannada-English file (loan-enquiry), three runs gave WER of 120%, 45%, and 40%, an 80-point swing on identical audio. To separate "bad random draw" from "the model genuinely can't handle this," I ran each ElevenLabs file 3 times with different random seeds and averaged the WER. This is a significant reliability concern for banking: production systems can't have a transcription engine that randomly fails on the same call.

### 4.2 The 2x2 correction matrix

To test whether model upgrades or post-ASR correction matters more, I ran the same correction pipeline across both model generations. I targeted all non-English files (since English WER was already below 14% for all providers). Files that were already well-transcribed passed through unchanged; the "improved/worsened/unchanged" counts below reflect this targeted subset.

**Legacy models + LLM correction:**


| Provider               | Base WER | Avg WER delta  | Improved / worsened / unchanged |
| ---------------------- | -------- | -------------- | ------------------------------- |
| Sarvam (saarika:v2.5)  | 15.67%   | +0.76% (worse) | 1 / 2 / 13                      |
| ElevenLabs (scribe_v1) | 25.24%   | **-5.10%**     | 10 / 3 / 4                      |
| Whisper (whisper-1)    | 42.96%   | **-15.28%**    | 16 / 0 / 2                      |


**Latest models + LLM correction:**


| Provider                    | Base WER | Avg WER delta  | Improved / worsened / unchanged |
| --------------------------- | -------- | -------------- | ------------------------------- |
| Sarvam (saaras:v3)          | 15.14%   | +0.92% (worse) | 1 / 2 / 14                      |
| ElevenLabs (scribe_v2)      | 32.23%   | -0.09%         | 4 / 4 / 11                      |
| Whisper (gpt-4o-transcribe) | 27.68%   | **+0.00%**     | 0 / 0 / 15                      |


### 4.3 Model quality > post-processing

**Correction benefit is inversely proportional to base model quality.**

- **Whisper-1** (43% WER): correction saved 15pp. **gpt-4o-transcribe** (28% WER): correction saved 0pp. The model upgrade alone achieved the same accuracy as the entire correction pipeline, with zero latency overhead and zero LLM cost.
- **ElevenLabs scribe_v1**: correction helped 5pp. **scribe_v2** (after normalization, already accurate): correction helped 0.09pp.
- **Sarvam** is barely correctable in either version (+0.76% / +0.92%). Its remaining errors are too subtle for an LLM to fix without overcorrecting, which is actually evidence of model quality.

**For a PM, this answers a critical build-vs-buy question:** Don't invest in correction pipelines as a product feature. Invest in base model quality. The correction pipeline is a band-aid for weak models; strong models don't need it.

### 4.4 Why pure Kannada correction failed

Of 13 Sarvam files sent through GPT-5.4, 4 worsened, all pure Kannada. Root cause: GPT-5.4 "corrects" dialectal Kannada toward standard written forms, but the ground truth transcribes what was actually said, dialect and all. The LLM merged "ಎಸ್ ಬಿ" (es bi / S B) into "ಎಸ್‌ಬಿಐ" (esbiai / SBI), plausible but wrong. It split colloquial "ಲೇಸನ್ನು" (lesannu) into formal "ಲೇಸ್ ಅನ್ನು" (les annu), grammatically cleaner but not what was spoken.

**The correction LLM's Kannada isn't strong enough to know when a dialectal form is correct.** Sarvam's recently launched open-source LLMs ([Sarvam 30B and 105B](https://www.sarvam.ai/blogs/sarvam-30b-105b), trained from scratch on Indian languages) could potentially do better here, though this remains untested.

This points to a concrete opportunity: language-routed correction that applies LLM post-processing to code-mixed content (where English banking terms provide strong signal) but skips pure Kannada where the LLM introduces more errors than it fixes.

### 4.5 ElevenLabs confidence calibration gap

ElevenLabs provides per-word logprobs, a useful signal for targeted correction. But the scores are poorly calibrated for Indian languages:


| File                    | WER     | Avg logprob | Words flagged (<-0.5) |
| ----------------------- | ------- | ----------- | --------------------- |
| loan-enquiry (115% WER) | 115.00% | -0.130      | 1/20                  |
| ka_05 (95% WER)         | 94.74%  | -0.069      | 0/19                  |
| ka_04 (56% WER)         | 55.56%  | -0.029      | 0/9                   |


The model assigns near-zero logprobs (high confidence) even on files with 50-115% WER. Without a full-transcript fallback, confidence-guided correction was a no-op for 9 of 12 files. Adding the fallback turned ElevenLabs correction from -0.81% to -7.82% average improvement.

**For any provider:** confidence calibration per language is a product gap worth closing. Published calibration curves per language would let enterprises build quality-gating workflows without guessing.

## 5. Product & developer experience

### 5.1 Developer experience


| Dimension             | Sarvam                                                                                       | ElevenLabs                                                 | OpenAI                       |
| --------------------- | -------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------- |
| **Auth**              | Custom header `api-subscription-key`                                                         | Standard SDK `api_key`                                     | Standard SDK `api_key`       |
| **SDK**               | Official `sarvamai` SDK exists on PyPI (not used in this project; raw REST was used instead) | Official SDK, typed, well-structured                       | Mature, well-documented      |
| **Error messages**    | Cryptic 400 on MIME mismatch                                                                 | Clear SDK exceptions                                       | Clear SDK exceptions         |
| **Determinism**       | Yes, same input, same output                                                                 | **No**, 80-point WER variance between seeds                | Yes                          |
| **Confidence scores** | Not available                                                                                | Per-word logprobs (poorly calibrated for Indian languages) | Word timestamps, no logprobs |


**Key integration bugs encountered:**

- Sarvam rejected `audio/mp4a-latm` for m4a files, required manual override to `audio/mp4`. The official `sarvamai` SDK may handle this automatically.
- Sarvam `saarika:v2` silently deprecated. Discovered `saarika:v2.5` through trial and error.
- OpenAI `gpt-4o-transcribe` requires `response_format="json"` not `"verbose_json"`, undocumented at time of testing.

**AI-assisted DX observation:** All three providers were integrated by an AI coding agent (Claude Code) with only API keys provided. In the AI-assisted development era, DX is increasingly about how well documentation is structured for machine consumption, not just human readability.

### 5.2 Dashboard & playground

Sarvam's India-first playground is the strongest product signal in the evaluation. The example cards (code-mixed Gujarati finance, Marathi cricket verbatim, Tamil healthcare diarization) immediately tell Indian enterprise buyers "this is built for you." ElevenLabs' voice agent in docs (talk to documentation using STT + TTS) is the standout DX innovation: it's dogfooding as a product feature, and it generates opt-in voice data for training. OpenAI has no dedicated STT experience.

### 5.3 Pricing (at scale)

**Per-unit pricing:**


| Provider                                                                    | Model                  | Price/hour     |
| --------------------------------------------------------------------------- | ---------------------- | -------------- |
| [Sarvam](https://docs.sarvam.ai/api-reference-docs/getting-started/pricing) | saaras:v3              | Rs 30 (~$0.36) |
| [ElevenLabs](https://elevenlabs.io/pricing/api)                             | scribe_v2 Realtime     | $0.28 (~Rs 24) |
| [OpenAI](https://developers.openai.com/api/docs/pricing)                    | gpt-4o-transcribe      | $0.36 (~Rs 30) |
| [OpenAI](https://developers.openai.com/api/docs/pricing)                    | gpt-4o-mini-transcribe | $0.18 (~Rs 15) |


**At-scale projection (mid-size Indian bank: 50K calls/day, 3 min avg):**


| Provider                   | Monthly raw cost      | Best WER achieved            |
| -------------------------- | --------------------- | ---------------------------- |
| Sarvam (saaras:v3)         | Rs 22.5 lakh ($26.8K) | 15.14%                       |
| ElevenLabs (scribe_v2 RT)  | Rs 17.6 lakh ($21K)   | 32.23% raw / ~22% normalized |
| OpenAI (gpt-4o-transcribe) | Rs 22.7 lakh ($27K)   | 27.68%                       |
| OpenAI (gpt-4o-mini)       | Rs 11.3 lakh ($13.5K) | Not tested                   |


Raw ASR price is a vanity metric. The real question: **what does it cost to get banking-grade accuracy?** Sarvam's lower WER means fewer transcripts need human review or LLM correction. ElevenLabs is cheapest per-hour but requires post-processing for Indian languages, adding cost and latency. The untested gpt-4o-mini-transcribe at half price is the dark horse; if its Indian language accuracy is close to gpt-4o-transcribe, it could be the most cost-effective option.

**A structural pricing advantage:** Sarvam recently open-sourced [Sarvam 30B and 105B](https://www.sarvam.ai/blogs/sarvam-30b-105b), MoE models trained from scratch on Indian languages. Since these run on Sarvam's own infrastructure, if Sarvam built a correction layer into their ASR API using their own LLM, they could offer banking-grade accuracy at Rs 30/hr with zero marginal LLM cost, an advantage no competitor can replicate.

### 5.4 Integration considerations for banking


| Dimension               | Sarvam                                                                                                                                                                                                                                                                                       | ElevenLabs                                                                                       | OpenAI                          |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------- |
| **Data residency**      | India-only (sovereign)                                                                                                                                                                                                                                                                       | [India available](https://elevenlabs.io/blog/introducing-india-data-residency) (Enterprise-only) | US default; Azure India partial |
| **On-premise**          | [Sarvam Edge](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2112485) (proven: UIDAI Aadhaar)                                                                                                                                                                                             | Not available                                                                                    | Not available                   |
| **8kHz telephony**      | Yes (recently added)                                                                                                                                                                                                                                                                         | Not documented                                                                                   | Not documented                  |
| **Streaming**           | WebSocket, 5 output modes                                                                                                                                                                                                                                                                    | Scribe v2 Realtime (150ms)                                                                       | Separate Realtime API           |
| **Certifications**      | ISO 27001, SOC 2 Type II                                                                                                                                                                                                                                                                     | ISO 27001, SOC 2 Type II, PCI DSS Level 1                                                        | SOC 2 Type II                   |
| **Banking deployments** | [Tata Capital](https://www.sarvam.ai/stories/tata-capital-ai-voice-transformation) (20M+ monthly), [SBI Life](https://www.businesstoday.in/technology/story/sarvam-partners-with-sbi-life-to-deploy-ai-tools-for-customer-engagement-sales-518227-2026-02-26) (8Cr customers, 11+ languages) | None documented                                                                                  | None documented                 |


For RBI-regulated banking workloads, Sarvam's India-only infrastructure is a structural advantage. ElevenLabs [offers India data residency](https://elevenlabs.io/blog/introducing-india-data-residency) but only at Enterprise tier with added cost and complexity. OpenAI's India offering through Azure covers at-rest storage but inference still runs in the US.

Sarvam's [air-gapped deployment for UIDAI Aadhaar](https://techcrunch.com/2026/02/18/indias-sarvam-wants-to-bring-its-ai-models-to-feature-phones-cars-and-smart-glasses/) and 8kHz telephony support directly address call center infrastructure requirements.

**Why 8kHz and streaming matter:** Consider a customer calling a bank to report a lost credit card. The call arrives over standard telephone lines at 8kHz sampling rate, half the 16kHz most ASR models are trained on. If the model doesn't natively handle 8kHz, the audio needs upsampling, which introduces artifacts that degrade accuracy on already-challenging Indian language audio. Streaming matters because an agent assist system needs to display a live transcript as the customer speaks. With batch processing, the agent sees nothing until the call ends. With streaming at sub-second latency, the system can surface relevant knowledge base articles, flag compliance issues, or suggest responses in real-time. Sarvam's 0.84s batch latency and native 8kHz support are table stakes for this use case.

## 6. If I were PM: prioritized recommendations

### 6.1 Model quality: close the Kannada gap

**The opportunity:** 60 million Kannada speakers, major banks headquartered in Karnataka (Canara Bank, Vijaya Bank, Corporation Bank), and a current 27% WER that's 3x worse than Hindi's 9%.

**Target:** Bring Kannada WER below 15%, matching Hindi's current level. This would unlock South Indian banking coverage and position Sarvam as the only provider with sub-15% WER across both Indo-Aryan and Dravidian language families.

**What I'd investigate:** Is the gap driven by training data volume (fewer Kannada hours in training), dialectal diversity (Kannada has significant regional variation), or acoustic model architecture? The CER-to-WER ratio (13% CER vs 27% WER) suggests the model is close on phonetics but struggles with word boundaries, a potentially tractable problem.

### 6.2 Product layer: confidence scores + language-routed correction

**Per-word confidence scores** are the highest-leverage API addition, but not for the reason you might think. Sarvam's Indian language accuracy is already strong enough that correction pipelines add no value (Section 4.3). The real value of confidence scores is **enterprise observability**: banks need to know which transcriptions are reliable and which to flag for human review. This is a compliance requirement, not an accuracy play. Specifically:

- **Quality gating:** Flag transcriptions below a confidence threshold for human review, creating audit trails regulators expect.
- **Selective routing:** High-confidence transcriptions go straight to automation; low-confidence ones route to human agents.
- **Production monitoring:** Track confidence distributions over time to detect model degradation or data distribution shifts before customers notice.

No provider offers well-calibrated confidence for Indian languages today. ElevenLabs has logprobs but they're near-zero even at 50%+ WER. Sarvam shipping calibrated confidence scores would let enterprise customers build quality-gating workflows without external tooling.

**Language-routed correction** as a thin product layer: apply lightweight LLM correction on code-mixed content (where English banking terms provide strong semantic signal) but pass through pure Indic language output unchanged. This could be offered as an optional API parameter using Sarvam's own open-source LLMs ([Sarvam 30B/105B](https://www.sarvam.ai/blogs/sarvam-30b-105b)) at zero marginal cost.

### 6.3 Competitive positioning for banking

**The pitch:** Sarvam is the only provider that simultaneously offers (1) best-in-class Indian language accuracy, (2) India-hosted infrastructure satisfying RBI data localization, (3) on-premise/air-gapped deployment, and (4) proven banking customers at scale. No competitor matches on all four.

**Watch:** OpenAI closed the gap from 27pp to 12.5pp in one model generation. gpt-4o-transcribe now beats everyone on Hinglish code-mixed. If they launch India-hosted inference and continue improving Indian language support, the accuracy moat narrows. Sarvam's durable advantages are sovereign infrastructure and specialization; these don't erode with model generations.

### 6.4 Production evaluation infrastructure

**What this project did in miniature is what Sarvam should run continuously.**

**Is n=28 enough?** For identifying the major patterns, yes. The effect sizes are large enough that they're visible even at small sample sizes: Sarvam's 27% vs Whisper's 58% on Kannada, the 80-point WER variance in ElevenLabs, the script mismatch inflating WER by 40pp. These findings won't reverse at scale. But for per-language confidence intervals and detecting subtle regressions, you'd want 50-100 files per language (250-500 total across 5 languages). The highest-ROI expansion would be more code-mixed personal recordings (currently n=7, the true banking test set), since those represent the actual banking use case better than public monolingual data.

**How to automate this:** The entire pipeline (audio ingestion, provider APIs, WER/CER computation, entity extraction, comparison) is already scripted in Python. Making it production-grade means:

- **Scheduled evaluation runs** triggered on model release announcements or on a weekly cadence against a growing test set.
- **Regression alerts** when any language's WER moves more than 2 percentage points. This would have caught the scribe_v2 script format change before customers did.
- **Multi-metric dashboards** tracking WER, CER, script-normalized WER, entity accuracy, and latency per language per domain, with trend lines over time.
- **Code-mixed banking test sets:** The Voice of India benchmark covers monolingual evaluation. There's a gap for code-mixed banking evaluation sets with ground truth. Sarvam could publish or contribute to this, which would both demonstrate confidence and shape how the industry measures Indian language ASR.

Tools like Braintrust, Arize, or an internal eval platform could serve as the backbone. The key insight is that evaluation infrastructure is not a one-time project; it's a continuous product function.

## 7. What I didn't test

- **Streaming performance.** All testing used batch file upload. Real banking calls need live streaming transcription. Sarvam's WebSocket API and ElevenLabs' Realtime STT were not evaluated under load.
- **Speaker diarization quality.** Multi-speaker calls are the norm in banking (agent + customer). I tested single-speaker clips only.
- **Noise robustness.** Real call center audio has background noise, cross-talk, hold music, telephony compression. I tested clean recordings and public dataset clips.
- **Production scale behavior.** 28 files over 4 days is not a load test. Rate limiting, cold start latency, and P99 behavior at 50K calls/day are unknowns.
- **TTS evaluation.** I didn't evaluate Sarvam Bulbul or ElevenLabs Turbo for voice synthesis, the other half of a voice AI system. A production evaluation would include MOS ratings on banking IVR sentences.
- **Sarvam LLM correction quality.** The correction pipeline used GPT-5.4. Testing whether [Sarvam 30B or 105B](https://www.sarvam.ai/blogs/sarvam-30b-105b) achieves comparable correction quality at zero cost is the obvious next experiment.

## 8. Conclusion

I tested three speech AI providers against the reality of Indian banking: multilingual customers, code-mixed speech, and compliance-driven infrastructure requirements.

**The core findings:**

1. **No single provider wins on every metric.** Sarvam leads on overall WER and Indian language accuracy. Whisper leads on Hinglish code-mixed. ElevenLabs leads on entity accuracy. The "best" choice depends on what the deployment optimizes for.
2. **Script format matters as much as accuracy.** A 40-percentage-point WER difference between providers can disappear with proper normalization. Evaluation methodology is as important as model quality.
3. **Model upgrades beat post-processing.** The 2x2 correction matrix shows that investing in base model quality delivers more value than building LLM correction pipelines, and at lower cost and complexity.
4. **Sarvam's position is strong but not unassailable.** Dominant Indian language accuracy, sovereign infrastructure, and proven banking deployments create a durable competitive advantage. But the Kannada gap and the pace of OpenAI's improvement mean standing still isn't an option.
5. **The real metric for banking isn't WER, it's entity accuracy.** Getting "₹18,500" and "credit card" right matters more than transcribing every filler word. Domain-specific evaluation is the foundation of model improvement.

*I ran this evaluation over 7 days as a methodology demonstration. The code, data, and results are in the [GitHub repository](https://github.com/reehan-ahmed/sarvam-speech-eval). Total API cost: ~Rs 29 ($0.35).*

### Appendix: data sources & references


| Source                          | Citation                                                                                                                                                                                                                       |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| RBI complaint data              | [Rootle AI, Voice AI for Indian Call Centers](https://rootle.ai/blog/voice-ai-for-indian-call-centers/)                                                                                                                        |
| India call center AI market     | [NextMSC, India Voice Assistant Market](https://www.nextmsc.com/news/india-voice-assistant-market)                                                                                                                             |
| Voice of India benchmark        | [SME Street, Global Speech AI Struggles](https://smestreet.in/technology/global-speech-ai-struggles-to-understand-india-new-national-benchmark-voice-of-india-reveals-11110091)                                                |
| Sarvam Saaras V3                | [Sarvam Blog, ASR](https://www.sarvam.ai/blogs/asr/), [Business Standard](https://www.business-standard.com/technology/tech-news/saaras-v3-beats-gemini-gpt-4o-on-indian-speech-benchmarks-says-sarvam-ai-126021200384_1.html) |
| Sarvam 30B / 105B               | [Sarvam Blog](https://www.sarvam.ai/blogs/sarvam-30b-105b), [TechCrunch](https://techcrunch.com/2026/02/18/indian-ai-lab-sarvams-new-models-are-a-major-bet-on-the-viability-of-open-source-ai/)                               |
| Tata Capital deployment         | [Sarvam case study](https://www.sarvam.ai/stories/tata-capital-ai-voice-transformation)                                                                                                                                        |
| SBI Life deployment             | [BusinessToday](https://www.businesstoday.in/technology/story/sarvam-partners-with-sbi-life-to-deploy-ai-tools-for-customer-engagement-sales-518227-2026-02-26)                                                                |
| Sarvam Edge / UIDAI             | [PIB](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2112485), [TechCrunch](https://techcrunch.com/2026/02/18/indias-sarvam-wants-to-bring-its-ai-models-to-feature-phones-cars-and-smart-glasses/)                         |
| ElevenLabs India data residency | [ElevenLabs blog](https://elevenlabs.io/blog/introducing-india-data-residency)                                                                                                                                                 |
| IndicVoices dataset             | [AI4Bharat](https://ai4bharat.iitm.ac.in/datasets/indicvoices), [HuggingFace](https://huggingface.co/datasets/ai4bharat/indicvoices_r)                                                                                         |
| Svarah dataset                  | [HuggingFace](https://huggingface.co/datasets/ai4bharat/Svarah)                                                                                                                                                                |
| Sarvam pricing                  | [Sarvam API Pricing](https://www.sarvam.ai/api-pricing/), [Docs](https://docs.sarvam.ai/api-reference-docs/getting-started/pricing)                                                                                            |
| ElevenLabs pricing              | [ElevenLabs Pricing](https://elevenlabs.io/pricing/api)                                                                                                                                                                        |
| OpenAI pricing                  | [OpenAI Pricing](https://developers.openai.com/api/docs/pricing)                                                                                                                                                               |
