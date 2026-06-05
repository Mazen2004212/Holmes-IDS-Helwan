import smtplib
import sqlite3

class Alert:
    def __init__(self, time, src_ip, dst_ip, message, attack,method):
        self.time = time
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.message = message
        self.attack = attack
        self.method = method
    
    def add_to_alert_table(self, conn):
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO alerts(timestamp,src_ip,dst_ip,message,attack,method)
            VALUES (?, ?, ?, ?, ?, ?)  
            """,
            (
                self.time,  
                self.src_ip, 
                self.dst_ip, 
                self.message,
                self.attack,
                self.method
            )
        )
        conn.commit()
        return cursor.lastrowid
        

    @classmethod
    def get_alerts_from_db(cls, conn):
        cursor = conn.cursor()
        query = "SELECT * FROM alerts"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        alerts = []
        
        for row in rows:
            alert = cls(
                time = row[1],  
                src_ip = row[2],
                dst_ip = row[3],
                message = row[4],
                attack = row[5],
                method = row[6]
            )
            alert.id = row[0]  # Store the DB id for SHAP/LIME explain links
            
            alerts.append(alert)

        return alerts
