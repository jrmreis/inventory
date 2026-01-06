# ECS Cluster and Service for running the bot

# ECS Cluster
resource "aws_ecs_cluster" "inventory_bot" {
  name = "${var.project_name}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-cluster"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "inventory_bot" {
  family                   = "${var.project_name}-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"   # 0.25 vCPU
  memory                   = "512"   # 512 MB
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "inventory-bot"
      image     = "${aws_ecr_repository.inventory_bot.repository_url}:latest"
      essential = true

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.inventory_bot.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      # Secrets from AWS Secrets Manager
      secrets = [
        {
          name      = "TELEGRAM_BOT_TOKEN"
          valueFrom = "${aws_secretsmanager_secret.bot_secrets.arn}:TELEGRAM_BOT_TOKEN::"
        },
        {
          name      = "SUPABASE_URL"
          valueFrom = "${aws_secretsmanager_secret.bot_secrets.arn}:SUPABASE_URL::"
        },
        {
          name      = "SUPABASE_KEY"
          valueFrom = "${aws_secretsmanager_secret.bot_secrets.arn}:SUPABASE_KEY::"
        },
        {
          name      = "GROQ_API_KEY"
          valueFrom = "${aws_secretsmanager_secret.bot_secrets.arn}:GROQ_API_KEY::"
        },
        {
          name      = "ALLOWED_USER_IDS"
          valueFrom = "${aws_secretsmanager_secret.bot_secrets.arn}:ALLOWED_USER_IDS::"
        }
      ]

      environment = [
        {
          name  = "LOG_LEVEL"
          value = "INFO"
        },
        {
          name  = "TEMP_DIR"
          value = "/tmp/inventory_bot"
        }
      ]

      # Health check
      healthCheck = {
        command     = ["CMD-SHELL", "python -c 'import sys; sys.exit(0)' || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name = "${var.project_name}-task-definition"
  }
}

# ECS Service
resource "aws_ecs_service" "inventory_bot" {
  name            = "${var.project_name}-${var.environment}"
  cluster         = aws_ecs_cluster.inventory_bot.id
  task_definition = aws_ecs_task_definition.inventory_bot.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  # Enable deployment circuit breaker for safer deployments
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 0
  }

  tags = {
    Name = "${var.project_name}-service"
  }
}

# Data source for default VPC
data "aws_vpc" "default" {
  default = true
}

# Data source for default subnets
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security group for ECS tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-${var.environment}-ecs-tasks"
  description = "Security group for Inventory Bot ECS tasks"
  vpc_id      = data.aws_vpc.default.id

  # Egress rule - allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "${var.project_name}-ecs-sg"
  }
}

# IAM Role for ECS Task Execution (pulls images, gets secrets)
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-${var.environment}-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-ecs-execution-role"
  }
}

# Attach AWS managed policy for ECS task execution
resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Policy for accessing Secrets Manager
resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "${var.project_name}-secrets-access"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.bot_secrets.arn
      }
    ]
  })
}

# IAM Role for ECS Task (runtime permissions)
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-${var.environment}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-ecs-task-role"
  }
}

# Policy for task runtime (if needed - currently minimal)
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${var.project_name}-task-policy"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.inventory_bot.arn}:*"
      }
    ]
  })
}

# Outputs
output "ecs_task_definition_arn" {
  description = "ECS task definition ARN"
  value       = aws_ecs_task_definition.inventory_bot.arn
}

output "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  value       = aws_security_group.ecs_tasks.id
}
