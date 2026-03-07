# Day 3: Full ASR Evaluation Results

**Date:** 2026-03-07
**Total files:** 28 | **Providers:** 3 | **Total API calls:** 84

## 1. Overall Summary by Provider


| Provider   | Files | Mean WER | Median WER | Mean CER | Mean Latency | P50 Latency | P95 Latency |
| ---------- | ----- | -------- | ---------- | -------- | ------------ | ----------- | ----------- |
| elevenlabs | 28    | 25.24%   | 18.34%     | 11.63%   | 2.73s        | 2.10s       | 6.22s       |
| sarvam     | 28    | 15.67%   | 14.64%     | 5.33%    | 0.78s        | 0.72s       | 1.27s       |
| whisper    | 28    | 42.96%   | 36.19%     | 21.46%   | 3.16s        | 2.77s       | 6.11s       |


## 2. WER by Provider x Scenario


| Scenario | elevenlabs | sarvam | whisper |
| -------- | ---------- | ------ | ------- |
| S1       | 7.15%      | 10.23% | 26.69%  |
| S2       | 9.87%      | 4.23%  | 6.28%   |
| S3       | 13.57%     | 10.44% | 24.30%  |
| S4       | 53.32%     | 29.58% | 87.49%  |


## 3. WER by Provider x Language


| Language | elevenlabs | sarvam | whisper |
| -------- | ---------- | ------ | ------- |
| en-IN    | 9.87%      | 4.23%  | 6.28%   |
| hi       | 7.15%      | 10.23% | 26.69%  |
| hi-en    | 13.57%     | 10.44% | 24.30%  |
| ka       | 51.42%     | 29.48% | 89.76%  |
| kn-en    | 57.77%     | 29.81% | 82.20%  |


### CER by Provider x Language


| Language | elevenlabs | sarvam | whisper |
| -------- | ---------- | ------ | ------- |
| en-IN    | 6.21%      | 2.80%  | 3.76%   |
| hi       | 2.74%      | 2.70%  | 10.37%  |
| hi-en    | 3.71%      | 2.64%  | 10.14%  |
| ka       | 18.16%     | 11.09% | 44.93%  |
| kn-en    | 40.36%     | 7.52%  | 48.93%  |


## 4. Public vs Personal Recordings


| Provider   | Source      | Files | Mean WER | Mean CER |
| ---------- | ----------- | ----- | -------- | -------- |
| elevenlabs | indicvoices | 14    | 29.28%   | 10.45%   |
| elevenlabs | personal    | 7     | 32.51%   | 19.42%   |
| elevenlabs | svarah      | 7     | 9.87%    | 6.21%    |
| sarvam     | indicvoices | 14    | 19.86%   | 6.90%    |
| sarvam     | personal    | 7     | 18.74%   | 4.73%    |
| sarvam     | svarah      | 7     | 4.23%    | 2.80%    |
| whisper    | indicvoices | 14    | 58.23%   | 27.65%   |
| whisper    | personal    | 7     | 49.11%   | 26.77%   |
| whisper    | svarah      | 7     | 6.28%    | 3.76%    |


## 5. Code-Mixed vs Monolingual Performance


| Provider   | Type        | Files | Mean WER | Mean CER |
| ---------- | ----------- | ----- | -------- | -------- |
| elevenlabs | Code-mixed  | 7     | 32.51%   | 19.42%   |
| elevenlabs | Monolingual | 21    | 22.81%   | 9.04%    |
| sarvam     | Code-mixed  | 7     | 18.74%   | 4.73%    |
| sarvam     | Monolingual | 21    | 14.65%   | 5.53%    |
| whisper    | Code-mixed  | 7     | 49.11%   | 26.77%   |
| whisper    | Monolingual | 21    | 40.91%   | 19.69%   |


## 6. Biggest Provider Divergences

Files where providers disagreed most:

### `indicvoices_ka_06.wav` (spread: 87.50%)

- elevenlabs: 25.00%
- sarvam: 0.00% **best**
- whisper: 87.50% **worst**

### `suspicious-transaction-1-Kannada.m4a` (spread: 75.68%)

- elevenlabs: 29.73% **best**
- sarvam: 35.14%
- whisper: 105.41% **worst**

### `loan-enquiry-1-Kannada.m4a` (spread: 75.00%)

