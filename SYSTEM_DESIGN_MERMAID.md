# HOLMES IDS - System Design Mermaid Diagrams

Export each diagram as PNG or SVG and send the rendered images back. Use the exact figure names below so they can be inserted into the final DOCX.

Recommended export names:

- `figure_3_1_admin_use_case.png`
- `figure_3_2_system_use_case.png`
- `figure_3_3_system_component.png`
- `figure_3_4_class_diagram.png`
- `figure_3_5_login_sequence.png`
- `figure_3_6_live_capture_sequence.png`
- `figure_3_7_csv_prediction_sequence.png`
- `figure_3_8_pcap_scan_sequence.png`
- `figure_3_9_retraining_sequence.png`
- `figure_3_10_activity_live_capture.png`
- `figure_3_11_er_diagram.png`
- `figure_4_1_high_level_architecture.png`
- `figure_4_2_detection_pipeline.png`
- `figure_4_3_deployment_diagram.png`

## Figure 3.1 - Admin Use Case Diagram

```mermaid
flowchart LR
    Admin(["Admin"])
    System["HOLMES IDS"]

    Admin --> Login["Login"]
    Admin --> ViewDash["View Dashboards"]
    Admin --> ManageUsers["Manage Users and Roles"]
    Admin --> ManageRules["View and Manage Rules"]
    Admin --> UploadCSV["Upload CSV for Anomaly Detection"]
    Admin --> UploadPCAP["Upload PCAP for Signature Detection"]
    Admin --> LiveCapture["Start/Stop Live Capture"]
    Admin --> Explain["View SHAP/LIME Explanation"]
    Admin --> Analytics["Run Analytics Queries"]
    Admin --> Retrain["Review Labels and Retrain Models"]

    Login --> System
    ViewDash --> System
    ManageUsers --> System
    ManageRules --> System
    UploadCSV --> System
    UploadPCAP --> System
    LiveCapture --> System
    Explain --> System
    Analytics --> System
    Retrain --> System
```

## Figure 3.2 - IDS System Use Case Diagram

```mermaid
flowchart LR
    SigAnalyst(["Signature Analyst"])
    AnomAnalyst(["Anomaly Analyst"])
    LiveOperator(["Live Operator"])
    Admin(["Admin"])
    System["HOLMES IDS"]

    SigAnalyst --> SigDash["View Signature Dashboard"]
    SigAnalyst --> Rules["Display Rules"]
    SigAnalyst --> PCAP["Upload PCAP"]

    AnomAnalyst --> AnomDash["View Anomaly Dashboard"]
    AnomAnalyst --> CSV["Upload CSV"]
    AnomAnalyst --> XAI["Explain Alert"]

    LiveOperator --> Interfaces["Select Interface"]
    LiveOperator --> Start["Start Capture"]
    LiveOperator --> Stop["Stop Capture"]
    LiveOperator --> Clear["Clear Live Alerts"]

    Admin --> Users["Manage Users"]
    Admin --> Retrain["Retrain Models"]
    Admin --> Analytics["Analytics Query Builder"]

    SigDash --> System
    Rules --> System
    PCAP --> System
    AnomDash --> System
    CSV --> System
    XAI --> System
    Interfaces --> System
    Start --> System
    Stop --> System
    Clear --> System
    Users --> System
    Retrain --> System
    Analytics --> System
```

## Figure 3.3 - System Component Diagram

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        Browser["Browser"]
        React["React + Vite SPA"]
    end

    subgraph Backend["Backend Layer - Flask"]
        APIAuth["api_auth.py\nAuthentication API"]
        APIRoutes["api_routes.py\nApplication API"]
        Auth["auth.py\nRBAC + Password Hashing"]
        State["app_state.py\nShared Runtime State"]
    end

    subgraph Detection["Detection Engine"]
        Packet["packet.py\nPacket Parser"]
        Rule["rule.py\nRule Matching"]
        Signature["signature_IDS.py\nSignature IDS"]
        Flow["flow.py\nFlow Features"]
        Anomaly["anomaly_IDS.py\nAnomaly IDS"]
        Live["live_capture.py\nLive Capture"]
    end

    subgraph Intelligence["Analysis and Learning"]
        Explain["explainability.py\nSHAP/LIME"]
        Learn["continual_learning.py\nRetrain Pipeline"]
        Analytics["analytics.py\nQuery Builder"]
        TLS["tls_decrypt.py\nTLS Metadata"]
    end

    subgraph Storage["Persistence"]
        SQLite[("SQLite DB\nrules/logs/alerts/users/features")]
        Models[("Model Artifacts\nClassifier, IsolationForest, Scaler, Encoder")]
        Uploads[("Uploads\nCSV/PCAP")]
    end

    Browser --> React
    React --> APIAuth
    React --> APIRoutes
    APIAuth --> Auth
    APIRoutes --> Auth
    APIRoutes --> State
    APIRoutes --> Uploads
    APIRoutes --> Signature
    APIRoutes --> Anomaly
    APIRoutes --> Live
    APIRoutes --> Explain
    APIRoutes --> Learn
    APIRoutes --> Analytics
    Live --> Packet
    Live --> Signature
    Live --> Flow
    Flow --> Anomaly
    Signature --> Rule
    Anomaly --> Models
    APIAuth --> SQLite
    APIRoutes --> SQLite
    Signature --> SQLite
    Anomaly --> SQLite
    Explain --> SQLite
    Learn --> SQLite
