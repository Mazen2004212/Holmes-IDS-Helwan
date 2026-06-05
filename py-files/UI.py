import threading
import os
import joblib
import numpy as np
import pandas as pd

from scapy.all import rdpcap, conf
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from DB import Database
from rule import Rule
from log import Log
from alert import Alert
from signature_IDS import SignatureIDS
from alert_analyzer import AlertAnalyzer
from anomaly_IDS import AnomalyIDS
from live_capture import LiveCapture
from packet import Packet
from auth import User, ROLES, role_required, get_default_route
from ntp_time import sync_ntp, get_ntp_time
from explainability import (explain_shap, explain_lime, get_alert_features,
                            get_feature_glossary)
from continual_learning import (get_training_stats, get_training_samples,
                                update_human_label, retrain_models,
                                get_retrain_history, get_retrain_status)
from analytics import execute_query

IDS_app = Flask(__name__)
IDS_app.secret_key = os.environ.get('SECRET_KEY', 'holmes-ids-dev-secret-key-change-in-production')

# ========== Flask-Login Setup ========== #
login_manager = LoginManager()
login_manager.init_app(IDS_app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please sign in to access HOLMES IDS.'

import app_state

@login_manager.user_loader
def load_user(user_id):
    db = Database(app_state.DB_PATH)
    conn = db.connect()
    if conn:
        user = User.get_by_id(conn, int(user_id))
        conn.close()
        return user
    return None


# ========== Load model components (into app_state) ========== #
app_state.model = joblib.load("Models/Models/tst1_stk_classifier.joblib")
app_state.iso_forest = joblib.load("Models/Models/isolation_forest.joblib")
app_state.scaler = joblib.load("Models/Scaler/scaler_minmax.save")
app_state.label_encoder = joblib.load("Models/Label Encoder/lb_encoder.pkl")
app_state.feature_order = joblib.load("Models/Features_Order/features_order.pkl")

os.makedirs(app_state.UPLOAD_FOLDER, exist_ok=True)


# ========== Register API Blueprints (React SPA backend) ========== #
from api_auth import api_auth
from api_routes import api as api_routes
IDS_app.register_blueprint(api_auth)
IDS_app.register_blueprint(api_routes)


# ========== Authentication Routes ========== #

@IDS_app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(get_default_route(current_user.role)))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = Database(app_state.DB_PATH)
        conn = db.connect()
        if conn:
            user = User.get_by_username(conn, username)
            conn.close()
            if user and user.check_password(password):
                login_user(user)
                # Always redirect to the user's role-specific default page
                # (ignoring 'next' param to prevent redirect loops for restricted roles)
                default_page = url_for(get_default_route(user.role))
                return redirect(default_page)
        flash("Invalid username or password.")

    return render_template("login.html", title="Login - HOLMES IDS")


@IDS_app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('login'))


# ========== Dashboard Routes ========== #

@IDS_app.route("/")
@login_required
@role_required('admin', 'signature_analyst')
def signature_dashboard():
    top_src_ip = 'N/A'
    top_dst_ip = 'N/A'
    alerts = []
    logs = []
    num_alerts = 0
    loaded_rules = []

    try:
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        logs = [log for log in Log.get_logs_from_db(conn) if log.method == "signature"]
        alerts = [alert for alert in Alert.get_alerts_from_db(conn) if alert.method == "signature"]
        loaded_rules = Rule.get_rules_from_db(conn)
        num_alerts = len(alerts)
        analyzer = AlertAnalyzer(alerts)
        top_src_ip = analyzer.get_top_src_ip()
        top_dst_ip = analyzer.get_top_dst_ip()
        conn.close()
    except Exception as e:
        print(f"[Error] {e}")
        return "Dashboard error", 500

    return render_template(
        "index.html", title="Signature IDS Dashboard",
        logs=logs, alerts=alerts, rules=loaded_rules,
        num_alerts=num_alerts, top_src_ip=top_src_ip, top_dst_ip=top_dst_ip
    )


@IDS_app.route("/anomaly")
@login_required
@role_required('admin', 'anomaly_analyst')
def anomaly_dashboard():
    top_src_ip = 'N/A'
    top_dst_ip = 'N/A'
    alerts = []
    logs = []
    num_alerts = 0

    try:
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        logs = [log for log in Log.get_logs_from_db(conn) if log.method == "anomaly"]
        alerts = [alert for alert in Alert.get_alerts_from_db(conn) if alert.method == "anomaly"]
        num_alerts = len(alerts)
        analyzer = AlertAnalyzer(alerts)
        top_src_ip = analyzer.get_top_src_ip()
        top_dst_ip = analyzer.get_top_dst_ip()
        conn.close()
    except Exception as e:
        print(f"[Error] {e}")
        return "Anomaly dashboard error", 500

    return render_template(
        "anomaly.html", title="Anomaly IDS Dashboard",
        logs=logs, alerts=alerts, num_alerts=num_alerts,
        top_src_ip=top_src_ip, top_dst_ip=top_dst_ip
    )


