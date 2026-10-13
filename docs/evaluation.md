# PII Guard: Detection Evaluation & Synthetic Fixture Specification
### Cadence Financial Group — Cyber Strategy & AI Governance Case Study
**Evaluation Ownership:** Nancy (Member 4 Coding Deliverables) & Tirth (Member 5 Integration)

---

## 1. Overview & Objectives

In regulatory environments such as Cadence Financial Group, PII detection systems cannot be evaluated solely on gross accuracy. A model that misses a single Social Security Number or banking credential introduces unacceptable compliance and breach exposure.

The **Evaluation Subsystem** (`src/pii_guard/reporting/metrics.py`) provides a rigorous, mathematical framework to evaluate PII detection and classification models against verified ground truth annotations without relying on unredacted live customer data.

---

## 2. Bipartite Matching Algorithm

Evaluating character-level entity spans requires solving a bipartite matching problem between:
- **Ground Truth Entities ($G$):** Verified real or synthetic PII spans $[s_g, e_g]$ with category $c_g$.
- **Predicted Entities ($P$):** Detector-identified spans $[s_p, e_p]$ with category $c_p$.

### Matching Rules
1. **Category Agreement:** A prediction can only match a ground truth annotation if $c_p = c_g$.
2. **One-to-One Match:** Each ground truth span can match at most one prediction. Duplicate predictions for the same span are treated as False Positives ($FP$).
3. **Greedy Assignment:** Predictions are matched to the best-overlapping available ground truth entity.

### Matching Strategies
The engine supports three matching criteria:
- **`exact`:** Strict boundary alignment: $s_p = s_g$ and $e_p = e_g$.
- **`overlap`:** Any non-zero intersection: $\max(s_p, s_g) < \min(e_p, e_g)$.
- **`iou_50`:** Intersection-over-Union thresholded at $\ge 0.50$:
  $$\text{IoU} = \frac{\max(0, \min(e_p, e_g) - \max(s_p, s_g))}{\max(e_p, e_g) - \min(s_p, s_g)} \ge 0.50$$

---

## 3. Mathematical Metrics & Formulas

| Metric | Formula | Definition & Compliance Significance |
| :--- | :---: | :--- |
| **True Positives ($TP$)** | Count of matched $(p, g)$ pairs | Accurately detected and classified PII entities. |
| **False Positives ($FP$)** | $|P| - TP$ | Spurious detections; leads to over-redaction of non-sensitive text. |
| **False Negatives ($FN$)** | $|G| - TP$ | **Critical Risk Metric:** Leaked PII entities that escaped detection. |
| **Precision** | $\frac{TP}{TP + FP}$ | Proportion of predicted PII that is truly sensitive. |
| **Recall** | $\frac{TP}{TP + FN}$ | Proportion of actual sensitive PII successfully detected. |
| **F1-Score** | $2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$ | Harmonic mean balancing over-redaction against under-redaction. |
| **False Negative Rate ($FNR$)** | $\frac{FN}{TP + FN} = 1 - \text{Recall}$ | **Cadence Primary KPI:** Rate of unmasked PII escaping to downstream AI. |

---

## 4. Zero-Denominator Conventions

Standard mathematical definitions yield undefined division-by-zero errors when ground truth or predictions contain zero elements. The evaluation subsystem implements explicit, auditable zero-denominator rules:

```python
# 1. Both Ground Truth and Predictions are Empty (Clean document correctly recognized)
if total_gt == 0 and total_pred == 0:
    precision = 1.0
    recall = 1.0
    f1 = 1.0
    fnr = 0.0

# 2. Ground Truth is Empty, but Predictions > 0 (Over-detection / False Alarms)
elif total_gt == 0 and total_pred > 0:
    precision = 0.0
    recall = 1.0   # No ground truth was missed
    f1 = 0.0
    fnr = 0.0

# 3. Ground Truth > 0, but Predictions are Empty (Complete Detection Failure)
elif total_gt > 0 and total_pred == 0:
    precision = 1.0
    recall = 0.0
    f1 = 0.0
    fnr = 1.0      # 100% of PII leaked
```

