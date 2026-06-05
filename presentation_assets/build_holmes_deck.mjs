import fs from "node:fs/promises";
import { readFileSync } from "node:fs";
import path from "node:path";

import {
  Presentation,
  PresentationFile,
  row,
  column,
  grid,
  layers,
  panel,
  text,
  image,
  shape,
  rule,
  fill,
  hug,
  fixed,
  wrap,
  grow,
  fr,
  auto,
} from "file:///C:/Users/moham/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const ROOT = "C:/Users/moham/Desktop/IDS-Grad-Helwan/IDS_GradProjecet";
const OUT = `${ROOT}/presentation_assets/output`;
const PREVIEWS = `${OUT}/previews`;
const SHOTS = `${ROOT}/presentation_assets/screenshots`;
const IMG = `${ROOT}/frontend/public/static/IMG`;
const UML = `${ROOT}/out/UML`;

await fs.mkdir(OUT, { recursive: true });
await fs.mkdir(PREVIEWS, { recursive: true });

const W = 1920;
const H = 1080;
const C = {
  bg: "#07111F",
  bg2: "#0B1728",
  ink: "#F8FAFC",
  muted: "#A8B5C7",
  dim: "#64748B",
  cyan: "#22D3EE",
  blue: "#2563EB",
  green: "#22C55E",
  amber: "#F59E0B",
  red: "#F43F5E",
  line: "#26384E",
  panel: "#101B2B",
  soft: "#162439",
};

const deck = Presentation.create({ slideSize: { width: W, height: H } });

function mimeFor(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
  if (ext === ".webp") return "image/webp";
  return "image/png";
}

function dataUrlFor(filePath) {
  const mime = mimeFor(filePath);
  const data = readFileSync(filePath).toString("base64");
  return `data:${mime};base64,${data}`;
}

function T(value, size = 34, opts = {}) {
  return text(value, {
    name: opts.name,
    width: opts.width ?? fill,
    height: hug,
    style: {
      fontSize: size,
      fontFace: opts.fontFace ?? "Aptos",
      bold: opts.bold ?? false,
      color: opts.color ?? C.ink,
      ...opts.style,
    },
    columnSpan: opts.columnSpan,
    rowSpan: opts.rowSpan,
  });
}

function eyebrow(value, accent = C.cyan) {
  return row({ width: fill, height: hug, gap: 14, align: "center" }, [
    rule({ width: fixed(76), stroke: accent, weight: 5 }),
    T(value.toUpperCase(), 18, { color: accent, bold: true, width: hug }),
  ]);
}

function slideShell(title, kicker, children, opts = {}) {
  const slide = deck.slides.add();
  slide.compose(
    panel(
      { width: fill, height: fill, fill: opts.bg ?? C.bg, padding: { x: 76, y: 56 } },
      column({ width: fill, height: fill, gap: 28 }, [
        column({ width: fill, height: hug, gap: 12 }, [
          eyebrow(kicker ?? "HOLMES IDS", opts.accent ?? C.cyan),
          T(title, opts.titleSize ?? 58, { bold: true, width: wrap(1500) }),
        ]),
        ...children,
      ]),
    ),
    { frame: { left: 0, top: 0, width: W, height: H }, baseUnit: 8 },
  );
}

function img(pathValue, alt, opts = {}) {
  return image({
    dataUrl: dataUrlFor(pathValue),
    contentType: mimeFor(pathValue),
    alt,
    width: opts.width ?? fill,
    height: opts.height ?? fill,
    fit: opts.fit ?? "cover",
    borderRadius: opts.borderRadius ?? 20,
    columnSpan: opts.columnSpan,
    rowSpan: opts.rowSpan,
  });
}

function shot(name, alt, opts = {}) {
  return img(`${SHOTS}/${name}.png`, alt, { fit: "contain", borderRadius: 18, ...opts });
}

function screenshotStage(name, alt, opts = {}) {
  return panel(
    {
      width: opts.width ?? fill,
      height: opts.height ?? fill,
      fill: "#07111F",
      line: { color: C.line, width: 2 },
      borderRadius: 20,
      padding: opts.padding ?? 10,
      columnSpan: opts.columnSpan,
      rowSpan: opts.rowSpan,
    },
    shot(name, alt),
  );
}

