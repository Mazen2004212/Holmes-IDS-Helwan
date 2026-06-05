"""
HOLMES IDS -- Anomaly Detection Evaluation Script
=================================================
Evaluates the stacking classifier + isolation forest on the CIC-IDS-2017
dataset and tests with simulated unknown attacks.

Usage:
    python evaluate_anomaly.py
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_score,
                             recall_score)


def load_models():
    """Load all saved model components."""
    model = joblib.load("Models/Models/tst1_stk_classifier.joblib")
    iso_forest = joblib.load("Models/Models/isolation_forest.joblib")
    scaler = joblib.load("Models/Scaler/scaler_minmax.save")
    label_encoder = joblib.load("Models/Label Encoder/lb_encoder.pkl")
    feature_order = joblib.load("Models/Features_Order/features_order.pkl")
    return model, iso_forest, scaler, label_encoder, feature_order


def evaluate_classifier(model, iso_forest, scaler, label_encoder,
                        feature_order, threshold=-0.000001):
    """Evaluate the stacking classifier on the training/test data."""
    print("=" * 60)
    print("  PART 1: Classifier Accuracy on CIC-IDS-2017 Dataset")
    print("=" * 60)

    # Load the full dataset
    df = pd.read_csv("Models/Dt/tst2_Cleaned_CIC_IDS2017_full_week.csv")
    X = df[feature_order]
    y_true_encoded = df["Label"].values

    # Scale features
    X_scaled = pd.DataFrame(scaler.transform(X), columns=feature_order)

    # Predict with the stacking classifier
    y_pred_encoded = model.predict(X_scaled)

    # Decode labels
    y_true_labels = label_encoder.inverse_transform(y_true_encoded)
    y_pred_labels = label_encoder.inverse_transform(y_pred_encoded)

    # Overall accuracy
    acc = accuracy_score(y_true_labels, y_pred_labels)
    f1 = f1_score(y_true_labels, y_pred_labels, average="weighted")
    prec = precision_score(y_true_labels, y_pred_labels, average="weighted",
                           zero_division=0)
    rec = recall_score(y_true_labels, y_pred_labels, average="weighted",
                       zero_division=0)

    print(f"\n  Overall Accuracy:     {acc * 100:.2f}%")
    print(f"  Weighted F1-Score:    {f1 * 100:.2f}%")
    print(f"  Weighted Precision:   {prec * 100:.2f}%")
    print(f"  Weighted Recall:      {rec * 100:.2f}%")
    print(f"  Total Samples:        {len(y_true_labels)}")

    # Per-class classification report
    print(f"\n{'-' * 60}")
    print("  Per-Class Classification Report")
    print(f"{'-' * 60}")
    report = classification_report(y_true_labels, y_pred_labels,
                                   zero_division=0)
    print(report)

    # Confusion matrix
    classes = label_encoder.classes_
    cm = confusion_matrix(y_true_labels, y_pred_labels, labels=classes)
    print(f"{'-' * 60}")
    print("  Confusion Matrix")
    print(f"{'-' * 60}")
    cm_df = pd.DataFrame(cm, index=classes, columns=classes)
    print(cm_df.to_string())
    print()

    return acc, f1


def test_isolation_forest(model, iso_forest, scaler, label_encoder,
                          feature_order, threshold=-0.000001):
    """Test the isolation forest with simulated unknown attacks."""
    print("\n" + "=" * 60)
    print("  PART 2: Isolation Forest -- Unknown Attack Detection")
    print("=" * 60)

    # Load simulated unknown attacks
    df_unknown = pd.read_csv("Models/test/unknown_attacks_simulated.csv")
    X_unknown = df_unknown[feature_order]
    X_unknown_scaled = pd.DataFrame(
        scaler.transform(X_unknown), columns=feature_order
    )

    # Score with isolation forest
    scores = iso_forest.decision_function(X_unknown_scaled)
    flagged_as_unknown = (scores < threshold).sum()
    total = len(scores)

    print(f"\n  Unknown Attack Samples:      {total}")
    print(f"  Flagged as 'Unknown Attack': {flagged_as_unknown} "
          f"({flagged_as_unknown / total * 100:.1f}%)")
    print(f"  Missed (classified as known):{total - flagged_as_unknown}")
    print(f"  Isolation Forest Threshold:  {threshold}")
    print(f"  Score Range:                 [{scores.min():.6f}, "
          f"{scores.max():.6f}]")
    print(f"  Mean Score:                  {scores.mean():.6f}")
    print()

    # What does the classifier predict for these "unknown" samples?
    print(f"{'-' * 60}")
    print("  Classifier predictions on unknown samples:")
    print(f"{'-' * 60}")
    preds = model.predict(X_unknown_scaled)
    pred_labels = label_encoder.inverse_transform(preds)
    unique, counts = np.unique(pred_labels, return_counts=True)
    for label, count in zip(unique, counts):
        pct = count / total * 100
        print(f"    {label:<20} {count:>5} ({pct:.1f}%)")
    print()

    return flagged_as_unknown, total


def test_with_known_attacks(model, iso_forest, scaler, label_encoder,
                            feature_order, threshold=-0.000001):
    """Test how well the combined system detects known attacks in the data."""
    print("\n" + "=" * 60)
    print("  PART 3: Full Pipeline (Isolation Forest + Classifier)")
    print("=" * 60)

    df = pd.read_csv("Models/Dt/tst2_Cleaned_CIC_IDS2017_full_week.csv")
    X = df[feature_order]
    y_true_encoded = df["Label"].values
    y_true_labels = label_encoder.inverse_transform(y_true_encoded)

    X_scaled = pd.DataFrame(scaler.transform(X), columns=feature_order)

    # Run the full pipeline: iso_forest first, then classifier
    scores = iso_forest.decision_function(X_scaled)
    preds_encoded = model.predict(X_scaled)
    preds_labels = label_encoder.inverse_transform(preds_encoded)

    # Apply the anomaly detection logic from anomaly_IDS.py
    final_predictions = []
    for i in range(len(X_scaled)):
        if scores[i] < threshold:
            final_predictions.append("Unknown Attack")
        else:
            final_predictions.append(preds_labels[i])

    final_predictions = np.array(final_predictions)

    # Stats
    benign_true = (y_true_labels == "BENIGN").sum()
    attack_true = (y_true_labels != "BENIGN").sum()
    benign_pred = (final_predictions == "BENIGN").sum()
    attack_pred = ((final_predictions != "BENIGN") &
                   (final_predictions != "Unknown Attack")).sum()
    unknown_pred = (final_predictions == "Unknown Attack").sum()

    print(f"\n  True BENIGN:           {benign_true}")
    print(f"  True ATTACK:           {attack_true}")
    print(f"  Predicted BENIGN:      {benign_pred}")
    print(f"  Predicted ATTACK:      {attack_pred}")
    print(f"  Predicted UNKNOWN:     {unknown_pred}")

    # For attack detection: is it correctly NOT marking attacks as BENIGN?
    attack_mask = y_true_labels != "BENIGN"
    if attack_mask.sum() > 0:
        attacks_correct = ((final_predictions[attack_mask] != "BENIGN")).sum()
        attack_detection_rate = attacks_correct / attack_mask.sum() * 100
        print(f"\n  Attack Detection Rate: {attack_detection_rate:.2f}% "
              f"({attacks_correct}/{attack_mask.sum()}) of actual attacks "
              f"correctly flagged as some kind of attack")

    # For benign: is it correctly marking benign as BENIGN?
    benign_mask = y_true_labels == "BENIGN"
    if benign_mask.sum() > 0:
        benign_correct = (final_predictions[benign_mask] == "BENIGN").sum()
        benign_accuracy = benign_correct / benign_mask.sum() * 100
        print(f"  Benign Accuracy:       {benign_accuracy:.2f}% "
              f"({benign_correct}/{benign_mask.sum()}) of actual benign "
              f"correctly classified")

    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  HOLMES IDS -- Anomaly Detection Model Evaluation")
    print("=" * 60 + "\n")

    model, iso_forest, scaler, label_encoder, feature_order = load_models()

    # Part 1: Classifier accuracy
    acc, f1 = evaluate_classifier(
        model, iso_forest, scaler, label_encoder, feature_order
    )

    # Part 2: Unknown attack detection
    flagged, total = test_isolation_forest(
        model, iso_forest, scaler, label_encoder, feature_order
    )

    # Part 3: Full pipeline
    test_with_known_attacks(
        model, iso_forest, scaler, label_encoder, feature_order
    )

    # Final summary
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Stacking Classifier Accuracy:     {acc * 100:.2f}%")
    print(f"  Stacking Classifier F1 Score:      {f1 * 100:.2f}%")
    print(f"  Unknown Attack Detection Rate:     "
          f"{flagged}/{total} ({flagged / total * 100:.1f}%)")
    print("=" * 60 + "\n")
