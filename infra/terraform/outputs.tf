output "vpc_id" {
  value = aws_vpc.solar.id
}

output "db_endpoint" {
  value = aws_db_instance.solar.address
}

output "orchestrator_mode" {
  value = var.orchestrator
}

output "ecs_cluster_name" {
  value = try(aws_ecs_cluster.solar[0].name, null)
}

output "ecs_gateway_service_name" {
  value = try(aws_ecs_service.gateway[0].name, null)
}

output "eks_cluster_name" {
  value = try(aws_eks_cluster.solar[0].name, null)
}

output "raw_data_bucket" {
  value = aws_s3_bucket.raw_data.bucket
}

output "ecr_repository_urls" {
  value = { for name, repo in aws_ecr_repository.services : name => repo.repository_url }
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.apps.name
}

output "alarm_topic_arn" {
  value = try(aws_sns_topic.alerts[0].arn, null)
}
