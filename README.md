# Evaluating ASR Models

After building a [local speech-to-text app](https://github.com/R-eehan/vox), I wanted to understand: how do you evaluate a model that has no system prompt? With typical LLM features/products involving text generation, you can perform error analysis, build LLM judges, and iterate on system prompts. Most ASR models don't work that way. Some newer models (Azure LLM Speech, Gemini) are starting to accept instructions, but the providers I tested here offer no meaningful prompt control. Audio goes in, text comes out.

This project is an attempt to evaluate three ASR providers against a real enterprise problem: **customer support using voice AI for Indian banking**. The RBI Ombudsman received [1.3 million escalated banking complaints in FY 2024-25](https://rbi.org.in/Scripts/AnnualReportPublications.aspx), up 68% in two years, and that's just the fraction customers escalate formally. Customers naturally code-mix (switch between different languages), making speech transcription a hard problem. In banking, getting "Rs 18,500" right matters more than transcribing every filler word.

**[Interactive code walkthrough](https://r-eehan.github.io/asr-evaluation-exploration/code-walkthrough.html)** : annotated pipeline architecture explaining design decisions.

## Key metrics for ASR evaluation

**1. Word Error Rate(WER)**: Measures the general accuracy of a transcript. It counts how many words the AI got wrong (by swapping, adding, or missing them) compared to what was actually said. Lower scores = better ASR model. Example:

- Human said: "I want to ***close my account***."
- AI heard: "I want to ***clothes my amount***."

The AI got 2 words wrong out of 5; WER = 40%

**2. Character Error Rate(CER)**: Double clicks on character level accuracy. A word comprises of many characters, this metric measures accuracy of each character transcribed in that word from an input audio. **Preferred metric** for Indic/multilingual languages and very useful for checking if the AI is misspelling names or technical terms by just one or two letters. Example:

- Human said: "My name is Smyth."
- AI heard: "My name is Smith."

The actual word(name) is wrong, but only one letter (character) is incorrect across 17 characters(includes spaces, punctuation); CER = 5.8%

**3. Entity Accuracy**: Think of this as a "Meaning Score." For the banking domain, specific details like an Account Number, a Date, or a Transaction Type are called "entities". Entity Accuracy measures if the ASR model successfully identified the "VIP" information needed to actually solve the customer's problem. Example:

The use case: A customer calls a bank’s Voice AI to report a lost card.
The sentence: "I lost my Visa credit card ending in 4242."
Entity Accuracy check:

- Did the AI catch the card type? (Visa credit): Let's say "yes"
- Did the AI catch the last 4 digits? (4242): Let's say 'no'

Entity accuracy: 50% in this specific example

Why it matters: Even if the AI misses a small word like "the" or "uhm" (which affects Word Error Rate), as long as it gets the Entity Accuracy right, the bank can still lock the correct card and help the customer.

### Benchmarks

| Language           | Acceptable WER | Acceptable CER | Industry Standard Note                                      |
|-----------------------------|------------|------------|--------------------------------------------------------------|
| English (General)           | 5% – 8%    | 2% – 5%    | The "Gold Standard" due to massive datasets              |
| Hindi (Indic)               | 15% – 20%  | 5% – 10%   | Acceptable range for high-performing Indic models          |
| Dravidian (Tamil/Telugu)    | 20% – 35%  | 10% – 15%  | Higher WER due to long, complex word structures           |

## Key Findings

**1. There is no "best" model.** Sarvam leads overall WER (15%). OpenAI wins Hinglish code-mixed (9%). ElevenLabs scores 100% on banking entity accuracy. The right choice depends on what you're optimizing for.

**2. Script normalization inflates WER by 40 percentage points.** ElevenLabs outputs English loanwords in Latin script while ground truth uses Devanagari. Raw WER: 57%. After normalizing scripts: 17%. Without this correction, you'd wrongly conclude the model can't handle code-mixing. This was the single most important discovery in the project.

**3. Model quality beats post-processing.** Upgrading from whisper-1 to gpt-4o-transcribe cut 15pp of WER. That's the same improvement as building an entire LLM correction pipeline, but at zero marginal cost. When the base model is strong enough (Sarvam), LLM correction actually makes things worse by overcorrecting.

**4. The Kannada gap is 3x.** Even Sarvam, the "Indic-first" provider, hits 27% WER on Kannada vs 9% on Hindi. If you're building voice AI for Karnataka's banks, "Indic-first" alone won't guarantee your language works.

## Results at a Glance

### Latest Models, Overall Performance


| Provider   | Model             | WER        | CER       | Entity Accuracy | Latency (P50) |
| ---------- | ----------------- | ---------- | --------- | --------------- | ------------- |
| **Sarvam** | saaras:v3         | **15.14%** | **6.67%** | 97.6%           | **0.84s**     |
| ElevenLabs | scribe_v2         | 32.23%     | 20.76%    | **100%**        | 1.14s         |
| OpenAI     | gpt-4o-transcribe | 27.68%     | 14.61%    | 82.9%           | 1.86s         |


### WER by Language

![WER by Language](report/figures/fig1_wer_by_language.png)

### Script Normalization Impact + Entity Accuracy

![Script Normalization](report/figures/fig2_script_normalization.png)

### Model Quality vs Post-Processing (The Correction Matrix)

![Correction Matrix](report/figures/fig3_correction_matrix.png)

## Methodology

### Test Data (n=28)


| Source                                                                   | Files | Languages                         | Content                                        |
| ------------------------------------------------------------------------ | ----- | --------------------------------- | ---------------------------------------------- |
| [IndicVoices-R](https://huggingface.co/datasets/ai4bharat/indicvoices_r) | 14    | Hindi (7), Kannada (7)            | Natural speech from diverse speakers           |
| [Svarah](https://huggingface.co/datasets/ai4bharat/Svarah)               | 7     | Indian English                    | Accented English queries                       |
| Personal recordings                                                      | 7     | Hinglish (4), Kannada-English (3) | Code-mixed banking scenarios I recorded myself |


### Providers Tested

- **Sarvam AI** : saaras:v3 (latest) + saarika:v2.5 (legacy)
- **ElevenLabs** : scribe_v2 (latest) + scribe_v1 (legacy)
- **OpenAI** : gpt-4o-transcribe (latest) + whisper-1 (legacy)

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


| File                                  | Purpose                                                                                         |
| ------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `src/run_eval.py`                     | Main evaluation runner. Loads ground truth, loops providers, computes metrics, saves results.   |
| `src/providers/sarvam.py`             | Sarvam API wrapper (REST, custom auth header, MIME workaround)                                  |
| `src/providers/elevenlabs_stt.py`     | ElevenLabs SDK wrapper (word-level timestamps, logprobs)                                        |
| `src/providers/whisper.py`            | OpenAI Whisper/GPT-4o wrapper                                                                   |
| `src/metrics/wer.py`                  | Word Error Rate via jiwer with Indic text normalization                                         |
| `src/metrics/cer.py`                  | Character Error Rate via jiwer                                                                  |
| `src/metrics/normalize.py`            | Indic text normalization. Nuqta stripping, chandrabindu handling, punctuation across 3 scripts. |
| `src/metrics/script_normalize.py`     | Latin-to-native script mapping for code-mixed WER fairness                                      |
| `src/correction/llm_correction.py`    | GPT-based banking domain correction (full-transcript + targeted modes)                          |
| `src/correction/confidence_guided.py` | ElevenLabs logprob-guided correction with fallback for uncalibrated confidence                  |
| `src/config.py`                       | Environment and path configuration                                                              |
| `scripts/download_data.py`            | Fetch audio from HuggingFace datasets                                                           |
| `analysis/visualizations.ipynb`       | Chart generation notebook (run to regenerate all figures)                                       |


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