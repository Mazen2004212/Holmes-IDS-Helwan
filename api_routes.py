"""
Flask JSON API endpoints for all HOLMES IDS pages.
Each returns JSON instead of render_template.
"""
import os
import threading
import pandas as pd
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from auth import role_required, ROLES, User
from DB import Database
from alert import Alert
from alert_analyzer import AlertAnalyzer
from log import Log
from rule import Rule
from live_capture import LiveCapture
from explainability import explain_shap, explain_lime, get_alert_features, get_feature_glossary
from continual_learning import (get_training_stats, get_training_samples,
                                 get_retrain_history, get_retrain_status,
                                 retrain_models, update_human_label)
import app_state

api = Blueprint('api_routes', __name__, url_prefix='/api')


# ========== Helper: serialize objects ========== #

def _alert_to_dict(a):
    # predict_from_pcap returns dicts with 'layer' key; DB returns Alert objects
    if isinstance(a, dict):
        return {
            'id': a.get('id'),
            'timestamp': str(a.get('time', '')),
            'src_ip': a.get('src_ip', ''),
            'dst_ip': a.get('dst_ip', ''),
            'message': a.get('message', ''),
            'attack': a.get('attack', a.get('layer', '')),
            'method': a.get('method', ''),
        }
    return {
        'id': getattr(a, 'id', None),
        'timestamp': str(getattr(a, 'time', '')),
        'src_ip': getattr(a, 'src_ip', ''),
        'dst_ip': getattr(a, 'dst_ip', ''),
        'message': getattr(a, 'message', ''),
        'attack': getattr(a, 'attack', ''),
        'method': getattr(a, 'method', ''),
    }

def _log_to_dict(l):
    return {
        'timestamp': str(getattr(l, 'time', '')),
        'event_type': getattr(l, 'action', ''),
        'src_ip': getattr(l, 'src_ip', ''),
        'dst_ip': getattr(l, 'dst_ip', ''),
        'message': getattr(l, 'message', ''),
        'attack': getattr(l, 'attack', ''),
        'method': getattr(l, 'method', ''),
    }

def _rule_to_dict(r):
    # Rule.get_rules_from_db returns dicts already
    if isinstance(r, dict):
        opts = r.get('options', {})
        return {
            'id': r.get('id'), 'action': r.get('action', ''),
            'protocol': r.get('protocol', ''), 'src_ip': r.get('src_ip', ''),
            'src_port': r.get('src_port', ''), 'direction': r.get('direction', ''),
            'dst_ip': r.get('dst_ip', ''), 'dst_port': r.get('dst_port', ''),
            'options': str(opts) if isinstance(opts, dict) else str(opts),
        }
    # Rule object (from app_state.rules)
    opts = getattr(r, 'options', {})
    return {
        'id': getattr(r, 'id', None), 'action': getattr(r, 'action', ''),
        'protocol': getattr(r, 'protocol', ''), 'src_ip': getattr(r, 'src_ip', ''),
        'src_port': getattr(r, 'src_port', ''), 'direction': getattr(r, 'direction', ''),
        'dst_ip': getattr(r, 'dst_ip', ''), 'dst_port': getattr(r, 'dst_port', ''),
        'options': str(opts) if isinstance(opts, dict) else str(opts),
    }

def _user_to_dict(u):
    return {
        'id': u.id, 'username': u.username,
        'role': u.role, 'role_label': u.role_label,
    }


# ========== Signature Dashboard ========== #