- elevenlabs: 115.00% **worst**
- sarvam: 40.00% **best**
- whisper: 65.00%

### `indicvoices_ka_01.wav` (spread: 68.75%)

- elevenlabs: 31.25%
- sarvam: 25.00% **best**
- whisper: 93.75% **worst**

### `indicvoices_ka_02.wav` (spread: 67.74%)

- elevenlabs: 51.61%
- sarvam: 25.81% **best**
- whisper: 93.55% **worst**

### `indicvoices_ka_04.wav` (spread: 66.67%)

- elevenlabs: 55.56%
- sarvam: 22.22% **best**
- whisper: 88.89% **worst**

### `debit-card-verification-1-Kannada.m4a` (spread: 61.90%)

- elevenlabs: 28.57%
- sarvam: 14.29% **best**
- whisper: 76.19% **worst**

## 7. Worst Cases per Provider

### SARVAM — Top 5 Worst WER

`**indicvoices_ka_03.wav`** (ka, S4) — WER: 57.89%

- **Reference:** ಎಸ್ ಬಿ ಅಕೌಂಟಾ ಕೆನರ ಬ್ಯಾಂಕ್ ಅಕೌಂಟಾ ಮುಂತಾದವು ಅದರಲ್ಲಿ ಉಳಿತಾಯ ಖಾತೆನ ಚಾಲ್ತಿ ಖಾತೆನ ವಿವರಿಸಬೇಕು ಈ ರೀತಿ ಉಳಿತಾಯ ಖಾತೆ ಅಂದರೆ ಏನಾಗುತ್...
- **Hypothesis:** ಎಸ್ ಬಿ ಅಕೌಂಟಾ ಕೆನರಾ ಬ್ಯಾಂಕ್ ಅಕೌಂಟಾ ಮುಂತಾದವು ಅದ್ರಲ್ಲಿ ಉಳಿತಾಯ ಖಾತೆನ ಚಾಲ್ತಿ ಖಾತೆನ ವಿವರಿಸಬೇಕು ಈ ರೀತಿ ಉಳಿತಾಯ ಖಾತೆ ಆದರೆ ಏನಾಗುತ...

`**indicvoices_ka_05.wav`** (ka, S4) — WER: 42.11%

- **Reference:** ಮನೆಯಲ್ಲೇ ಎಲ್ಲರ್ಗು ಏನು ಬೇಕೊ ಎಲ್ಲ ಕೇಳಿ ಮಾಡಿ ಹಾಕ್ತೀನಿ ಎಲ್ಲರ್ಗು ಮಾಡ್ಕೊಡ್ತೀನಿ ನಾನು ಮಸಾಲೆ ಐಟಮ್ಮು ಆಚೆ ಆಚೆ ಫುಡ್ಡು ಎಲ್ಲ ಅವಾಯ್ಡ್ ಮ...
- **Hypothesis:** ಮನೆಯಲ್ಲೇ ಎಲ್ಲರಿಗೂ ಏನು ಬೇಕು ಎಲ್ಲ ಕೇಳಿ ಮಾಡಿ ಹಾಕ್ತೀನಿ ಎಲ್ಲರಿಗೂ ಮಾಡಿಕೊಡ್ತೀನಿ ನಾನು ಮಸಾಲೆ ಐಟಂ ಆಚೆ ಆಚೆ ಫುಡ್ ಎಲ್ಲ ವೈರ್ ಮಾಡಿಬಿಡ್ತ...

`**loan-enquiry-1-Kannada.m4a`** (kn-en, S4) — WER: 40.00%

- **Reference:** ಹಲೋ ಸರ್ ನಿಮ್ಮ ಪರ್ಸನಲ್ ಲೋನ್ ಇನ್ಕ್ವೈರಿ ಬಗ್ಗೆ ಕಾಲ್ ಮಾಡ್ತಿದ್ದೀನಿ ನಿಮಗೆ ಲೋನ್ ಯಾವ ಪರ್ಪಸ್‌ಗೆ ಬೇಕು ಅಂತ ಸ್ವಲ್ಪ ಎಕ್ಸ್‌ಪ್ಲೈನ್ ಮಾಡಬಹ...
- **Hypothesis:** ನಮಸ್ಕಾರ ಸರ್, ನಿಮ್ಮ ಪರ್ಸನಲ್ ಲೋನ್ ಎನ್ಕ್ವೈರಿ ಬಗ್ಗೆ ಕಾಲ್ ಮಾಡ್ತಾ ಇದೀನಿ. ನಿಮಗೆ ಲೋನ್ ಯಾವ ಪರ್ಪಸ್ಗೆ ಬೇಕು ಅಂತ ಸ್ವಲ್ಪ ಎಕ್ಸ್ಪ್ಲೈನ್ ಮ...

