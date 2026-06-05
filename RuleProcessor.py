import json
import sqlite3
from DB import Database

def extract_rules(file_path):
        rules = []
        current_rule = ""

        try:
            
            with open(file_path, "r") as f:
                
                for line in f:
            
                    line = line.strip()
            
                    if line.startswith("#") or not line:
                        continue
            
                    if "(" in line and ")" not in line:
                        current_rule = line
            
                    elif current_rule:
                        current_rule += " " + line
            
                        if ")" in line:
                            rules.append(current_rule)
                            current_rule = ""
            
                    else:
                        rules.append(line)
                        
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
            
        except Exception as e:
            print(f"Error while reading rules: {e}")

        return rules

def parse_rule(rule):
    parts = rule.split('(')
    header = parts[0].strip()
    options = parts[1].strip(')').split(';')

    header_parts = header.split()
    
    action = header_parts[0]
    proto = header_parts[1] 
    src_ip = header_parts[2]
    src_port = header_parts[3]
    direction = header_parts[4]
    dst_ip = header_parts[5]
    dst_port = header_parts[6]

    options_dict = {}

    for option in options:
        
        if ':' in option:
            key, value = option.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"')

            if key == 'dsize' or key == 'threshold' or key == 'itype':
                options_dict[key] = int(value)
            
            elif key == 'pcre':
                options_dict[key] = rf"{value}"
            
            else:
                options_dict[key] = value  
   
    return {
        "action": action,
        "protocol": proto,
        "src_ip": src_ip,
        "src_port": src_port,
        "dst_ip": dst_ip,
        "dst_port": dst_port,
        "direction": direction,
        "options": options_dict
    }

def load_rules_to_db(file_path, conn):
    cursor = conn.cursor()
    rules = extract_rules(file_path)
    
    for rule in rules:
        parsed_rule = parse_rule(rule)
        
        cursor.execute(
            """
            INSERT INTO rules 
            (
                action, 
                protocol, 
                src_ip, 
                src_port, 
                direction, 
                dst_ip, 
                dst_port, 
                options
            )
            
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                parsed_rule['action'],
                parsed_rule['protocol'],
                parsed_rule['src_ip'],
                parsed_rule['src_port'],
                parsed_rule['direction'],
                parsed_rule['dst_ip'],
                parsed_rule['dst_port'],
                json.dumps(parsed_rule['options'])  
            )
        )

    conn.commit()
    
    print(f"Inserted {len(rules)} rules into the database.")

def get_rules_from_db(conn):
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rules")
    rows = cursor.fetchall()

   
    rules = []
    
    for row in rows:
        rules.append({
            "id": row[0],
            "action": row[1],
            "protocol": row[2],
            "src_ip": row[3],
            "src_port": row[4],
            "direction": row[5],
            "dst_ip": row[6],
            "dst_port": row[7],
            "options": json.loads(row[8]) 
        })
   
    return rules

if __name__ == "__main__":
    
    DB = Database('DB/IDS.db')
    conn = DB.connect()

    file_path = 'Rules/new.txt'

    load_rules_to_db(file_path, conn)

    rules = get_rules_from_db(conn)
    
    for rule in rules:
        payload = "GET /admin HTTP/1.1\r\nHost: google.com\r\nUser-Agent: attack_tool\r\n\r\n"
        
        content = rule["options"].get("content")
        
        if content:
            if content.startswith("!"):
        
                if content[1:] not in payload:
                    print(f"Negation match: {content[1:]}")
            else:
        
                if content in payload:
                    print(f"Content match: {content}")

    conn.close()