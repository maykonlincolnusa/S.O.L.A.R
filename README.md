<div align="center">

# ☀️ S.O.L.A.R

### **Strategic Operations, Learning, Analytics and Response**

*Cognitive Infrastructure for Sovereign Intelligence*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docs.docker.com/compose/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![PostGIS](https://img.shields.io/badge/PostGIS-Enabled-2C8EBB.svg)](https://postgis.net/)
[![Terraform](https://img.shields.io/badge/Terraform-AWS-7B42BC.svg)](https://www.terraform.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[Overview](#-overview)** •
**[Architecture](#-architecture)** •
**[Quick Start](#-quick-start)** •
**[ML/DL Models](#-machine-learning--deep-learning)** •
**[API Reference](#-api-reference)** •
**[Deployment](#-cloud-deployment-aws)**

---

</div>

## 🌍 Overview

**S.O.L.A.R** (Strategic Operations, Learning, Analytics and Response) is a next-generation cognitive infrastructure platform designed to **illuminate complexity**, **enable sovereign intelligence**, and **empower governments and institutions** to make real-time, data-driven decisions that benefit society at large.

Built on a **data-fabric architecture** with **AI-powered analytics**, S.O.L.A.R unifies fragmented data sources into a single operational intelligence platform, providing tactical awareness, predictive insights, and automated decision support.

### 💡 The Vision

In an increasingly complex world, organizations face critical challenges:
- **Data Silos**: Information scattered across incompatible systems
- **Response Delays**: Minutes lost in critical situations cost lives
- **Limited Insight**: Inability to detect patterns and predict events
- **Compliance Burden**: Manual processes for governance and audit trails
- **Resource Constraints**: Expensive proprietary solutions out of reach

**S.O.L.A.R addresses these challenges by providing an open, scalable, and intelligent platform that transforms how institutions operate.**

---

## 🎯 Problem & Solution

### 🏛️ For Governments

**Challenges:**
- Fragmented public safety and mobility data
- Slow emergency response times
- Lack of predictive capabilities
- Compliance and audit requirements

**S.O.L.A.R Solutions:**
✅ **Unified Operational View** - Integrates police records, camera feeds, GPS tracking, and public data  
✅ **Reduced Response Latency** - Predictive alerts, anomaly detection, and geospatial visibility  
✅ **Enhanced Oversight** - Complete audit trails, role-based access control, retention policies  
✅ **Regulatory Compliance** - Built-in GDPR/LGPD workflows, data sanitization, human-in-the-loop approvals

---

### 🏢 For Private Companies

**Challenges:**
- Risk signals from distributed assets
- Reactive security operations
- Inconsistent decision-making
- Limited operational intelligence

**S.O.L.A.R Solutions:**
✅ **Centralized Risk Management** - Monitor physical assets, logistics, sites, and IoT sensors  
✅ **Proactive Security** - Real-time monitoring with AI-powered risk scoring  
✅ **Decision Consistency** - Explainable AI outputs and standardized workflows  
✅ **Cost Efficiency** - Open-source alternative to expensive proprietary platforms

---

### 🌐 For Organizations (NGOs, Critical Infrastructure, Institutions)

**Challenges:**
- Limited budget for situational awareness
- Distributed operations across regions
- Manual incident tracking
- Lack of governance tools

**S.O.L.A.R Solutions:**
✅ **Affordable Stack** - Docker-based deployment on commodity hardware  
✅ **Early Pattern Detection** - Identify abnormal patterns in field operations  
✅ **Transparent Governance** - Human-in-the-loop approvals and action logs  
✅ **Scalable Architecture** - Start small, scale to enterprise

---

## 🏗️ Architecture

### System Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Frontend Dashboard                             │
│            (Tactical Map, Timeline, AI Assistant)                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   API Gateway   │
                    │   (Port 8080)   │
                    │  RBAC + Routing │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┬────────────────────┐
        │                    │                    │                    │
        ▼                    ▼                    ▼                    ▼
┌───────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Ingestion    │    │  Analytics   │    │   Semantic   │    │   Alerting   │
│  Service      │    │   Service    │    │   Service    │    │   Service    │
│  (Port 8001)  │    │  (Port 8002) │    │  (Port 8003) │    │  (Port 8004) │
└───────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
        │                   │                   │                   │
        └───────────────────┼───────────────────┴───────────────────┘
                            │
        ┌───────────────────┼───────────────────┬───────────────────┐
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌───────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  PostgreSQL   │   │    Redis     │   │   PostGIS    │   │Stream Processor│
│  + PostGIS    │   │   Streams    │   │  Geospatial  │   │  (Optional)  │
│               │   │              │   │              │   │ (Port 8005)  │
└───────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

### 🧩 Functional Layers

| Layer | Purpose | Technologies |
|-------|---------|--------------|
| **Data Ingestion** | Multi-source data collection | Camera feeds, GPS, OCR, public APIs, police records |
| **Data Fabric** | Unified data storage | PostgreSQL + PostGIS + shared data contracts |
| **Semantic Layer** | Context and relationships | Entity graph, knowledge graph, relationship mapping |
| **AI & Analytics** | Intelligence generation | ML/DL models, pattern detection, risk scoring, clustering |
| **Cognitive Interface** | Human interaction | Tactical maps, timelines, alerts, AI chat assistant |
| **Compliance** | Governance & audit | RBAC, audit trails, retention policies, data sanitization |

---

## 📦 Microservices Architecture

### Core Services

| Service | Port | Responsibility | Key Features |
|---------|------|----------------|--------------|
| **Gateway** | 8080 | Unified API + Frontend serving | RBAC, API key auth, request routing |
| **Ingestion** | 8001 | Data ingestion + compliance | Multi-source ingestion, privacy controls, stream publishing |
| **Analytics** | 8002 | AI/ML analytics | Risk scoring (rule-based, ML, DL), pattern detection, anomaly detection |
| **Semantic** | 8003 | Knowledge graph | Entity relationships, context enrichment |
| **Alerting** | 8004 | Predictive alerts | Alert generation, approval workflows, notification routing |
| **Stream Processor** | 8005 | Real-time processing | Redis stream consumer, real-time signals (optional) |

### Infrastructure Services

| Service | Technology | Purpose |
|---------|-----------|---------|
| **PostgreSQL** | PostgreSQL 15 | Primary data store with PostGIS extension |
| **Redis** | Redis 7 | Stream processing, caching, pub/sub |
| **PostGIS** | PostGIS 3.4 | Geospatial queries and analysis |

---

## 🤖 Machine Learning & Deep Learning

S.O.L.A.R features a **three-tier AI architecture** for comprehensive risk assessment:

### 1️⃣ Rule-Based Analytics
**Traditional deterministic scoring**

Factors:
- Event density (spatial clustering)
- Severity levels (weighted scoring)
- Recency (temporal decay)
- Proximity to critical zones

**Endpoint:** `GET /api/analytics/risk`

**Use Case:** Fast, explainable baseline risk assessment

---

### 2️⃣ Machine Learning (Logistic Regression)
**Statistical classification model**

Features:
- Event frequency patterns
- Temporal features (hour, day, season)
- Geospatial features (zone, density)
- Historical severity scores

**Endpoints:**
- `GET /api/analytics/ml/risk` - Get ML predictions
- `POST /api/analytics/models/train` - Train new model

**Use Case:** Probabilistic risk estimation with feature importance

---

### 3️⃣ Deep Learning (Multi-Layer Perceptron)
**Neural network for non-linear patterns**

Architecture:
```python
Input Layer (20 features)
    ↓
Hidden Layer 1 (64 neurons + ReLU + Dropout 0.3)
    ↓
Hidden Layer 2 (32 neurons + ReLU + Dropout 0.2)
    ↓
Output Layer (1 neuron + Sigmoid)
```

**Endpoints:**
- `GET /api/analytics/deep/risk` - Get DL predictions
- `POST /api/analytics/models/train` - Train deep model

**Use Case:** Complex pattern recognition, temporal sequence analysis

---

### 🔄 Model Management & MLOps

#### Model Registry

```bash
# List all model versions
GET /api/analytics/models/registry

# Response:
{
  "models": [
    {
      "id": "ml_v1_20260216",
      "type": "logistic_regression",
      "accuracy": 0.87,
      "trained_at": "2026-02-16T10:30:00Z",
      "is_deployed": true
    },
    {
      "id": "dl_v2_20260216",
      "type": "mlp_neural_network",
      "accuracy": 0.92,
      "trained_at": "2026-02-16T14:20:00Z",
      "is_deployed": false
    }
  ]
}
```

#### Model Deployment

```bash
# Deploy a specific model version
PATCH /api/analytics/models/{model_id}/deploy

# Get currently deployed models
GET /api/analytics/models/deployed
```

#### Model Comparison

```bash
# Compare all three model types
GET /api/analytics/models/compare

# Response:
{
  "rule_based": {"risk_score": 0.65, "factors": [...]},
  "ml": {"risk_score": 0.72, "probability": 0.68},
  "deep_learning": {"risk_score": 0.78, "confidence": 0.85},
  "ensemble_average": 0.72
}
```

#### Training Pipeline

```bash
# Train both ML and DL models
POST /api/analytics/models/train
Content-Type: application/json

{
  "models": ["ml", "deep"],
  "auto_deploy": true,
  "hyperparameters": {
    "ml": {
      "C": 1.0,
      "max_iter": 1000
    },
    "deep": {
      "hidden_layers": [64, 32],
      "epochs": 50,
      "batch_size": 32,
      "learning_rate": 0.001
    }
  }
}
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ with Docker Compose 2.0+
- **Python** 3.11+ (for scripts)
- **Minimum Resources:** 4GB RAM, 20GB disk
- **Recommended:** 8GB RAM, 50GB disk for production
- **Available Ports:** 8080, 8001-8005, 5432, 6379

---

### 🎯 Deployment Modes

#### 1️⃣ Light Mode (Recommended for Development)

**Best for:** Lower-spec machines, development, testing

```bash
# Clone repository
git clone https://github.com/maykonlincolnusa/S.O.L.A.R.git
cd S.O.L.A.R

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start core services only (no streaming)
docker compose up --build -d postgres redis ingestion analytics semantic alerting gateway
```

**Resources:** ~2GB RAM

**What's included:**
- ✅ Core microservices
- ✅ PostgreSQL + PostGIS
- ✅ Redis for caching
- ❌ Stream processor (optional)

---

#### 2️⃣ Full Stack with Streaming

**Best for:** Production, high-volume scenarios

```bash
# Start all services including stream processor
docker compose --profile streaming up --build -d
```

**Resources:** ~3-4GB RAM

**What's included:**
- ✅ All core services
- ✅ Real-time stream processing
- ✅ Event-driven architecture
- ✅ Redis stream consumer

---

#### 3️⃣ Frontend Preview Only (No Backend)

**Best for:** UI development, demos without infrastructure

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_frontend_preview.ps1 -Port 5500
```

**Linux/macOS:**
```bash
python3 -m http.server 5500 --directory frontend
```

**Access:** http://localhost:5500

---

### 📊 Initial Setup & Data Seeding

#### Step 1: Seed Demo Data

```bash
# Populate database with sample events
python scripts/seed_demo_data.py
```

**Creates:**
- 100+ sample security events
- Geospatial data points
- Historical patterns
- Test entities

#### Step 2: Train AI Models

```bash
# Train both ML and DL models
python scripts/train_models.py
```

**Process:**
1. Extracts features from seeded data
2. Trains logistic regression model
3. Trains deep neural network
4. Validates model performance
5. Auto-deploys to production

---

### 🔐 Authentication & Access

S.O.L.A.R uses **API key authentication** with role-based access control.

#### Default API Keys

| Role | API Key | Permissions |
|------|---------|-------------|
| **Admin** | `dev-admin-key` | Full system access |
| **Analyst** | `dev-analyst-key` | Read + Write analytics |
| **Operator** | `dev-operator-key` | Basic operations |
| **Viewer** | `dev-viewer-key` | Read-only access |
| **Ingestion** | `dev-ingest-key` | Data ingestion only |
| **Compliance** | `dev-compliance-key` | Compliance workflows |

⚠️ **Change these keys in production!**

#### Using API Keys

```bash
# Include in request header
curl -H "X-API-Key: dev-admin-key" http://localhost:8080/api/analytics/risk
```

**Frontend access:**
```
http://localhost:8080/?apiKey=dev-admin-key
```

---

## 📡 API Reference

### Data Ingestion

#### Camera Feed Ingestion

```bash
POST /api/ingest/camera
X-API-Key: dev-ingest-key
Content-Type: application/json

{
  "camera_id": "CAM_001",
  "location": {
    "lat": -23.5505,
    "lon": -46.6333
  },
  "timestamp": "2026-02-16T10:30:00Z",
  "event_type": "suspicious_activity",
  "severity": 7,
  "metadata": {
    "objects_detected": ["person", "vehicle"],
    "confidence": 0.92
  }
}
```

#### GPS Tracking

```bash
POST /api/ingest/gps
X-API-Key: dev-ingest-key
Content-Type: application/json

{
  "device_id": "GPS_123",
  "location": {
    "lat": -23.5505,
    "lon": -46.6333
  },
  "speed": 45.5,
  "heading": 180,
  "timestamp": "2026-02-16T10:30:00Z"
}
```

#### License Plate OCR

```bash
POST /api/ingest/ocr-plate
X-API-Key: dev-ingest-key
Content-Type: application/json

{
  "plate_text": "ABC1234",
  "location": {
    "lat": -23.5505,
    "lon": -46.6333
  },
  "timestamp": "2026-02-16T10:30:00Z",
  "confidence": 0.95,
  "camera_id": "CAM_OCR_001"
}
```

**Privacy:** Set `HASH_PLATE_TEXT=true` in `.env` to automatically hash plate numbers.

---

### Analytics Endpoints

#### Get Risk Assessment

```bash
# Rule-based risk
GET /api/analytics/risk?lat=-23.5505&lon=-46.6333&radius_km=5

# Machine Learning risk
GET /api/analytics/ml/risk?lat=-23.5505&lon=-46.6333&radius_km=5

# Deep Learning risk
GET /api/analytics/deep/risk?lat=-23.5505&lon=-46.6333&radius_km=5

# Compare all models
GET /api/analytics/models/compare?lat=-23.5505&lon=-46.6333&radius_km=5
```

**Response:**
```json
{
  "rule_based": {
    "risk_score": 0.65,
    "factors": {
      "density": 0.7,
      "severity": 0.8,
      "recency": 0.5,
      "proximity": 0.6
    }
  },
  "ml": {
    "risk_score": 0.72,
    "probability": 0.68,
    "feature_importance": {...}
  },
  "deep_learning": {
    "risk_score": 0.78,
    "confidence": 0.85
  },
  "ensemble_average": 0.72,
  "recommendation": "high_alert"
}
```

#### Pattern Detection

```bash
GET /api/analytics/patterns?days=7&min_frequency=3
```

**Response:**
```json
{
  "patterns": [
    {
      "pattern_id": "PAT_001",
      "type": "temporal",
      "description": "Increased activity between 22:00-02:00",
      "frequency": 15,
      "confidence": 0.87,
      "locations": [...]
    }
  ]
}
```

#### Anomaly Detection

```bash
GET /api/analytics/anomalies?threshold=0.8
```

**Response:**
```json
{
  "anomalies": [
    {
      "event_id": "EVT_12345",
      "anomaly_score": 0.92,
      "reasons": [
        "Unusual time of day",
        "Atypical location",
        "High severity deviation"
      ],
      "timestamp": "2026-02-16T03:45:00Z"
    }
  ]
}
```

---

### Alert Management

#### Evaluate Alert Conditions

```bash
POST /api/alerts/evaluate
X-API-Key: dev-analyst-key
Content-Type: application/json

{
  "location": {
    "lat": -23.5505,
    "lon": -46.6333
  },
  "event_type": "high_risk_area",
  "risk_threshold": 0.7
}
```

#### List Alerts

```bash
GET /api/alerts?status=pending_approval&priority=high
```

#### Approve Alert

```bash
PATCH /api/alerts/{alert_id}/approve
X-API-Key: dev-admin-key
Content-Type: application/json

{
  "approved_by": "admin@solar.gov",
  "notes": "Verified through camera feeds"
}
```

#### Close Alert

```bash
PATCH /api/alerts/{alert_id}/close
X-API-Key: dev-analyst-key
Content-Type: application/json

{
  "resolution": "False alarm - construction activity",
  "closed_by": "analyst@solar.gov"
}
```

---

### Compliance & Privacy

#### Erase Vehicle Data (GDPR/LGPD Right to Erasure)

```bash
POST /api/compliance/erase-vehicle/ABC1234
X-API-Key: dev-compliance-key
Content-Type: application/json

{
  "reason": "User data deletion request",
  "requested_by": "privacy@solar.gov"
}
```

#### Data Retention Policy

```bash
POST /api/compliance/retention
X-API-Key: dev-compliance-key
Content-Type: application/json

{
  "retention_days": 90,
  "data_types": ["gps_tracking", "camera_events"],
  "action": "archive"
}
```

#### Audit Log Query

```bash
GET /api/audit/logs?action=data_access&user=analyst@solar.gov&days=7
```

---

### Security & Authentication

#### Who Am I (Verify API Key)

```bash
GET /api/security/whoami
X-API-Key: dev-admin-key
```

**Response:**
```json
{
  "role": "admin",
  "permissions": [
    "read:all",
    "write:all",
    "delete:all",
    "admin:users",
    "admin:compliance"
  ],
  "key_id": "dev-admin-key"
}
```

---

## 🗄️ Database Schema

### Core Tables

#### Events Table

```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    severity INT CHECK (severity BETWEEN 0 AND 10),
    location GEOGRAPHY(POINT, 4326),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255)
);

CREATE INDEX idx_events_location ON events USING GIST(location);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_severity ON events(severity);
CREATE INDEX idx_events_type ON events(event_type);
```

#### Alerts Table

```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    priority VARCHAR(20) CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(50) DEFAULT 'pending_approval',
    location GEOGRAPHY(POINT, 4326),
    risk_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    approved_by VARCHAR(255),
    closed_at TIMESTAMPTZ,
    resolution TEXT
);
```

#### Audit Logs Table

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action VARCHAR(100) NOT NULL,
    user_id VARCHAR(255),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    metadata JSONB,
    ip_address INET,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
```

---

## ☁️ Cloud Deployment (AWS)

S.O.L.A.R includes complete **Terraform Infrastructure-as-Code** for AWS deployment.

### Architecture Components

| AWS Service | Purpose |
|-------------|---------|
| **VPC** | Isolated network with public/private subnets |
| **RDS PostgreSQL** | Managed database with PostGIS |
| **ElastiCache Redis** | Managed Redis for streams |
| **ECS Fargate** | Containerized microservices (or EKS for Kubernetes) |
| **ECR** | Docker image registry |
| **ALB** | Application Load Balancer |
| **CloudWatch** | Logging and monitoring |
| **SNS** | Alert notifications |
| **S3** | Artifact storage, backups |
| **IAM** | Role-based access control |

### Deployment Steps

#### 1️⃣ Prerequisites

```bash
# Install Terraform
brew install terraform  # macOS
# or download from terraform.io

# Configure AWS credentials
aws configure
```

#### 2️⃣ Initialize Terraform

```bash
cd infra/terraform

# Initialize providers
terraform init

# Review planned changes
terraform plan -var-file="production.tfvars"
```

#### 3️⃣ Deploy Infrastructure

```bash
# Apply configuration
terraform apply -var-file="production.tfvars"

# Outputs will include:
# - RDS endpoint
# - Redis endpoint
# - ALB DNS name
# - ECR repository URLs
```

#### 4️⃣ Deploy Services

```bash
# Build and push Docker images
make docker-build-all
make docker-push-all

# Update ECS services
make ecs-deploy
```

### Terraform Configuration

**File:** `infra/terraform/production.tfvars`

```hcl
# Region Configuration
aws_region = "us-east-1"
environment = "production"

# Network
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

# Database
db_instance_class = "db.t3.medium"
db_allocated_storage = 100
db_multi_az = true
db_backup_retention_days = 7

# Cache
redis_node_type = "cache.t3.medium"
redis_num_cache_nodes = 2

# Compute
ecs_task_cpu = 512
ecs_task_memory = 1024
ecs_desired_count = 2
ecs_max_count = 10

# Monitoring
enable_cloudwatch_alarms = true
log_retention_days = 30

# Tags
tags = {
  Project = "SOLAR"
  Environment = "Production"
  ManagedBy = "Terraform"
}
```

### Cost Optimization

**Estimated Monthly Cost (Production):**

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| RDS PostgreSQL | db.t3.medium | ~$60 |
| ElastiCache | cache.t3.medium x2 | ~$100 |
| ECS Fargate | 2 tasks x 6 services | ~$150 |
| ALB | 1 load balancer | ~$20 |
| CloudWatch | Logs + Metrics | ~$30 |
| **Total** | | **~$360/month** |

**Cost Optimization Tips:**
- Use Reserved Instances for RDS (save 40-60%)
- Enable auto-scaling to reduce idle capacity
- Use S3 lifecycle policies for log archival
- Implement CloudWatch log filtering

---

## 🔧 Configuration Guide

### Environment Variables

**File:** `.env`

```bash
# ============================================
# DATABASE CONFIGURATION
# ============================================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=solar
POSTGRES_USER=solar_user
POSTGRES_PASSWORD=change_me_in_production

# PostGIS Extension
ENABLE_POSTGIS=true

# ============================================
# REDIS CONFIGURATION
# ============================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_STREAM_KEY=solar:events

# ============================================
# SERVICE PORTS
# ============================================
GATEWAY_PORT=8080
INGESTION_PORT=8001
ANALYTICS_PORT=8002
SEMANTIC_PORT=8003
ALERTING_PORT=8004
STREAM_PROCESSOR_PORT=8005

# ============================================
# SECURITY & COMPLIANCE
# ============================================
# API Keys (CHANGE IN PRODUCTION!)
ADMIN_API_KEY=dev-admin-key
ANALYST_API_KEY=dev-analyst-key
OPERATOR_API_KEY=dev-operator-key
VIEWER_API_KEY=dev-viewer-key
INGEST_API_KEY=dev-ingest-key
COMPLIANCE_API_KEY=dev-compliance-key

# Privacy
HASH_PLATE_TEXT=true
ENABLE_AUDIT_LOGGING=true

# ============================================
# AI/ML CONFIGURATION
# ============================================
ML_MODEL_PATH=/app/models
ML_AUTO_TRAIN=false
ML_TRAIN_INTERVAL_HOURS=24

# Deep Learning
DL_HIDDEN_LAYERS=64,32
DL_DROPOUT_RATE=0.3
DL_LEARNING_RATE=0.001
DL_EPOCHS=50
DL_BATCH_SIZE=32

# ============================================
# ALERTING
# ============================================
ALERT_HIGH_RISK_THRESHOLD=0.7
ALERT_CRITICAL_THRESHOLD=0.85
REQUIRE_APPROVAL_THRESHOLD=high
NOTIFICATION_ENABLED=true

# ============================================
# MONITORING
# ============================================
LOG_LEVEL=INFO
ENABLE_METRICS=true
METRICS_PORT=9090
```

---

## 🧪 Testing & Validation

### Unit Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_analytics_engine.py -v

# Run with coverage
python -m pytest --cov=services --cov-report=html tests/
```

### Code Validation

```bash
# Compile all Python files
python -m compileall shared services scripts tests

# Type checking
mypy services/ --ignore-missing-imports

# Linting
flake8 services/ --max-line-length=100
```

### Integration Tests

```bash
# Start test environment
docker compose -f docker-compose.test.yml up -d

# Run integration tests
python -m pytest tests/integration/ -v

# Cleanup
docker compose -f docker-compose.test.yml down -v
```

---

## 📊 Monitoring & Observability

### Health Checks

```bash
# Gateway health
curl http://localhost:8080/health

# Individual service health
curl http://localhost:8001/health  # Ingestion
curl http://localhost:8002/health  # Analytics
curl http://localhost:8003/health  # Semantic
curl http://localhost:8004/health  # Alerting
```

### Metrics Endpoints

```bash
# Prometheus-compatible metrics
curl http://localhost:8080/metrics
```

**Available Metrics:**
- `solar_events_ingested_total` - Total events ingested
- `solar_risk_assessments_total` - Risk assessments performed
- `solar_alerts_generated_total` - Alerts generated
- `solar_ml_predictions_total` - ML model predictions
- `solar_api_request_duration_seconds` - API latency
- `solar_database_connections` - Active DB connections

### Log Aggregation

```bash
# View logs from all services
docker compose logs -f

# View specific service
docker compose logs -f analytics

# Filter by time
docker compose logs --since 1h analytics
```

---

## 🤝 Contributing

We welcome contributions to S.O.L.A.R!

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Write** tests for new functionality
4. **Ensure** all tests pass (`pytest tests/`)
5. **Commit** changes (`git commit -m 'Add amazing feature'`)
6. **Push** to branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### Code Standards

- Follow PEP 8 for Python code
- Add type hints to all functions
- Write docstrings for modules, classes, and functions
- Maintain test coverage above 80%
- Update documentation for new features

---

## 🗺️ Roadmap

### Version 1.0 (Current)
- [x] Core microservices architecture
- [x] Multi-source data ingestion
- [x] Triple AI risk assessment (Rule-based, ML, DL)
- [x] Model registry and versioning
- [x] RBAC with API keys
- [x] Compliance workflows (GDPR/LGPD)
- [x] Geospatial analysis with PostGIS
- [x] Real-time alerting with approval flows
- [x] Audit logging
- [x] AWS Terraform deployment

### Version 2.0 (Q2 2026)
- [ ] Advanced NLP for incident reports
- [ ] Computer vision integration for camera analysis
- [ ] Graph neural networks for relationship detection
- [ ] Federated learning across jurisdictions
- [ ] Mobile app for field operations
- [ ] Advanced visualization (3D maps, AR)
- [ ] Blockchain-based audit trail
- [ ] Multi-language support

### Version 3.0 (Q4 2026)
- [ ] Quantum-resistant encryption
- [ ] Edge computing for camera processing
- [ ] Generative AI for scenario simulation
- [ ] Cross-border intelligence sharing
- [ ] Drone integration for aerial monitoring
- [ ] IoT sensor network (environmental, acoustic)
- [ ] Predictive policing ethics framework
- [ ] Open data portal for researchers

---

## 📚 Documentation

### Official Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Security Best Practices](docs/SECURITY.md)
- [ML Model Training](docs/ML_TRAINING.md)

### External Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [Redis Streams Guide](https://redis.io/docs/data-types/streams/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Maykon Lincoln USA**

- GitHub: [@maykonlincolnusa](https://github.com/maykonlincolnusa)
- LinkedIn: [Maykon Lincoln](https://linkedin.com/in/maykonlincolnusa)
- Website: [maykonlincoln.com](https://maykonlincoln.com)
- Email: contact@maykonlincoln.com

---

## 🙏 Acknowledgments

- Inspired by data fabric and cognitive operations architectures
- Built with open-source technologies
- Designed for the public good and sovereign intelligence
- Committed to privacy, transparency, and ethical AI

---

## 💬 Support & Community

### Get Help

- 🐛 [Report Bug](https://github.com/maykonlincolnusa/S.O.L.A.R/issues)
- 💡 [Request Feature](https://github.com/maykonlincolnusa/S.O.L.A.R/issues)
- 💬 [Discussions](https://github.com/maykonlincolnusa/S.O.L.A.R/discussions)
- 📧 Email: maykon_zero@hotmail.com 

### Community Guidelines

We are committed to providing a welcoming and inclusive environment. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

---

## ⭐ Star History

If S.O.L.A.R helps your organization, please consider giving it a star!

[![Star History Chart](https://api.star-history.com/svg?repos=maykonlincolnusa/S.O.L.A.R&type=Date)](https://star-history.com/#maykonlincolnusa/S.O.L.A.R&Date)

---

<div align="center">

### ☀️ Illuminating Complexity, Empowering Intelligence

**Building a safer, smarter world through sovereign cognitive infrastructure**

**[⬆ Back to top](#-solar)**

---

![Profile Views](https://komarev.com/ghpvc/?username=maykonlincolnusa&repo=S.O.L.A.R&color=orange&style=flat-square&label=Repository+Views)

</div>
