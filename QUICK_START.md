# Quick Start Guide - 5 Minutes to First Run

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Tesseract OCR installed
- [ ] Telegram bot created (@BotFather)
- [ ] Supabase account created
- [ ] Groq API key obtained

## Step 1: Get Credentials (10 minutes)

### Telegram Bot
```
1. Open Telegram → Message @BotFather
2. Send: /newbot
3. Name: My Inventory Bot
4. Username: my_inventory_bot
5. Copy the token
```

### Your Telegram User ID
```
1. Message @userinfobot
2. Copy your numeric ID
```

### Supabase
```
1. Go to supabase.com
2. Create project (free tier)
3. Copy Project URL
4. Copy anon/public key
```

### Groq AI
```
1. Go to console.groq.com
2. Sign up (free)
3. Create API key
4. Copy key (starts with gsk_)
```

## Step 2: Install & Configure (2 minutes)

```bash
# Navigate to project
cd /home/joel/repos/github/Dev/Inventory

# Install dependencies
pip install -r requirements.txt

# Install Tesseract (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Configure environment
cp .env.example .env
nano .env  # or use your favorite editor
```

Edit `.env`:
```bash
TELEGRAM_BOT_TOKEN=your_token_here
SUPABASE_URL=https://your_project.supabase.co
SUPABASE_KEY=your_anon_key_here
GROQ_API_KEY=gsk_your_key_here
ALLOWED_USER_IDS=your_telegram_user_id
```

## Step 3: Setup Database (2 minutes)

```
1. Open Supabase Dashboard
2. Go to SQL Editor
3. Copy & paste migrations/001_create_components_table.sql
4. Click "Run"
5. Copy & paste migrations/002_create_views.sql
6. Click "Run"
```

## Step 4: Run! (1 minute)

```bash
python main.py
```

You should see:
```
✅ Environment configuration verified
✅ Temporary directory ready
🤖 Inventory Bot starting...
```

## Step 5: Test (1 minute)

1. Open Telegram
2. Search for your bot username
3. Send: `/start`
4. Send: `/help`
5. Take a photo of an electronic component
6. Send the photo to the bot
7. Watch it recognize and extract data!

## Common Commands

```
/start      - Welcome message
/help       - All commands
/add        - Add component manually
/search led - Search for LEDs
/status     - Inventory summary
/low_stock  - Low stock alert
/myid       - Get your Telegram ID
```

## Troubleshooting

**Bot doesn't respond:**
- Check TELEGRAM_BOT_TOKEN is correct
- Check ALLOWED_USER_IDS includes your ID
- Check bot is running (no errors in terminal)

**Image recognition fails:**
- Check GROQ_API_KEY is correct
- Ensure tesseract is installed: `tesseract --version`
- Try better lighting/clearer photo

**Database errors:**
- Check SUPABASE_URL and SUPABASE_KEY
- Verify migrations ran successfully
- Check internet connection

## What's Next?

### For Local Development
→ Read [SETUP.md](SETUP.md)

### For AWS Deployment
→ Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### For Architecture Details
→ Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

## Example Workflow

1. **Add a resistor with photo:**
   - Take photo of resistor
   - Send to bot
   - Bot recognizes: "10kΩ resistor, ±5%, 0.25W"
   - Confirm details
   - Enter quantity: 50
   - Enter location: "Drawer A1"
   - ✅ Saved!

2. **Search inventory:**
   - Send: `/search resistor`
   - Bot shows all resistors with quantities and locations

3. **Check low stock:**
   - Send: `/low_stock`
   - Bot shows items below minimum quantity

4. **View status:**
   - Send: `/status`
   - Bot shows inventory summary by type

## Tips for Best Results

**Photography:**
- 📸 Good lighting (natural light is best)
- 🔍 Clear focus on component
- 📏 Close-up shot
- 🏷️ Include all labels and markings
- 🎨 Plain background (white/light color)

**Components that work best:**
- ✅ Resistors (with color bands visible)
- ✅ ICs with clear part numbers
- ✅ Modules with labels (Arduino, ESP32)
- ✅ Capacitors with markings
- ✅ Any component with printed text

**If recognition fails:**
- Use `/add` for manual entry
- Try different angle/lighting
- Clean component surface
- Check OCR text with `/help`

## File Locations

```
Configuration:    .env
Application:      main.py
Bot logic:        app/bot.py
Database schema:  migrations/*.sql
Documentation:    *.md files
```

## Support

- 📖 Read documentation files
- 🐛 Check logs in terminal
- 🔍 Search error messages
- 💬 Open GitHub issue

---

**You're all set! Start managing your components! 🎉**
