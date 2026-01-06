# 🔍 Vision Recognition Guide - Google Lens-like Functionality

This guide explains how to add visual component recognition to your Inventory Bot, similar to Google Lens.

## 📋 Table of Contents
- [Overview](#overview)
- [Available Options](#available-options)
- [Setup Instructions](#setup-instructions)
- [Integration Example](#integration-example)
- [Cost Comparison](#cost-comparison)

---

## Overview

Currently, your bot uses:
1. **OCR (Tesseract)** - Extracts text from images
2. **Groq AI (Llama)** - Analyzes OCR text to identify components
3. **Color Detection (OpenCV)** - Detects resistor color bands

**Vision Recognition adds:**
- Direct image analysis (no OCR needed)
- Better component identification
- Visual similarity search
- Handling of components without text markings

---

## Available Options

### Option 1: OpenAI GPT-4 Vision ⭐ **RECOMMENDED**

**Pros:**
- Best accuracy for component recognition
- Can read tiny text on chips
- Understands resistor color bands visually
- Identifies components by shape and appearance
- Easy to integrate

**Cons:**
- Paid service (~$0.01-0.03 per image)
- Requires OpenAI account

**Best for:** Maximum accuracy, professional use

---

### Option 2: Google Cloud Vision

**Pros:**
- Object detection and labeling
- OCR included
- Web entity detection (finds similar images online)
- Good for general object recognition

**Cons:**
- Not specifically trained on electronics
- Paid service
- Requires Google Cloud account

**Best for:** General purpose, when you need web search

---

### Option 3: Open Source (CLIP + Vector Search)

**Pros:**
- Free and runs locally
- Privacy-friendly
- Can build custom component database

**Cons:**
- Lower accuracy than commercial options
- Requires more setup
- Needs GPU for best performance

**Best for:** Privacy, cost savings, offline use

---

## Setup Instructions

### Using OpenAI GPT-4 Vision (Recommended)

#### 1. Get an OpenAI API Key

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-...`)

#### 2. Install Dependencies

```bash
cd /home/joel/repos/github/Dev/Inventory
source venv/bin/activate
pip install -r requirements-vision.txt
```

#### 3. Add API Key to .env

```bash
nano .env
```

Add this line:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

#### 4. Test Vision Recognition

```bash
python -c "from app.vision_recognition import VisionRecognizer; vr = VisionRecognizer(); print('Vision available:', vr.is_available())"
```

---

### Using Google Cloud Vision

#### 1. Set up Google Cloud

1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable Cloud Vision API
4. Create a service account
5. Download JSON credentials

#### 2. Install Dependencies

```bash
pip install google-cloud-vision
```

#### 3. Set Environment Variable

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

Or add to `.env`:
```
GOOGLE_VISION_API_KEY=/path/to/credentials.json
```

---

## Integration Example

### Update bot.py to Use Vision

Add this to your `handle_photo` function:

```python
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages for component recognition."""
    if not is_authorized(update.effective_user):
        await update.message.reply_text("⛔ You are not authorized.")
        return

    await update.message.reply_text("📸 Processing image... This may take a moment.")

    try:
        # Get processors
        img_proc, data_ext, _ = get_processors()

        # NEW: Try vision recognition first
        from .vision_recognition import VisionRecognizer
        vision = VisionRecognizer()

        # Download photo
        photo = await update.message.photo[-1].get_file()
        photo_path = f"/tmp/inventory_{update.effective_user.id}_{datetime.now().timestamp()}.jpg"
        await photo.download_to_drive(photo_path)

        extracted_data = None

        # Try vision recognition if available
        if vision.is_available():
            logger.info("Attempting vision recognition...")
            vision_result = vision.recognize_component(photo_path)

            if vision_result and vision_result.get('recognition_confidence', 0) > 50:
                extracted_data = vision_result
                logger.info(f"✅ Vision recognized: {vision_result.get('component_type')}")

        # Fallback to OCR + AI if vision fails or unavailable
        if not extracted_data:
            logger.info("Using OCR + AI fallback...")
            ocr_result = img_proc.process_image(photo_path)
            # ... existing OCR logic ...

        # ... rest of your existing code ...
```

---

## Cost Comparison

### OpenAI GPT-4 Vision
- **Cost:** ~$0.01-0.03 per image
- **100 components/month:** ~$1-3
- **1000 components/month:** ~$10-30

### Google Cloud Vision
- **Cost:** First 1000 images free/month
- **After:** $1.50 per 1000 images
- **100 components/month:** FREE
- **1000 components/month:** FREE

### Groq (Current)
- **Cost:** FREE
- **Limitation:** OCR-dependent, less accurate

---

## Recommendation

**For Your Use Case:**

1. **Start with Groq (current)** - It's free and working reasonably well
2. **Add OpenAI Vision for critical components** - Use it only when Groq confidence is low
3. **Hybrid approach** - Best of both worlds:
   - Try Groq first (free)
   - If confidence < 40%, use OpenAI Vision ($0.01)
   - Save money while maintaining accuracy

### Hybrid Integration Example

```python
# Try cheap method first
ocr_result = img_proc.process_image(photo_path)
groq_result = data_ext.extract_component_data(ocr_result['text'], photo_path)

# If low confidence, use premium vision
if groq_result.get('recognition_confidence', 0) < 40:
    logger.info("Low confidence, trying OpenAI Vision...")
    vision_result = vision.recognize_component(photo_path)
    if vision_result and vision_result['recognition_confidence'] > groq_result['recognition_confidence']:
        extracted_data = vision_result
    else:
        extracted_data = groq_result
else:
    extracted_data = groq_result
```

---

## Next Steps

1. ✅ **You already have**: OCR + Groq AI (working well for resistors!)
2. 🔄 **Consider adding**: OpenAI Vision for complex components
3. 💡 **Future**: Build a custom component image database for exact matching

Would you like me to:
- [ ] Integrate OpenAI Vision into your bot?
- [ ] Set up the hybrid approach (Groq + Vision fallback)?
- [ ] Create a local component image database?
- [ ] Just keep the current OCR + Groq setup?

Let me know! 🚀