`**suspicious-transaction-1-Kannada.m4a`** (kn-en, S4) — WER: 35.14%

- **Reference:** ಹಲೋ ಸರ್ ನಾನು ಬ್ಯಾಂಕ್ ಫ್ರಾಡ್ ಮಾನಿಟರಿಂಗ್ ಟೀಮ್ ಇಂದ ಕಾಲ್ ಮಾಡ್ತಿದ್ದೀನಿ ನಿಮ್ಮ ಡೆಬಿಟ್ ಕಾರ್ಡ್ ಮೇಲೆ ಒಂದು ಅನ್‌ಯೂಜುಅಲ್ ಆನ್‌ಲೈನ್ ಟ್ರ...
- **Hypothesis:** ಹಲೋ ಸರ್ ನಾನು ಬ್ಯಾಂಕ್ ಫ್ರಾಡ್ ಮಾನಿಟರಿಂಗ್ ಟೀಮ್ ಇಂದ ಕಾಲ್ ಮಾಡ್ತಾಯಿದ್ದೀನಿ ನಿಮ್ಮ ಡೆಬಿಟ್ ಕಾರ್ಡ್ ಮೇಲೆ ಒಂದು ಅನ್ಯೂಶುವಲ್ ಆನ್ಲೈನ್ ಟ್ರ...

`**indicvoices_ka_07.wav`** (ka, S4) — WER: 33.33%

- **Reference:** ಮರುಪಾವತಿಸಬೇಕಾಗಿ ವಿನಂತಿಸುತ್ತೇನೆ ಆ ಆರ್ಡರ್ನ ಸಂಖ್ಯೆಯು ಮತ್ತು ಹಣ ಪಾವತಿಸಿದ ಮಾಹಿತಿಯಂತ
- **Hypothesis:** ಮರುಪಾವತಿಸಬೇಕಾಗಿ ವಿನಂತಿಸುತ್ತೇನೆ ಆ ಆರ್ಡರ್ ನ ಸಂಖ್ಯೆಯು ಮತ್ತು ಹಣ ಪಾವತಿಸಿದ ಮಾಹಿತಿಯಂತಹ

### ELEVENLABS — Top 5 Worst WER

`**loan-enquiry-1-Kannada.m4a`** (kn-en, S4) — WER: 115.00%

