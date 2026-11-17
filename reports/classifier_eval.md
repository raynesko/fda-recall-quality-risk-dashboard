# Classifier Evaluation

## Keyword baseline (T3.2.1)

Rules file `data/reference/keyword_rules.yaml` sha256 `54eef7b4996a67dd8431ee4143779bcbecf4e62e1d8f4513f474cb746bca5d3e` (frozen at first evaluation).

### Subset: all (n=300)

macro-F1 0.802 | accuracy 0.837 | coverage (not OTHER) 0.923

```
                    precision    recall  f1-score   support

          ALLERGEN       0.93      0.90      0.92        61
              CGMP       0.69      0.79      0.73        14
           FOREIGN       1.00      0.76      0.86        29
          IMPURITY       0.92      0.96      0.94        25
          LABELING       0.57      0.65      0.60        20
             MICRO       0.98      0.91      0.94        54
             MIXUP       0.85      0.58      0.69        19
             OTHER       0.13      1.00      0.23         3
         PACKAGING       1.00      1.00      1.00         3
           POTENCY       1.00      0.83      0.91        12
PROCESS_SANITATION       0.82      0.69      0.75        13
         SPEC_FAIL       0.77      0.77      0.77        13
         STERILITY       1.00      0.95      0.98        22
        UNAPPROVED       1.00      0.83      0.91        12

          accuracy                           0.84       300
         macro avg       0.83      0.83      0.80       300
      weighted avg       0.90      0.84      0.86       300

```

### Subset: random (n=200)

macro-F1 0.780 | accuracy 0.820 | coverage (not OTHER) 0.900

```
                    precision    recall  f1-score   support

          ALLERGEN       0.96      0.90      0.93        51
              CGMP       0.55      0.86      0.67         7
           FOREIGN       1.00      0.68      0.81        19
          IMPURITY       0.92      0.92      0.92        13
          LABELING       0.62      0.67      0.65        15
             MICRO       0.97      0.90      0.94        41
             MIXUP       0.86      0.55      0.67        11
             OTHER       0.15      1.00      0.26         3
         PACKAGING       1.00      1.00      1.00         2
           POTENCY       1.00      0.83      0.91         6
PROCESS_SANITATION       0.83      0.62      0.71         8
         SPEC_FAIL       0.75      0.75      0.75         8
         STERILITY       1.00      0.91      0.95        11
        UNAPPROVED       1.00      0.60      0.75         5

          accuracy                           0.82       200
         macro avg       0.83      0.80      0.78       200
      weighted avg       0.90      0.82      0.85       200

```

## TF-IDF + logistic regression (T3.2.2)

Config fixed a priori (see module docstring). GroupKFold(5) by normalized firm; out-of-fold (OOF) predictions compared with the keyword baseline on identical rows. 95% CIs: paired bootstrap, 2,000 resamples, seed 42. McNemar exact test on per-row correctness.

### Subset: all (n=300)

| model | macro-F1 | 95% CI | accuracy |
|---|---|---|---|
| TF-IDF + LR (OOF) | 0.677 | 0.627-0.718 | 0.807 |
| Keyword baseline | 0.802 | 0.727-0.844 | 0.837 |

Difference (ML - baseline): -0.126, 95% CI -0.173 to -0.050. McNemar exact p = 0.243 (table both-right/ML-only/base-only/both-wrong = 223/19/28/30).

Target (charter M2/M3, NOT a result): ML macro-F1 >= 0.80 and uplift >= +0.10 with CI excluding 0. Met: macro-F1 no; uplift no.

### Subset: random (n=200)

| model | macro-F1 | 95% CI | accuracy |
|---|---|---|---|
| TF-IDF + LR (OOF) | 0.636 | 0.553-0.696 | 0.785 |
| Keyword baseline | 0.780 | 0.669-0.831 | 0.820 |

Difference (ML - baseline): -0.143, 95% CI -0.203 to -0.042. McNemar exact p = 0.265 (table both-right/ML-only/base-only/both-wrong = 146/11/18/25).

Target (charter M2/M3, NOT a result): ML macro-F1 >= 0.80 and uplift >= +0.10 with CI excluding 0. Met: macro-F1 no; uplift no.

### Per-class report (TF-IDF + LR, OOF, all 300)

```
                    precision    recall  f1-score   support

          ALLERGEN       0.78      0.97      0.86        61
              CGMP       0.68      0.93      0.79        14
           FOREIGN       0.86      0.83      0.84        29
          IMPURITY       0.86      0.76      0.81        25
          LABELING       0.65      0.65      0.65        20
             MICRO       0.86      0.91      0.88        54
             MIXUP       0.50      0.47      0.49        19
             OTHER       0.00      0.00      0.00         3
         PACKAGING       0.00      0.00      0.00         3
           POTENCY       1.00      0.92      0.96        12
PROCESS_SANITATION       0.88      0.54      0.67        13
         SPEC_FAIL       1.00      0.69      0.82        13
         STERILITY       0.95      0.91      0.93        22
        UNAPPROVED       0.82      0.75      0.78        12

          accuracy                           0.81       300
         macro avg       0.70      0.67      0.68       300
      weighted avg       0.80      0.81      0.80       300

```