```

## Figure 3.4 - Class Diagram

```mermaid
classDiagram
    class Database {
        +db_name
        +connect()
        +close()
        +create_table_rules()
        +create_table_logs()
        +create_table_alerts()
        +create_table_users()
        +create_table_alert_features()
        +create_table_training_data()
        +create_table_retrain_jobs()
        +clear_table(table_name)
    }

    class User {
        +id
        +username
        +password_hash
        +role
        +check_password(password)
        +has_access(route_name)
        +get_by_id(conn, user_id)
        +get_by_username(conn, username)
        +create(conn, username, password, role)
    }

    class Packet {
        +protocol
        +src_ip
        +dst_ip
        +src_port
        +dst_port
        +flags
        +payload
        +packet_size
        +get_src_ip()
        +get_dst_ip()
        +reset_counts()
    }

    class Rule {
        +action
        +protocol
        +src_ip
        +src_port
        +direction
        +dst_ip
        +dst_port
        +options
        +match_rule(packet)
        +get_rules_from_db(conn)
    }

    class SignatureIDS {
        +rules
        +predict_from_pcap(packets)
    }

    class Flow {
        +packets
        +flows
        +compute_features(flow_packets)
    }

    class AnomalyIDS {
        +model
        +iso_model
        +scaler
        +label_encoder
        +feature_order
        +predict_from_csv(path)
        +process_flow(flow_packets)
    }

    class LiveCapture {
        +rules
        +interface
        +packets_captured
        +alerts_generated
        +start()
        +stop()
        +get_status()
        -_capture_loop()
        -_process_packet(raw_pkt)
        -_process_flow_buffer()
    }

    class Alert {
        +time
        +src_ip
        +dst_ip
        +message
        +attack
        +method
        +add_to_alert_table(conn)
        +get_alerts_from_db(conn)
    }

    class Log {
        +time
        +action
        +src_ip
        +dst_ip
        +message
        +attack
        +method
        +add_to_log_table(conn)
        +get_logs_from_db(conn)
    }

    SignatureIDS --> Rule
    SignatureIDS --> Packet
    LiveCapture --> Packet
    LiveCapture --> SignatureIDS
    LiveCapture --> Flow
    Flow --> AnomalyIDS
    AnomalyIDS --> Alert
    SignatureIDS --> Alert
    Alert --> Database
    Log --> Database
    User --> Database
```

## Figure 3.5 - Login Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant React as React Login Page
    participant API as Flask /api/auth/login
    participant DB as SQLite users table
    participant Session as Flask-Login Session

    User->>React: Enter username and password
    React->>API: POST credentials
    API->>DB: Select user by username
    DB-->>API: User row with password hash
    API->>API: Verify password hash
    alt Valid credentials
        API->>Session: login_user(user)
        API-->>React: success + user role + default route
        React-->>User: Redirect to authorized dashboard
    else Invalid credentials
        API-->>React: error response
        React-->>User: Show login error
    end
```

## Figure 3.6 - Live Capture Sequence Diagram

```mermaid
sequenceDiagram
    actor Operator
    participant React as Live Capture Page
    participant API as Flask /api/live/start
    participant LC as LiveCapture
    participant Scapy as Scapy sniff()
    participant DB as SQLite
    participant ML as Anomaly Pipeline

    Operator->>React: Select interface and click Start
    React->>API: POST /api/live/start
    API->>LC: Create LiveCapture instance
    API->>LC: start()
    LC->>Scapy: Begin sniff loop
    alt Capture available
        Scapy-->>LC: Raw packets
        LC->>LC: Packet parsing and signature matching
        LC->>ML: Batch flow features every window
        ML-->>LC: Prediction and anomaly result
        LC->>DB: Insert logs, alerts, features
        API-->>React: Capture started
        React-->>Operator: Running status
    else Capture driver unavailable
        Scapy-->>LC: Capture error
        LC-->>API: start failed with last_error
        API-->>React: Failure message
        React-->>Operator: Show capture error
    end
```

