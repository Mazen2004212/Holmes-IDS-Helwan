"""
Continual Learning for HOLMES IDS.
===================================
Stores flow features from live capture, allows admin relabeling,
and triggers full model retraining with evaluation gate.
"""

import hashlib
import json
import os
import shutil
import threading
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

# Try to import SMOTE for class balancing
try:
    from imblearn.over_sampling import SMOTE
    HAS_SMOTE = True
except ImportError:
    HAS_SMOTE = False
    print("[Warning] imbalanced-learn not installed. SMOTE not available.")


# ========== Constants ========== #

MODELS_DIR = "Models/Models"
CANDIDATE_DIR = "Models/candidate"
ROLLBACK_DIR = "Models/rollback"
SCALER_DIR = "Models/Scaler"
ENCODER_DIR = "Models/Label Encoder"
FEATURES_DIR = "Models/Features_Order"
TRAINING_CSV = "Models/Dt/tst2_Cleaned_CIC_IDS2017_full_week.csv"

# Promotion thresholds
MIN_F1_THRESHOLD = 0.95
MAX_FPR_THRESHOLD = 0.05
MIN_SAMPLES_PER_CLASS = 10

# Global lock to prevent concurrent retrains
_retrain_lock = threading.Lock()
_retrain_status = {"running": False, "progress": "", "error": None}


# ========== Feature Versioning ========== #

def get_feature_version(feature_order):
    """Generate a hash of the feature order for versioning."""
    feature_str = ",".join(feature_order)
    return hashlib.md5(feature_str.encode()).hexdigest()[:8]


# ========== Store Flow Features ========== #

def store_flow_features(conn, features_dict, predicted_label, confidence,
                        feature_order, source="live_capture"):
    """
    Store extracted flow features in the training_data table.
    The predicted_label is stored separately from human_label.
    Only human-labeled samples will be used for retraining.
    """
    try:
        feature_version = get_feature_version(feature_order)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO training_data
               (features_json, predicted_label, confidence, feature_version, source)
               VALUES (?, ?, ?, ?, ?)""",
            (json.dumps(features_dict), predicted_label, confidence,
             feature_version, source)
        )
        conn.commit()
    except Exception as e:
        print(f"[Store Training Data Error] {e}")


def store_batch_features(conn, batch, feature_order):
    """Store a batch of flow features at once (for efficiency)."""
    try:
        feature_version = get_feature_version(feature_order)
        cursor = conn.cursor()
        cursor.executemany(
            """INSERT INTO training_data
               (features_json, predicted_label, confidence, feature_version, source)
               VALUES (?, ?, ?, ?, ?)""",
            [(json.dumps(item['features']), item['predicted_label'],
              item.get('confidence'), feature_version, 'live_capture')
             for item in batch]
        )
        conn.commit()
    except Exception as e:
        print(f"[Batch Store Error] {e}")


# ========== Training Data Stats ========== #

def get_training_stats(conn):
    """Get training data statistics."""
    try:
        cursor = conn.cursor()

        # Total counts
        cursor.execute("SELECT COUNT(*) FROM training_data")
        total = cursor.fetchone()[0]

        # Human-labeled counts
        cursor.execute(
            "SELECT COUNT(*) FROM training_data WHERE human_label IS NOT NULL"
        )
        labeled = cursor.fetchone()[0]

        # Per-class distribution (human labels)
        cursor.execute(
            """SELECT human_label, COUNT(*) FROM training_data
               WHERE human_label IS NOT NULL
               GROUP BY human_label ORDER BY COUNT(*) DESC"""
        )
        class_dist = {row[0]: row[1] for row in cursor.fetchall()}

        # Per-class distribution (predicted)
        cursor.execute(
            """SELECT predicted_label, COUNT(*) FROM training_data
               GROUP BY predicted_label ORDER BY COUNT(*) DESC"""
        )
        predicted_dist = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            "total": total,
            "labeled": labeled,
            "unlabeled": total - labeled,
            "class_distribution": class_dist,
            "predicted_distribution": predicted_dist,
        }
    except Exception as e:
        print(f"[Stats Error] {e}")
        return {"total": 0, "labeled": 0, "unlabeled": 0,
                "class_distribution": {}, "predicted_distribution": {}}


def get_training_samples(conn, limit=100, offset=0, filters=None):
    """Get training data samples with optional filters for admin review.

    Args:
        filters: dict with optional keys:
            - label: predicted_label filter
            - labeled: 'yes'|'no' for human_label status
            - source: source filter
            - date_from: start date (YYYY-MM-DD)
            - date_to: end date (YYYY-MM-DD)
    """
    try:
        where_clauses = []
        params = []
        filters = filters or {}

        if filters.get("label"):
            where_clauses.append("predicted_label = ?")
            params.append(filters["label"])
        if filters.get("labeled") == "yes":
            where_clauses.append("human_label IS NOT NULL")
        elif filters.get("labeled") == "no":
            where_clauses.append("human_label IS NULL")
        if filters.get("source"):
            where_clauses.append("source = ?")
            params.append(filters["source"])
        if filters.get("date_from"):
            where_clauses.append("created_at >= ?")
            params.append(filters["date_from"] + " 00:00:00")
        if filters.get("date_to"):
            where_clauses.append("created_at <= ?")
            params.append(filters["date_to"] + " 23:59:59")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        cursor = conn.cursor()
        cursor.execute(
            f"""SELECT id, predicted_label, confidence, human_label, source,
                      created_at FROM training_data
               {where_sql}
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            params + [limit, offset]
        )
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[Get Samples Error] {e}")
        return []