@api.route('/signature/dashboard')
@login_required
@role_required('admin', 'signature_analyst')
def signature_dashboard():
    try:
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        logs = [_log_to_dict(l) for l in Log.get_logs_from_db(conn) if l.method == "signature"]
        alerts = [_alert_to_dict(a) for a in Alert.get_alerts_from_db(conn) if a.method == "signature"]
        rules = [_rule_to_dict(r) for r in Rule.get_rules_from_db(conn)]
        num_alerts = len(alerts)
        all_alert_objs = [a for a in Alert.get_alerts_from_db(conn) if a.method == "signature"]
        analyzer = AlertAnalyzer(all_alert_objs)
        top_src_ip = analyzer.get_top_src_ip()
        top_dst_ip = analyzer.get_top_dst_ip()
        conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'alerts': alerts, 'logs': logs, 'rules': rules,
        'num_alerts': num_alerts, 'top_src_ip': top_src_ip, 'top_dst_ip': top_dst_ip,
    })


# ========== Anomaly Dashboard ========== #

@api.route('/anomaly/dashboard')
@login_required
@role_required('admin', 'anomaly_analyst')
def anomaly_dashboard():
    try:
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        logs = [_log_to_dict(l) for l in Log.get_logs_from_db(conn) if l.method == "anomaly"]
        alerts = [_alert_to_dict(a) for a in Alert.get_alerts_from_db(conn) if a.method == "anomaly"]
        num_alerts = len(alerts)
        all_alert_objs = [a for a in Alert.get_alerts_from_db(conn) if a.method == "anomaly"]
        analyzer = AlertAnalyzer(all_alert_objs)
        top_src_ip = analyzer.get_top_src_ip()
        top_dst_ip = analyzer.get_top_dst_ip()
        conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'alerts': alerts, 'logs': logs,
        'num_alerts': num_alerts, 'top_src_ip': top_src_ip, 'top_dst_ip': top_dst_ip,
    })


# ========== CSV Upload ========== #

@api.route('/uploads/csv', methods=['POST'])
@login_required
@role_required('admin', 'anomaly_analyst')
def upload_csv():
    file = request.files.get('csv_file')
    filename, error = app_state._validate_file(file, app_state.ALLOWED_CSV_EXTENSIONS)
    if error:
        return jsonify({'success': False, 'error': error}), 400

    try:
        path = os.path.join(app_state.UPLOAD_FOLDER, filename)
        file.save(path)
        from anomaly_IDS import AnomalyIDS
        anomaly_ids = AnomalyIDS(app_state.model, app_state.iso_forest,
                                  app_state.scaler, app_state.label_encoder,
                                  app_state.feature_order)
        predictions, stats, _ = anomaly_ids.predict_from_csv(path)
        # Limit returned predictions to prevent huge JSON (stats cover full dataset)
        max_return = 500
        limited = predictions[:max_return]
        truncated = len(predictions) > max_return
        return jsonify({
            'success': True,
            'predictions': limited,
            'stats': stats,
            'total_rows': len(predictions),
            'truncated': truncated,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== PCAP Upload ========== #

@api.route('/uploads/pcap', methods=['POST'])
@login_required
@role_required('admin', 'signature_analyst')
def upload_pcap():
    file = request.files.get('pcap_file')
    filename, error = app_state._validate_file(file, app_state.ALLOWED_PCAP_EXTENSIONS)
    if error:
        return jsonify({'success': False, 'error': error}), 400

    filepath = os.path.join(app_state.UPLOAD_FOLDER, filename)
    file.save(filepath)
    alerts = []
    tls_results = None
    tls_metadata = None
    messages = []

    try:
        from scapy.all import rdpcap
        from signature_IDS import SignatureIDS
        packets = rdpcap(filepath)
        sig_ids = SignatureIDS(app_state.rules)
        alert_objs = sig_ids.predict_from_pcap(packets)
        alerts = [_alert_to_dict(a) for a in alert_objs]
        messages.append('PCAP scanned successfully.')
    except Exception as e:
        messages.append(f'Failed to process PCAP: {e}')

    # TLS decryption
    keylog_file = request.files.get('keylog_file')
    if keylog_file and keylog_file.filename:
        keylog_path = os.path.join(app_state.UPLOAD_FOLDER, 'sslkeylog_' + secure_filename(keylog_file.filename))
        keylog_file.save(keylog_path)
        try:
            from tls_decrypt import decrypt_pcap
            tls_results = decrypt_pcap(filepath, keylog_path)
            if tls_results.get('error'):
                messages.append(f"TLS decryption warning: {tls_results['error']}")
            elif tls_results.get('results'):
                messages.append(f"TLS decryption: found {len(tls_results['results'])} HTTP requests.")
        except Exception as e:
            messages.append(f'TLS decryption failed: {e}')
        finally:
            try:
                os.remove(keylog_path)
            except OSError:
                pass
    else:
        try:
            from tls_decrypt import extract_tls_metadata, check_tshark
            tshark_path, _ = check_tshark()
            if tshark_path:
                tls_metadata = extract_tls_metadata(filepath)
        except Exception:
            pass

    return jsonify({
        'success': True, 'alerts': alerts,
        'tls_results': tls_results, 'tls_metadata': tls_metadata,
        'messages': messages,
    })


# ========== Rules ========== #

@api.route('/rules')
@login_required
@role_required('admin', 'signature_analyst')
def rules_list():
    try:
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        if not conn:
            return jsonify({'error': 'Database connection error'}), 500
        rules = [_rule_to_dict(r) for r in Rule.get_rules_from_db(conn)]
        conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'rules': rules})


