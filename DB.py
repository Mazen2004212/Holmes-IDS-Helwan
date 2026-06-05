import sqlite3

ALLOWED_TABLES = {"logs", "alerts", "rules", "users", "alert_features", "training_data", "retrain_jobs"}

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False, timeout=10)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute('PRAGMA journal_mode=WAL;')
            return self.conn
        except sqlite3.Error as e:
            print(f"[Error] Failed to connect to the database: {e}")
            return None

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def create_table_rules(self):
        create_table_rules = """
        CREATE TABLE IF NOT EXISTS rules 
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            protocol TEXT,
            src_ip TEXT,
            src_port TEXT,
            direction TEXT,
            dst_ip TEXT,
            dst_port TEXT,
            options TEXT
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(create_table_rules)
            self.conn.commit()
            print("[Success] 'rules' table created or already exists.")
        except sqlite3.Error as e:
            print(f"[Database Error] {e}")

    def create_table_logs(self):
        create_table_logs = """
        CREATE TABLE IF NOT EXISTS logs 
        (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME,
            event_type TEXT,
            src_ip TEXT,
            dst_ip TEXT,
            message TEXT,
            attack TEXT,
            method TEXT
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(create_table_logs)
            self.conn.commit()
            print("[Success] 'logs' table created or already exists.")
        except sqlite3.Error as e:
            print(f"[Database Error] {e}")

    def create_table_alerts(self):
        create_table_alerts = """
        CREATE TABLE IF NOT EXISTS alerts 
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            src_ip TEXT,
            dst_ip TEXT,
            message TEXT,
            attack TEXT,
            method TEXT
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(create_table_alerts)
            self.conn.commit()
            print("[Success] 'alerts' table created or already exists.")
        except sqlite3.Error as e:
            print(f"[Database Error] {e}")

    def create_table_users(self):
        create_table_users = """
        CREATE TABLE IF NOT EXISTS users 
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'live_operator',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(create_table_users)
            self.conn.commit()
            print("[Success] 'users' table created or already exists.")
        except sqlite3.Error as e:
            print(f"[Database Error] {e}")

    def clear_table(self, table_name):
        if table_name not in ALLOWED_TABLES:
            print(f"[Error] Invalid table name: '{table_name}'. Allowed: {ALLOWED_TABLES}")
            return False

        try:
            if not self.conn:
                print("[Error] No database connection.")
                return False

            cursor = self.conn.cursor()
            cursor.execute(f"DELETE FROM {table_name};")
            self.conn.commit()
            print(f"[Success] All records from '{table_name}' have been deleted.")
            return True
        except sqlite3.Error as e:
            print(f"[Database Error] {e}")
            return False

    def create_table_alert_features(self):
        """Store raw feature vectors linked to anomaly alerts for SHAP/LIME."""
        sql = """
        CREATE TABLE IF NOT EXISTS alert_features
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL,
            features_json TEXT NOT NULL,
            predicted_label TEXT,
            confidence REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (alert_id) REFERENCES alerts(id)
        );
        """
        try:
            self.conn.cursor().execute(sql)
            self.conn.commit()
            print("[Success] 'alert_features' table created or already exists.")
        except sqlite3.Error as e:
            print(f"[Database Error] {e}")

    def create_table_training_data(self):
        """Store flow features for continual learning."""
        sql = """
        CREATE TABLE IF NOT EXISTS training_data
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            features_json TEXT NOT NULL,
            predicted_label TEXT,
            confidence REAL,
            human_label TEXT,
            feature_version TEXT,
            source TEXT DEFAULT 'live_capture',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            self.conn.cursor().execute(sql)
            self.conn.commit()
            print("[Success] 'training_data' table created or already exists.")
        except sqlite3.Error as e:
            print(f"[Database Error] {e}")

    def create_table_retrain_jobs(self):
        """Track model retraining jobs."""
        sql = """
        CREATE TABLE IF NOT EXISTS retrain_jobs
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL DEFAULT 'pending',
            started_by TEXT,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            finished_at DATETIME,
            old_accuracy REAL,
            new_accuracy REAL,
            old_f1 REAL,
            new_f1 REAL,
            promoted INTEGER DEFAULT 0,
            samples_used INTEGER DEFAULT 0,
            error_message TEXT
        );
        """
        try:
            self.conn.cursor().execute(sql)
            self.conn.commit()
            print("[Success] 'retrain_jobs' table created or already exists.")
        except sqlite3.Error as e:
            print(f"[Database Error] {e}")
