"""Tests for the Database class."""
import pytest
import json
from DB import Database, ALLOWED_TABLES
from log import Log
from alert import Alert


class TestDatabaseConnection:
    def test_connect_in_memory(self):
        db = Database(":memory:")
        conn = db.connect()
        assert conn is not None
        db.close()

    def test_close(self):
        db = Database(":memory:")
        db.connect()
        db.close()
        assert db.conn is None

    def test_context_manager(self):
        with Database(":memory:") as db:
            assert db.conn is not None
        assert db.conn is None


class TestDatabaseTableCreation:
    def test_create_rules_table(self):
        db = Database(":memory:")
        db.connect()
        db.create_table_rules()
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rules'")
        assert cursor.fetchone() is not None
        db.close()

    def test_create_logs_table(self):
        db = Database(":memory:")
        db.connect()
        db.create_table_logs()
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
        assert cursor.fetchone() is not None
        db.close()

    def test_create_alerts_table(self):
        db = Database(":memory:")
        db.connect()
        db.create_table_alerts()
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
        assert cursor.fetchone() is not None
        db.close()


class TestClearTable:
    def test_clear_valid_table(self, in_memory_db):
        """Should successfully clear a whitelisted table."""
        db = Database(":memory:")
        db.conn = in_memory_db  # Use the fixture's connection
        
        # Insert a row first
        in_memory_db.cursor().execute(
            "INSERT INTO logs (timestamp, event_type, src_ip, dst_ip, message, attack, method) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("2024-01-01", "alert", "10.0.0.1", "10.0.0.2", "test", "test", "signature")
        )
        in_memory_db.commit()
        
        result = db.clear_table("logs")
        assert result is True
        
        cursor = in_memory_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs")
        assert cursor.fetchone()[0] == 0

    def test_clear_invalid_table(self, in_memory_db):
        """Should reject table names not in the whitelist (SQL injection prevention)."""
        db = Database(":memory:")
        db.conn = in_memory_db
        
        result = db.clear_table("users; DROP TABLE rules; --")
        assert result is False

    def test_allowed_tables_defined(self):
        """Verify the whitelist contains expected tables."""
        assert "logs" in ALLOWED_TABLES
        assert "alerts" in ALLOWED_TABLES
        assert "rules" in ALLOWED_TABLES


class TestLogAlertIntegration:
    def test_add_and_retrieve_log(self, in_memory_db):
        log = Log("2024-01-01 12:00:00", "alert", "10.0.0.1", "10.0.0.2",
                  "Test message", "Test Attack", "signature")
        log.add_to_log_table(in_memory_db)
        
        logs = Log.get_logs_from_db(in_memory_db)
        assert len(logs) == 1
        assert logs[0].message == "Test message"
        assert logs[0].method == "signature"

    def test_add_and_retrieve_alert(self, in_memory_db):
        alert = Alert("2024-01-01 12:00:00", "10.0.0.1", "10.0.0.2",
                      "Test alert", "Network Attack", "anomaly")
        alert.add_to_alert_table(in_memory_db)
        
        alerts = Alert.get_alerts_from_db(in_memory_db)
        assert len(alerts) == 1
        assert alerts[0].message == "Test alert"
        assert alerts[0].method == "anomaly"
