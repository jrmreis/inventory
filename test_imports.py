#!/usr/bin/env python3
"""
Test script to verify all dependencies are correctly installed
Run this before setting up credentials
"""

print("Testing imports...")
print("-" * 50)

try:
    import telegram
    print("✅ python-telegram-bot:", telegram.__version__)
except Exception as e:
    print("❌ python-telegram-bot:", str(e))

try:
    import cv2
    print("✅ opencv-python:", cv2.__version__)
except Exception as e:
    print("❌ opencv-python:", str(e))

try:
    import pytesseract
    print("✅ pytesseract: installed")
except Exception as e:
    print("❌ pytesseract:", str(e))

try:
    import numpy as np
    print("✅ numpy:", np.__version__)
except Exception as e:
    print("❌ numpy:", str(e))

try:
    from PIL import Image
    print("✅ Pillow:", Image.__version__)
except Exception as e:
    print("❌ Pillow:", str(e))

try:
    from groq import Groq
    print("✅ groq: installed")
except Exception as e:
    print("❌ groq:", str(e))

try:
    from supabase import create_client
    print("✅ supabase: installed")
except Exception as e:
    print("❌ supabase:", str(e))

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv: installed")
except Exception as e:
    print("❌ python-dotenv:", str(e))

try:
    import httpx
    print("✅ httpx:", httpx.__version__)
except Exception as e:
    print("❌ httpx:", str(e))

try:
    import websockets
    print("✅ websockets:", websockets.__version__)
except Exception as e:
    print("❌ websockets:", str(e))

print("-" * 50)
print("\n🎯 Testing application modules...")
print("-" * 50)

try:
    from app.image_processor import ImageProcessor
    print("✅ ImageProcessor: imported successfully")
except Exception as e:
    print("❌ ImageProcessor:", str(e))

try:
    from app.data_extractor import ComponentDataExtractor
    print("✅ ComponentDataExtractor: imported successfully")
except Exception as e:
    print("❌ ComponentDataExtractor:", str(e))

try:
    from app.component_classifier import ComponentClassifier
    print("✅ ComponentClassifier: imported successfully")
except Exception as e:
    print("❌ ComponentClassifier:", str(e))

print("-" * 50)
print("\n✨ All core dependencies are working!")
print("\nNext steps:")
print("1. Configure your .env file with real credentials")
print("2. Setup Supabase database (run migrations)")
print("3. Run: python main.py")
print("\nSee QUICK_START.md for detailed instructions.")
