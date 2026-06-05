"""
Analytics Query Builder Engine for HOLMES IDS.
===============================================
Parses GUI_QUERY JSON from the frontend query builder and executes
safe parameterized queries against the alerts database.

NEVER exposes raw SQL to the user. All queries are built internally
using whitelisted field names and parameterized values.
"""

import re
from datetime import datetime, timedelta

# ========== Field Mapping ========== #
# Maps user-facing GUI_QUERY field names to actual DB column names.

FIELD_MAP = {
    "timestamp":  "timestamp",
    "src_ip":     "src_ip",
    "dst_ip":     "dst_ip",
    "signature":  "message",      # rule name / alert text
    "message":    "message",
    "category":   "attack",       # attack layer
    "attack":     "attack",
    "action":     "method",       # signature / anomaly
    "method":     "method",
}

# Fields that are valid for filtering / grouping
ALLOWED_FIELDS = set(FIELD_MAP.keys())

# Operators and their SQL equivalents
OP_MAP = {
    "eq":         ("= ?",              False),
    "neq":        ("!= ?",             False),
    "gt":         ("> ?",              False),
    "gte":        (">= ?",            False),
    "lt":         ("< ?",              False),
    "lte":        ("<= ?",            False),
    "contains":   ("LIKE ?",           True),   # wrap value in %..%
    "startswith": ("LIKE ?",           True),   # wrap value in ..%
    "endswith":   ("LIKE ?",           True),   # wrap value in %..
    "in":         ("IN",               False),  # special handling
    "between":    ("BETWEEN ? AND ?",  False),  # special handling
}


def execute_query(conn, gui_query):
    """
    Main entry point. Parse a GUI_QUERY dict and return results.

    Returns:
        dict with keys: rows, columns, summary, chart_data, explain
    """
    dataset = gui_query.get("dataset", "alerts")
    if dataset != "alerts":
        return _error("Only the 'alerts' dataset is currently supported.")

    try:
        # 1. Build time range filter
        time_clauses, time_params = _build_time_range(gui_query.get("time_range"))

        # 2. Build user filters
        filter_clauses, filter_params = _build_filters(gui_query.get("filters", []))

        # 3. Combine WHERE
        all_clauses = time_clauses + filter_clauses
        all_params = time_params + filter_params
        where_sql = ""
        if all_clauses:
            where_sql = "WHERE " + " AND ".join(all_clauses)

        # 4. Check for detection patterns first (special queries)
        detections = gui_query.get("detections", [])
        if detections:
            return _run_detections(conn, detections, where_sql, all_params, gui_query)

        # 5. Build GROUP BY + metrics
        group_by = gui_query.get("group_by", [])
        metrics = gui_query.get("metrics", [{"name": "alert_count", "type": "count"}])
        time_bucket = gui_query.get("time_bucket")

        if group_by or time_bucket:
            return _run_grouped_query(conn, group_by, metrics, time_bucket,
                                       where_sql, all_params, gui_query)
        else:
            return _run_raw_query(conn, where_sql, all_params, gui_query)

    except Exception as e:
        return _error(str(e))


# ========== Time Range ========== #

def _build_time_range(time_range):
    if not time_range:
        return [], []

    clauses = []
    params = []
    mode = time_range.get("mode", "relative")

    if mode == "relative":
        last = time_range.get("last", "24h")
        delta = _parse_relative(last)
        if delta:
            cutoff = (datetime.utcnow() - delta).strftime("%Y-%m-%d %H:%M:%S")
            clauses.append("timestamp >= ?")
            params.append(cutoff)
    elif mode == "absolute":
        start = time_range.get("start")
        end = time_range.get("end")
        if start:
            clauses.append("timestamp >= ?")
            params.append(start)
        if end:
            clauses.append("timestamp <= ?")
            params.append(end)

    return clauses, params


