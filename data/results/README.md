# Results

Final evaluation outputs from the ASR benchmark.

| File | Description |
|------|-------------|
| `eval_legacy_models.csv/json` | Full evaluation with legacy models (saarika:v2.5, scribe_v1, whisper-1) |
| `eval_latest_models.csv/json` | Full evaluation with latest models (saaras:v3, scribe_v2, gpt-4o-transcribe) |
| `correction_legacy_models.csv/json` | Post-ASR LLM correction results (legacy models) |
| `correction_latest_models.csv/json` | Post-ASR LLM correction results (latest models) |
| `script_normalized_wer.json` | WER recomputed after Latin-to-native script normalization for code-mixed audio |

Each CSV contains one row per (audio file, provider) pair with columns: `filename`, `source`, `language`, `scenario`, `provider`, `model`, `reference`, `hypothesis`, `wer`, `cer`, `substitutions`, `deletions`, `insertions`, `latency_seconds`, `status`, `error`.
