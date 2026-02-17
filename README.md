# S.O.L.A.R - Strategic Operations, Learning, Analytics and Response

S.O.L.A.R is an intelligence and operational decision platform inspired by data-fabric and cognitive operations architectures. It unifies ingestion, semantic intelligence, analytics, and AI-assisted decision support into one system.

## What Problem It Solves

### Governments

- Integrates fragmented public safety and mobility data into one operational view.
- Reduces response latency with predictive alerts, anomaly detection, and tactical geospatial visibility.
- Improves oversight with audit trails, role-based access, retention controls, and compliance workflows.

### Companies

- Centralizes risk signals from physical assets, logistics, sites, and sensors.
- Supports proactive security operations through real-time monitoring and risk scoring.
- Enables decision consistency with explainable model outputs and standardized workflows.

### Organizations (NGOs, institutions, critical infrastructure)

- Provides an affordable situational awareness stack for distributed operations.
- Detects abnormal patterns early in field operations, mobility, and incident intake.
- Improves governance with human-in-the-loop approvals and transparent action logs.

## Functional Layers

- Ingestion: camera, public data, police records, GPS tracking, plate OCR
- Data Fabric / Mesh: PostgreSQL + PostGIS + shared data contracts
- Semantic Layer: entities, relationships, context graph
- AI and Agents: pattern detection, risk forecasting, clustering, anomaly detection, analytical chat
- Cognitive Interface: tactical map, timeline, predictive alerts, AI assistant

## Machine Learning and Deep Learning

S.O.L.A.R includes three complementary risk engines:

- Rule-based analytics: deterministic factors (density, severity, recency, proximity)
- Machine Learning: logistic regression classifier trained on operational event features
- Deep Learning: lightweight multi-layer perceptron (MLP) for nonlinear risk scoring

Model APIs:

- `GET /api/analytics/risk` (rule-based)
- `GET /api/analytics/ml/risk` (machine learning)
- `GET /api/analytics/deep/risk` (deep learning)
- `GET /api/analytics/models/compare` (ensemble comparison)
- `POST /api/analytics/models/train` (train and optionally deploy models)
- `GET /api/analytics/models/registry` (versioned model registry)
- `PATCH /api/analytics/models/{model_id}/deploy` (promote model to production)
- `GET /api/analytics/models/deployed` (active deployed models)

## Services

- `gateway` (8080): unified API + frontend
- `ingestion` (8001): ingestion + compliance controls + stream publish
- `analytics` (8002): analytical endpoints + ML/DL + real-time signal query
- `semantic` (8003): entity graph and context
- `alerting` (8004): predictive alerts with approval flow
- `stream-processor` (8005, optional): Redis stream consumer for real-time risk/anomaly signals

## Security and Compliance (Implemented)

- RBAC in gateway with API keys (`X-API-Key`)
  - Roles: `admin`, `analyst`, `operator`, `viewer`, `ingestion`, `compliance`
- Persistent audit trail (`audit_logs`)
- Ingestion privacy controls:
  - sensitive key sanitization
  - optional plate hashing (`HASH_PLATE_TEXT=true`)
  - retention workflow (`/api/compliance/retention`)
  - vehicle erase workflow (`/api/compliance/erase-vehicle/{plate_text}`)
- Human-in-the-loop safety:
  - high-priority alerts start as `pending_approval`
  - explicit `/approve` required before closure

## Quick Start (Light Docker Mode)

Recommended for lower-spec machines.

1. Copy environment file:

```bash
cp .env.example .env
```

2. Start core stack (without optional stream processor):

```bash
docker compose up --build -d postgres redis ingestion analytics semantic alerting gateway
```

3. Open frontend:

- `http://localhost:8080/?apiKey=dev-admin-key`

4. Seed demo data:

```bash
python scripts/seed_demo_data.py
```

5. Train and deploy ML/DL models:

```bash
python scripts/train_models.py
```

## Optional Real-Time Streaming Mode

Enable Redis Stream processing when needed:

```bash
docker compose --profile streaming up --build -d
```

## Frontend Preview Only (No Backend)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_frontend_preview.ps1 -Port 5500
```

Open:

- `http://localhost:5500`

## Key API Endpoints

Gateway prefix: `/api`

- Ingestion:
  - `POST /api/ingest/{source_type}`
  - `POST /api/ingest/camera`
  - `POST /api/ingest/public-data`
  - `POST /api/ingest/police-records`
  - `POST /api/ingest/gps`
  - `POST /api/ingest/ocr-plate`
- Analytics:
  - `GET /api/analytics/patterns`
  - `GET /api/analytics/risk`
  - `GET /api/analytics/ml/risk`
  - `GET /api/analytics/deep/risk`
  - `GET /api/analytics/models/compare`
  - `POST /api/analytics/models/train`
  - `GET /api/analytics/models/registry`
  - `PATCH /api/analytics/models/{id}/deploy`
  - `GET /api/analytics/models/deployed`
  - `GET /api/analytics/clusters`
  - `GET /api/analytics/anomalies`
- Streams:
  - `GET /api/stream/signals`
  - `GET /api/stream/health`
- Alerts:
  - `POST /api/alerts/evaluate`
  - `GET /api/alerts`
  - `PATCH /api/alerts/{id}/approve`
  - `PATCH /api/alerts/{id}/close`
- Compliance:
  - `POST /api/compliance/erase-vehicle/{plate_text}`
  - `POST /api/compliance/retention`
- Security and audit:
  - `GET /api/security/whoami`
  - `GET /api/audit/logs`

## Development Validation

```bash
python -m compileall shared services scripts tests
python -m pytest -q tests/test_analytics_engine.py
```

## AWS and Terraform

- AWS is the cloud provider.
- Terraform is the Infrastructure-as-Code tool.
- Terraform provisions and manages AWS resources for this platform (VPC, RDS, ECS/EKS, ECR, CloudWatch, SNS).

Terraform files:

- `infra/terraform/main.tf`
- `infra/terraform/variables.tf`
- `infra/terraform/outputs.tf`
- `infra/terraform/README.md`