@IDS_app.route("/csv", methods=["GET", "POST"])
@login_required
@role_required('admin', 'anomaly_analyst')
def upload_csv():
    predictions = []
    stats = {}

    if request.method == "POST":
        file = request.files.get("csv_file")
        filename, error = app_state._validate_file(file, app_state.ALLOWED_CSV_EXTENSIONS)
        if error:
            flash(error)
            return redirect(request.url)
        try:
            df = pd.read_csv(file)
            path = os.path.join(app_state.UPLOAD_FOLDER, filename)
            df.to_csv(path, index=False)
            anomaly_ids = AnomalyIDS(app_state.model, app_state.iso_forest, app_state.scaler, app_state.label_encoder, app_state.feature_order)
            predictions, stats, _ = anomaly_ids.predict_from_csv(path)
        except Exception as e:
            print(f"[CSV Error] {e}")
            flash("An error occurred while processing the file.")
            return redirect(request.url)

    return render_template("csv.html", predictions=predictions, stats=stats, title="CSV Anomaly Detection")


@IDS_app.route("/upload_pcap", methods=["GET", "POST"])
@login_required
@role_required('admin', 'signature_analyst')
def upload_pcap():
    alerts = []
    tls_results = None
    tls_metadata = None

    if request.method == "POST":
        file = request.files.get("pcap_file")
        filename, error = app_state._validate_file(file, app_state.ALLOWED_PCAP_EXTENSIONS)
        if error:
            flash(error)
            return redirect(request.url)
        filepath = os.path.join(app_state.UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            # Standard signature detection
            packets = rdpcap(filepath)
            sig_ids = SignatureIDS(app_state.rules)
            alerts = sig_ids.predict_from_pcap(packets)
            flash("PCAP scanned successfully.")
        except Exception as e:
            print(f"[PCAP Error] {type(e).__name__}: {e}")
            flash("Failed to process PCAP.")

        # TLS decryption with keylog file (optional)
        keylog_file = request.files.get("keylog_file")
        if keylog_file and keylog_file.filename:
            keylog_path = os.path.join(app_state.UPLOAD_FOLDER, "sslkeylog_" + secure_filename(keylog_file.filename))
            keylog_file.save(keylog_path)
            try:
                from tls_decrypt import decrypt_pcap
                tls_results = decrypt_pcap(filepath, keylog_path)
                if tls_results.get("error"):
                    flash(f"TLS decryption warning: {tls_results['error']}")
                elif tls_results.get("results"):
                    flash(f"TLS decryption: found {len(tls_results['results'])} HTTP requests.")
                elif tls_results.get("message"):
                    flash(tls_results["message"])
            except Exception as e:
                print(f"[TLS Decrypt Error] {e}")
                flash(f"TLS decryption failed: {e}")
            finally:
                # Clean up keylog file
                try:
                    os.remove(keylog_path)
                except OSError:
                    pass
        else:
            # No keylog: extract TLS metadata (SNI, JA3) as fallback
            try:
                from tls_decrypt import extract_tls_metadata, check_tshark
                tshark_path, _ = check_tshark()
                if tshark_path:
                    tls_metadata = extract_tls_metadata(filepath)
                    if tls_metadata.get("results"):
                        flash(f"TLS metadata: extracted {len(tls_metadata['results'])} TLS handshakes.")
            except Exception as e:
                print(f"[TLS Metadata Error] {e}")

    return render_template("pcap.html", alerts=alerts,
                           tls_results=tls_results, tls_metadata=tls_metadata,
                           title="PCAP Signature Detection")


@IDS_app.route("/rules")
@login_required
@role_required('admin', 'signature_analyst')
def rules_dashboard():
    loaded_rules = []
    try:
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        if not conn:
            return "Database connection error", 500
        loaded_rules = Rule.get_rules_from_db(conn)
        conn.close()
    except Exception as e:
        print(f"[Error] {e}")
        return "Rules dashboard error", 500

    return render_template("rules.html", title="Rules Dashboard", rules=loaded_rules)


# ========== Live Capture Routes ========== #

@IDS_app.route("/live")
@login_required
@role_required('admin', 'signature_analyst', 'anomaly_analyst', 'live_operator')
def live_dashboard():
    alerts = []
    status = {
        "running": False,
        "packets_captured": 0,
        "alerts_generated": 0,
        "interface": "",
        "interface_name": "None selected",
        "interface_desc": ""
    }

    if app_state.live_capture_instance:
        status = app_state.live_capture_instance.get_status()

    interfaces = app_state.get_interfaces()

    try:
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        all_alerts = Alert.get_alerts_from_db(conn)
        alerts = all_alerts  # Show all alerts (signature + anomaly) in live view
        conn.close()
    except Exception as e:
        print(f"[Error] {e}")

    return render_template(
        "live.html", title="Live Capture",
        status=status, alerts=alerts, interfaces=interfaces
    )


@IDS_app.route("/live/start", methods=["POST"])
@login_required
@role_required('admin', 'live_operator')
def live_start():

    if not app_state.rules:
        flash("No rules loaded. Cannot start live capture.")
        return redirect("/live")

    if app_state.live_capture_instance and app_state.live_capture_instance.is_running:
        flash("Live capture is already running.")
        return redirect("/live")

    selected_iface = request.form.get("interface", None)

    # Resolve friendly name for the selected interface
    iface_name = selected_iface or "default"
    iface_desc = ""
    try:
        if selected_iface:
            from scapy.all import conf as scapy_conf
            if selected_iface in scapy_conf.ifaces:
                iface_obj = scapy_conf.ifaces[selected_iface]
                iface_name = getattr(iface_obj, 'name', str(selected_iface))
                iface_desc = getattr(iface_obj, 'description', '')
    except Exception:
        pass

    app_state.live_capture_instance = LiveCapture(
        rules=app_state.rules,
        model=app_state.model,
        iso_forest=app_state.iso_forest,
        scaler=app_state.scaler,
        label_encoder=app_state.label_encoder,
        feature_order=app_state.feature_order,
        db_path=app_state.DB_PATH,
        interface=selected_iface
    )
    app_state.live_capture_instance._interface_name = iface_name
    app_state.live_capture_instance._interface_desc = iface_desc
    app_state.live_capture_instance.start()
    flash(f"Live capture started on: {iface_name}")
    return redirect("/live")


@IDS_app.route("/live/stop", methods=["POST"])
@login_required
@role_required('admin', 'live_operator')
def live_stop():
    if not app_state.live_capture_instance or not app_state.live_capture_instance.is_running:
        flash("No live capture is running.")
        return redirect("/live")
    app_state.live_capture_instance.stop()
    flash("Live capture stopped.")
    return redirect("/live")


@IDS_app.route("/live/clear", methods=["POST"])
@login_required
@role_required('admin', 'live_operator')
def live_clear_alerts():
    """Clear all live alerts and logs."""
    try:
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        if conn:
            db.clear_table("alerts")
            db.clear_table("logs")
            db.clear_table("alert_features")
            conn.close()
            flash("All alerts cleared.")
        else:
            flash("Database connection error.")
    except Exception as e:
        flash(f"Error clearing alerts: {e}")
    return redirect("/live")


@IDS_app.route("/live/delete", methods=["POST"])
@login_required
@role_required('admin', 'live_operator')
def live_delete_alerts():
    """Delete selected alerts by ID."""
    alert_ids = request.form.getlist("alert_ids")
    if not alert_ids:
        flash("No alerts selected.")
        return redirect("/live")

    try:
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        if conn:
            cursor = conn.cursor()
            placeholders = ",".join(["?"] * len(alert_ids))
            cursor.execute(f"DELETE FROM alerts WHERE id IN ({placeholders})", alert_ids)
            cursor.execute(f"DELETE FROM alert_features WHERE alert_id IN ({placeholders})", alert_ids)
            conn.commit()
            conn.close()
            flash(f"Deleted {len(alert_ids)} alert(s).")
    except Exception as e:
        flash(f"Error deleting alerts: {e}")
    return redirect("/live")

@IDS_app.route("/admin")
@login_required
@role_required('admin')
def admin_panel():
    db = Database(app_state.DB_PATH)
    conn = db.connect()
    users = User.get_all(conn)
    conn.close()
    return render_template("admin.html", title="Admin - User Management", users=users, roles=ROLES)


@IDS_app.route("/admin/create", methods=["POST"])
@login_required
@role_required('admin')
def admin_create_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "live_operator")

    if not username or not password:
        flash("Username and password are required.")
        return redirect(url_for('admin_panel'))

    if role not in ROLES:
        flash("Invalid role selected.")
        return redirect(url_for('admin_panel'))

    db = Database(app_state.DB_PATH)
    conn = db.connect()
    success = User.create(conn, username, password, role)
    conn.close()

    if success:
        flash(f"User '{username}' created with role '{ROLES[role]['label']}'.")
    else:
        flash(f"Failed to create user. Username '{username}' may already exist.")
    return redirect(url_for('admin_panel'))