function chip(label, color = C.cyan) {
  return panel(
    { width: hug, height: hug, fill: `${color}22`, line: { color, width: 1.5 }, borderRadius: 18, padding: { x: 18, y: 9 } },
    T(label, 19, { color, bold: true, width: hug }),
  );
}

function point(title, body, color = C.cyan) {
  return row({ width: fill, height: hug, gap: 18, align: "start" }, [
    shape({ width: fixed(12), height: fixed(64), fill: color, borderRadius: 8 }),
    column({ width: fill, height: hug, gap: 5 }, [
      T(title, 27, { bold: true }),
      T(body, 20, { color: C.muted, width: wrap(660) }),
    ]),
  ]);
}

function node(label, sub, color = C.cyan) {
  return panel(
    { width: fill, height: fixed(138), fill: C.soft, line: { color, width: 2 }, borderRadius: 18, padding: { x: 22, y: 18 } },
    column({ width: fill, height: fill, gap: 8, justify: "center" }, [
      T(label, 27, { bold: true }),
      T(sub, 17, { color: C.muted }),
    ]),
  );
}

function processSlide(title, kicker, steps, opts = {}) {
  slideShell(title, kicker, [
    row({ width: fill, height: fill, gap: 22, align: "center" },
      steps.flatMap((s, i) => [
        panel(
          { width: grow(1), height: fixed(260), fill: C.panel, line: { color: s.color, width: 2 }, borderRadius: 22, padding: { x: 24, y: 24 } },
          column({ width: fill, height: fill, gap: 14, justify: "center" }, [
            T(String(i + 1).padStart(2, "0"), 24, { color: s.color, bold: true }),
            T(s.title, 32, { bold: true }),
            T(s.body, 20, { color: C.muted }),
          ]),
        ),
        ...(i < steps.length - 1 ? [T("->", 42, { color: C.dim, bold: true, width: hug })] : []),
      ]),
    ),
  ], opts);
}

function cover() {
  const slide = deck.slides.add();
  slide.compose(
    layers({ width: fill, height: fill }, [
      img(`${IMG}/intrusion-detection.png`, "Intrusion detection illustration", { borderRadius: 0, fit: "cover" }),
      shape({ width: fill, height: fill, fill: "#020617CC" }),
      column({ width: fill, height: fill, padding: { x: 92, y: 76 }, justify: "between" }, [
        row({ width: fill, height: hug, align: "center", gap: 20 }, [
          img(`${IMG}/white.png`, "HOLMES logo", { width: fixed(118), height: fixed(74), fit: "contain", borderRadius: 0 }),
          T("HOLMES IDS", 34, { bold: true, width: hug }),
        ]),
        column({ width: wrap(1250), height: hug, gap: 24 }, [
          eyebrow("Hybrid Online Learning Model for Enhanced Security", C.green),
          T("A hybrid intrusion detection platform for known and unknown threats", 72, { bold: true, width: wrap(1250) }),
          T("Signature detection, flow-based anomaly ML, live capture, explainability, analytics, and continual learning in one web application.", 29, { color: C.muted, width: wrap(980) }),
        ]),
        row({ width: fill, height: hug, justify: "between", align: "center" }, [
          T("Graduation Project - Capital University", 22, { color: C.muted, width: hug }),
          T("20-slide project overview", 22, { color: C.muted, width: hug }),
        ]),
      ]),
    ]),
    { frame: { left: 0, top: 0, width: W, height: H }, baseUnit: 8 },
  );
}

cover();

