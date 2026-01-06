# Terraform configuration for Electronic Components Inventory Bot
# Deploys to AWS ECS Fargate

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration - Update with your S3 bucket for state storage
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "inventory-bot/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "InventoryBot"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "inventory-bot"
}

# Outputs
output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.inventory_bot.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.inventory_bot.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.inventory_bot.name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.inventory_bot.name
}

output "secrets_manager_arn" {
  description = "AWS Secrets Manager ARN"
  value       = aws_secretsmanager_secret.bot_secrets.arn
}
