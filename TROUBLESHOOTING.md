# Troubleshooting Guide

## Common Issues and Solutions

### ✅ Bot Successfully Starting

If you see these messages, the bot is working correctly:
```
✅ Environment configuration verified
✅ Temporary directory ready
Application started
```

### Warnings You Can Ignore

**PTBUserWarning about per_message**
```
PTBUserWarning: If 'per_message=False', 'CallbackQueryHandler' will not be tracked...
```
This is a harmless warning from python-telegram-bot about conversation handler settings. The bot works fine with this warning.

### Dependency Issues

#### 1. **ModuleNotFoundError: No module named 'websockets.asyncio'**

**Cause:** Old websockets version (< 13.0)

**Solution:**
```bash
source venv/bin/activate
pip install --upgrade 'websockets>=13.0'
```

#### 2. **NumPy compatibility error with OpenCV**

**Error:**
```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x
```

**Solution:**
```bash
source venv/bin/activate
pip install 'numpy<2.0'
```

#### 3. **Missing Tesseract OCR**

**Error:**
```
pytesseract.pytesseract.TesseractNotFoundError
```

**Solution:**

Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

macOS:
```bash
brew install tesseract
```

Windows:
- Download from https://github.com/UB-Mannheim/tesseract/wiki
- Add to PATH

### Configuration Issues

#### 1. **Invalid API key (Supabase)**

**Error:**
```
SupabaseException: Invalid API key
```

**Solution:**
- Check `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`
- Verify credentials from Supabase dashboard → Settings → API
- Make sure you're using the **anon/public** key, not the service_role key

#### 2. **Bot not responding to commands**

**Possible causes:**

**A. User not whitelisted**
```bash
# Check ALLOWED_USER_IDS in .env
ALLOWED_USER_IDS=your_telegram_user_id
```

Get your ID:
- Message @userinfobot on Telegram
- Or send `/myid` to the bot (if it responds)

**B. Bot token invalid**
- Verify `TELEGRAM_BOT_TOKEN` in `.env`
- Get new token from @BotFather if needed

**C. Bot not running**
- Check terminal for errors
- Make sure `python main.py` is running

#### 3. **Database connection errors**

**Error:**
```
Connection error / Timeout
```

**Solution:**
- Check internet connection
- Verify Supabase project is active (not paused)
- Run database migrations in Supabase SQL Editor
- Test connection:
  ```bash
  python test_db.py  # Create this test file
  ```

### Image Recognition Issues

#### 1. **OCR not extracting text**

**Symptoms:** Bot says "Could not extract text from the image"

**Solutions:**
- Take photo in better lighting
- Ensure component labels are in focus
- Clean component surface
- Try different angle
- Use `/add` for manual entry instead

#### 2. **AI extraction failing**

**Error:**
```
Groq API error
```

**Solutions:**
- Check `GROQ_API_KEY` in `.env`
- Verify API key at https://console.groq.com
- Check rate limits (free tier limits)
- Try again in a few moments

#### 3. **Component misidentified**

**Solution:**
- This is normal - AI isn't perfect
- Review the recognized data before confirming
- Edit incorrect fields manually
- Use `/add` for precise manual entry

### Runtime Errors

#### 1. **Permission denied on /tmp**

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/tmp/inventory_bot'
```

**Solution:**
```bash
sudo mkdir -p /tmp/inventory_bot
sudo chmod 777 /tmp/inventory_bot
```

Or set different temp directory in `.env`:
```bash
TEMP_DIR=/home/youruser/inventory_temp
```

#### 2. **Out of memory**

**Symptoms:** Bot crashes during image processing

**Solution:**
- Reduce image size before sending
- Close other applications
- For deployment: increase ECS task memory

#### 3. **Timeout errors**

**Error:**
```
asyncio.TimeoutError
```

**Solutions:**
- Check internet connection
- Verify API endpoints are reachable
- Try again - may be temporary network issue

### Testing and Verification

#### Test All Dependencies

```bash
source venv/bin/activate
python test_imports.py
```

Should show all ✅ green checkmarks.

#### Test Database Connection

Create `test_db.py`:
```python
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

try:
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    result = supabase.table('components').select('count').execute()
    print("✅ Database connection successful!")
except Exception as e:
    print(f"❌ Database error: {e}")
```

Run:
```bash
python test_db.py
```

#### Test Telegram Bot

```bash
# Run bot
python main.py

# In another terminal, check if process is running
ps aux | grep "python main.py"
```

Then test in Telegram:
1. Search for your bot
2. Send `/start`
3. Should get welcome message

### Getting More Information

#### Enable Debug Logging

In `.env`:
```bash
LOG_LEVEL=DEBUG
```

Restart bot:
```bash
python main.py
```

#### Save Logs to File

```bash
python main.py 2>&1 | tee bot.log
```

Check the `bot.log` file for detailed error information.

#### Check System Resources

```bash
# Memory usage
free -h

# Disk space
df -h

# CPU usage
top
```

### Still Having Issues?

1. **Check logs** - Look for ERROR messages in bot output
2. **Verify environment** - Run `test_imports.py`
3. **Test components individually**:
   - Database: `test_db.py`
   - OCR: Test with simple image
   - Telegram: Check bot token
4. **Read documentation**:
   - [QUICK_START.md](QUICK_START.md)
   - [SETUP.md](SETUP.md)
   - [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
5. **Check GitHub Issues** - See if others had similar problems
6. **Create detailed issue report** with:
   - Error messages
   - Steps to reproduce
   - Environment (OS, Python version)
   - Log output

### Known Limitations

1. **Image Recognition Accuracy**
   - OCR works best with clear, well-lit photos
   - Some fonts may not be recognized
   - Handwritten labels won't work
   - Very small text may be missed

2. **AI Extraction**
   - May misidentify uncommon components
   - Confidence varies by component type
   - Always verify extracted data

3. **Free Tier Limits**
   - Groq: Rate limits on API calls
   - Supabase: 500MB database, 2GB bandwidth/month
   - May hit limits with heavy usage

4. **Performance**
   - Image processing takes 5-10 seconds
   - Large inventory searches may be slow
   - Database queries depend on internet speed

### Best Practices

1. **Keep credentials secure**
   - Never commit `.env` to git
   - Use strong, unique keys
   - Rotate keys periodically

2. **Regular backups**
   - Export Supabase data regularly
   - Keep local copy of important data
   - Test restore process

3. **Monitor usage**
   - Check CloudWatch logs (AWS deployment)
   - Watch for error patterns
   - Monitor API rate limits

4. **Update dependencies**
   - Run `pip list --outdated` monthly
   - Update to latest compatible versions
   - Test after updates

---

## Quick Reference

### Reinstall Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Reset Virtual Environment
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Check Service Status
```bash
# Bot process
ps aux | grep "python main.py"

# Network connectivity
ping -c 3 api.telegram.org
ping -c 3 your-project.supabase.co
```

### Restart Bot
```bash
# Find process ID
ps aux | grep "python main.py"

# Kill process
kill <PID>

# Restart
python main.py
```

---

**Need more help?** Check the other documentation files or open a GitHub issue with detailed information about your problem.
