# Local Development Setup

Guide for running the Inventory Bot locally for development and testing.

## Prerequisites

- Python 3.11 or higher
- Docker (optional, for containerized testing)
- Git

## Quick Start

### 1. Clone the Repository

```bash
cd /home/joel/repos/github/Dev
git clone <your-repo-url> Inventory
cd Inventory
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install System Dependencies

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0
```

**On macOS:**
```bash
brew install tesseract
```

**On Windows:**
Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki

### 5. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# Supabase Database
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Groq AI
GROQ_API_KEY=gsk_your_groq_api_key

# Security - Your Telegram user ID(s)
ALLOWED_USER_IDS=123456789,987654321

# Optional
LOG_LEVEL=INFO
TEMP_DIR=/tmp/inventory_bot
```

### 6. Setup Database

1. Go to your Supabase project
2. Open SQL Editor
3. Run the migrations:
   - `migrations/001_create_components_table.sql`
   - `migrations/002_create_views.sql`

### 7. Run the Bot

```bash
python main.py
```

You should see:
```
✅ Environment configuration verified
✅ Temporary directory ready: /tmp/inventory_bot
🤖 Inventory Bot starting...
```

### 8. Test the Bot

1. Open Telegram
2. Search for your bot
3. Send `/start`
4. Try sending a photo of a component!

## Development Workflow

### Project Structure

```
Inventory/
├── app/
│   ├── __init__.py
│   ├── bot.py                    # Main bot logic
│   ├── image_processor.py        # OCR and image processing
│   ├── data_extractor.py         # AI data extraction
│   └── component_classifier.py   # Component classification
├── migrations/
│   ├── 001_create_components_table.sql
│   └── 002_create_views.sql
├── terraform/                    # AWS infrastructure
├── .github/workflows/            # CI/CD
├── main.py                       # Entry point
├── requirements.txt
├── Dockerfile
└── .env                          # Your local config (not in git)
```

### Making Changes

1. **Edit code** in `app/` directory
2. **Test locally** by running `python main.py`
3. **Check logs** for errors
4. **Commit changes**:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push
   ```

### Testing Image Recognition

Create a test script `test_image.py`:

```python
from app.image_processor import ImageProcessor
from app.data_extractor import ComponentDataExtractor

# Process an image
processor = ImageProcessor()
result = processor.process_image("path/to/component.jpg")
print("OCR Text:", result['text'])

# Extract component data
extractor = ComponentDataExtractor()
data = extractor.extract_component_data(result['text'])
print("Extracted Data:", data)
```

Run it:
```bash
python test_image.py
```

### Testing Database Operations

Create a test script `test_db.py`:

```python
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Test query
result = supabase.table('components').select('*').limit(5).execute()
print(f"Found {len(result.data)} components")
for comp in result.data:
    print(f"  - {comp['name']}: {comp['quantity']}")
```

Run it:
```bash
python test_db.py
```

## Docker Testing

Build and run locally:

```bash
# Build image
docker build -t inventory-bot:local .

# Run container
docker run --env-file .env inventory-bot:local
```

Test with docker-compose (create `docker-compose.yml`):

```yaml
version: '3.8'
services:
  bot:
    build: .
    env_file: .env
    restart: unless-stopped
```

Run:
```bash
docker-compose up
```

## Debugging

### Enable Debug Logging

In `.env`:
```bash
LOG_LEVEL=DEBUG
```

### View Detailed Logs

The bot logs to stdout. To save logs:
```bash
python main.py 2>&1 | tee bot.log
```

### Common Issues

**ModuleNotFoundError:**
```bash
pip install -r requirements.txt
```

**Tesseract not found:**
- Ensure Tesseract is installed and in PATH
- On Windows, add to PATH: `C:\Program Files\Tesseract-OCR`

**Database connection error:**
- Verify Supabase credentials
- Check internet connection
- Ensure database migrations are applied

**Bot not responding in Telegram:**
- Check `ALLOWED_USER_IDS` includes your user ID
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check logs for errors

## Code Style

Format code with:
```bash
pip install black
black app/*.py main.py
```

Check types with:
```bash
pip install mypy
mypy app/*.py main.py
```

## Adding New Features

### Add a New Bot Command

Edit `app/bot.py`:

```python
async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /mycommand"""
    if not is_authorized(update.effective_user):
        await update.message.reply_text("⛔ You are not authorized.")
        return

    # Your logic here
    await update.message.reply_text("Hello from my command!")

# In main() function, add:
application.add_handler(CommandHandler("mycommand", my_command))
```

### Add a New Component Type

Edit `app/component_classifier.py`:

```python
COMPONENT_CATEGORIES = {
    # ... existing types ...
    'my_component': {
        'keywords': ['keyword1', 'keyword2'],
        'description': 'Description of component'
    }
}
```

### Modify Database Schema

1. Create new migration file: `migrations/003_my_changes.sql`
2. Write SQL changes
3. Apply in Supabase SQL Editor
4. Update in production via deployment

## Performance Testing

Test image processing speed:

```python
import time
from app.image_processor import ImageProcessor

processor = ImageProcessor()

start = time.time()
result = processor.process_image("test_image.jpg")
elapsed = time.time() - start

print(f"Processing took {elapsed:.2f} seconds")
```

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot authentication token | `123456:ABC-DEF...` |
| `SUPABASE_URL` | Yes | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Yes | Supabase anon/public key | `eyJhbG...` |
| `GROQ_API_KEY` | Yes | Groq API key for AI | `gsk_...` |
| `ALLOWED_USER_IDS` | Yes | Authorized Telegram user IDs | `123,456,@user` |
| `LOG_LEVEL` | No | Logging level | `INFO` (default) |
| `TEMP_DIR` | No | Temporary files directory | `/tmp/inventory_bot` |

## Useful Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run bot
python main.py

# Run with debug logging
LOG_LEVEL=DEBUG python main.py

# Build Docker image
docker build -t inventory-bot .

# Run tests (if you add them)
pytest tests/

# Format code
black app/*.py

# Check for issues
pylint app/*.py
```

## Next Development Tasks

Ideas for enhancements:

- [ ] Add unit tests
- [ ] Add barcode/QR code scanning
- [ ] Add CSV import/export
- [ ] Add photo storage to S3
- [ ] Add usage analytics dashboard
- [ ] Add scheduled low-stock alerts
- [ ] Add multi-user collaboration features
- [ ] Add project/BOM (Bill of Materials) tracking
- [ ] Add supplier price comparison
- [ ] Add notification system (low stock alerts)

## Getting Help

- Check the [README.md](README.md) for overview
- See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for AWS deployment
- Check logs for error messages
- Review Telegram Bot API docs: https://core.telegram.org/bots/api
- Open an issue on GitHub

---

Happy coding! 🚀