def _parse_relative(last_str):
    """Parse '24h', '7d', '30d', '1h', '60m' into timedelta."""
    match = re.match(r'^(\d+)([hdm])$', last_str)
    if not match:
        return None
    val, unit = int(match.group(1)), match.group(2)
    if unit == 'h':
        return timedelta(hours=val)
    elif unit == 'd':
        return timedelta(days=val)
    elif unit == 'm':
        return timedelta(minutes=val)
    return None


# ========== Filters ========== #

def _build_filters(filters):
    clauses = []
    params = []

    for f in filters:
        field = f.get("field", "")
        op = f.get("op", "eq")
        value = f.get("value", "")

        if field not in ALLOWED_FIELDS:
            continue  # skip unknown fields silently

        col = FIELD_MAP[field]

        if op == "in":
            if isinstance(value, list):
                placeholders = ",".join(["?"] * len(value))
                clauses.append(f"{col} IN ({placeholders})")
                params.extend(value)
        elif op == "between":
            if isinstance(value, list) and len(value) == 2:
                clauses.append(f"{col} BETWEEN ? AND ?")
                params.extend(value)
        elif op in OP_MAP:
            sql_op, is_like = OP_MAP[op]
            if is_like:
                if op == "contains":
                    value = f"%{value}%"
                elif op == "startswith":
                    value = f"{value}%"
                elif op == "endswith":
                    value = f"%{value}"
            clauses.append(f"{col} {sql_op}")
            params.append(value)

    return clauses, params


# ========== Raw Query (no grouping) ========== #

def _run_raw_query(conn, where_sql, params, gui_query):
    sort = gui_query.get("sort", [{"field": "timestamp", "direction": "desc"}])
    limit = min(gui_query.get("limit", 100), 500)

    order_sql = _build_order(sort)

    sql = f"SELECT id, timestamp, src_ip, dst_ip, message, attack, method FROM alerts {where_sql} {order_sql} LIMIT ?"
    params.append(limit)

    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()

    columns = ["id", "timestamp", "src_ip", "dst_ip", "signature", "category", "method"]
    data = [dict(zip(columns, row)) for row in rows]

    return {
        "success": True,
        "type": "table",
        "columns": columns,
        "rows": data,
        "total": len(data),
        "explain": _build_explain(gui_query, len(data)),
    }


# ========== Grouped Query ========== #

def _run_grouped_query(conn, group_by, metrics, time_bucket, where_sql, params, gui_query):
    select_parts = []
    group_cols = []

    # Time bucketing
    if time_bucket or "time_bucket" in group_by:
        unit = "hour"
        if time_bucket:
            unit = time_bucket.get("unit", "hour")
        if unit == "minute":
            bucket_expr = "strftime('%Y-%m-%d %H:%M', timestamp)"
        elif unit == "hour":
            bucket_expr = "strftime('%Y-%m-%d %H:00', timestamp)"
        elif unit == "day":
            bucket_expr = "strftime('%Y-%m-%d', timestamp)"
        else:
            bucket_expr = "strftime('%Y-%m-%d %H:00', timestamp)"

        select_parts.append(f"{bucket_expr} AS time_bucket")
        group_cols.append(bucket_expr)

    # Regular group-by fields
    for field in group_by:
        if field == "time_bucket":
            continue
        if field in FIELD_MAP:
            col = FIELD_MAP[field]
            select_parts.append(f"{col} AS {field}")
            group_cols.append(col)

    # Metrics
    for m in metrics:
        mtype = m.get("type", "count")
        mname = m.get("name", "count")
        if mtype == "count":
            select_parts.append(f"COUNT(*) AS {mname}")
        elif mtype == "count_distinct":
            mfield = m.get("field", "src_ip")
            if mfield in FIELD_MAP:
                select_parts.append(f"COUNT(DISTINCT {FIELD_MAP[mfield]}) AS {mname}")

    if not select_parts:
        return _error("No valid columns for grouping.")

    select_sql = ", ".join(select_parts)
    group_sql = ""
    if group_cols:
        group_sql = "GROUP BY " + ", ".join(group_cols)

    sort = gui_query.get("sort", [{"field": "alert_count", "direction": "desc"}])
    order_sql = _build_order_grouped(sort)
    limit = min(gui_query.get("limit", 50), 500)

    sql = f"SELECT {select_sql} FROM alerts {where_sql} {group_sql} {order_sql} LIMIT ?"
    params.append(limit)

    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()

    col_names = [desc[0] for desc in cursor.description]
    data = [dict(zip(col_names, row)) for row in rows]

    # Determine visualization type
    visuals = gui_query.get("visuals", [])
    vis_type = "table"
    if visuals:
        vis_type = visuals[0].get("type", "table")
    elif "time_bucket" in [c for c in col_names]:
        vis_type = "timeseries"

    return {
        "success": True,
        "type": vis_type,
        "columns": col_names,
        "rows": data,
        "total": len(data),
        "explain": _build_explain(gui_query, len(data)),
    }