slideShell("Why HOLMES exists", "Problem", [
  grid({ width: fill, height: fill, columns: [fr(0.95), fr(1.05)], columnGap: 54, alignItems: "center" }, [
    column({ width: fill, height: hug, gap: 32 }, [
      T("Network defense has two uncomfortable truths:", 48, { bold: true, width: wrap(760) }),
      point("Known attacks need speed", "Signature rules are deterministic and fast when patterns are already understood.", C.green),
      point("Unknown attacks need behavior", "Novel traffic often has no rule yet, so flow statistics and ML become the detection signal.", C.cyan),
      point("Analysts need trust", "Alerts are only useful when the system shows why they happened and what evidence supports them.", C.amber),
    ]),
    img(`${IMG}/Anomaly_based.png`, "Anomaly detection visual", { height: fixed(740), fit: "contain" }),
  ]),
]);

processSlide("Hybrid detection is the core idea", "Solution", [
  { title: "Packet parsing", body: "Scapy traffic becomes normalized Packet objects.", color: C.blue },
  { title: "Signature rules", body: "Known patterns are matched with Snort-like logic.", color: C.green },
  { title: "Flow ML", body: "Packets are grouped into flows and scored by ML.", color: C.cyan },
  { title: "Alerts and learning", body: "Results feed dashboards, explanations, and retraining data.", color: C.amber },
]);

slideShell("Architecture in one view", "System", [
  grid({ width: fill, height: fill, columns: [fr(1.1), fr(0.9)], columnGap: 48 }, [
    grid({ width: fill, height: fill, columns: [fr(1), fr(1)], rows: [auto, auto, auto], columnGap: 22, rowGap: 22, alignItems: "center" }, [
      node("React SPA", "Vite frontend on :5174", C.cyan),
      node("Flask API", "UI.py + blueprints on :8000", C.green),
      node("Detection engine", "SignatureIDS + AnomalyIDS + LiveCapture", C.amber),
      node("SQLite WAL DB", "alerts, logs, rules, users, features", C.blue),
      node("Model artifacts", "Stacking classifier, IsolationForest, scaler", C.red),
      node("Analyst workflow", "dashboards, uploads, labeling, retraining", C.cyan),
    ]),
    screenshotStage("01_signature_dashboard", "Signature dashboard screenshot"),
  ]),
]);

slideShell("The web application is the operator console", "Frontend", [
  grid({ width: fill, height: fill, columns: [fr(1.05), fr(0.95)], columnGap: 46, alignItems: "center" }, [
    screenshotStage("00_login", "Login screen screenshot"),
    column({ width: fill, height: hug, gap: 24 }, [
      T("React routes map directly to security workflows.", 44, { bold: true, width: wrap(720) }),
      row({ width: fill, height: hug, gap: 12 }, [chip("Admin"), chip("Signature Analyst", C.green), chip("Anomaly Analyst", C.amber), chip("Live Operator", C.blue)]),
      point("Authentication and RBAC", "Protected routes expose only the pages each role needs.", C.cyan),
      point("Dark SOC-style interface", "Dashboards prioritize alert scanning, sorting, upload actions, and live status.", C.green),
      point("JSON API client", "The React frontend talks to Flask through the Vite API proxy.", C.amber),
    ]),
  ]),
]);

slideShell("Signature dashboard: known attacks at a glance", "Feature 1", [
  grid({ width: fill, height: fill, columns: [fr(1.3), fr(0.7)], columnGap: 42 }, [
    screenshotStage("01_signature_dashboard", "Signature dashboard screenshot"),
    column({ width: fill, height: hug, gap: 24, justify: "center" }, [
      T("This is the fast path for known threats.", 42, { bold: true }),
      point("Alert counts", "The page summarizes total signature alerts and top source/destination IPs.", C.green),
      point("Sortable evidence", "Analysts can sort rows by timestamp, IP, attack layer, method, and message.", C.cyan),
      point("Rule-driven messages", "Alert text comes from rule metadata, so findings are explainable by design.", C.amber),
    ]),
  ]),
]);

processSlide("How signature detection works", "Signature engine", [
  { title: "Load rules", body: "Rules are parsed and stored in the database.", color: C.green },
  { title: "Wrap packet", body: "Raw Scapy packets become Packet objects.", color: C.cyan },
  { title: "Match fields", body: "Protocol, IP, ports, direction, and options are checked.", color: C.amber },
  { title: "Write alert", body: "Matching packets create log and alert records.", color: C.red },
]);

