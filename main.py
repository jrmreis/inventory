"""
Electronic Components Inventory Bot - Main Entry Point
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=os.getenv('LOG_LEVEL', 'INFO'),
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'GROQ_API_KEY',
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please check your .env file")
        sys.exit(1)

    # Check ALLOWED_USER_IDS
    if not os.getenv('ALLOWED_USER_IDS'):
        logger.warning("⚠️  ALLOWED_USER_IDS is not set. Bot will be locked to all users.")
        logger.warning("   Set ALLOWED_USER_IDS in .env to enable access.")

    logger.info("✅ Environment configuration verified")


def create_temp_directory():
    """Create temporary directory for file processing."""
    temp_dir = os.getenv('TEMP_DIR', '/tmp/inventory_bot')

    try:
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"✅ Temporary directory ready: {temp_dir}")
    except Exception as e:
        logger.error(f"Failed to create temp directory: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    logger.info("🚀 Starting Electronic Components Inventory Bot...")

    # Check environment
    check_environment()

    # Create temp directory
    create_temp_directory()

    # Import and run bot
    try:
        from app.bot import main as bot_main
        bot_main()
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
