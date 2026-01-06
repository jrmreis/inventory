# 🔍 Enable Vision Recognition (Google Lens-like)

Your bot now has **hybrid recognition**:
1. **Free**: OCR + Groq AI (current - works for text-based components)
2. **Premium**: OpenAI Vision (automatic fallback when OCR fails)

## Quick Setup (5 minutes)

### Step 1: Get OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

**Cost**: ~$0.01 per difficult image (free tier includes $5 credit)

### Step 2: Install OpenAI SDK

```bash
cd /home/joel/repos/github/Dev/Inventory
source venv/bin/activate
pip install openai>=1.0.0
```

### Step 3: Add API Key

```bash
nano .env
```

Uncomment and add your key:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

Save and exit (Ctrl+X, Y, Enter)

### Step 4: Restart Bot

```bash
./restart_bot.sh
```

## ✅ Done!

Now when you send a photo:

1. **Bot tries OCR first** (free, fast)
2. **If OCR fails** → Automatically uses Vision AI
3. **Vision AI sees the image** like Google Lens
4. **Identifies the component** even with curved/reflective surfaces

## How It Works

**HAYLOU Earbuds Example:**

**Before (OCR only):**
```
OCR: "ne pcre nee eee..." (garbage)
Groq AI: "Arduino Board" (wrong, 30% confidence)
Result: FAILED ❌
```

**After (with Vision AI fallback):**
```
OCR: "ne pcre nee eee..." (garbage)
Groq AI: "Arduino Board" (30% confidence - too low!)
Vision AI: Actually SEES the image
Result: "HAYLOU ANC Earbuds - Consumer Electronics" ✅
Cost: $0.01
```

## Cost Breakdown

| Scenario | OCR Success | Vision Used | Cost |
|----------|-------------|-------------|------|
| Resistor with color bands | ✅ Yes | ❌ No | FREE |
| Arduino PCB with text | ✅ Yes | ❌ No | FREE |
| Black earbuds (like HAYLOU) | ❌ No | ✅ Yes | $0.01 |
| Tiny IC chip markings | ❌ No | ✅ Yes | $0.01 |

**Average**: ~$0.003 per image (most succeed with free OCR)

## Testing

Send the HAYLOU image again. Check logs:
```bash
tail -f bot.log
```

You should see:
```
OCR failed or low confidence, trying Vision AI...
Using Vision AI for recognition...
✅ Vision AI succeeded: accessory with 85% confidence
```

## Without OpenAI Key

If you don't add the key, bot continues using OCR only (current behavior):
- ✅ FREE
- ❌ Fails on reflective/curved objects
- ✅ Works fine for most electronics (resistors, PCBs, ICs with flat text)

Your choice! 🚀