@IDS_app.route("/admin/delete", methods=["POST"])
@login_required
@role_required('admin')
def admin_delete_user():
    user_id = request.form.get("user_id")
    if not user_id:
        flash("Invalid user.")
        return redirect(url_for('admin_panel'))

    db = Database(app_state.DB_PATH)
    conn = db.connect()
    # Prevent deleting the default admin
    user = User.get_by_id(conn, int(user_id))
    if user and user.username == "admin":
        flash("Cannot delete the default admin account.")
        conn.close()
        return redirect(url_for('admin_panel'))

    success = User.delete(conn, int(user_id))
    conn.close()

    if success:
        flash("User deleted.")
    else:
        flash("Failed to delete user.")
    return redirect(url_for('admin_panel'))


@IDS_app.route("/admin/update_role", methods=["POST"])
@login_required
@role_required('admin')
def admin_update_role():
    user_id = request.form.get("user_id")
    new_role = request.form.get("role")

    if not user_id or new_role not in ROLES:
        flash("Invalid request.")
        return redirect(url_for('admin_panel'))

    db = Database(app_state.DB_PATH)
    conn = db.connect()
    success = User.update_role(conn, int(user_id), new_role)
    conn.close()

    if success:
        flash("Role updated.")
    else:
        flash("Failed to update role.")
    return redirect(url_for('admin_panel'))