slideShell("Rules and PCAP upload support offline investigation", "Feature 2", [
  grid({ width: fill, height: fill, columns: [fr(1), fr(1)], rows: [fr(1), auto], columnGap: 28, rowGap: 22 }, [
    screenshotStage("04_rules", "Rules page screenshot"),
    screenshotStage("06_pcap_upload", "PCAP upload screenshot"),
    row({ width: fill, height: hug, columnSpan: 2, gap: 18, justify: "center" }, [
      chip("Rule database", C.green),
      chip("PCAP scanning", C.cyan),
      chip("TLS metadata", C.amber),
      chip("SSLKEYLOGFILE decryption", C.red),
    ]),
  ]),
]);

slideShell("Anomaly dashboard: behavior-based findings", "Feature 3", [
  grid({ width: fill, height: fill, columns: [fr(1.25), fr(0.75)], columnGap: 42 }, [
    screenshotStage("02_anomaly_dashboard", "Anomaly dashboard screenshot"),
    column({ width: fill, height: hug, gap: 24, justify: "center" }, [
      T("ML raises alerts from flow behavior, not rule text.", 42, { bold: true }),
      point("Flow-level analysis", "Packets are grouped by source, destination, ports, and protocol.", C.cyan),
      point("Model labels", "The classifier outputs labels such as Bot, DoS, DDoS, Port_Scan, or Web_Attack.", C.green),
      point("Stored features", "Feature vectors are saved for explanations and continual learning.", C.amber),
    ]),
  ]),
]);

processSlide("The ML prediction pipeline", "Anomaly ML", [
  { title: "Group flow", body: "Packets become a 5-tuple network flow.", color: C.blue },
  { title: "Extract 20 features", body: "Duration, packet counts, bytes, rates, and flag behavior.", color: C.cyan },
  { title: "Scale values", body: "MinMaxScaler aligns live data with training scale.", color: C.green },
  { title: "Score and classify", body: "IsolationForest detects abnormality; stacking model labels the attack.", color: C.amber },
]);

slideShell("The model is an ensemble of different opinions", "Algorithms", [
  grid({ width: fill, height: fill, columns: [fr(1), fr(1)], columnGap: 42 }, [
    column({ width: fill, height: fill, gap: 18, justify: "center" }, [
      T("IsolationForest", 44, { bold: true, color: C.cyan }),
      T("Finds flows that look statistically unusual compared with the trained traffic distribution.", 24, { color: C.muted }),
      rule({ width: fill, stroke: C.line, weight: 2 }),
      T("StackingClassifier", 44, { bold: true, color: C.green }),
      T("Combines Decision Tree, Logistic Regression, KNN, and CatBoost predictions.", 24, { color: C.muted }),
      rule({ width: fill, stroke: C.line, weight: 2 }),
      T("RandomForest meta-classifier", 38, { bold: true, color: C.amber }),
      T("Learns how to combine the base model outputs into one final attack label.", 24, { color: C.muted }),
    ]),
    grid({ width: fill, height: fill, columns: [fr(1), fr(1)], rows: [auto, auto, auto], columnGap: 20, rowGap: 20, alignItems: "center" }, [
      node("Decision Tree", "Rule-like splits", C.green),
      node("Logistic Regression", "Linear baseline", C.blue),
      node("KNN", "Similarity to known flows", C.cyan),
      node("CatBoost", "Boosted tabular patterns", C.amber),
      panel({ width: fill, height: fixed(130), fill: "#251B0C", line: { color: C.amber, width: 2 }, borderRadius: 18, padding: { x: 18, y: 14 }, columnSpan: 2 },
        column({ width: fill, height: fill, justify: "center", gap: 6 }, [
          T("Random Forest", 31, { bold: true, color: C.amber }),
          T("Final / meta decision", 18, { color: C.muted }),
        ])),
    ]),
  ]),
]);

