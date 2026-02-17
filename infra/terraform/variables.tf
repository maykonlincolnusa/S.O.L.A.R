variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project prefix"
  type        = string
  default     = "solar"
}

variable "orchestrator" {
  description = "Container orchestrator to deploy (ecs or eks)"
  type        = string
  default     = "ecs"

  validation {
    condition     = contains(["ecs", "eks"], var.orchestrator)
    error_message = "orchestrator must be either ecs or eks."
  }
}

variable "db_username" {
  description = "RDS username"
  type        = string
  default     = "solar"
}

variable "db_password" {
  description = "RDS password"
  type        = string
  sensitive   = true
}

variable "db_allocated_storage" {
  description = "RDS storage in GB"
  type        = number
  default     = 30
}

variable "gateway_image" {
  description = "Container image for gateway ECS service"
  type        = string
  default     = "public.ecr.aws/docker/library/nginx:stable"
}

variable "gateway_cpu" {
  description = "Gateway ECS task CPU"
  type        = number
  default     = 512
}

variable "gateway_memory" {
  description = "Gateway ECS task memory"
  type        = number
  default     = 1024
}

variable "gateway_desired_count" {
  description = "Gateway ECS desired tasks"
  type        = number
  default     = 1
}

variable "enable_observability" {
  description = "Enable CloudWatch dashboard and alarms"
  type        = bool
  default     = true
}

variable "alarm_email" {
  description = "Email address for alarm notifications (optional)"
  type        = string
  default     = ""
}

variable "eks_version" {
  description = "Kubernetes version for EKS"
  type        = string
  default     = "1.31"
}

variable "eks_node_desired_size" {
  description = "Desired node count for EKS"
  type        = number
  default     = 2
}

variable "eks_node_min_size" {
  description = "Min node count for EKS"
  type        = number
  default     = 1
}

variable "eks_node_max_size" {
  description = "Max node count for EKS"
  type        = number
  default     = 4
}

variable "eks_node_instance_types" {
  description = "EKS node instance types"
  type        = list(string)
  default     = ["t3.medium"]
}
