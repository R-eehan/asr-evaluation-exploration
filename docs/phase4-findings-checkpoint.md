# Phase 4 Findings Checkpoint

Date: 2026-03-15
Status: Analysis complete, pre-writeup

## Core Thesis

The assumption that deploying the same model on any inference platform gives you equivalent results is wrong. We proved this by running Whisper Large v3 across 4 inference platforms (Together AI, Groq, Fireworks AI, Baseten) on 28 Indic/code-mixed audio files. The platforms agreed on easy audio but diverged by up to 67 percentage points on challenging audio — same model, same input, different output.

The implication for product teams: you cannot skip provider-specific evaluation. The model choice is necessary but not sufficient; the platform choice also affects your product's quality in ways that aggregate benchmarks don't capture.

---

## The Framing: What This Project Is and Isn't

This project is **not** a benchmark that ranks inference platforms. It's a methodology demonstration that proves why you need to run your own benchmark.

The artifact is not the numbers — it's the method and the proof that the method is necessary.

**Generic version** (what most people would publish): "We compared 4 providers. Here are the WER numbers. Provider X is cheapest."

**What we're actually saying**: There is no shortcut to choosing an inference provider. You cannot rely on published benchmarks, pricing pages, or aggregate WER numbers. You must evaluate on your own data, with your own ground truth conventions, on your own criteria.

---

## Key Findings

### 1. Platform choice doesn't matter for easy audio, matters enormously for hard audio

Of 28 files tested across 4 providers:
- **13 files**: All 4 providers agreed within 5pp WER (consensus). Mostly English and straightforward Hindi.
- **6 files**: Moderate disagreement (5-15pp spread).
- **9 files**: Major disagreement (>15pp spread). Mostly challenging Hindi and Kannada. Worst case: 67pp spread on a single Hindi file.

**The implication**: If your product handles clean English audio, any provider works. If your product handles accented, noisy, or code-mixed audio — the hard cases that matter most — your choice of provider significantly affects quality.

### 2. Same model, different failure modes

Providers with similar overall WER fail in fundamentally different ways:

| Provider | Hindi WER | Failure pattern | Substitution rate | Deletion rate |
|----------|:---------:|-----------------|:-----------------:|:------------:|
| Together AI | 41.4% | Drops words — shorter transcripts | 15.7% | 38.6% |
| Groq | 36.1% | Wrong words — same length, different text | 36.3% | 8.1% |
| Fireworks | 28.0% | Balanced errors | 19.7% | 9.9% |
| Baseten | 28.6% | Fewest deletions | 23.8% | 3.6% |

**Why this matters for product decisions**: A provider that silently drops words (Together AI's deletion pattern) is a different product risk than one that replaces words (Groq's substitution pattern). For a banking product, a missing "eighteen thousand five hundred" is worse than a misspelled version of it. The right provider depends on which failure mode your product can tolerate.

### 3. WER is deeply dependent on ground truth conventions

Script normalization impact on Hinglish (code-mixed Hindi-English) files:

| Provider | Original WER | Normalized WER | Improvement |
|----------|:-----------:|:--------------:|:-----------:|
| Together AI | 53.8% | 43.9% | -9.9pp |
| Groq | 52.1% | 39.8% | -12.3pp |
| Fireworks | 53.7% | 37.5% | -16.2pp |
| Baseten | 52.5% | 36.3% | -16.2pp |

13 of 16 provider-file pairs improved after normalization. One file dropped from 54.5% to 13.6% across all providers — a 41pp improvement from correcting a measurement artifact, not a quality improvement.

Kannada-English normalization had zero effect — confirming that Kannada WER (65-87%) is genuinely high, not inflated by script mismatch.

**The deeper point**: Your ground truth format determines which model/provider looks good. Most benchmarks report WER as if it's an objective metric. It's not — it's deeply dependent on annotation conventions (Devanagari vs Roman for loanwords, spelled-out numbers vs digits, punctuation conventions). Any PM evaluating ASR must define their ground truth conventions explicitly and acknowledge that WER comparisons across studies with different conventions are invalid.

### 4. Turbo vs Full is use-case dependent, not universally better or worse

Aggregate comparison suggests Turbo is "only 2-3pp worse." The per-file paired analysis tells a different story:

- **Mean difference**: +2.8pp (Groq), +0.6pp (Fireworks)
- **Standard deviation**: 24pp (Groq), 19pp (Fireworks)
- **Range**: Turbo is better by 50pp on some files, worse by 60pp on others