slideShell("Live capture connects the network to the model", "Feature 4", [
  grid({ width: fill, height: fill, columns: [fr(1.28), fr(0.72)], columnGap: 42 }, [
    screenshotStage("03_live_capture", "Live capture screenshot"),
    column({ width: fill, height: hug, gap: 24, justify: "center" }, [
      T("Three background threads keep capture responsive.", 40, { bold: true }),
      point("_capture_loop", "Runs Scapy sniff and per-packet signature matching.", C.green),
      point("_flow_processing_loop", "Every 10 seconds, drains buffered packets and runs anomaly ML.", C.cyan),
      point("_batch_writer_loop", "Writes flow features to training_data in batches of 50.", C.amber),
    ]),
  ]),
]);

slideShell("Explainability turns model output into analyst evidence", "Feature 5", [
  grid({ width: fill, height: fill, columns: [fr(0.85), fr(1.15)], columnGap: 48, alignItems: "center" }, [
    column({ width: fill, height: hug, gap: 28 }, [
      T("Every anomaly alert can keep its raw feature vector.", 46, { bold: true }),
      point("SHAP", "Shows which features pushed the prediction toward the final class.", C.green),
      point("LIME", "Builds a local approximation around one alert for model-agnostic explanation.", C.cyan),
      point("Feature glossary", "Turns flow metrics into language an analyst can interpret.", C.amber),
    ]),
    layers({ width: fill, height: fixed(620) }, [
      shape({ width: fill, height: fill, fill: C.panel, line: { color: C.line, width: 2 }, borderRadius: 24 }),
      grid({ width: fill, height: fill, columns: [fr(1), fr(1)], rows: [auto, auto, auto, auto], padding: { x: 44, y: 42 }, columnGap: 28, rowGap: 22 }, [
        T("Flow Duration", 24, { bold: true, color: C.ink }),
        T("+0.42", 24, { bold: true, color: C.green, width: hug }),
        T("Packet Length Mean", 24, { bold: true }),
        T("+0.31", 24, { bold: true, color: C.cyan, width: hug }),
        T("Flow Bytes/s", 24, { bold: true }),
        T("+0.27", 24, { bold: true, color: C.amber, width: hug }),
        T("The slide illustrates the explanation concept; actual values are generated per alert.", 18, { color: C.dim, columnSpan: 2 }),
      ]),
    ]),
  ]),
]);

slideShell("Continual learning closes the feedback loop", "Feature 6", [
  grid({ width: fill, height: fill, columns: [fr(1.25), fr(0.75)], columnGap: 42 }, [
    screenshotStage("08_retrain", "Retrain dashboard screenshot"),
    column({ width: fill, height: hug, gap: 24, justify: "center" }, [
      T("The project does not blindly retrain on raw predictions.", 40, { bold: true }),
      point("Human labels are required", "Retraining selects rows where human_label is set.", C.green),
      point("SMOTE balances classes", "Minority classes get synthetic samples during retraining.", C.cyan),
      point("Evaluation gate", "Candidate models need strong F1 and acceptable false-positive rate.", C.amber),
    ]),
  ]),
]);

processSlide("Retraining pipeline", "Continual learning", [
  { title: "Collect", body: "Live flow features are saved to training_data.", color: C.blue },
  { title: "Review", body: "Admin labels samples with human_label.", color: C.green },
  { title: "Retrain", body: "Stacking model and IsolationForest are cloned and fit again.", color: C.cyan },
  { title: "Promote", body: "Candidate is promoted only if metrics pass the gate.", color: C.amber },
]);

slideShell("TLS and upload workflows expand visibility", "Feature 7", [
  grid({ width: fill, height: fill, columns: [fr(1), fr(1)], columnGap: 42 }, [
    screenshotStage("06_pcap_upload", "PCAP upload screenshot"),
    column({ width: fill, height: hug, gap: 24, justify: "center" }, [
      T("Offline PCAP analysis supports both signature review and TLS insight.", 42, { bold: true }),
      point("PCAP input", "Upload capture files for rule-based detection outside live capture.", C.green),
      point("TLS decryption", "With SSLKEYLOGFILE, tshark can recover HTTP content from HTTPS sessions.", C.cyan),
      point("Metadata fallback", "Without keys, the project can still extract SNI and JA3-style fingerprints.", C.amber),
    ]),
  ]),
]);