# ========== Live Capture ========== #

@api.route('/live/status')
@login_required
@role_required('admin', 'signature_analyst', 'anomaly_analyst', 'live_operator')
def live_status():
    status = {
        'running': False, 'packets_captured': 0, 'alerts_generated': 0,
        'interface': '', 'interface_name': 'None selected', 'interface_desc': '',
        'last_error': '',
    }
    lc = app_state.live_capture_instance
    if lc:
        status = {
            'running': lc.is_running,
            'packets_captured': getattr(lc, 'packets_captured', 0),
            'alerts_generated': getattr(lc, 'alerts_generated', 0),
            'interface': getattr(lc, 'interface', ''),
            'interface_name': getattr(lc, '_interface_name', 'Unknown'),
            'interface_desc': getattr(lc, '_interface_desc', ''),
            'last_error': getattr(lc, 'last_error', ''),
        }

    interfaces = app_state.get_interfaces()
    alerts = []
    try:
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        alerts = [_alert_to_dict(a) for a in Alert.get_alerts_from_db(conn)]
        conn.close()
    except Exception:
        pass

    # get_interfaces() already returns list of dicts with id/name/description
    return jsonify({'status': status, 'alerts': alerts, 'interfaces': interfaces})


@api.route('/live/start', methods=['POST'])
@login_required
@role_required('admin', 'live_operator')
def live_start():
    if not app_state.rules:
        return jsonify({'success': False, 'message': 'No rules loaded.'}), 400

    if app_state.live_capture_instance and app_state.live_capture_instance.is_running:
        return jsonify({'success': False, 'message': 'Already running.'}), 400

    data = request.get_json(silent=True) or {}
    selected_iface = data.get('interface')

    iface_name = selected_iface or 'default'
    iface_desc = ''
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
        rules=app_state.rules, model=app_state.model,
        iso_forest=app_state.iso_forest, scaler=app_state.scaler,
        label_encoder=app_state.label_encoder,
        feature_order=app_state.feature_order,
        db_path=app_state.DB_PATH, interface=selected_iface,
    )
    app_state.live_capture_instance._interface_name = iface_name
    app_state.live_capture_instance._interface_desc = iface_desc
    started = app_state.live_capture_instance.start()
    if not started:
        error = getattr(app_state.live_capture_instance, 'last_error', '') or 'Capture could not start.'
        return jsonify({
            'success': False,
            'message': f'Live capture failed to start: {error}',
        }), 500
    return jsonify({'success': True, 'message': f'Live capture started on: {iface_name}'})


