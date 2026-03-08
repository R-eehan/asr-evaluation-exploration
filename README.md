# Evaluating ASR Models for Indian Banking

After building a [local speech-to-text app](https://github.com/R-eehan/vox), I had a question I couldn't answer: how do you evaluate a model that has no system prompt? With LLM pipelines, you tweak prompts, build judges, and iterate. ASR models give you none of that. The model is a black box.

This project is an open-source evaluation of three ASR providers against a real enterprise problem: **customer service voice AI for Indian banking**. India's banking sector handles 10M+ complaints annually, customers naturally code-mix between languages, and getting "Rs 18,500" right matters more than transcribing every filler word.

**[Interactive code walkthrough](https://r-eehan.github.io/asr-evaluation-exploration/walkthrough.html)** — annotated pipeline architecture explaining design decisions.

## Key Findings

**1. There is no "best" model.** Sarvam leads overall WER (15%). OpenAI wins Hinglish code-mixed (9%). ElevenLabs scores 100% on banking entity accuracy. The right choice depends on what you're optimizing for.

**2. Script normalization inflates WER by 40 percentage points.** ElevenLabs outputs English loanwords in Latin script while ground truth uses Devanagari. Raw WER: 57%. After normalizing scripts: 17%. Without this correction, you'd wrongly conclude the model can't handle code-mixing.

**3. Model quality beats post-processing.** Upgrading from whisper-1 to gpt-4o-transcribe saved 15pp WER — the same improvement as an entire LLM correction pipeline, but at zero marginal cost. When the base model is strong (Sarvam), LLM correction actually makes things worse by overcorrecting.

**4. The Kannada gap is 3x.** Even Sarvam, the "Indic-first" provider, hits 27% WER on Kannada vs 9% on Hindi. If you're building voice AI for Karnataka's banks, "Indic-first" alone won't guarantee your language works.

## Results at a Glance

### Latest Models — Overall Performance

| Provider | Model | WER | CER | Entity Accuracy | Latency (P50) |
|----------|-------|-----|-----|-----------------|---------------|
| **Sarvam** | saaras:v3 | **15.14%** | **6.67%** | 97.6% | **0.84s** |
| ElevenLabs | scribe_v2 | 32.23% | 20.76% | **100%** | 1.14s |
| OpenAI | gpt-4o-transcribe | 27.68% | 14.61% | 82.9% | 1.86s |

### WER by Language

![WER by Language](report/figures/fig1_wer_by_language.png)

### Script Normalization Impact + Entity Accuracy

![Script Normalization](report/figures/fig2_script_normalization.png)

### Model Quality vs Post-Processing (The Correction Matrix)

![Correction Matrix](report/figures/fig3_correction_matrix.png)

## Methodology

### Test Data (n=28)

| Source | Files | Languages | Content |
|--------|-------|-----------|---------|
| [IndicVoices-R](https://huggingface.co/datasets/ai4bharat/indicvoices_r) | 14 | Hindi (7), Kannada (7) | Natural speech from diverse speakers |
| [Svarah](https://huggingface.co/datasets/ai4bharat/Svarah) | 7 | Indian English | Accented English queries |
| Personal recordings | 7 | Hinglish (4), Kannada-English (3) | Code-mixed banking scenarios I recorded myself |

### Providers Tested

- **Sarvam AI** — saaras:v3 (latest) + saarika:v2.5 (legacy)
- **ElevenLabs** — scribe_v2 (latest) + scribe_v1 (legacy)
- **OpenAI** — gpt-4o-transcribe (latest) + whisper-1 (legacy)

### Metrics

- **WER** (Word Error Rate) — standard ASR metric
- **CER** (Character Error Rate) — better for agglutinative Indic languages where a single character error inflates WER
- **Script-normalized WER** — WER recomputed after mapping Latin loanwords to native script
- **Entity accuracy** — did the model capture banking-critical terms (amounts, card types, transaction terms)?
- **Latency** — API response time per audio file

### Caveats

This is a directional evaluation, not a statistically significant benchmark. n=28 is too small for definitive conclusions. The public dataset audio covers general topics (cooking, sports), not banking-specific conversations. Code-mixed recordings are personal (confound: speaker identity vs. code-mixing difficulty). These findings suggest patterns worth investigating at scale.

## Architecture

```
[Audio Files] → [Provider Abstraction] → [Evaluation Runner] → [Metrics Engine] → [Results]
                 src/providers/           src/run_eval.py        src/metrics/        data/results/
                                                                      ↓
                                                              [Text Normalization]
                                                               src/metrics/normalize.py
                                                               src/metrics/script_normalize.py
                                                                      ↓
                                                              [Post-ASR Correction PoC]
                                                               src/correction/
```

| File | Purpose |
|------|---------|
| `src/run_eval.py` | Main evaluation runner — loads ground truth, loops providers, computes metrics, saves results |
| `src/providers/sarvam.py` | Sarvam API wrapper (REST, custom auth header, MIME workaround) |
| `src/providers/elevenlabs_stt.py` | ElevenLabs SDK wrapper (word-level timestamps, logprobs) |
| `src/providers/whisper.py` | OpenAI Whisper/GPT-4o wrapper |
| `src/metrics/wer.py` | Word Error Rate via jiwer with Indic text normalization |
| `src/metrics/cer.py` | Character Error Rate via jiwer |
| `src/metrics/normalize.py` | Indic text normalization — nuqta stripping, chandrabindu handling, punctuation across 3 scripts |
| `src/metrics/script_normalize.py` | Latin-to-native script mapping for code-mixed WER fairness |
| `src/correction/llm_correction.py` | GPT-based banking domain correction (full-transcript + targeted modes) |
| `src/correction/confidence_guided.py` | ElevenLabs logprob-guided correction with fallback for uncalibrated confidence |
| `src/config.py` | Environment and path configuration |
| `scripts/download_data.py` | Fetch audio from HuggingFace datasets |
| `analysis/visualizations.ipynb` | Chart generation notebook (run to regenerate all figures) |

## Quick Start

```bash
# Clone
git clone https://github.com/R-eehan/asr-evaluation-exploration.git
cd asr-evaluation-exploration

# Setup
cp .env.template .env
# Add your API keys to .env (Sarvam, ElevenLabs, OpenAI)

pip install -r requirements.txt

# Run evaluation (all 28 files, all 3 providers)
python src/run_eval.py

# Run with a subset
python src/run_eval.py --limit 5
```

Audio files are included in the repo. To re-download from HuggingFace (requires HF token for gated datasets):

```bash
python scripts/download_data.py
```

## Attribution

Audio data from [IndicVoices-R](https://huggingface.co/datasets/ai4bharat/indicvoices_r) and [Svarah](https://huggingface.co/datasets/ai4bharat/Svarah) by AI4Bharat (IIT Madras), released under CC-BY-4.0. See [ATTRIBUTION.md](ATTRIBUTION.md) for full citation details.

## License

MIT