def update_human_label(conn, sample_id, human_label):
    """Set the human-verified label for a training sample."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE training_data SET human_label = ? WHERE id = ?",
            (human_label, sample_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"[Update Label Error] {e}")
        return False


# ========== Retrain Jobs ========== #

def get_retrain_history(conn, limit=10):
    """Get retraining job history."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM retrain_jobs ORDER BY started_at DESC LIMIT ?""",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[Retrain History Error] {e}")
        return []


def get_retrain_status():
    """Get current retrain status."""
    return _retrain_status.copy()


# ========== Model Retraining ========== #

def retrain_models(conn, started_by="admin"):
    """
    Full model retraining pipeline:
    1. Load original training CSV + human-labeled samples from DB
    2. Validate feature compatibility
    3. Apply SMOTE for class balancing
    4. Full retrain stacking classifier + isolation forest
    5. Save to candidate directory
    6. Evaluate on holdout set
    7. Promote if metrics pass thresholds
    8. Keep previous model as rollback
    """
    global _retrain_status

    if not _retrain_lock.acquire(blocking=False):
        return {"error": "A retraining job is already running."}

    try:
        _retrain_status = {"running": True, "progress": "Starting...", "error": None}

        # Create retrain job record
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO retrain_jobs (status, started_by) VALUES (?, ?)",
            ("running", started_by)
        )
        conn.commit()
        job_id = cursor.lastrowid

        # Step 1: Load original training data
        _retrain_status["progress"] = "Loading original training data..."
        feature_order = joblib.load(f"{FEATURES_DIR}/features_order.pkl")
        label_encoder = joblib.load(f"{ENCODER_DIR}/lb_encoder.pkl")

        original_df = pd.read_csv(TRAINING_CSV)
        X_orig = original_df[feature_order]
        y_orig = original_df["Label"]

        # Step 2: Load human-labeled samples from DB
        _retrain_status["progress"] = "Loading human-labeled samples..."
        cursor.execute(
            """SELECT features_json, human_label FROM training_data
               WHERE human_label IS NOT NULL"""
        )
        rows = cursor.fetchall()

        if len(rows) < MIN_SAMPLES_PER_CLASS:
            error_msg = (
                f"Not enough human-labeled samples ({len(rows)}). "
                f"Need at least {MIN_SAMPLES_PER_CLASS}."
            )
            _update_job(conn, job_id, "failed", error_message=error_msg)
            _retrain_status = {"running": False, "progress": error_msg, "error": error_msg}
            return {"error": error_msg}

        # Parse DB samples
        new_features = []
        new_labels = []
        for row in rows:
            features = json.loads(row[0])
            label = row[1]
            feature_values = [features.get(f, 0) for f in feature_order]
            new_features.append(feature_values)
            # Encode label
            if label in list(label_encoder.classes_):
                new_labels.append(label_encoder.transform([label])[0])
            else:
                # Skip unknown labels (e.g., "Unknown Attack" can't be trained on)
                continue

        if not new_labels:
            error_msg = "No valid labeled samples (labels must match existing classes)."
            _update_job(conn, job_id, "failed", error_message=error_msg)
            _retrain_status = {"running": False, "progress": error_msg, "error": error_msg}
            return {"error": error_msg}

        new_df = pd.DataFrame(new_features, columns=feature_order)
        new_y = pd.Series(new_labels)

        # Combine original + new data
        X_combined = pd.concat([X_orig, new_df], ignore_index=True)
        y_combined = pd.concat([y_orig, new_y], ignore_index=True)

        # Step 3: Train/test split
        _retrain_status["progress"] = "Splitting data..."
        X_train, X_test, y_train, y_test = train_test_split(
            X_combined, y_combined, test_size=0.2, random_state=42,
            stratify=y_combined
        )

        # Step 4: Scale
        _retrain_status["progress"] = "Scaling features..."
        scaler = joblib.load(f"{SCALER_DIR}/scaler_minmax.save")
        X_train_scaled = pd.DataFrame(
            scaler.transform(X_train), columns=feature_order
        )
        X_test_scaled = pd.DataFrame(
            scaler.transform(X_test), columns=feature_order
        )

        # Step 5: Apply SMOTE for class balancing (on training set only)
        if HAS_SMOTE:
            _retrain_status["progress"] = "Applying SMOTE for class balancing..."
            try:
                smote = SMOTE(random_state=42, k_neighbors=min(5, min(
                    pd.Series(y_train).value_counts().values) - 1))
                X_train_balanced, y_train_balanced = smote.fit_resample(
                    X_train_scaled, y_train
                )
            except Exception as e:
                print(f"[SMOTE Warning] Falling back without SMOTE: {e}")
                X_train_balanced, y_train_balanced = X_train_scaled, y_train
        else:
            X_train_balanced, y_train_balanced = X_train_scaled, y_train

        # Step 6: Evaluate old model on test set (baseline)
        _retrain_status["progress"] = "Evaluating old model..."
        old_model = joblib.load(f"{MODELS_DIR}/tst1_stk_classifier.joblib")
        old_preds = old_model.predict(X_test_scaled)
        old_acc = accuracy_score(y_test, old_preds)
        old_f1 = f1_score(y_test, old_preds, average="weighted", zero_division=0)

        # Step 7: Retrain
        _retrain_status["progress"] = "Retraining stacking classifier (this may take several minutes)..."
        from sklearn.base import clone
        new_model = clone(old_model)
        new_model.fit(X_train_balanced, y_train_balanced)

        # Retrain isolation forest
        _retrain_status["progress"] = "Retraining isolation forest..."
        old_iso = joblib.load(f"{MODELS_DIR}/isolation_forest.joblib")
        new_iso = clone(old_iso)
        new_iso.fit(X_train_balanced)

        # Step 8: Evaluate new model
        _retrain_status["progress"] = "Evaluating candidate model..."
        new_preds = new_model.predict(X_test_scaled)
        new_acc = accuracy_score(y_test, new_preds)
        new_f1 = f1_score(y_test, new_preds, average="weighted", zero_division=0)

        # Compute FPR (benign misclassified as attack)
        benign_label = label_encoder.transform(["BENIGN"])[0]
        benign_mask = y_test == benign_label
        if benign_mask.sum() > 0:
            benign_misclassified = (new_preds[benign_mask] != benign_label).sum()
            fpr = benign_misclassified / benign_mask.sum()
        else:
            fpr = 0

        _retrain_status["progress"] = (
            f"Evaluation complete. New F1={new_f1:.4f} (old={old_f1:.4f}), "
            f"FPR={fpr:.4f}"
        )

        # Step 9: Save candidate
        os.makedirs(CANDIDATE_DIR, exist_ok=True)
        joblib.dump(new_model, f"{CANDIDATE_DIR}/tst1_stk_classifier.joblib")
        joblib.dump(new_iso, f"{CANDIDATE_DIR}/isolation_forest.joblib")

        # Step 10: Decide promotion
        promoted = False
        if new_f1 >= MIN_F1_THRESHOLD and fpr <= MAX_FPR_THRESHOLD:
            _retrain_status["progress"] = "Promoting candidate model..."

            # Save rollback
            os.makedirs(ROLLBACK_DIR, exist_ok=True)
            shutil.copy(f"{MODELS_DIR}/tst1_stk_classifier.joblib",
                        f"{ROLLBACK_DIR}/tst1_stk_classifier.joblib")
            shutil.copy(f"{MODELS_DIR}/isolation_forest.joblib",
                        f"{ROLLBACK_DIR}/isolation_forest.joblib")

            # Promote
            shutil.copy(f"{CANDIDATE_DIR}/tst1_stk_classifier.joblib",
                        f"{MODELS_DIR}/tst1_stk_classifier.joblib")
            shutil.copy(f"{CANDIDATE_DIR}/isolation_forest.joblib",
                        f"{MODELS_DIR}/isolation_forest.joblib")
            promoted = True
            _retrain_status["progress"] = "Model promoted successfully!"
        else:
            reasons = []
            if new_f1 < MIN_F1_THRESHOLD:
                reasons.append(f"F1={new_f1:.4f} < {MIN_F1_THRESHOLD}")
            if fpr > MAX_FPR_THRESHOLD:
                reasons.append(f"FPR={fpr:.4f} > {MAX_FPR_THRESHOLD}")
            _retrain_status["progress"] = (
                f"Candidate NOT promoted: {'; '.join(reasons)}. "
                f"Saved to {CANDIDATE_DIR}/ for manual review."
            )

        # Update job record
        _update_job(
            conn, job_id, "completed",
            old_accuracy=old_acc, new_accuracy=new_acc,
            old_f1=old_f1, new_f1=new_f1,
            promoted=promoted,
            samples_used=len(X_combined)
        )

        result = {
            "job_id": job_id,
            "old_f1": old_f1,
            "new_f1": new_f1,
            "old_accuracy": old_acc,
            "new_accuracy": new_acc,
            "fpr": fpr,
            "promoted": promoted,
            "samples_used": len(X_combined),
        }

        _retrain_status["running"] = False
        return result

    except Exception as e:
        error_msg = str(e)
        print(f"[Retrain Error] {e}")
        _retrain_status = {"running": False, "progress": f"Failed: {error_msg}", "error": error_msg}
        try:
            _update_job(conn, job_id, "failed", error_message=error_msg)
        except Exception:
            pass
        return {"error": error_msg}

    finally:
        _retrain_lock.release()


def rollback_models():
    """Restore the previous model from rollback directory."""
    try:
        if not os.path.exists(f"{ROLLBACK_DIR}/tst1_stk_classifier.joblib"):
            return {"error": "No rollback model available."}

        shutil.copy(f"{ROLLBACK_DIR}/tst1_stk_classifier.joblib",
                    f"{MODELS_DIR}/tst1_stk_classifier.joblib")
        shutil.copy(f"{ROLLBACK_DIR}/isolation_forest.joblib",
                    f"{MODELS_DIR}/isolation_forest.joblib")

        return {"success": True, "message": "Model rolled back successfully."}
    except Exception as e:
        return {"error": f"Rollback failed: {e}"}


def _update_job(conn, job_id, status, **kwargs):
    """Update a retrain job record."""
    try:
        fields = ["status = ?", "finished_at = ?"]
        values = [status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]

        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            if isinstance(value, bool):
                values.append(1 if value else 0)
            else:
                values.append(value)

        values.append(job_id)
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE retrain_jobs SET {', '.join(fields)} WHERE id = ?",
            values
        )
        conn.commit()
    except Exception as e:
        print(f"[Update Job Error] {e}")