@api.route('/live/stop', methods=['POST'])
@login_required
@role_required('admin', 'live_operator')
def live_stop():
    if not app_state.live_capture_instance or not app_state.live_capture_instance.is_running:
        return jsonify({'success': False, 'message': 'No live capture is running.'}), 400
    app_state.live_capture_instance.stop()
    return jsonify({'success': True, 'message': 'Live capture stopped.'})


@api.route('/live/clear', methods=['POST'])
@login_required
@role_required('admin', 'live_operator')
def live_clear():
    try:
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        if conn:
            db.clear_table('alerts')
            db.clear_table('logs')
            db.clear_table('alert_features')
            conn.close()
            return jsonify({'success': True, 'message': 'All alerts cleared.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': False, 'message': 'Database connection error.'}), 500


@api.route('/live/delete', methods=['POST'])
@login_required
@role_required('admin', 'live_operator')
def live_delete():
    data = request.get_json(silent=True) or {}
    alert_ids = data.get('alert_ids', [])
    if not alert_ids:
        return jsonify({'success': False, 'message': 'No alerts selected.'}), 400
    try:
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        if conn:
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(alert_ids))
            cursor.execute(f'DELETE FROM alerts WHERE id IN ({placeholders})', alert_ids)
            cursor.execute(f'DELETE FROM alert_features WHERE alert_id IN ({placeholders})', alert_ids)
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': f'Deleted {len(alert_ids)} alert(s).', 'deleted_count': len(alert_ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': False, 'message': 'Database error.'}), 500


# ========== Admin ========== #

@api.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    db = Database(app_state.DB_PATH)
    conn = db.connect()
    users = [_user_to_dict(u) for u in User.get_all(conn)]
    conn.close()
    roles_dict = {k: {'label': v['label'], 'description': v['description']} for k, v in ROLES.items()}
    return jsonify({'users': users, 'roles': roles_dict})


@api.route('/admin/users', methods=['POST'])
@login_required
@role_required('admin')
def admin_create():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'live_operator')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required.'}), 400
    if role not in ROLES:
        return jsonify({'success': False, 'message': 'Invalid role.'}), 400

    db = Database(app_state.DB_PATH)
    conn = db.connect()
    success = User.create(conn, username, password, role)
    conn.close()

    if success:
        return jsonify({'success': True, 'message': f"User '{username}' created."})
    return jsonify({'success': False, 'message': f"Username '{username}' may already exist."}), 400