# ========== Detection Patterns ========== #

def _run_detections(conn, detections, where_sql, params, gui_query):
    results = []

    for det in detections:
        if not det.get("enabled", True):
            continue

        det_type = det.get("type", "")
        det_params = det.get("parameters", {})

        if det_type == "bruteforce":
            results.extend(_detect_bruteforce(conn, where_sql, params, det_params))
        elif det_type == "port_scan":
            results.extend(_detect_repeated_source(conn, where_sql, params, det_params,
                                                     "Possible Port Scan"))
        elif det_type == "dos_spike":
            results.extend(_detect_dos_spike(conn, where_sql, params, det_params))
        elif det_type in ("credential_stuffing", "beaconing"):
            results.extend(_detect_repeated_source(conn, where_sql, params, det_params,
                                                     f"Possible {det_type.replace('_', ' ').title()}"))
        else:
            results.extend(_detect_repeated_source(conn, where_sql, params, det_params,
                                                     f"Detection: {det_type}"))

    columns = ["detection", "src_ip", "alert_count", "details"]
    return {
        "success": True,
        "type": "detection",
        "columns": columns,
        "rows": results,
        "total": len(results),
        "explain": _build_explain(gui_query, len(results)),
    }


def _detect_bruteforce(conn, where_sql, params, det_params):
    """Detect source IPs with high alert volume (possible brute force)."""
    min_attempts = det_params.get("min_attempts", 10)
    time_window = det_params.get("time_window_minutes", 5)

    # Build a time-windowed query
    window_clause = ""
    window_params = list(params)
    if time_window:
        cutoff = (datetime.utcnow() - timedelta(minutes=time_window)).strftime("%Y-%m-%d %H:%M:%S")
        if where_sql:
            window_clause = where_sql + " AND timestamp >= ?"
        else:
            window_clause = "WHERE timestamp >= ?"
        window_params.append(cutoff)
    else:
        window_clause = where_sql

    sql = f"""SELECT src_ip, COUNT(*) as cnt, 
              GROUP_CONCAT(DISTINCT message) as sigs
              FROM alerts {window_clause}
              GROUP BY src_ip
              HAVING cnt >= ?
              ORDER BY cnt DESC LIMIT 50"""
    window_params.append(min_attempts)

    cursor = conn.cursor()
    cursor.execute(sql, window_params)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        results.append({
            "detection": "Brute Force Candidate",
            "src_ip": row[0],
            "alert_count": row[1],
            "details": f"Signatures: {row[2][:200] if row[2] else 'N/A'}",
        })
    return results


