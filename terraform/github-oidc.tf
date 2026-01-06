# GitHub OIDC Provider for secure CI/CD without long-term credentials

# OIDC Provider for GitHub Actions
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  # GitHub's thumbprint (valid as of 2024)
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = {
    Name = "${var.project_name}-github-oidc"
  }
}

# IAM Role for GitHub Actions
resource "aws_iam_role" "github_actions" {
  name = "${var.project_name}-${var.environment}-github-actions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            # Update this with your GitHub repository
            "token.actions.githubusercontent.com:sub" = "repo:YOUR_GITHUB_USERNAME/Inventory:*"
          }
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-github-actions-role"
  }
}

# Policy for GitHub Actions (ECR, ECS, Secrets Manager)
resource "aws_iam_role_policy" "github_actions" {
  name = "${var.project_name}-github-actions-policy"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # ECR permissions
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = "*"
      },
      # ECS permissions
      {
        Effect = "Allow"
        Action = [
          "ecs:UpdateService",
          "ecs:DescribeServices",
          "ecs:DescribeTaskDefinition",
          "ecs:RegisterTaskDefinition",
          "ecs:ListTasks",
          "ecs:DescribeTasks"
        ]
        Resource = "*"
      },
      # IAM PassRole for ECS task execution
      {
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = [
          aws_iam_role.ecs_task_execution.arn,
          aws_iam_role.ecs_task.arn
        ]
      },
      # Secrets Manager permissions
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret",
          "secretsmanager:UpdateSecret"
        ]
        Resource = aws_secretsmanager_secret.bot_secrets.arn
      },
      # CloudWatch Logs for monitoring deployments
      {
        Effect = "Allow"
        Action = [
          "logs:GetLogEvents",
          "logs:FilterLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.inventory_bot.arn}:*"
      }
    ]
  })
}

# Outputs
output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions IAM role"
  value       = aws_iam_role.github_actions.arn
}

output "github_oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider"
  value       = aws_iam_openid_connect_provider.github.arn
}

output "github_actions_setup_instructions" {
  description = "Instructions for configuring GitHub Actions"
  value       = <<-EOT
    GitHub Actions Setup:

    1. Update github-oidc.tf with your repository name:
       "repo:YOUR_GITHUB_USERNAME/Inventory:*"

    2. Apply Terraform to create the OIDC provider and role

    3. Add these secrets to your GitHub repository:
       - AWS_REGION: ${var.aws_region}
       - (No AWS credentials needed - OIDC handles authentication)

    4. In your GitHub Actions workflow, use:
       - role-to-assume: ${aws_iam_role.github_actions.arn}
       - aws-region: ${var.aws_region}
  EOT
}
