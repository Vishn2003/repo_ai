# System Evaluation and Operational Analysis Report

This report evaluates our claims verification system on `dataset/sample_claims.csv` (20 claims) comparing two strategies: **Gemini 3.1 Flash Lite With History** (Strategy A) and **Gemini 3.1 Flash Lite Without History** (Strategy B).

---

## 📊 Strategy Performance Comparison

| Metric | Strategy A: Flash Lite With History | Strategy B: Flash Lite Without History |
| :--- | :--- | :--- |
| **Claim Status Accuracy** | 75.0% | 75.0% |
| **Evidence Standard Accuracy** | 95.0% | 95.0% |
| **Issue Type Accuracy** | 55.0% | 50.0% |
| **Object Part Accuracy** | 85.0% | 80.0% |
| **Severity Accuracy** | 35.0% | 35.0% |
| **Average Latency / Claim** | 15.97 sec | 16.05 sec |
| **Total Pipeline Latency** | 319.5 sec (~5.3 min) | 320.9 sec (~5.3 min) |
| **Total Images Processed** | 29 | 29 |
| **Estimated Input Tokens** | 23482 | 23482 |
| **Estimated Output Tokens** | 5000 | 5000 |
| **Estimated Cost (Sample Set)** | $0.00326 | $0.00326 |

---

## 📈 Detailed Precision / Recall Breakdown

### Strategy A: Flash Lite With History
* **supported**: Precision: 80.0%, Recall: 92.3%, F1: 85.7% (Support: 13)
* **contradicted**: Precision: 50.0%, Recall: 20.0%, F1: 28.6% (Support: 5)
* **not_enough_information**: Precision: 66.7%, Recall: 100.0%, F1: 80.0% (Support: 2)

### Strategy B: Flash Lite Without History
* **supported**: Precision: 80.0%, Recall: 92.3%, F1: 85.7% (Support: 13)
* **contradicted**: Precision: 50.0%, Recall: 20.0%, F1: 28.6% (Support: 5)
* **not_enough_information**: Precision: 66.7%, Recall: 100.0%, F1: 80.0% (Support: 2)

---

## 💸 Cost Analysis & Operational Estimation (Full Test Set - 44 Claims)

Based on the performance metrics and API costs, we estimate the following values to process the full test set of **44 claims** (containing 112 images):

### Gemini 3.1 Flash Lite
- **Images:** 112 images * 258 tokens = 28,896 tokens
- **Text input:** 44 claims * 800 tokens = 35,200 tokens
- **Total input tokens:** 64,096 tokens
- **Total output tokens:** 44 claims * 250 tokens = 11,000 tokens
- **Pricing:** Input: $0.075/1M, Output: $0.30/1M
- **Total Cost:** (64,096 * $0.075 / 1M) + (11,000 * $0.30 / 1M) = **$0.00811** (under 1 cent!)

---

## 🛡️ Rate Limiting & Throttling Strategy
Gemini API has a standard limit of 5 RPM (Requests Per Minute) on our free tier.
Our pipeline implements a rate-limiting strategy:
1. **RPM Sleep**: An intentional 12.0-second delay between processing each claim is enforced, guaranteeing that the request rate stays under 5 RPM.
2. **Exponential Backoff**: If the API returns a rate-limiting exception (HTTP 429), the code waits for `2**attempt` seconds before retrying, up to a maximum of 3 retries.
3. **Image Compression**: Pre-resizing images to a maximum dimension of 1024x1024 reduces the data payload, making requests faster and lighter on the API context.

---

## 🏆 Final Recommendation
We recommend **Gemini 3.1 Flash Lite (With History)**. It provides context about historical exaggeration and repeat submissions, enabling the model to accurately flag risk while maintaining high claim verification accuracy.