---

## 5. Per-Category Breakdown

In addition to aggregate dataset-level metrics, `evaluate_predictions()` produces an isolated breakdown for each entity category:

```json
{
  "precision": 0.95,
  "recall": 0.98,
  "f1_score": 0.9647,
  "false_negative_rate": 0.02,
  "true_positives": 40,
  "false_positives": 2,
  "false_negatives": 1,
  "by_category": {
    "US_SSN": {
      "support": 10,
      "tp": 10,
      "fp": 0,
      "fn": 0,
      "precision": 1.0,
      "recall": 1.0,
      "f1": 1.0,
      "fnr": 0.0
    },
    "EMAIL_ADDRESS": {
      "support": 15,
      "tp": 14,
      "fp": 1,
      "fn": 1,
      "precision": 0.9333,
      "recall": 0.9333,
      "f1": 0.9333,
      "fnr": 0.0667
    }
  }
}
```

This allows auditors to verify that zero-tolerance categories (such as `US_SSN` and `CREDIT_CARD`) achieve $100\%$ recall ($FNR = 0.00$), even if broader linguistic categories (such as `PERSON` or `LOCATION`) exhibit slight variance.

---

## 6. Synthetic Fixtures & Ground Truth Manifest

Member 4's deliverables include a fully reproducible synthetic fixture generator (`demo_tools/generate_synthetic_samples.py`) and manifest (`demo_samples/manifest.json`):

### Fixture Catalog
| Fixture | Scenario | Categories Covered | Ground Truth Count | Expected Status |
| :--- | :--- | :--- | :---: | :---: |
| `01_synthetic_email.txt` | Standard Customer Inquiry | `PERSON`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `US_SSN` | 4 | PASS |
| `02_synthetic_loan_application.txt` | Residential Mortgage Application | `PERSON`, `US_SSN`, `PHONE_NUMBER`, `US_BANK_NUMBER`, `EMAIL_ADDRESS` | 6 | PASS |
| `03_synthetic_wire_transfer.txt` | Cross-Border Commercial Wire | `PERSON`, `IBAN_CODE`, `ORGANIZATION`, `EMAIL_ADDRESS` | 4 | PASS |
| `04_synthetic_medical_record.txt` | Health Insurance Claim | `PERSON`, `MEDICAL_LICENSE`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `US_SSN` | 5 | PASS |
| `05_synthetic_executive_briefing.txt` | Corporate Board Briefing | `PERSON`, `EMAIL_ADDRESS`, `ORGANIZATION`, `LOCATION` | 5 | PASS |
| `06_synthetic_credit_dispute.txt` | Cardholder Dispute Report | `PERSON`, `CREDIT_CARD`, `EMAIL_ADDRESS`, `PHONE_NUMBER` | 4 | PASS |
| `07_clean_business_memo.txt` | Non-Sensitive Policy Announcement | None (Clean baseline) | 0 | PASS |
| `08_high_density_multi_entity.txt` | High-Volume Batch Record | `PERSON`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `US_SSN`, `CREDIT_CARD`, etc. | 8 | PASS |
| `09_edge_case_formatting.txt` | Unusual Spacing & Obfuscation | `US_SSN`, `PHONE_NUMBER`, `EMAIL_ADDRESS` | 3 | PASS |
| `10_malformed_binary.xyz` | Invalid Format Attack Vector | None (Invalid header) | 0 | FAIL / BLOCKED |

### Generating Fixtures
```bash
# Deterministic generation using PRNG seed 42
python -m demo_tools.generate_synthetic_samples --output-dir demo_samples --seed 42
```

---

## 7. Running Evaluation Tests

The evaluation test suite verifies all mathematical edge cases, matching strategies, and duplicate handling:

```bash
# Run evaluation test suite
pytest tests/evaluation/test_metrics.py -v
```
All 10 test cases run in $< 0.1$ seconds with 100% pass rate.