def _detect_repeated_source(conn, where_sql, params, det_params, label):
    """Generic: find source IPs with high alert count."""
    min_attempts = det_params.get("min_attempts", 20)

    sql = f"""SELECT src_ip, COUNT(*) as cnt,
              COUNT(DISTINCT dst_ip) as targets,
              GROUP_CONCAT(DISTINCT message) as sigs
              FROM alerts {where_sql}
              GROUP BY src_ip
              HAVING cnt >= ?
              ORDER BY cnt DESC LIMIT 50"""
    p = list(params) + [min_attempts]

    cursor = conn.cursor()
    cursor.execute(sql, p)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        results.append({
            "detection": label,
            "src_ip": row[0],
            "alert_count": row[1],
            "details": f"Targets: {row[2]} unique IPs | Sigs: {row[3][:200] if row[3] else 'N/A'}",
        })
    return results


def _detect_dos_spike(conn, where_sql, params, det_params):
    """Detect time buckets with abnormally high alert counts."""
    threshold = det_params.get("min_attempts", 50)

    sql = f"""SELECT strftime('%Y-%m-%d %H:%M', timestamp) as bucket,
              COUNT(*) as cnt,
              GROUP_CONCAT(DISTINCT src_ip) as sources
              FROM alerts {where_sql}
              GROUP BY bucket
              HAVING cnt >= ?
              ORDER BY cnt DESC LIMIT 20"""
    p = list(params) + [threshold]

    cursor = conn.cursor()
    cursor.execute(sql, p)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        results.append({
            "detection": "DoS Spike",
            "src_ip": row[2][:100] if row[2] else "N/A",
            "alert_count": row[1],
            "details": f"Time: {row[0]}",
        })
    return results


# ========== Helpers ========== #

def _build_order(sort_list):
    if not sort_list:
        return "ORDER BY timestamp DESC"
    parts = []
    for s in sort_list:
        field = s.get("field", "timestamp")
        direction = s.get("direction", "desc").upper()
        if direction not in ("ASC", "DESC"):
            direction = "DESC"
        if field in FIELD_MAP:
            parts.append(f"{FIELD_MAP[field]} {direction}")
    return "ORDER BY " + ", ".join(parts) if parts else "ORDER BY timestamp DESC"


def _build_order_grouped(sort_list):
    if not sort_list:
        return "ORDER BY 1 DESC"
    parts = []
    for s in sort_list:
        field = s.get("field", "alert_count")
        direction = s.get("direction", "desc").upper()
        if direction not in ("ASC", "DESC"):
            direction = "DESC"
        # Use field name directly for aggregated aliases
        parts.append(f"{field} {direction}")
    return "ORDER BY " + ", ".join(parts) if parts else "ORDER BY 1 DESC"


def _build_explain(gui_query, total_results):
    explain = gui_query.get("explain", {})
    filters = gui_query.get("filters", [])
    time_range = gui_query.get("time_range", {})

    # Auto-generate summary if not provided
    summary = explain.get("human_summary", "")
    if not summary:
        parts = [f"Queried alerts table."]
        if time_range:
            mode = time_range.get("mode", "relative")
            if mode == "relative":
                parts.append(f"Time range: last {time_range.get('last', '24h')}.")
            else:
                parts.append(f"Time range: {time_range.get('start', '?')} to {time_range.get('end', '?')}.")
        if filters:
            parts.append(f"Applied {len(filters)} filter(s).")
        parts.append(f"Found {total_results} result(s).")
        summary = " ".join(parts)

    # Note missing fields
    limits = list(explain.get("limits", []))
    missing_fields = []
    for f in gui_query.get("filters", []):
        if f.get("field") not in ALLOWED_FIELDS:
            missing_fields.append(f.get("field"))
    if missing_fields:
        limits.append(f"Fields not available in alerts table: {', '.join(missing_fields)}")

    return {
        "human_summary": summary,
        "assumptions": explain.get("assumptions", []),
        "limits": limits,
        "total_results": total_results,
    }


def _error(message):
    return {
        "success": False,
        "type": "error",
        "columns": [],
        "rows": [],
        "total": 0,
        "explain": {
            "human_summary": f"Error: {message}",
            "assumptions": [],
            "limits": [message],
            "total_results": 0,
        }
    }
