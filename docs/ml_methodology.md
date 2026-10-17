
# PRJ_221 – Machine Learning Methodology

## 1. Dataset

The project uses the `LongitudinalEngagement.csv` dataset.

The dataset contains 1,136 records from 142 users, with 8 sequential
observations per user. The `Sequence` variable represents the order of
the course sequence and is not a calendar-based week or month.

The dataset contains engagement and activity variables such as:

- Course views
- Forum consumption
- Forum contribution
- Lecture views
- Activity regularity
- Session count
- Total duration
- Active days
- Final grade

The dataset does not directly contain attendance, task-completion, or
productivity variables.

The dataset is treated as simulated longitudinal learning data, and
results are not interpreted as population-level conclusions about real
students.

## 2. Behavioural Change Index

The dataset does not contain a direct target representing:

- Improving
- Stable
- Declining

Therefore, a Behavioural Change Index (BCI) was constructed.

For each user, behavioural changes between Sequence 1 and Sequence 8
were calculated for the 11 behavioural variables.

Because the variables have different scales, their changes were
standardized using StandardScaler.

The BCI was calculated as the mean of the standardized behavioural
changes across the 11 variables.

A positive BCI indicates an overall positive direction of change across
the selected behavioural variables, while a negative BCI indicates an
overall negative direction.

## 3. Behavioural State

Users were divided into three relative behavioural states using the
25th and 75th percentiles of the BCI distribution:

- Declining: BCI below the 25th percentile
- Stable: BCI between the 25th and 75th percentiles
- Improving: BCI above the 75th percentile

Thresholds obtained from the dataset:

- Declining: BCI < -0.429
- Stable: -0.429 <= BCI <= 0.394
- Improving: BCI > 0.394

The resulting distribution was:

- Stable: 70 users
- Declining: 36 users
- Improving: 36 users

These are relative data-driven categories and should not be interpreted
as absolute measures of a person's overall wellbeing or performance.

## 4. Feature Engineering

The first seven sequences were used as historical input information.

For each behavioural variable, the following features were created:

1. Mean across Sequences 1–7
2. Standard deviation across Sequences 1–7
3. Recent value from Sequence 7
4. Linear trend across Sequences 1–7

This produced 44 input features.

Trend features were calculated using the slope of a linear regression
between Sequence number and the corresponding behavioural variable.

## 5. Random Forest Classification

A Random Forest classifier was trained to predict the behavioural state.

Configuration:

- Number of trees: 200
- Random state: 42
- Class weighting: balanced
- Test size: 20%
- Stratified train/test split
- Training users: 113
- Test users: 29

The model using historical statistics and trend features achieved:

- Accuracy: 68.97%
- Macro F1-score: 0.70

The test set contained only 29 users, so these results should be
interpreted cautiously.

The model is intended to identify behavioural patterns in the available
dataset and does not establish causal relationships.

## 6. Isolation Forest Anomaly Detection

Isolation Forest was used to identify users whose behavioural feature
patterns were unusual relative to the dataset.

Configuration:

- Number of trees: 200
- Contamination assumption: 0.10
- Random state: 42

The model identified:

- 127 normal users
- 15 anomalous users

An anomaly means that the behavioural feature pattern is unusual
relative to the reference dataset. It does not automatically mean that
the behaviour is negative.

## 7. Explainable AI – SHAP

SHAP TreeExplainer was used to explain Random Forest predictions.

For each prediction, SHAP values indicate how individual features
contributed toward or away from the predicted class.

SHAP explanations are interpreted as model explanations, not causal
explanations.

The Random Forest class order is:

- Declining
- Improving
- Stable

## 8. Recommendation Layer

Recommendations are generated using transparent rule-based logic based
on:

- Behavioural state
- Anomaly status

The recommendation layer does not use an LLM to make decisions.

Examples:

- Improving + normal → continue the current positive pattern
- Stable + normal → maintain the current pattern
- Stable + anomaly → review recent activity
- Declining + normal → monitor recent activity and consider support
- Declining + anomaly → timely review and support

## 9. Alert Priority

Alert priority is generated using explicit rules:

| Behaviour State | Anomaly | Priority |
|---|---|---|
| Declining | Yes | High |
| Declining | No | Medium |
| Stable | Yes | Medium |
| Stable | No | Low |
| Improving | Yes | Medium |
| Improving | No | Low |

Priority represents the software's monitoring priority and is not a
diagnosis or judgement about a person.

## 10. Saved ML Artifacts

The following files are saved in the `models/` directory:

- `random_forest_v2.pkl`
- `isolation_forest.pkl`
- `anomaly_scaler.pkl`
- `feature_columns.json`

`feature_columns.json` preserves the exact 44-feature order expected by
the Random Forest model.

## 11. Important Limitations

1. The dataset contains only 142 users.
2. The target is engineered rather than directly labelled.
3. Behavioural state is defined relative to the BCI distribution.
4. The target uses Sequence 1-to-8 change, while prediction features
   use historical information through Sequence 7.
5. The current evaluation uses a single train/test split and therefore
   should not be treated as a definitive estimate of generalization.
6. The dataset represents simulated learning data and should not be
   generalized directly to real-world populations.
7. Model feature importance and SHAP values describe model behaviour;
   they do not establish causation.
8. Anomaly detection identifies unusual patterns, not necessarily
   undesirable behaviour.