By language:
- English: +5.6pp (slight degradation)
- Hindi: -11.8pp on Groq (Turbo better — the Full model hallucinated on 2 files where Turbo didn't)
- Hinglish: -8.8pp to -11.7pp (Turbo better — but this is a ground truth format artifact, not genuine quality improvement. Turbo outputs more Devanagari for English loanwords, which matches our Devanagari ground truth)
- Kannada-English: +25-31pp collapse (avoid Turbo for Dravidian code-mixed speech)

**The generalizable claim is not "Turbo is better/worse for language X." The claim is: your ground truth format determines which model variant looks good.** Anyone evaluating Turbo vs Full must run their own eval with their own ground truth and accept that the results are specific to their annotation conventions.

### 5. Why outputs differ across platforms

Four documented causes (none can be individually isolated without provider-internal access):

1. **Quantization**: Providers may reduce model precision differently (FP32 → FP16 → INT8). Different quantization methods (GPTQ, AWQ, GGUF) retain 90-95% quality with different error profiles.

2. **Inference engine**: Together AI likely uses vLLM, Groq uses custom LPU silicon, Fireworks uses their own engine, Baseten uses TensorRT-LLM. Research shows implementation differences can produce variance comparable to FP8 quantization (Karvonen, 2025).

3. **GPU floating-point non-determinism**: >98% of tokens match across hardware, but ~2% diverge due to floating-point arithmetic order (a+b)+c ≠ a+(b+c). On easy audio, this doesn't change output. On hard audio, a probability flip cascades into completely different transcription.

4. **Decoding configuration**: Beam width, VAD, audio preprocessing, language detection behavior — all potentially different per provider. We controlled temperature (=0) and language code, but couldn't control the rest.

**The honest claim**: We can prove outputs differ. We cannot prove which cause is responsible. "Same model name, different output" is the finding. Causal attribution is out of scope.

Sources:
- [DiFR: Inference Verification Despite Nondeterminism](https://adamkarvonen.github.io/machine_learning/2025/11/28/difr.html) — >98% token match, ~2% diverge
- [Model Equality Testing (ICLR 2025)](https://arxiv.org/abs/2410.20247) — 11/31 LLM endpoints deviate from reference weights
- [GGUF vs GPTQ vs AWQ](https://localaimaster.com/blog/quantization-explained) — different quantization methods retain 90-95% quality

---

## Decision Framework for PMs

This is the methodology for evaluating inference providers, not a recommendation of which one to choose.

### Step 1: Define your eval set
Representative of your actual audio. Languages, accents, domains, recording quality, edge cases. Not a generic benchmark — your product's real-world distribution.

### Step 2: Define your ground truth conventions
What script for multilingual text? Digits or spelled-out numbers? What counts as "correct"? These conventions determine your WER numbers. Make them explicit.

### Step 3: Run across candidate providers
Same files, same conditions. Control what you can (temperature, language code). Document what you can't (beam width, audio preprocessing, model checkpoint version). Add a delay between calls for rate limits.

### Step 4: Compare on your criteria
WER is one metric. Others that matter:
- **Latency** (Groq: 0.9s mean; Fireworks: 4.4s; matters for real-time products)
- **Cost at scale** (ranges from $400/10K hours to $37,500/10K hours across providers)
- **Error type** (does the provider drop words or replace them? Which is worse for your use case?)
- **Entity accuracy** (does it capture domain-specific terms — "credit card", "transaction"?)
- **Edge-case behavior** (hallucinations, language switching, repetitive tokens)

### Step 5: Accept results are perishable
Providers update models, pricing, and infrastructure continuously. Your evaluation is a snapshot, not a permanent truth. Date-stamp everything.

---

## Cost-Quality Summary (March 2026 pricing)

### Macro-Average WER (mean of per-category means — never report single overall WER)

| Provider | English | Hindi | Hinglish | Kannada | Kn-EN | Macro-Avg |
|----------|:-------:|:-----:|:--------:|:-------:|:-----:|:---------:|
| Baseten | 4.2% | 28.6% | 37.4% | 81.8% | 72.7% | 44.9% |
| Groq | 2.6% | 36.1% | 34.3% | 83.1% | 75.9% | 46.4% |
| Fireworks | 4.2% | 28.0% | 39.5% | 88.4% | 72.7% | 46.6% |
| Together AI | 4.2% | 41.4% | 33.6% | 83.6% | 80.8% | 48.7% |

### Latency

| Provider | Mean | P50 | P95 | Hardware |
|----------|:----:|:---:|:---:|----------|
| Groq | 0.9s | 0.7s | 2.6s | Custom LPU silicon (not GPU) |
| Together AI | 1.4s | 1.3s | 2.2s | GPU (likely H100) |
| Baseten | 3.9s | 2.7s | 10.3s | H100 MIG (dedicated) |
| Fireworks | 4.4s | 4.0s | 9.9s | GPU |

### Scale Economics (per month)

| Provider | 100 hrs | 1,000 hrs | 10,000 hrs |
|----------|--------:|----------:|-----------:|
| Groq Turbo | $4 | $40 | $400 |
| Fireworks Turbo | $5 | $54 | $540 |
| Together AI | $9 | $90 | $900 |
| Fireworks | $9 | $90 | $900 |
| Groq (Large v3) | $11 | $111 | $1,110 |
| OpenAI (gpt-4o-mini) | $18 | $180 | $1,800 |
| OpenAI (gpt-4o) | $36 | $360 | $3,600 |
| Baseten (H100 MIG) | $375 | $3,750 | $37,500 |

Note: Baseten cost assumes H100 MIG at $0.0625/GPU-min with dedicated instance. Actual cost depends heavily on utilization — at >90% utilization with consistent load, effective per-audio cost drops. At low utilization with idle time, it's the most expensive option. All pricing verified from provider websites, March 2026.

### Entity Accuracy (banking terms in code-mixed files)

| Provider | Accuracy | Notes |
|----------|:--------:|-------|
| Fireworks | 68.3% | Best on Hinglish entities |
| Baseten | 65.9% | |
| Groq | 63.4% | |
| Together AI | 56.1% | Misses more Kannada-English entities |

All providers nail Hinglish banking terms. All fail on Kannada-English entities (debit card, date of birth, monitoring team consistently missed).

---

## Methodology Controls

### What we controlled
- **Model**: Whisper Large v3 (1.55B params) on all 4 providers — verified via Phase 0 API checks and model alignment correction
- **Temperature**: 0 (greedy decoding) on all providers
- **Language code**: Explicitly set per file (hi, kn, en, etc.) — identical across providers
- **Audio input**: Same files, same format (WAV/M4A), sent without modification
- **Self-consistency**: 4 files × 4 providers × 3 runs confirmed deterministic output at temperature=0

### What we could not control
- Quantization level (FP32/FP16/INT8) — undisclosed by providers
- Inference engine (vLLM, TensorRT-LLM, custom) — undisclosed
- Beam width and other decoding parameters — not exposed by all APIs
- Audio preprocessing (resampling, normalization, VAD) — provider-side, invisible to us
- Model checkpoint version — "whisper-large-v3" may map to different checkpoints across providers

### Limitations
- 28 files across 5 language categories (N=3 to N=7 per category) — descriptive findings, not statistically generalizable
- Single ground truth annotator — introduces annotation noise on absolute WER (does not affect cross-provider relative comparison)
- Batch mode only — streaming/real-time performance not evaluated
- Single evaluation session — provider behavior may vary over time, under different load

---

## Baseten Deployment Experience Notes

### What happened
1. Initially deployed "Whisper Large v3 Turbo Streaming" — WebSocket-based, designed for live microphone input
2. Realized this breaks apples-to-apples comparison (different serving method, not just different platform)
3. Redeployed "Whisper Large v3 Turbo" (non-streaming, REST API) — base64 audio upload, same pattern as managed APIs
4. Then caught that Turbo (809M params) ≠ Full (1.55B params) — redeployed again with Whisper Large v3

### Key observations
- Model Library deployment is straightforward: pick model, pick GPU, deploy
- GPU choice matters: H100 MIG ($0.0625/min) vs full H100 ($0.108/min)
- Scale-to-zero works but adds cold start latency (~3-5s for first request after wakeup)
- Streaming vs batch distinction is critical and not immediately obvious — you need to understand what you're deploying
- 3 deployments were needed to get the right model variant — this is the learning curve

### The product insight
Managed APIs (Together AI, Groq, Fireworks) abstract deployment entirely. You pass a model name and get results. Baseten gives you control (GPU choice, autoscaling, dedicated instance) but expects you to know what you're asking for. The streaming/batch confusion and the model variant mismatch are exactly the kind of mistakes a first-time deployer makes. This is the tradeoff: control vs simplicity.

---

## What Remains (Phase 5)

1. Visualization figures (cross-platform agreement heatmap, cost-quality scatter, WER bar charts)
2. README Part 2 with the framing above
3. Update interactive visualizer (index.html) with new providers
4. Update code walkthrough (code-walkthrough.html)
5. Document methodology controls in README (identical audio input, decoding parameters)
6. Push to GitHub
