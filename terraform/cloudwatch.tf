# CloudWatch Logs for monitoring and debugging

resource "aws_cloudwatch_log_group" "inventory_bot" {
  name              = "/ecs/${var.project_name}-${var.environment}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-logs"
  }
}

# CloudWatch Log Metric Filters for monitoring

# Filter for errors
resource "aws_cloudwatch_log_metric_filter" "errors" {
  name           = "${var.project_name}-errors"
  log_group_name = aws_cloudwatch_log_group.inventory_bot.name
  pattern        = "[time, request_id, level = ERROR*, ...]"

  metric_transformation {
    name      = "ErrorCount"
    namespace = "InventoryBot"
    value     = "1"
  }
}

# Filter for component additions
resource "aws_cloudwatch_log_metric_filter" "components_added" {
  name           = "${var.project_name}-components-added"
  log_group_name = aws_cloudwatch_log_group.inventory_bot.name
  pattern        = "[..., msg = \"*Component saved successfully*\"]"

  metric_transformation {
    name      = "ComponentsAdded"
    namespace = "InventoryBot"
    value     = "1"
  }
}

# CloudWatch Alarms

# Alarm for high error rate
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.project_name}-${var.environment}-high-errors"
  alarm_description   = "Alert when error rate is high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ErrorCount"
  namespace           = "InventoryBot"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  treat_missing_data  = "notBreaching"

  tags = {
    Name = "${var.project_name}-error-alarm"
  }
}

# Alarm for ECS service task count
resource "aws_cloudwatch_metric_alarm" "ecs_service_running" {
  alarm_name          = "${var.project_name}-${var.environment}-task-stopped"
  alarm_description   = "Alert when ECS service has no running tasks"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "RunningTaskCount"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "1"

  dimensions = {
    ClusterName = aws_ecs_cluster.inventory_bot.name
    ServiceName = aws_ecs_service.inventory_bot.name
  }

  tags = {
    Name = "${var.project_name}-task-alarm"
  }
}

# Outputs
output "cloudwatch_error_alarm_arn" {
  description = "CloudWatch error alarm ARN"
  value       = aws_cloudwatch_metric_alarm.high_error_rate.arn
}

output "cloudwatch_task_alarm_arn" {
  description = "CloudWatch task alarm ARN"
  value       = aws_cloudwatch_metric_alarm.ecs_service_running.arn
}