- **Reference:** ಹಲೋ ಸರ್ ನಿಮ್ಮ ಪರ್ಸನಲ್ ಲೋನ್ ಇನ್ಕ್ವೈರಿ ಬಗ್ಗೆ ಕಾಲ್ ಮಾಡ್ತಿದ್ದೀನಿ ನಿಮಗೆ ಲೋನ್ ಯಾವ ಪರ್ಪಸ್‌ಗೆ ಬೇಕು ಅಂತ ಸ್ವಲ್ಪ ಎಕ್ಸ್‌ಪ್ಲೈನ್ ಮಾಡಬಹ...
- **Hypothesis:** नमस्कार सर। निम् पर्सनल लोन इन्क्वायरी बगे कॉल मरता इडीनी। निमगे लोन याव पर्पस गे बेको अन्त स्वल्पा एक्सप्लेन माडबोडा? (...

`**indicvoices_ka_05.wav`** (ka, S4) — WER: 94.74%

- **Reference:** ಮನೆಯಲ್ಲೇ ಎಲ್ಲರ್ಗು ಏನು ಬೇಕೊ ಎಲ್ಲ ಕೇಳಿ ಮಾಡಿ ಹಾಕ್ತೀನಿ ಎಲ್ಲರ್ಗು ಮಾಡ್ಕೊಡ್ತೀನಿ ನಾನು ಮಸಾಲೆ ಐಟಮ್ಮು ಆಚೆ ಆಚೆ ಫುಡ್ಡು ಎಲ್ಲ ಅವಾಯ್ಡ್ ಮ...
- **Hypothesis:** ಮನೆಯಲ್ಲೇ ಎಲ್ಲಾರಿಗೂ ಏನ್ ಬೇಕೋ ಎಲ್ಲಾ ಕೇಳಿ ಮಾಡಿ ಹಾಕ್ತೀನಿ. ಎಲ್ಲಾರಿಗೂ ಮಾಡಿಕೊಟ್ಟಿದ್ದೀನಿ ನಾನು. ಮಸಾಲಾ ಐಟಂ ಆಗಿ (ಕೆಫಿ ಮುರಿಯುವ ಶಬ್ದ)...

`**indicvoices_ka_03.wav`** (ka, S4) — WER: 68.42%

- **Reference:** ಎಸ್ ಬಿ ಅಕೌಂಟಾ ಕೆನರ ಬ್ಯಾಂಕ್ ಅಕೌಂಟಾ ಮುಂತಾದವು ಅದರಲ್ಲಿ ಉಳಿತಾಯ ಖಾತೆನ ಚಾಲ್ತಿ ಖಾತೆನ ವಿವರಿಸಬೇಕು ಈ ರೀತಿ ಉಳಿತಾಯ ಖಾತೆ ಅಂದರೆ ಏನಾಗುತ್...
- **Hypothesis:** ಎಸ್ ಬಿ ಅಕೌಂಟಾ , ಕೆನರಾ ಬ್ಯಾಂಕ್ ಅಕೌಂಟಾ ಮುಂತಾದ ಅದರಲ್ಲಿ ಉಳಿತಾಯ ಖಾತೆನ ಚಾಲ್ತಿ ಖಾತೆನ ವಿವರಿಸ್ಬೇಕು. ಈ ರೀತಿ ಉಳಿತಾಯ ಖಾತೆ ಇದ್ರೆ ಏನಾಗ...

`**indicvoices_ka_04.wav`** (ka, S4) — WER: 55.56%

- **Reference:** ನಲ್ವತ್ತು ಶೇಕಡಾ ಡಿಸ್ಕೌಂಟ್ ಎಲ್ಲ ಹಣ್ಣಿನ ರಸಗಳ ಮೇಲೂ ಅನ್ವಯ ಆಗುತ್ತಾ
- **Hypothesis:** ನಲವತ್ತು ಶೇಕಡ ಡಿಸ್ಕಾಂಟ್ ಎಲ್ಲಾ ಹಣ್ಣಿನ ರಸಗಳ ಮೇಲೂ ಅನ್ವಯ ಆಗತ್ತಾ?

`**indicvoices_ka_02.wav`** (ka, S4) — WER: 51.61%

- **Reference:** ತುಂಬವೂ ಸ್ವಲ್ಪ ಚಿಕ್ಕದಾಗಿತ್ತು ಸೊ ಅದಕ್ಕಾಗಿ ನಾನು ಒಂದು ಎಕ್ಸ್ಟ್ರಾ ಲೇಸನ್ನು ಆರ್ಡರ್ ಮಾಡಿದೆ ಅದು ಕೂಡ ಇಮಿಡಿಯೇಟಾಗೆ ಬಂದಿತ್ತು ಈಗ ಬಿಸ್ ಬ...
- **Hypothesis:** ತುಂಬಾ ಸ್ವಲ್ಪ ಚಿಕ್ಕದಾಗಿದೆ. ಸೋ ಅದಕ್ಕಾಗಿ ನಾನು ಒಂದು ಎಕ್ಸ್‌ಟ್ರಾ ಲೇಸನ್ ಆರ್ಡರ್ ಮಾಡಿದೆ. ಅದು ಕೂಡಾ ಇಮೀಡಿಯಟ್ ಆಗಿ ಬಂದಿತು. ಈಗ ಬಿಗ್ ಬ್...

### WHISPER — Top 5 Worst WER

`**suspicious-transaction-1-Kannada.m4a`** (kn-en, S4) — WER: 105.41%

- **Reference:** ಹಲೋ ಸರ್ ನಾನು ಬ್ಯಾಂಕ್ ಫ್ರಾಡ್ ಮಾನಿಟರಿಂಗ್ ಟೀಮ್ ಇಂದ ಕಾಲ್ ಮಾಡ್ತಿದ್ದೀನಿ ನಿಮ್ಮ ಡೆಬಿಟ್ ಕಾರ್ಡ್ ಮೇಲೆ ಒಂದು ಅನ್‌ಯೂಜುಅಲ್ ಆನ್‌ಲೈನ್ ಟ್ರ...
- **Hypothesis:** Hello Sir, I am calling from the Bank Fraud Monitoring Team. An unusual online transaction has been tried on your debit ...

`**indicvoices_ka_05.wav`** (ka, S4) — WER: 94.74%

- **Reference:** ಮನೆಯಲ್ಲೇ ಎಲ್ಲರ್ಗು ಏನು ಬೇಕೊ ಎಲ್ಲ ಕೇಳಿ ಮಾಡಿ ಹಾಕ್ತೀನಿ ಎಲ್ಲರ್ಗು ಮಾಡ್ಕೊಡ್ತೀನಿ ನಾನು ಮಸಾಲೆ ಐಟಮ್ಮು ಆಚೆ ಆಚೆ ಫುಡ್ಡು ಎಲ್ಲ ಅವಾಯ್ಡ್ ಮ...
- **Hypothesis:** ಮಾನೆಯಲ್ಲಿ ಎಲ್ಲಾ ಕೇಳಿ ಅಮ್ಮಾ ಡಾಕ್ತಿನ್ನು ಮಾಡ್ಕೊಸ್ತಿನ್ನಾನು ಮಸಾಲ ಆಯ್ಟಮ್ಮು ಆಜ್ಯ ಆಜ್ಯ ಕುಡ್ಡು ಎಲ್ಲಾ ವಾಯಡ್ ಮಾಡ್ಗೊಡುತ್ತಿಂದು.

`**indicvoices_ka_01.wav`** (ka, S4) — WER: 93.75%

- **Reference:** ನಂತರ ಅದು ಅದಾದ ನಂತರ ನನ್ನ ವಿವಿದ ಕಾರ್ಯಕ್ರಮಗಳು ಅಥ್ವಾ ಆಟಗಳು ಅಂತ ಹೇಳಿದರೆ ನಾನು ಕಬಡ್ಡಿ ಆಡೋದು ಇಷ್ಟ ವಾಲಿಬಾಲ್
- **Hypothesis:** ಅದಾದ ನಂತರಮನ್ನಾ ಇವೀದ ಕರೆಕರಮಗಳು ಅಥವಾ ಆಟಗಳು ಅಂತರ ವೇಳಿದರೆ ನನು ಕಬಡಿ ಆಡು, ಮುಗಿಷ್ಟಾ, ವಲಿಬಾಳ್ ಮುಗಿಷ್ಟಾ

`**indicvoices_ka_02.wav`** (ka, S4) — WER: 93.55%

- **Reference:** ತುಂಬವೂ ಸ್ವಲ್ಪ ಚಿಕ್ಕದಾಗಿತ್ತು ಸೊ ಅದಕ್ಕಾಗಿ ನಾನು ಒಂದು ಎಕ್ಸ್ಟ್ರಾ ಲೇಸನ್ನು ಆರ್ಡರ್ ಮಾಡಿದೆ ಅದು ಕೂಡ ಇಮಿಡಿಯೇಟಾಗೆ ಬಂದಿತ್ತು ಈಗ ಬಿಸ್ ಬ...
- **Hypothesis:** ತುಮ್ಬ ಸಲ್ಪ ಶಿಕ್ಕದಾಗಿದ್ದು. ಸೋದಕ್ಕಾಗಿ ನಾನು ಒಂದೆ ಎಕ್ಷಾಲೇಸನ್ನು ಆಡರ್ಮಾಡಿದೆ. ಅದು ಕೂಡೆ ಇಮ್ಮಿಡಿಟಾಗೆ ಬಂದಿದ್ದು.

`**indicvoices_ka_03.wav`** (ka, S4) — WER: 92.11%

- **Reference:** ಎಸ್ ಬಿ ಅಕೌಂಟಾ ಕೆನರ ಬ್ಯಾಂಕ್ ಅಕೌಂಟಾ ಮುಂತಾದವು ಅದರಲ್ಲಿ ಉಳಿತಾಯ ಖಾತೆನ ಚಾಲ್ತಿ ಖಾತೆನ ವಿವರಿಸಬೇಕು ಈ ರೀತಿ ಉಳಿತಾಯ ಖಾತೆ ಅಂದರೆ ಏನಾಗುತ್...
- **Hypothesis:** ಅದರಲ್ಲಿ ಉಳಿತಾಯ ಕಾತ್ಯನ್ನು ಚಾಲ್ತಿ ಕಾತ್ಯನ್ನು ವಿವರಿಸ್ಪೆಕ್ಕು.

## 8. Pattern Analysis

### Number Handling

`**indicvoices_hi_06.wav`**

- **Reference:** देखिए मैंने कितने चार हज़ार का ऑर्डर बुक किया है और आपने मुझे डिस्काउंट नहीं दिया बिल्कुल बिल्कुल भी डिस्काउंट नहीं दिया है इसपे मुझे आपसे चालीस प्रतिश
- **sarvam** (WER 9.59%): देखिए मैंने कितना चार हज़ार का ऑर्डर बुक किया है और आपने मुझे डिस्काउंट नहीं दिया बिल्कुल बिल्कुल भी डिस्काउंट नहीं दिया है इस पर मुझे आप से चालीस प्र
- **elevenlabs** (WER 10.96%): देखिए मैंने कितना चार हज़ार का ऑर्डर बुक किया है और आपने मुझे डिस्काउंट नहीं दिया। बिल्कुल बिल्कुल भी डिस्काउंट नहीं दिया है। इसमें मुझे आप 40 प्रतिशत 
- **whisper** (WER 43.84%): देखी मैंने किता 4000 का order की आ है और आपने मुझे discount नहीं दिया बिलकुल बिलकुल भी discount नहीं दिया है इस पे मुझे आप 40% discount दे सकते हैं यह

`**indicvoices_hi_07.wav`**

- **Reference:** मेरे पास ऑनलाइन रुपए नही है तो मैं आपको नगद भुगतान कर सकता हूँ
- **sarvam** (WER 21.43%): मेरे पास ऑनलाइन रुपये नहीं है, तो मैं आपको नगर भुगतान कर सकता हूँ।
- **elevenlabs** (WER 7.14%): मेरे पास ऑनलाइन रुपए नहीं है तो मैं आपको नगद भुगतान कर सकता हूं।
- **whisper** (WER 35.71%): मेरे पास ओन्लैन रूपे नहीं है, तो मैं आपको नगर बुक्तान कर सकता हूँ

`**transaction-check-1-hinglish.m4a`**

- **Reference:** हेलो सर मैं बैंक से बोल रहा हूँ हमें आपके कार्ड पर एक अनयूज़ुअल ट्रांज़ैक्शन दिखा है क्या आपने कल अठारह हज़ार पाँच सौ का ऑनलाइन पेमेंट किया था
- **sarvam** (WER 6.90%): हेलो सर मैं बैंक से बोल रहा हूँ हमें आपके कार्ड पर एक अनयूजुअल ट्रांजाक्शन दिखा है क्या आपने कल अठरा हजार पाँच सौ का ऑनलाइन पेमेंट किया था
- **elevenlabs** (WER 10.34%): हैलो सर, मैं बैंक से बोल रहा हूं। हमें आपके कार्ड पर एक अन्यूज़ुअल ट्रांजैक्शन दिखा है। क्या आपने कल अठरह हज़ार पाँच सौ का ऑनलाइन पेमेंट किया था?
- **whisper** (WER 34.48%): Hello Sir, मैं बैंक से बोल रहा हूँ. हमें आपके कार्ड पर एक अन्यूजूल ट्रण्जाक्शन दिखा है. क्या आपने कल अट्रा आजार पांजो का अन्लाइन पेविंट किया था?

### Proper Noun Handling

`**svarah_en_01.wav`**

- **Reference:** How much money is left in my Arunachal Pradesh Rural Bank account?
- **sarvam** (WER 0.00%): How much money is left in my Arunachal Pradesh Rural Bank account?
- **elevenlabs** (WER 0.00%): How much money is left in my Arunachal Pradesh Rural Bank account?
- **whisper** (WER 0.00%): How much money is left in my Arunachal Pradesh rural bank account?

`**svarah_en_02.wav`**

- **Reference:** Will I be able to pay using UPI apps on Hotstar website?
- **sarvam** (WER 0.00%): Will I be able to pay using UPI apps on Hotstar website?
- **elevenlabs** (WER 0.00%): Will I be able to pay using UPI apps on Hotstar website?
- **whisper** (WER 0.00%): Will I be able to pay using UPI apps on Hotstar website?