# ========== Explainability Routes ========== #

@IDS_app.route("/explain/<int:alert_id>")
@login_required
@role_required('admin', 'anomaly_analyst')
def explain_alert(alert_id):
    """Show SHAP/LIME explanation for an anomaly alert."""
    db = Database(app_state.DB_PATH)
    conn = db.connect()
    if not conn:
        flash("Database connection error.")
        return redirect(url_for('anomaly_dashboard'))

    try:
        # Get stored features for this alert
        alert_data = get_alert_features(conn, alert_id)
        if not alert_data:
            flash("No feature data available for this alert.")
            return redirect(url_for('anomaly_dashboard'))

        features = alert_data['features']
        predicted_label = alert_data['predicted_label']
        confidence = alert_data['confidence']

        # Generate SHAP explanation
        shap_result = explain_shap(app_state.model, app_state.scaler, app_state.feature_order, features)

        # Generate LIME explanation
        # Load background data (sample from training CSV)
        try:
            bg_df = pd.read_csv("Models/Dt/tst2_Cleaned_CIC_IDS2017_full_week.csv",
                                nrows=500)
            bg_features = bg_df[app_state.feature_order]
            bg_scaled = pd.DataFrame(app_state.scaler.transform(bg_features),
                                     columns=app_state.feature_order)
        except Exception:
            bg_scaled = None

        lime_result = explain_lime(app_state.model, app_state.scaler, app_state.label_encoder,
                                   app_state.feature_order, features, bg_scaled)

        glossary = get_feature_glossary()

    except Exception as e:
        print(f"[Explain Error] {e}")
        flash(f"Error generating explanation: {e}")
        return redirect(url_for('anomaly_dashboard'))
    finally:
        conn.close()

    return render_template(
        "explain.html",
        title=f"Explain Alert #{alert_id}",
        alert_id=alert_id,
        features=features,
        predicted_label=predicted_label,
        confidence=confidence,
        shap_result=shap_result,
        lime_result=lime_result,
        glossary=glossary
    )


# ========== Continual Learning Routes ========== #

@IDS_app.route("/retrain")
@login_required
@role_required('admin')
def retrain_dashboard():
    """Admin dashboard for continual learning with filter support."""
    db = Database(app_state.DB_PATH)
    conn = db.connect()
    if not conn:
        flash("Database connection error.")
        return redirect(url_for('signature_dashboard'))

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    # Filters from query string
    filters = {
        "label": request.args.get("label", ""),
        "labeled": request.args.get("labeled", ""),
        "source": request.args.get("source", ""),
        "date_from": request.args.get("date_from", ""),
        "date_to": request.args.get("date_to", ""),
    }
    # Remove empty filters
    active_filters = {k: v for k, v in filters.items() if v}

    # Build query string for pagination links (exclude 'page')
    qs_parts = [f"{k}={v}" for k, v in active_filters.items()]
    query_string = "&".join(qs_parts)

    try:
        stats = get_training_stats(conn)
        samples = get_training_samples(conn, limit=per_page, offset=offset,
                                       filters=active_filters)
        history = get_retrain_history(conn)
        retrain_status = get_retrain_status()
        label_classes = list(app_state.label_encoder.classes_)
    finally:
        conn.close()

    return render_template("retrain.html", title="Continual Learning",
                           stats=stats, samples=samples, history=history,
                           retrain_status=retrain_status,
                           label_classes=label_classes,
                           page=page, per_page=per_page,
                           query_string=query_string)