slideShell("CSV upload supports batch anomaly prediction", "Feature 8", [
  grid({ width: fill, height: fill, columns: [fr(1.2), fr(0.8)], columnGap: 42 }, [
    screenshotStage("05_csv_upload", "CSV upload screenshot"),
    column({ width: fill, height: hug, gap: 24, justify: "center" }, [
      T("The same anomaly model can run on offline flow-feature datasets.", 42, { bold: true }),
      point("Column normalization", "CSV columns are mapped to the saved feature order.", C.cyan),
      point("Vectorized inference", "Rows are scaled and predicted in batch.", C.green),
      point("Stats output", "Results separate benign, attack, and unknown buckets.", C.amber),
    ]),
  ]),
]);

slideShell("Analytics query builder enables threat hunting", "Feature 9", [
  grid({ width: fill, height: fill, columns: [fr(1.25), fr(0.75)], columnGap: 42 }, [
    screenshotStage("07_analytics", "Analytics query builder screenshot"),
    column({ width: fill, height: hug, gap: 24, justify: "center" }, [
      T("Analysts can ask questions without writing raw SQL.", 40, { bold: true }),
      point("Safe table allowlist", "Queries are limited to approved IDS tables.", C.green),
      point("Conditions and ordering", "The UI builds filtered views across alerts, logs, rules, users, and training data.", C.cyan),
      point("Detection patterns", "Prebuilt patterns cover brute force, port scan, and DoS-style spikes.", C.amber),
    ]),
  ]),
]);

slideShell("Data model keeps detection, evidence, and learning connected", "Database", [
  grid({ width: fill, height: fill, columns: [fr(1), fr(1)], columnGap: 38 }, [
    column({ width: fill, height: hug, gap: 18, justify: "center" }, [
      T("SQLite is the project memory.", 46, { bold: true }),
      point("alerts + logs", "Operational evidence for dashboards and investigations.", C.green),
      point("rules", "Signature detection knowledge base.", C.cyan),
      point("alert_features", "Per-alert feature vectors for SHAP/LIME.", C.amber),
      point("training_data + retrain_jobs", "Human-in-the-loop learning state and retraining history.", C.red),
    ]),
    img(`${UML}/System_Component_Diagram/sys1/IDS_Component_Diagram.png`, "System component UML diagram", { fit: "contain", borderRadius: 18 }),
  ]),
]);

slideShell("Final takeaway", "Closing", [
  grid({ width: fill, height: fill, columns: [fr(1.1), fr(0.9)], columnGap: 48, alignItems: "center" }, [
    column({ width: fill, height: hug, gap: 28 }, [
      T("HOLMES IDS turns network traffic into evidence, then turns evidence into learning.", 62, { bold: true, width: wrap(900) }),
      T("The result is a complete graduation project platform: detection engine, web console, model explainability, and a feedback loop for improvement.", 27, { color: C.muted, width: wrap(840) }),
      row({ width: fill, height: hug, gap: 14 }, [
        chip("Signature"),
        chip("Anomaly ML", C.green),
        chip("Live Capture", C.amber),
        chip("Explainability", C.blue),
        chip("Retraining", C.red),
      ]),
    ]),
    img(`${IMG}/Signature_based2.png`, "Network security visual", { fit: "contain", borderRadius: 20 }),
  ]),
]);

const ppt = await PresentationFile.exportPptx(deck);
await ppt.save(`${OUT}/HOLMES_IDS_Project_Overview.pptx`);

for (let i = 0; i < deck.slides.count; i++) {
  const slide = deck.slides.getItem(i);
  const png = await slide.export({ format: "png" });
  const bytes = Buffer.from(await png.arrayBuffer());
  await fs.writeFile(path.join(PREVIEWS, `slide_${String(i + 1).padStart(2, "0")}.png`), bytes);
}

console.log(JSON.stringify({
  slides: deck.slides.count,
  pptx: `${OUT}/HOLMES_IDS_Project_Overview.pptx`,
  previews: PREVIEWS,
}, null, 2));
