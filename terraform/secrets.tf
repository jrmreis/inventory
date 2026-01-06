# AWS Secrets Manager for storing sensitive credentials

resource "aws_secretsmanager_secret" "bot_secrets" {
  name                    = "${var.project_name}-${var.environment}-secrets"
  description             = "Secrets for Inventory Bot"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-secrets"
  }
}

# Secret version with placeholder values
# IMPORTANT: Update these values after creation or use GitHub Actions to update
resource "aws_secretsmanager_secret_version" "bot_secrets" {
  secret_id = aws_secretsmanager_secret.bot_secrets.id

  secret_string = jsonencode({
    TELEGRAM_BOT_TOKEN = "REPLACE_WITH_YOUR_TELEGRAM_BOT_TOKEN"
    SUPABASE_URL       = "REPLACE_WITH_YOUR_SUPABASE_URL"
    SUPABASE_KEY       = "REPLACE_WITH_YOUR_SUPABASE_KEY"
    GROQ_API_KEY       = "REPLACE_WITH_YOUR_GROQ_API_KEY"
    ALLOWED_USER_IDS   = "REPLACE_WITH_COMMA_SEPARATED_USER_IDS"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

output "secret_update_command" {
  description = "AWS CLI command to update secrets"
  value       = <<-EOT
    Update secrets using AWS CLI:

    aws secretsmanager update-secret \
      --secret-id ${aws_secretsmanager_secret.bot_secrets.name} \
      --secret-string '{
        "TELEGRAM_BOT_TOKEN": "your_token",
        "SUPABASE_URL": "your_url",
        "SUPABASE_KEY": "your_key",
        "GROQ_API_KEY": "your_key",
        "ALLOWED_USER_IDS": "123456789,987654321"
      }'
  EOT
}
