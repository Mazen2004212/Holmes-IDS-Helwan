import sqlite3

class Log:
    def __init__(self, time, action, src_ip, dst_ip, message, attack,method):
        self.time = time
        self.action = action
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.message = message
        self.attack = attack
        self.method = method
        
    def add_to_log_table(self, conn):
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO logs (timestamp, event_type, src_ip, dst_ip, message, attack,method)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (self.time, self.action, self.src_ip, self.dst_ip, self.message, self.attack,self.method)
        )
        
        conn.commit()
       
        
    @classmethod
    def get_logs_from_db(cls, conn):
        cursor = conn.cursor()
        query = "SELECT * FROM logs"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        logs = []
        
        for row in rows:
            log = cls(
                time = row[1], 
                action = row[2],  
                src_ip = row[3],
                dst_ip = row[4],
                message = row[5],
                attack = row[6],
                method = row[7]
            )
            
            logs.append(log)
        
        return logs

    