@api.route('/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def admin_delete(user_id):
    db = Database(app_state.DB_PATH)
    conn = db.connect()
    user = User.get_by_id(conn, user_id)
    if user and user.username == 'admin':
        conn.close()
        return jsonify({'success': False, 'message': 'Cannot delete the default admin.'}), 400

    success = User.delete(conn, user_id)
    conn.close()
    if success:
        return jsonify({'success': True, 'message': 'User deleted.'})
    return jsonify({'success': False, 'message': 'Failed to delete user.'}), 400


@api.route('/admin/users/<int:user_id>/role', methods=['PUT'])
@login_required
@role_required('admin')
def admin_update_role(user_id):
    data = request.get_json(silent=True) or {}
    new_role = data.get('role')
    if new_role not in ROLES:
        return jsonify({'success': False, 'message': 'Invalid role.'}), 400

    db = Database(app_state.DB_PATH)
    conn = db.connect()
    success = User.update_role(conn, user_id, new_role)
    conn.close()
    if success:
        return jsonify({'success': True, 'message': 'Role updated.'})
    return jsonify({'success': False, 'message': 'Failed to update role.'}), 400


# ========== Explain ========== #

@api.route('/explain/<int:alert_id>')
@login_required
@role_required('admin', 'anomaly_analyst')
def explain_alert(alert_id):
    db = Database(app_state.DB_PATH)
    conn = db.connect()
    if not conn:
        return jsonify({'error': 'Database connection error.'}), 500

    try:
        alert_data = get_alert_features(conn, alert_id)
        if not alert_data:
            return jsonify({'error': 'No feature data available for this alert.'}), 404

        features = alert_data['features']
        predicted_label = alert_data['predicted_label']
        confidence = alert_data['confidence']

        shap_result = explain_shap(app_state.model, app_state.scaler, app_state.feature_order, features)

        try:
            bg_df = pd.read_csv('Models/Dt/tst2_Cleaned_CIC_IDS2017_full_week.csv', nrows=500)
            bg_features = bg_df[app_state.feature_order]
            bg_scaled = pd.DataFrame(app_state.scaler.transform(bg_features), columns=app_state.feature_order)
        except Exception:
            bg_scaled = None

        lime_result = explain_lime(app_state.model, app_state.scaler, app_state.label_encoder,
                                    app_state.feature_order, features, bg_scaled)
        glossary = get_feature_glossary()

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

    return jsonify({
        'alert_id': alert_id, 'features': features,
        'predicted_label': predicted_label, 'confidence': confidence,
        'shap_result': shap_result, 'lime_result': lime_result,
        'glossary': glossary,
    })


# ========== Retrain ========== #

@api.route('/retrain/dashboard')
@login_required
@role_required('admin')
def retrain_dashboard():
    db = Database(app_state.DB_PATH)
    conn = db.connect()
    if not conn:
        return jsonify({'error': 'Database connection error.'}), 500

    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    filters = {}
    for key in ('label', 'labeled', 'source', 'date_from', 'date_to'):
        val = request.args.get(key, '')
        if val:
            filters[key] = val

    try:
        stats = get_training_stats(conn)
        samples = get_training_samples(conn, limit=per_page, offset=offset, filters=filters)
        history = get_retrain_history(conn)
        retrain_status = get_retrain_status()
        label_classes = list(app_state.label_encoder.classes_)
    finally:
        conn.close()

    return jsonify({
        'stats': stats, 'samples': samples, 'history': history,
        'retrain_status': retrain_status, 'label_classes': label_classes,
        'page': page, 'per_page': per_page,
    })


@api.route('/retrain/start', methods=['POST'])
@login_required
@role_required('admin')
def retrain_start():
    retrain_status = get_retrain_status()
    if retrain_status.get('running'):
        return jsonify({'success': False, 'message': 'Already running.'}), 400

    username = current_user.username

    def run_retrain():
        db = Database(app_state.DB_PATH)
        conn = db.connect()
        if conn:
            try:
                retrain_models(conn, started_by=username)
            finally:
                conn.close()

    threading.Thread(target=run_retrain, daemon=True).start()
    return jsonify({'success': True, 'message': 'Retraining started.'})


@api.route('/retrain/label', methods=['POST'])
@login_required
@role_required('admin')
def retrain_label():
    data = request.get_json(silent=True) or {}
    sample_id = data.get('sample_id')
    label = data.get('label')

    if not sample_id or not label:
        return jsonify({'success': False, 'message': 'Sample ID and label required.'}), 400

    db = Database(app_state.DB_PATH)
    conn = db.connect()
    if conn:
        try:
            if update_human_label(conn, int(sample_id), label):
                return jsonify({'success': True, 'message': f'Label updated for #{sample_id}: {label}'})
            return jsonify({'success': False, 'message': 'Failed to update label.'}), 400
        finally:
            conn.close()
    return jsonify({'success': False, 'message': 'Database error.'}), 500


# ========== Analytics ========== #

# Map SQL operators from frontend to analytics engine semantic operators
_SQL_OP_TO_SEMANTIC = {
    '=': 'eq', '==': 'eq', '!=': 'neq', '<>': 'neq',
    '>': 'gt', '>=': 'gte', '<': 'lt', '<=': 'lte',
    'LIKE': 'contains', 'like': 'contains', 'IN': 'in', 'in': 'in',
}

# Tables allowed for direct queries (beyond the analytics engine)
_DIRECT_QUERY_TABLES = {'alerts', 'logs', 'rules', 'users', 'training_data'}

# Columns allowed per table (whitelist to prevent injection)
_TABLE_COLUMNS = {
    'alerts':        ['id', 'timestamp', 'src_ip', 'dst_ip', 'message', 'attack', 'method'],
    'logs':          ['id', 'timestamp', 'event_type', 'src_ip', 'dst_ip', 'message', 'attack', 'method'],
    'rules':         ['id', 'action', 'protocol', 'src_ip', 'src_port', 'direction', 'dst_ip', 'dst_port', 'options'],
    'users':         ['id', 'username', 'role', 'created_at'],
    'training_data': ['id', 'predicted_label', 'confidence', 'human_label', 'source', 'created_at'],
}


@api.route('/analytics/query', methods=['POST'])
@login_required
@role_required('admin', 'signature_analyst', 'anomaly_analyst')
def analytics_query():
    raw_query = request.get_json()
    if not raw_query:
        return jsonify({'success': False, 'error': 'No query provided.'}), 400

    db = Database(app_state.DB_PATH)
    conn = db.connect()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection error.'}), 500

    try:
        # Detect frontend simple-query format (has 'table' or 'conditions' keys)
        if 'table' in raw_query or 'conditions' in raw_query:
            result = _run_direct_query(conn, raw_query)
        else:
            # Original analytics engine format (GUI_QUERY with 'dataset', 'filters', etc.)
            from analytics import execute_query
            result = execute_query(conn, raw_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()


def _run_direct_query(conn, raw_query):
    """Handle the frontend's simple query format with parameterized SQL."""
    table = raw_query.get('table', 'alerts')
    if table not in _DIRECT_QUERY_TABLES:
        return {'success': False, 'error': f"Invalid table: {table}"}

    allowed_cols = _TABLE_COLUMNS.get(table, [])
    conditions = raw_query.get('conditions', [])
    order_by = raw_query.get('order_by', '')
    order_dir = raw_query.get('order_dir', 'DESC').upper()
    limit = min(int(raw_query.get('limit', 100)), 500)

    # Build SELECT
    select_cols = ', '.join(allowed_cols)

    # Build WHERE from conditions (parameterized)
    where_parts = []
    params = []
    for cond in conditions:
        col = cond.get('column', '')
        op = cond.get('operator', '=')
        val = cond.get('value', '')
        if not col or col not in allowed_cols:
            continue
        if not val and op not in ('=', '!=', '<>'):
            continue
        # Validate operator
        if op in ('=', '==', '!=', '<>', '>', '<', '>=', '<='):
            where_parts.append(f"{col} {op} ?")
            params.append(val)
        elif op.upper() == 'LIKE':
            where_parts.append(f"{col} LIKE ?")
            # Auto-wrap in % if user didn't include them
            if '%' not in val:
                val = f"%{val}%"
            params.append(val)
        elif op.upper() == 'IN':
            values = [v.strip() for v in val.split(',') if v.strip()]
            if values:
                placeholders = ', '.join(['?'] * len(values))
                where_parts.append(f"{col} IN ({placeholders})")
                params.extend(values)

    where_sql = ''
    if where_parts:
        where_sql = 'WHERE ' + ' AND '.join(where_parts)

    # Build ORDER BY
    order_sql = ''
    if order_by and order_by in allowed_cols:
        if order_dir not in ('ASC', 'DESC'):
            order_dir = 'DESC'
        order_sql = f"ORDER BY {order_by} {order_dir}"
    elif 'timestamp' in allowed_cols:
        order_sql = "ORDER BY timestamp DESC"

    sql = f"SELECT {select_cols} FROM {table} {where_sql} {order_sql} LIMIT ?"
    params.append(limit)

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        data = [dict(zip(allowed_cols, row)) for row in rows]
        return {
            'success': True,
            'columns': allowed_cols,
            'rows': data,
            'total': len(data),
        }
    except Exception as e:
        return {'success': False, 'error': f"Query error: {e}"}
