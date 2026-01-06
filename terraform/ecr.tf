# ECR Repository for Docker images

resource "aws_ecr_repository" "inventory_bot" {
  name                 = "${var.project_name}-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${var.project_name}-ecr"
  }
}

# Lifecycle policy to keep only recent images
resource "aws_ecr_lifecycle_policy" "inventory_bot" {
  repository = aws_ecr_repository.inventory_bot.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

output "ecr_registry_id" {
  description = "ECR registry ID"
  value       = aws_ecr_repository.inventory_bot.registry_id
}