## Figure 3.7 - CSV Prediction Sequence Diagram

```mermaid
sequenceDiagram
    actor Analyst
    participant React as CSV Upload Page
    participant API as Flask /api/uploads/csv
    participant Anomaly as AnomalyIDS
    participant Models as Model Artifacts
    participant DB as SQLite

    Analyst->>React: Choose CSV file
    React->>API: POST multipart CSV
    API->>API: Validate extension and save file
    API->>Anomaly: predict_from_csv(path)
    Anomaly->>Models: Load/use scaler, IsolationForest, classifier, label encoder
    Anomaly->>Anomaly: Align features and scale data
    Anomaly->>Anomaly: Score unknown attacks and classify known labels
    Anomaly->>DB: Store anomaly alerts and alert features if needed
    API-->>React: Return predictions and statistics
    React-->>Analyst: Display result table
```

## Figure 3.8 - PCAP Scan Sequence Diagram

```mermaid
sequenceDiagram
    actor Analyst
    participant React as PCAP Upload Page
    participant API as Flask /api/uploads/pcap
    participant Scapy as rdpcap()
    participant Signature as SignatureIDS
    participant Rule as Rule objects
    participant TLS as tshark/TLS helper

    Analyst->>React: Choose PCAP/PCAPNG file
    React->>API: POST multipart PCAP
    API->>API: Validate extension and save file
    API->>Scapy: Read packets
    API->>Signature: predict_from_pcap(packets)
    Signature->>Rule: Match packets against rules
    Rule-->>Signature: Matching alerts
    opt TLS metadata/decryption requested
        API->>TLS: Extract metadata or decrypt where keys exist
        TLS-->>API: TLS results
    end
    API-->>React: Return alerts and optional TLS details
    React-->>Analyst: Display scan results
```

## Figure 3.9 - Retraining Sequence Diagram

```mermaid
sequenceDiagram
    actor Admin
    participant React as Retrain Page
    participant API as Flask /api/retrain/*
    participant DB as SQLite training_data
    participant Retrain as continual_learning.py
    participant Models as Current/Candidate Models

    Admin->>React: Review samples and assign labels
    React->>API: POST label updates
    API->>DB: Update human_label
    Admin->>React: Click Start Retraining
    React->>API: POST /api/retrain/start
    API->>Retrain: Start background retraining thread
    Retrain->>DB: Load labeled samples and baseline data
    Retrain->>Models: Load old classifier and IsolationForest
    Retrain->>Retrain: Train candidate models
    Retrain->>Retrain: Evaluate F1, accuracy, false positive rate
    alt Candidate passes gates
        Retrain->>Models: Promote candidate and save rollback copy
        Retrain->>DB: Mark job completed/promoted
    else Candidate fails gates
        Retrain->>DB: Mark job completed/not promoted
    end
    React->>API: Poll retraining status
    API-->>React: Progress and metrics
```

## Figure 3.10 - Live Capture Activity Diagram

```mermaid
flowchart TD
    A([Start]) --> B[Select network interface]
    B --> C[Create LiveCapture instance]
    C --> D{Packet capture available?}
    D -- No --> E[Store last_error and show capture error]
    E --> Z([Stop])
    D -- Yes --> F[Start capture thread]
    F --> G[Receive raw packet]
    G --> H[Normalize packet]
    H --> I[Run signature rule matching]
    I --> J{Rule matched?}
    J -- Yes --> K[Insert signature alert and log]
    J -- No --> L[Append packet to flow buffer]
    K --> L
    L --> M{Flow window elapsed?}
    M -- No --> G
    M -- Yes --> N[Compute flow features]
    N --> O[Scale features]
    O --> P[IsolationForest score]
    P --> Q[Stacking classifier prediction]
    Q --> R{Attack or unknown?}
    R -- Yes --> S[Insert anomaly alert and store features]
    R -- No --> T[Queue features for retraining]
    S --> T
    T --> U{Stop requested?}
    U -- No --> G
    U -- Yes --> V[Flush feature queue]
    V --> Z([Stop])
```

## Figure 3.11 - ER Diagram

