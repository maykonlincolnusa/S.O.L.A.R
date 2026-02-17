# Terraform Baseline for S.O.L.A.R

This Terraform stack provisions AWS infrastructure for S.O.L.A.R with two orchestration modes:

- `ecs` (default): ECS/Fargate deployment baseline
- `eks`: EKS cluster + managed node group baseline

It also provisions:

- VPC, subnets, route table, and security groups
- RDS PostgreSQL
- ECR repositories for each microservice
- S3 raw-data bucket
- CloudWatch log groups, dashboard, alarms, and SNS topic

## Quick Start

```bash
cd infra/terraform
terraform init
terraform plan -var="db_password=change-me" -var="orchestrator=ecs"
terraform apply -var="db_password=change-me" -var="orchestrator=ecs"
```

## Deploying EKS Mode

```bash
terraform plan -var="db_password=change-me" -var="orchestrator=eks"
terraform apply -var="db_password=change-me" -var="orchestrator=eks"
```

## Optional Alarm Email

```bash
terraform apply \
  -var="db_password=change-me" \
  -var="orchestrator=ecs" \
  -var="alarm_email=you@example.com"
```

## Notes

- This is a production-ready baseline, not a full enterprise landing zone.
- Add WAF, private subnets/NAT, IAM least-privilege refinements, KMS policy hardening, and CI/CD promotion flows before go-live.
- ECS and EKS are alternatives selected by `orchestrator`. Terraform handles either mode from one codebase.
