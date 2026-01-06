# Deployment Guide - Electronic Components Inventory Bot

Complete guide for deploying the Inventory Bot to AWS using Terraform and GitHub Actions.

## Prerequisites

Before deploying, ensure you have:

- **AWS Account** with administrator access
- **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
- **Supabase Account** (free tier) with database created
- **Groq API Key** (free tier) from [Groq](https://console.groq.com)
- **GitHub Repository** for your code
- **AWS CLI** installed and configured
- **Terraform** >= 1.0 installed
- **Docker** installed (for local testing)

## Step 1: Create Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Choose a name: `My Inventory Bot`
4. Choose a username: `my_inventory_bot` (must be unique)
5. Copy the bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. Get your Telegram user ID:
   - Message [@userinfobot](https://t.me/userinfobot)
   - Copy your numeric ID (e.g., `123456789`)

## Step 2: Setup Supabase Database

1. Go to [Supabase](https://supabase.com) and create a free account
2. Create a new project
3. Go to **SQL Editor** in the dashboard
4. Run the migration files in order:
   - Copy contents of `migrations/001_create_components_table.sql`
   - Click "Run" to execute
   - Copy contents of `migrations/002_create_views.sql`
   - Click "Run" to execute
5. Get your connection details:
   - Go to **Settings** → **API**
   - Copy the **Project URL** (SUPABASE_URL)
   - Copy the **anon public** key (SUPABASE_KEY)

## Step 3: Get Groq API Key

1. Go to [Groq Console](https://console.groq.com)
2. Sign up for a free account
3. Go to **API Keys**
4. Click **Create API Key**
5. Copy the key (starts with `gsk_...`)

## Step 4: Configure Terraform

1. **Update GitHub repository name** in `terraform/github-oidc.tf`:
   ```hcl
   # Line ~35
   "token.actions.githubusercontent.com:sub" = "repo:YOUR_GITHUB_USERNAME/Inventory:*"
   ```
   Replace `YOUR_GITHUB_USERNAME` with your GitHub username

2. **Copy variables file**:
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   ```

3. **Edit terraform.tfvars** (optional - defaults are fine):
   ```hcl
   aws_region   = "us-east-1"
   environment  = "production"
   project_name = "inventory-bot"
   ```

## Step 5: Deploy Infrastructure with Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Apply infrastructure (creates AWS resources)
terraform apply
```

Type `yes` when prompted.

**What gets created:**
- ECR repository for Docker images
- ECS Cluster (Fargate)
- ECS Task Definition and Service
- IAM roles and policies
- Secrets Manager secret
- CloudWatch log group
- CloudWatch alarms
- GitHub OIDC provider for CI/CD

**Note the outputs:**
```
ecr_repository_url = "123456789.dkr.ecr.us-east-1.amazonaws.com/inventory-bot-production"
github_actions_role_arn = "arn:aws:iam::123456789:role/inventory-bot-production-github-actions"
secrets_manager_arn = "arn:aws:secretsmanager:us-east-1:123456789:secret:inventory-bot-production-secrets-AbCdEf"
```

## Step 6: Update Secrets in AWS

Update the secrets in AWS Secrets Manager with your actual values:

```bash
aws secretsmanager update-secret \
  --secret-id inventory-bot-production-secrets \
  --secret-string '{
    "TELEGRAM_BOT_TOKEN": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
    "SUPABASE_URL": "https://xxxxx.supabase.co",
    "SUPABASE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "GROQ_API_KEY": "gsk_...",
    "ALLOWED_USER_IDS": "123456789,987654321"
  }'
```

**ALLOWED_USER_IDS**: Comma-separated list of Telegram user IDs or usernames (@username) who can use the bot.

## Step 7: Configure GitHub Secrets

Add these secrets to your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** for each:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ROLE_ARN` | Output from terraform: `github_actions_role_arn` | IAM role for OIDC |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | For updating secrets |
| `SUPABASE_URL` | Your Supabase project URL | For updating secrets |
| `SUPABASE_KEY` | Your Supabase anon key | For updating secrets |
| `GROQ_API_KEY` | Your Groq API key | For updating secrets |
| `ALLOWED_USER_IDS` | Comma-separated user IDs | For updating secrets |

**Note:** The workflow uses OIDC (no AWS access keys needed!), but the other secrets are used to update AWS Secrets Manager during deployment.

## Step 8: Deploy with GitHub Actions

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit: Inventory Bot"
   git push origin main
   ```

2. **GitHub Actions will automatically**:
   - Validate Python syntax
   - Build Docker image
   - Push to ECR
   - Update secrets
   - Deploy to ECS
   - Verify deployment

3. **Monitor deployment**:
   - Go to **Actions** tab in GitHub
   - Click on the running workflow
   - Watch the deployment progress

## Step 9: Verify Deployment

1. **Check ECS Service**:
   ```bash
   aws ecs describe-services \
     --cluster inventory-bot-production \
     --services inventory-bot-production \
     --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'
   ```

2. **Check CloudWatch Logs**:
   ```bash
   aws logs tail /ecs/inventory-bot-production --follow
   ```

3. **Test the bot**:
   - Open Telegram
   - Search for your bot username
   - Send `/start`
   - You should get a welcome message!

## Step 10: Using the Bot

### Basic Commands

- `/start` - Welcome message
- `/help` - Show all commands
- `/add` - Add a component manually
- `/search <query>` - Search components
- `/status` - Inventory summary
- `/low_stock` - Show low stock items

### Adding Components with Photos

1. Take a clear photo of the component
2. Send it to the bot
3. Bot will recognize the component using OCR + AI
4. Review and confirm the details
5. Enter the quantity
6. Component is saved!

**Tips for best results:**
- Good lighting
- Clear focus
- Include labels and markings
- Take close-up shots

## Monitoring and Troubleshooting

### View Logs

**Via AWS CLI:**
```bash
aws logs tail /ecs/inventory-bot-production --follow
```

**Via AWS Console:**
1. Go to [CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
2. Navigate to **Logs** → **Log groups**
3. Click `/ecs/inventory-bot-production`

### Common Issues

**Bot not responding:**
1. Check ECS service is running:
   ```bash
   aws ecs list-tasks --cluster inventory-bot-production
   ```
2. Check logs for errors
3. Verify secrets are correct in Secrets Manager

**Image recognition not working:**
1. Check Groq API key is valid
2. Verify Tesseract is installed (it's in the Docker image)
3. Try manual entry with `/add` instead

**Database errors:**
1. Verify Supabase credentials
2. Check database migrations ran successfully
3. Test connection from local environment

### Update Bot Code

Simply push to the `main` branch:

```bash
git add .
git commit -m "Update bot features"
git push origin main
```

GitHub Actions will automatically deploy the changes.

### Rollback Deployment

If you need to rollback:

```bash
# List previous task definitions
aws ecs list-task-definitions --family-prefix inventory-bot-production

# Update service to previous version
aws ecs update-service \
  --cluster inventory-bot-production \
  --service inventory-bot-production \
  --task-definition inventory-bot-production:X  # Replace X with version number
```

## Costs Estimate

All services have free tiers:

- **AWS ECS Fargate**: ~$5-10/month for always-running bot
- **Supabase**: Free tier (500MB database, 50MB file storage)
- **Groq API**: Free tier (generous limits)
- **AWS Secrets Manager**: $0.40/month per secret
- **AWS CloudWatch**: Free tier covers basic logging

**Total estimated cost: $5-12/month**

To reduce costs:
- Use ECS scheduled tasks (run on schedule, not 24/7)
- Use smaller Fargate task size (currently 0.25 vCPU, 512 MB)

## Security Best Practices

✅ **Implemented:**
- OIDC for GitHub Actions (no long-term AWS keys)
- Secrets in AWS Secrets Manager (encrypted)
- User whitelist for bot access
- Non-root container user
- Minimal IAM permissions

⚠️ **Additional recommendations:**
- Enable MFA on AWS account
- Enable CloudTrail for audit logs
- Use VPC with private subnets (current: default VPC)
- Regular security updates (rebuild Docker image monthly)

## Cleanup / Destroy Infrastructure

To completely remove all AWS resources:

```bash
cd terraform
terraform destroy
```

Type `yes` when prompted.

**This will delete:**
- All ECS resources
- ECR repository and images
- IAM roles
- Secrets
- CloudWatch logs
- Everything created by Terraform

**Note:** Supabase database is separate and won't be affected.

## Support

For issues:
1. Check logs in CloudWatch
2. Review GitHub Actions workflow output
3. Open an issue on GitHub
4. Check [Telegram Bot API docs](https://core.telegram.org/bots/api)

## Next Steps

- Add more bot commands (see `app/bot.py`)
- Customize component types (see `app/component_classifier.py`)
- Add notification alerts for low stock
- Create web dashboard (Supabase has built-in REST API)
- Add barcode/QR code scanning
- Export inventory reports to CSV/PDF

---

**Congratulations! Your Inventory Bot is deployed and running! 🎉**
