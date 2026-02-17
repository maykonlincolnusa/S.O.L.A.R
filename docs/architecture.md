# S.O.L.A.R Layer Mapping

Reference stack implemented in this repo:

1. Ingestion
2. Data Fabric / Data Mesh
3. Semantic Layer
4. AI and Agents
5. Cognitive Interface

## Logical View

```text
                 +------------------------------+
                 |    Cognitive Interface       |
                 |  map + timeline + chat +    |
                 |       predictive alerts      |
                 +---------------+--------------+
                                 |
                    +------------v-----------+
                    |     AI and Agents      |
                    | pattern/risk/anomaly   |
                    | + ML + Deep Learning   |
                    | + analytic chat agent  |
                    +------------+-----------+
                                 |
                    +------------v-----------+
                    |      Semantic Layer    |
                    | entities + relations   |
                    | contextual graph       |
                    +------------+-----------+
                                 |
                    +------------v-----------+
                    | Data Fabric / Mesh     |
                    | PostgreSQL/PostGIS     |
                    | shared data contracts  |
                    +------------+-----------+
                                 |
                    +------------v-----------+
                    |       Ingestion        |
                    | camera/public/police   |
                    | gps/plate OCR          |
                    +------------------------+
```

## Runtime Topology

- `gateway` orchestrates API and serves UI
- `ingestion` normalizes event ingestion
- `analytics` computes operational intelligence
  - rule-based analytics
  - machine learning risk model
  - deep learning risk model
  - model registry and deployment promotion endpoints
- `semantic` stores entities and graph edges
- `alerting` turns intelligence into operator alerts
- `stream-processor` (optional) consumes Redis streams for real-time signals
- `postgres` stores events, entities, analytics, alerts
- `redis` powers lightweight stream and cache use cases

## Security and Compliance Runtime

- API-key RBAC in gateway (`X-API-Key`)
- persistent audit trail in `audit_logs`
- ingestion data minimization and optional plate hashing
- high-priority alerts require explicit approval (`pending_approval` -> `open`)

## Terraform Scope

Terraform baseline provisions:

- VPC and subnets
- security groups
- PostgreSQL (RDS)
- ECS or EKS baseline (select via `orchestrator`)
- raw-data S3 bucket
- ECR repositories
- CloudWatch dashboard and alarms

The current Terraform folder is intentionally minimal for extension with:

- managed Kafka/MSK
- EKS or full ECS services
- WAF, IAM least-privilege modules
- observability stack (OTel, CloudWatch, SIEM sink)
