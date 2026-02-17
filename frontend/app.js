const API = "/api";
const API_KEY_PARAM = new URLSearchParams(window.location.search).get("apiKey");
if (API_KEY_PARAM) {
  localStorage.setItem("solar_api_key", API_KEY_PARAM);
}

function getApiKey() {
  return localStorage.getItem("solar_api_key") || "dev-admin-key";
}

const map = L.map("map").setView([-23.5505, -46.6333], 11);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

let markersLayer = L.layerGroup().addTo(map);
let clusterLayer = L.layerGroup().addTo(map);

const timelineEl = document.getElementById("timeline");
const alertsEl = document.getElementById("alerts");
const chatOutputEl = document.getElementById("chat-output");
const modelOutputEl = document.getElementById("model-output");

function fmtDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

function itemHtml(title, subtitle, meta = "") {
  return `<div class="item"><strong>${title}</strong><br/><small>${subtitle}</small>${meta ? `<div>${meta}</div>` : ""}</div>`;
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", "X-API-Key": getApiKey() },
    ...options,
  });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `Request failed: ${res.status}`);
  }
  return res.json();
}

async function loadTimeline() {
  const data = await fetchJson(`${API}/timeline?limit=120`);
  const events = data.events || [];
  timelineEl.innerHTML = events
    .slice(0, 50)
    .map((event) =>
      itemHtml(
        `${event.source_type} | sev ${event.severity}`,
        fmtDate(event.occurred_at),
        event.plate_text ? `Plate: ${event.plate_text}` : ""
      )
    )
    .join("");
}

async function loadAlerts() {
  const data = await fetchJson(`${API}/alerts?limit=80`);
  const alerts = data.alerts || [];
  alertsEl.innerHTML = alerts
    .slice(0, 30)
    .map((alert) => {
      const priorityClass = `priority-${alert.priority || "low"}`;
      return `<div class="item ${priorityClass}">
        <strong>${alert.alert_type}</strong><br/>
        <small>${fmtDate(alert.created_at)} | status: ${alert.status}</small>
        <div>${alert.message}</div>
      </div>`;
    })
    .join("");
}

async function loadMap() {
  const data = await fetchJson(`${API}/map/tactical?hours=24`);
  const features = data.geojson?.features || [];
  const clusters = data.clusters || [];

  markersLayer.clearLayers();
  clusterLayer.clearLayers();

  for (const feature of features) {
    const [lon, lat] = feature.geometry.coordinates;
    const props = feature.properties || {};
    const marker = L.circleMarker([lat, lon], {
      radius: 6 + Number(props.severity || 1),
      color: props.severity >= 4 ? "#ff5c5c" : "#33c3ff",
      fillOpacity: 0.7,
    });
    marker.bindPopup(
      `<b>${props.source_type}</b><br/>sev: ${props.severity}<br/>${fmtDate(props.occurred_at)}`
    );
    marker.addTo(markersLayer);
  }

  for (const cluster of clusters) {
    const center = cluster.center || {};
    if (center.latitude == null || center.longitude == null) continue;
    const marker = L.circle([center.latitude, center.longitude], {
      radius: Math.min(1200, 120 * Number(cluster.count || 1)),
      color: "#f39c12",
      fillOpacity: 0.2,
    });
    marker.bindPopup(
      `Cluster | count: ${cluster.count} | avg sev: ${cluster.avg_severity} | score: ${cluster.score}`
    );
    marker.addTo(clusterLayer);
  }
}

