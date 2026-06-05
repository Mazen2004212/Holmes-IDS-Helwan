"""
SHAP/LIME Explainability for HOLMES IDS Anomaly Detection.
==========================================================
Provides feature importance explanations for individual anomaly alerts
using SHAP (TreeExplainer) and LIME.
"""

import io
import json
import base64
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


# ========== Feature Glossary ========== #

FEATURE_GLOSSARY = {
    "FwdPacketLengthMean": {
        "name": "Fwd Packet Length Mean",
        "description": "Average size of packets in the forward direction (client -> server)",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "FwdPacketLengthMax": {
        "name": "Fwd Packet Length Max",
        "description": "Maximum size of a single forward packet",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "FlowIATMax": {
        "name": "Flow IAT Max",
        "description": "Maximum inter-arrival time between packets in the flow",
        "unit": "seconds",
        "suspicious_direction": "varies",
    },
    "SubflowBwdBytes": {
        "name": "Subflow Bwd Bytes",
        "description": "Total bytes in backward sub-flow",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "Init_Win_bytes_backward": {
        "name": "Init Win Bytes Backward",
        "description": "Initial TCP window size in backward direction",
        "unit": "bytes",
        "suspicious_direction": "varies",
    },
    "TotalLengthofBwdPackets": {
        "name": "Total Bwd Packet Length",
        "description": "Total size of all backward packets",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "FlowPackets/s": {
        "name": "Flow Packets/sec",
        "description": "Number of packets per second in the flow",
        "unit": "packets/s",
        "suspicious_direction": "high",
    },
    "TotalLengthofFwdPackets": {
        "name": "Total Fwd Packet Length",
        "description": "Total size of all forward packets",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "BwdPackets/s": {
        "name": "Bwd Packets/sec",
        "description": "Number of backward packets per second",
        "unit": "packets/s",
        "suspicious_direction": "high",
    },
    "AveragePacketSize": {
        "name": "Average Packet Size",
        "description": "Mean size across all packets in the flow",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "FlowDuration": {
        "name": "Flow Duration",
        "description": "Total duration of the flow",
        "unit": "seconds",
        "suspicious_direction": "varies",
    },
    "BwdPacketLengthMean": {
        "name": "Bwd Packet Length Mean",
        "description": "Average size of backward packets",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "SubflowFwdBytes": {
        "name": "Subflow Fwd Bytes",
        "description": "Total bytes in forward sub-flow",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "AvgBwdSegmentSize": {
        "name": "Avg Bwd Segment Size",
        "description": "Average backward TCP segment payload size",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "FwdPacketLengthStd": {
        "name": "Fwd Packet Length Std",
        "description": "Standard deviation of forward packet sizes (variability)",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "AvgFwdSegmentSize": {
        "name": "Avg Fwd Segment Size",
        "description": "Average forward TCP segment payload size",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "DestinationPort": {
        "name": "Destination Port",
        "description": "Target port number (e.g., 80=HTTP, 443=HTTPS, 22=SSH)",
        "unit": "port",
        "suspicious_direction": "varies",
    },
    "BwdHeaderLength": {
        "name": "Bwd Header Length",
        "description": "Total length of backward packet headers",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "PacketLengthMean": {
        "name": "Packet Length Mean",
        "description": "Average packet size across the entire flow",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
    "BwdPacketLengthStd": {
        "name": "Bwd Packet Length Std",
        "description": "Standard deviation of backward packet sizes",
        "unit": "bytes",
        "suspicious_direction": "high",
    },
}


def get_feature_glossary():
    """Return the feature glossary dict."""
    return FEATURE_GLOSSARY


# ========== SHAP Explanation ========== #

def explain_shap(model, scaler, feature_order, features_dict):
    """
    Generate SHAP explanation for a single prediction.

    Args:
        model: The stacking classifier (final estimator is RandomForest)
        scaler: MinMaxScaler used during training
        feature_order: List of feature names in order
        features_dict: Dict of {feature_name: value} (raw, unscaled)

    Returns:
        dict with 'shap_values', 'base_value', 'predicted_class',
        'feature_contributions' (sorted), 'chart_base64'
    """
    try:
        import shap

        # Prepare features
        df = pd.DataFrame([features_dict], columns=feature_order)
        df_scaled = pd.DataFrame(scaler.transform(df), columns=feature_order)

        # Use the final estimator (RandomForest) for TreeExplainer
        final_estimator = model.final_estimator_

        # Get stacked predictions from base estimators (what final estimator sees)
        # For explanation, we explain the final estimator's decision
        # But we need to explain in terms of ORIGINAL features, not stacked meta-features
        # So we use KernelExplainer on the full pipeline as fallback

        try:
            # Try TreeExplainer on the full model's predict_proba
            explainer = shap.TreeExplainer(final_estimator)

            # Get the stacked features that final estimator receives
            from sklearn.utils.metaestimators import _BaseComposition
            stacked_features = np.column_stack([
                est.predict_proba(df_scaled) if hasattr(est, 'predict_proba')
                else est.predict(df_scaled).reshape(-1, 1)
                for est in model.estimators_
            ])
            stacked_df = pd.DataFrame(stacked_features)

            shap_values_raw = explainer.shap_values(stacked_df)
            base_value = explainer.expected_value

            # Map stacked SHAP values back to original features (approximate)
            # This is a simplification - we distribute importance proportionally
            feature_importance = _map_stacked_to_original(
                model, df_scaled, shap_values_raw, feature_order
            )

        except Exception:
            # Fallback: KernelExplainer on the full pipeline
            def predict_fn(X):
                return model.predict_proba(X)

            background = shap.sample(df_scaled, 1)
            explainer = shap.KernelExplainer(predict_fn, background)
            shap_values_raw = explainer.shap_values(df_scaled, nsamples=100)
            base_value = explainer.expected_value

            # Get predicted class
            pred = model.predict(df_scaled)[0]
            if isinstance(shap_values_raw, list):
                # Multi-class: use values for predicted class
                sv = shap_values_raw[pred][0]
            else:
                sv = shap_values_raw[0]

            feature_importance = {
                feature_order[i]: float(sv[i])
                for i in range(len(feature_order))
            }

        # Get prediction
        pred = model.predict(df_scaled)[0]

        # Sort by absolute importance
        sorted_contributions = sorted(
            feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        # Generate chart
        chart_b64 = _generate_shap_chart(sorted_contributions, "SHAP Feature Importance")

        return {
            "method": "SHAP",
            "predicted_class_idx": int(pred),
            "feature_contributions": sorted_contributions,
            "chart_base64": chart_b64,
            "glossary": FEATURE_GLOSSARY,
        }

    except Exception as e:
        print(f"[SHAP Error] {e}")
        return {"error": str(e)}


def _map_stacked_to_original(model, X_scaled, shap_values_raw, feature_order):
    """
    Approximate mapping of stacked meta-feature SHAP values back to original features.
    Uses each base estimator's feature_importances_ or coefficients.
    """
    importance = {f: 0.0 for f in feature_order}

    try:
        # Get predicted class index
        pred = model.predict(X_scaled)[0]

        if isinstance(shap_values_raw, list):
            sv = shap_values_raw[pred][0]
        else:
            sv = shap_values_raw[0]

        idx = 0
        for est in model.estimators_:
            if hasattr(est, 'predict_proba'):
                n_outputs = est.predict_proba(X_scaled).shape[1]
            else:
                n_outputs = 1

            est_shap_sum = sum(abs(sv[idx:idx + n_outputs]))

            # Distribute based on estimator's own feature importance
            if hasattr(est, 'feature_importances_'):
                fi = est.feature_importances_
                fi_norm = fi / (fi.sum() + 1e-10)
                for j, feat in enumerate(feature_order):
                    importance[feat] += float(fi_norm[j] * est_shap_sum)
            elif hasattr(est, 'coef_'):
                coef = np.abs(est.coef_).mean(axis=0)
                coef_norm = coef / (coef.sum() + 1e-10)
                for j, feat in enumerate(feature_order):
                    importance[feat] += float(coef_norm[j] * est_shap_sum)
            else:
                # Equal distribution
                for feat in feature_order:
                    importance[feat] += est_shap_sum / len(feature_order)

            idx += n_outputs

    except Exception as e:
        print(f"[SHAP Mapping Warning] {e}")

    return importance


# ========== LIME Explanation ========== #

def explain_lime(model, scaler, label_encoder, feature_order,
                 features_dict, background_data=None):
    """
    Generate LIME explanation for a single prediction.

    Args:
        model: The stacking classifier
        scaler: MinMaxScaler
        label_encoder: LabelEncoder
        feature_order: List of feature names
        features_dict: Dict of {feature_name: raw_value}
        background_data: DataFrame of training samples for LIME

    Returns:
        dict with 'lime_contributions', 'predicted_class', 'chart_base64'
    """
    try:
        from lime.lime_tabular import LimeTabularExplainer

        # Prepare features
        df = pd.DataFrame([features_dict], columns=feature_order)
        df_scaled = pd.DataFrame(scaler.transform(df), columns=feature_order)
        instance = df_scaled.values[0]

        # Prepare background data
        if background_data is not None:
            bg = background_data.values
        else:
            # Use the single instance as minimal background
            bg = df_scaled.values

        # Create LIME explainer
        class_names = list(label_encoder.classes_) + ["Unknown Attack"]
        explainer = LimeTabularExplainer(
            bg,
            feature_names=feature_order,
            class_names=class_names,
            mode='classification',
            discretize_continuous=True
        )

        # Get prediction
        pred = model.predict(df_scaled)[0]

        # Explain
        exp = explainer.explain_instance(
            instance,
            model.predict_proba,
            num_features=len(feature_order),
            labels=[pred]
        )

        # Extract contributions
        contributions = exp.as_list(label=pred)
        # contributions is [(feature_desc, weight), ...]

        # Map back to clean feature names
        clean_contributions = []
        for desc, weight in contributions:
            # LIME uses descriptions like "Feature > 0.5", extract the feature name
            matched_feat = None
            for feat in feature_order:
                if feat in desc:
                    matched_feat = feat
                    break
            name = matched_feat or desc
            clean_contributions.append((name, float(weight)))

        # Sort by absolute weight
        clean_contributions.sort(key=lambda x: abs(x[1]), reverse=True)

        # Generate chart
        chart_b64 = _generate_shap_chart(clean_contributions, "LIME Feature Contributions")

        return {
            "method": "LIME",
            "predicted_class_idx": int(pred),
            "feature_contributions": clean_contributions,
            "chart_base64": chart_b64,
            "glossary": FEATURE_GLOSSARY,
        }

    except Exception as e:
        print(f"[LIME Error] {e}")
        return {"error": str(e)}


# ========== Chart Generation ========== #

def _generate_shap_chart(contributions, title="Feature Importance"):
    """
    Generate a horizontal bar chart for feature contributions.
    Returns base64-encoded PNG string.
    """
    try:
        # Take top 15 features
        top = contributions[:15]
        features = [c[0] for c in reversed(top)]
        values = [c[1] for c in reversed(top)]

        # Map to friendly names
        friendly = []
        for f in features:
            info = FEATURE_GLOSSARY.get(f, {})
            friendly.append(info.get("name", f))

        fig, ax = plt.subplots(figsize=(10, 6))

        colors = ['#e74c3c' if v > 0 else '#3498db' for v in values]
        bars = ax.barh(range(len(friendly)), values, color=colors, edgecolor='none',
                       height=0.7)

        ax.set_yticks(range(len(friendly)))
        ax.set_yticklabels(friendly, fontsize=10)
        ax.set_xlabel('Impact on Prediction', fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold')

        # Style
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.axvline(x=0, color='gray', linewidth=0.8, linestyle='-')

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#e74c3c', label='Pushes toward attack'),
            Patch(facecolor='#3498db', label='Pushes toward benign')
        ]
        ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

        plt.tight_layout()

        # Convert to base64
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                    facecolor='white')
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        return b64

    except Exception as e:
        print(f"[Chart Error] {e}")
        return ""


# ========== Alert Feature Storage ========== #

def store_alert_features(conn, alert_id, features_dict, predicted_label,
                         confidence=None):
    """Store raw features linked to an alert for later explanation."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO alert_features
               (alert_id, features_json, predicted_label, confidence)
               VALUES (?, ?, ?, ?)""",
            (alert_id, json.dumps(features_dict), predicted_label, confidence)
        )
        conn.commit()
    except Exception as e:
        print(f"[Store Features Error] {e}")


def get_alert_features(conn, alert_id):
    """Retrieve stored features for an alert."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT features_json, predicted_label, confidence FROM alert_features WHERE alert_id = ?",
            (alert_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "features": json.loads(row[0]),
                "predicted_label": row[1],
                "confidence": row[2],
            }
    except Exception as e:
        print(f"[Get Features Error] {e}")
    return None