```mermaid
erDiagram
    USERS {
        int id PK
        string username
        string password_hash
        string role
        datetime created_at
    }

    RULES {
        int id PK
        string action
        string protocol
        string src_ip
        string src_port
        string direction
        string dst_ip
        string dst_port
        text options
    }

    LOGS {
        int id PK
        datetime timestamp
        string event_type
        string src_ip
        string dst_ip
        text message
        string attack
        string method
    }

    ALERTS {
        int id PK
        datetime timestamp
        string src_ip
        string dst_ip
        text message
        string attack
        string method
    }

    ALERT_FEATURES {
        int id PK
        int alert_id FK
        text features_json
        string predicted_label
        float confidence
        datetime created_at
    }

    TRAINING_DATA {
        int id PK
        text features_json
        string predicted_label
        float confidence
        string human_label
        string feature_version
        string source
        datetime created_at
    }

    RETRAIN_JOBS {
        int id PK
        string status
        string started_by
        datetime started_at
        datetime finished_at
        float old_accuracy
        float new_accuracy
        float old_f1
        float new_f1
        int promoted
        int samples_used
        text error_message
    }

    ALERTS ||--o{ ALERT_FEATURES : "has explanation features"
```

## Figure 4.1 - High-Level Architecture

```mermaid
flowchart LR
    Traffic["Live Network Traffic"] --> Capture["Scapy Live Capture"]
    PCAP["Uploaded PCAP"] --> PCAPScan["PCAP Signature Scan"]
    CSV["Uploaded CSV Features"] --> CSVPred["CSV Anomaly Prediction"]

    Capture --> Packet["Packet Normalization"]
    PCAPScan --> Packet
    Packet --> Signature["Signature-Based IDS"]
    Packet --> Flow["Flow Feature Extraction"]
    Flow --> Isolation["Isolation Forest"]
    Flow --> Classifier["Stacking Classifier"]
    CSVPred --> Isolation
    CSVPred --> Classifier

    Signature --> Alerts["Alerts and Logs"]
    Isolation --> Alerts
    Classifier --> Alerts

    Alerts --> DB[("SQLite Database")]
    Alerts --> XAI["SHAP/LIME Explanation"]
    Flow --> Training["Training Data Store"]
    Training --> Retrain["Continual Learning"]
    Retrain --> Models[("Updated Model Artifacts")]

    React["React Dashboard"] <--> Flask["Flask API"]
    Flask <--> DB
    Flask <--> Signature
    Flask <--> CSVPred
    Flask <--> Capture
    Flask <--> XAI
    Flask <--> Retrain
```

## Figure 4.2 - Detection Pipeline

```mermaid
flowchart TD
    A[Input Traffic or File] --> B{Input Type}
    B -->|Live Packet| C[Scapy sniff packet]
    B -->|PCAP| D[Read packets with rdpcap]
    B -->|CSV| E[Read flow feature rows]

    C --> F[Packet object]
    D --> F
    F --> G[Signature rule matching]
    G --> H{Rule matched?}
    H -->|Yes| I[Create signature alert]
    H -->|No| J[Continue packet processing]

    F --> K[Group packets into flows]
    K --> L[Compute 20 flow features]
    E --> M[Normalize and align feature columns]
    L --> M
    M --> N[MinMax scaling]
    N --> O[IsolationForest decision score]
    N --> P[Stacking classifier prediction]
    O --> Q{Unknown or anomalous?}
    P --> R{Known attack class?}
    Q -->|Yes| S[Create Unknown Attack alert]
    R -->|Attack| T[Create classified anomaly alert]
    R -->|BENIGN| U[No alert]
    I --> V[Store log/alert in SQLite]
    S --> V
    T --> V
    V --> W[Dashboard + explanation + analytics]
```

## Figure 4.3 - Deployment Diagram

```mermaid
flowchart TB
    subgraph UserDevice["User Workstation"]
        Browser["Web Browser"]
    end

    subgraph AppHost["HOLMES IDS Host Machine"]
        Vite["Vite Dev Server\n127.0.0.1:5174"]
        Flask["Flask Backend\n127.0.0.1:8000"]
        SQLite[("DB/IDS.db")]
        Uploads[("uploads/")]
        Models[("Models/")]
        Npcap["Npcap/libpcap Driver"]
        Wireshark["tshark/Wireshark\noptional TLS analysis"]
    end

    subgraph Network["Monitored Network"]
        Interface["Selected Network Interface"]
        Packets["Network Packets"]
    end

    Browser --> Vite
    Vite --> Flask
    Flask --> SQLite
    Flask --> Uploads
    Flask --> Models
    Flask --> Npcap
    Flask --> Wireshark
    Packets --> Interface
    Interface --> Npcap
```