@IDS_app.route("/retrain/start", methods=["POST"])
@login_required
@role_required('admin')
def retrain_start():
    """Trigger model retraining in background."""
    import threading

    retrain_status = get_retrain_status()
    if retrain_status.get("running"):
        flash("A retraining job is already running.")
        return redirect(url_for('retrain_dashboard'))

    def run_retrain():
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        if conn:
            try:
                result = retrain_models(conn, started_by=current_user.username)
                if result.get("promoted"):
                    print(f"[Retrain] Model promoted. New F1={result['new_f1']:.4f}")
                elif result.get("error"):
                    print(f"[Retrain] Failed: {result['error']}")
                else:
                    print(f"[Retrain] Candidate not promoted. F1={result.get('new_f1', 'N/A')}")
            finally:
                conn.close()

    threading.Thread(target=run_retrain, daemon=True).start()
    flash("Retraining started in background. Refresh to see progress.")
    return redirect(url_for('retrain_dashboard'))


@IDS_app.route("/retrain/label", methods=["POST"])
@login_required
@role_required('admin')
def retrain_label():
    """Update the human label for a training sample."""
    sample_id = request.form.get("sample_id")
    label = request.form.get("label")

    if not sample_id or not label:
        flash("Sample ID and label are required.")
        return redirect(url_for('retrain_dashboard'))

    db = Database(app_state.DB_PATH)
    conn = db.connect()
    if conn:
        try:
            if update_human_label(conn, int(sample_id), label):
                flash(f"Label updated for sample #{sample_id}: {label}")
            else:
                flash("Failed to update label.")
        finally:
            conn.close()

    return redirect(url_for('retrain_dashboard'))


# ========== Analytics Routes ========== #

@IDS_app.route("/analytics")
@login_required
@role_required('admin', 'signature_analyst', 'anomaly_analyst')
def analytics_dashboard():
    """Render the analytics query builder page."""
    return render_template("analytics.html", title="Analytics")


@IDS_app.route("/analytics/query", methods=["POST"])
@login_required
@role_required('admin', 'signature_analyst', 'anomaly_analyst')
def analytics_query():
    """Execute a GUI_QUERY and return JSON results."""
    gui_query = request.get_json()
    if not gui_query:
        return jsonify({"success": False, "error": "No query provided."}), 400

    db = Database(app_state.DB_PATH)
    conn = db.connect()
    if not conn:
        return jsonify({"success": False, "error": "Database connection error."}), 500

    try:
        result = execute_query(conn, gui_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


# ========== Main ========== #
if __name__ == "__main__":
    try:
        # Sync NTP time
        sync_ntp()

        db = Database(app_state.DB_PATH)
        conn = db.connect()

        if not conn:
            print("[Error] DB Connection Failed.")
            exit(1)

        # Create tables (including users and new feature tables)
        db.create_table_rules()
        db.create_table_logs()
        db.create_table_alerts()
        db.create_table_users()
        db.create_table_alert_features()
        db.create_table_training_data()
        db.create_table_retrain_jobs()

        # Create default admin user
        User.ensure_default_admin(conn)

        # Load rules
        app_state.rules = Rule.get_rules_from_db(conn)

        conn.close()

        # Reset packet counters
        Packet.reset_counts()

        # NOTE: We no longer auto-process test3.pcap on startup.
        # Alerts are now only generated from:
        #   1. Live capture (real-time traffic)
        #   2. PCAP upload (manual analysis)
        # This prevents stale 1970-epoch alerts from reappearing on every restart.

        print("\n" + "=" * 50)
        print("  HOLMES IDS — Starting on http://127.0.0.1:8000")
        print("  Default login: admin / admin")
        print("=" * 50 + "\n")

        IDS_app.run(debug=False, use_reloader=False, threaded=True, port=8000)

    except Exception as e:
        print(f"[Startup Error] {e}")