async function loadModelInsights() {
  const data = await fetchJson(`${API}/analytics/models/compare?hours=24`);
  const ensemble = data.ensemble || {};
  const ml = data.ml || {};
  const deep = data.deep_learning || {};
  const rule = data.rule_based || {};

  modelOutputEl.innerHTML = [
    itemHtml(
      `Ensemble Risk: ${ensemble.label || "-"} (${ensemble.score ?? "-"})`,
      "Combined rule-based + ML + deep learning"
    ),
    itemHtml(
      `Rule-based: ${rule.label || "-"} (${rule.score ?? "-"})`,
      "Deterministic analytical model"
    ),
    itemHtml(
      `ML Logistic: ${ml.label || "-"} (${ml.score ?? "-"})`,
      `Model=${ml.model || "-"} | train=${ml.training_samples ?? 0} test=${ml.test_samples ?? 0}`
    ),
    itemHtml(
      `Deep MLP: ${deep.label || "-"} (${deep.score ?? "-"})`,
      `Model=${deep.model || "-"} | train=${deep.training_samples ?? 0} test=${deep.test_samples ?? 0}`
    ),
  ].join("");
}

async function trainModelsNow() {
  await fetchJson(`${API}/analytics/models/train`, {
    method: "POST",
    body: JSON.stringify({
      hours: 168,
      ml_epochs: 180,
      ml_learning_rate: 0.08,
      deep_epochs: 260,
      deep_learning_rate: 0.03,
      deep_hidden_dim: 10,
      deploy_after_train: true,
      created_by: "frontend-operator",
    }),
  });
}

async function ingestDemoEvent() {
  const sources = ["camera", "gps_tracking", "plate_ocr", "police_records", "public_data"];
  const source = sources[Math.floor(Math.random() * sources.length)];

  const payload = {
    latitude: -23.55 + (Math.random() - 0.5) * 0.2,
    longitude: -46.63 + (Math.random() - 0.5) * 0.2,
    severity: Math.floor(Math.random() * 5) + 1,
    plate_text: Math.random() > 0.45 ? `SOL${Math.floor(1000 + Math.random() * 9000)}` : null,
    device_id: `cam-${Math.floor(10 + Math.random() * 90)}`,
    metadata: { zone: "demo", operator: "console-ui" },
    payload: { note: "synthetic event for testing" },
  };

  await fetchJson(`${API}/ingest/${source}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function evaluateAlerts() {
  await fetchJson(`${API}/alerts/evaluate`, {
    method: "POST",
    body: JSON.stringify({
      lookback_hours: 24,
      risk_threshold: 0.6,
      anomaly_threshold: 0.8,
      pattern_threshold: 0.75,
    }),
  });
}

async function sendChat(question) {
  const data = await fetchJson(`${API}/chat`, {
    method: "POST",
    body: JSON.stringify({ question }),
  });
  const insights = (data.insights || []).map((x) => `<li>${x}</li>`).join("");
  const block = `<div class="item">
    <strong>Question:</strong> ${question}<br/>
    <strong>Answer:</strong> ${data.answer}<br/>
    <small>source=${data.source} confidence=${data.confidence}</small>
    <ul>${insights}</ul>
  </div>`;
  chatOutputEl.innerHTML = block + chatOutputEl.innerHTML;
}

async function refreshAll() {
  try {
    await Promise.all([loadTimeline(), loadAlerts(), loadMap(), loadModelInsights()]);
  } catch (err) {
    console.error(err);
  }
}

document.getElementById("refresh-btn").addEventListener("click", async () => {
  await refreshAll();
});

document.getElementById("ingest-btn").addEventListener("click", async () => {
  try {
    await ingestDemoEvent();
    await refreshAll();
  } catch (err) {
    console.error(err);
  }
});

document.getElementById("evaluate-btn").addEventListener("click", async () => {
  try {
    await evaluateAlerts();
    await refreshAll();
  } catch (err) {
    console.error(err);
  }
});

document.getElementById("train-models-btn").addEventListener("click", async () => {
  try {
    await trainModelsNow();
    await refreshAll();
  } catch (err) {
    console.error(err);
  }
});

document.getElementById("chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.getElementById("chat-input");
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  try {
    await sendChat(question);
  } catch (err) {
    console.error(err);
  }
});

refreshAll();
