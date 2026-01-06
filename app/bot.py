"""
Telegram Bot for Electronic Components Inventory Management
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from supabase import create_client, Client

from .image_processor import ImageProcessor
from .data_extractor import ComponentDataExtractor
from .component_classifier import ComponentClassifier

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, log_level, logging.INFO)
)
logger = logging.getLogger(__name__)

# Conversation states
(WAITING_FOR_IMAGE, WAITING_FOR_MANUAL_TYPE, WAITING_FOR_MANUAL_NAME,
 WAITING_FOR_MANUAL_SPECS, WAITING_FOR_MANUAL_QUANTITY, WAITING_FOR_MANUAL_LOCATION,
 CONFIRM_COMPONENT, WAITING_FOR_SEARCH_QUERY, WAITING_FOR_USE_QUANTITY,
 WAITING_FOR_PROJECT_NAME) = range(10)

# Global variables for lazy initialization
supabase: Optional[Client] = None
image_processor = None
data_extractor = None
component_classifier = None

# Security: Allowed users
ALLOWED_USER_IDS = os.getenv("ALLOWED_USER_IDS", "").split(",")


def get_supabase() -> Client:
    """Get or create Supabase client (lazy initialization)."""
    global supabase
    if supabase is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

        supabase = create_client(supabase_url, supabase_key)
    return supabase


def get_processors():
    """Get or create processors (lazy initialization)."""
    global image_processor, data_extractor, component_classifier

    if image_processor is None:
        image_processor = ImageProcessor()
    if data_extractor is None:
        data_extractor = ComponentDataExtractor()
    if component_classifier is None:
        component_classifier = ComponentClassifier()

    return image_processor, data_extractor, component_classifier


def is_authorized(user) -> bool:
    """Check if user is authorized to use the bot."""
    if not ALLOWED_USER_IDS or ALLOWED_USER_IDS == [""]:
        logger.warning("No allowed users configured! Bot is locked.")
        return False

    user_id_str = str(user.id)
    username = f"@{user.username}" if user.username else None

    return user_id_str in ALLOWED_USER_IDS or username in ALLOWED_USER_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message."""
    user = update.effective_user

    if not is_authorized(user):
        await update.message.reply_text(
            "⛔ You are not authorized to use this bot.\n"
            f"Your user ID is: {user.id}\n"
            "Please contact the administrator to request access."
        )
        return

    welcome_message = f"""
👋 Welcome to the Electronic Components Inventory Bot, {user.first_name}!

I can help you manage your electronic components inventory using AI-powered image recognition.

📸 *What I can do:*
• Add components by taking photos (automatic recognition)
• Add components manually
• Search your inventory
• Track component usage in projects
• Alert you about low stock
• Generate inventory reports

🚀 *Quick Start:*
1. Send me a photo of a component to add it
2. Use /add for manual entry
3. Use /search to find components
4. Use /help to see all commands

Let's get started! 🎯
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message with all commands."""
    if not is_authorized(update.effective_user):
        await update.message.reply_text("⛔ You are not authorized.")
        return

    help_text = """
📚 *Available Commands:*

*Inventory Management:*
/add - Add a new component (manual entry)
/search - Search for components
/list - List all components (paginated)
/view - View component details by ID

*Stock Management:*
/use - Record component usage in a project
/adjust - Adjust component quantity
/low_stock - Show components with low stock
/location - Find components by location

*Reports & Analytics:*
/status - Inventory summary and statistics
/summary - Summary by component type
/history - Recent stock movements
/most_used - Most frequently used components

*Utility:*
/help - Show this help message
/myid - Get your Telegram user ID
/cancel - Cancel current operation

*Image Recognition:*
Just send me a photo of a component and I'll try to identify it!

💡 *Tips:*
• For best results, take clear photos with good lighting
• Include component labels and markings in the photo
• I can read resistor color codes, part numbers, and labels
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's Telegram ID."""
    user = update.effective_user
    await update.message.reply_text(
        f"👤 Your Telegram User ID: `{user.id}`\n"
        f"Username: @{user.username if user.username else 'Not set'}",
        parse_mode='Markdown'
    )


async def add_component_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start adding a component manually."""
    if not is_authorized(update.effective_user):
        await update.message.reply_text("⛔ You are not authorized.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("Resistor", callback_data="type_resistor")],
        [InlineKeyboardButton("Capacitor", callback_data="type_capacitor")],
        [InlineKeyboardButton("Microcontroller", callback_data="type_microcontroller")],
        [InlineKeyboardButton("Connector", callback_data="type_connector")],
        [InlineKeyboardButton("IC (Integrated Circuit)", callback_data="type_ic")],
        [InlineKeyboardButton("LED", callback_data="type_led")],
        [InlineKeyboardButton("Sensor", callback_data="type_sensor")],
        [InlineKeyboardButton("Other", callback_data="type_other")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📦 Let's add a new component!\n\n"
        "First, select the component type:",
        reply_markup=reply_markup
    )
    return WAITING_FOR_MANUAL_TYPE


async def component_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle component type selection."""
    query = update.callback_query
    await query.answer()

    component_type = query.data.replace("type_", "")
    context.user_data['component'] = {'component_type': component_type}

    await query.edit_message_text(
        f"✅ Type: {component_type}\n\n"
        f"Now, enter the component name or part number:\n"
        f"(e.g., '10kΩ resistor', 'Arduino Uno', 'JST connector')"
    )
    return WAITING_FOR_MANUAL_NAME


async def component_name_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle component name entry."""
    context.user_data['component']['name'] = update.message.text

    await update.message.reply_text(
        "📝 Enter technical specifications (or type 'skip'):\n\n"
        "*Examples:*\n"
        "Resistor: 10k, 5%, 0.25W\n"
        "Capacitor: 100uF, 25V, electrolytic\n"
        "Arduino: Uno R3, 5V, ATmega328P\n"
        "Connector: 2.54mm pitch, 10 pins",
        parse_mode='Markdown'
    )
    return WAITING_FOR_MANUAL_SPECS


async def component_specs_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle component specs entry."""
    specs_text = update.message.text

    if specs_text.lower() != 'skip':
        _, data_ext, _ = get_processors()
        context.user_data['component']['specifications'] = data_ext.parse_specifications(
            specs_text,
            context.user_data['component']['component_type']
        )

    await update.message.reply_text(
        "🔢 Enter the quantity you have:"
    )
    return WAITING_FOR_MANUAL_QUANTITY


async def component_quantity_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity entry."""
    try:
        quantity = int(update.message.text)
        if quantity < 0:
            raise ValueError("Quantity must be positive")

        context.user_data['component']['quantity'] = quantity

        await update.message.reply_text(
            "📍 Enter storage location (or type 'skip'):\n"
            "(e.g., 'Drawer A3', 'Box 12', 'Shelf 2-B')"
        )
        return WAITING_FOR_MANUAL_LOCATION

    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid number for quantity."
        )
        return WAITING_FOR_MANUAL_QUANTITY


async def component_location_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location entry and show confirmation."""
    location = update.message.text

    if location.lower() != 'skip':
        context.user_data['component']['storage_location'] = location

    # Show summary for confirmation
    component = context.user_data['component']
    summary = f"""
📦 *Component Summary:*

*Type:* {component.get('component_type', 'N/A')}
*Name:* {component.get('name', 'N/A')}
*Quantity:* {component.get('quantity', 0)}
*Location:* {component.get('storage_location', 'Not specified')}
*Specs:* {component.get('specifications', {})}

Confirm to save this component?
"""

    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm_yes")],
        [InlineKeyboardButton("❌ Cancel", callback_data="confirm_no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode='Markdown')
    return CONFIRM_COMPONENT


async def confirm_component(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle component confirmation and save to database."""
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_no":
        await query.edit_message_text("❌ Component not saved. Operation cancelled.")
        context.user_data.clear()
        return ConversationHandler.END

    # Save to database
    component = context.user_data['component']
    component['created_by'] = update.effective_user.id
    component['last_modified_by'] = update.effective_user.id

    try:
        db = get_supabase()
        result = db.table('components').insert(component).execute()

        component_id = result.data[0]['id']
        await query.edit_message_text(
            f"✅ Component saved successfully!\n"
            f"Component ID: {component_id}\n\n"
            f"Use /view {component_id} to view details."
        )
    except Exception as e:
        logger.error(f"Error saving component: {e}")
        await query.edit_message_text(
            f"❌ Error saving component: {str(e)}\n"
            f"Please try again later."
        )

    context.user_data.clear()
    return ConversationHandler.END


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages for component recognition."""
    if not is_authorized(update.effective_user):
        await update.message.reply_text("⛔ You are not authorized.")
        return

    await update.message.reply_text("📸 Processing image... This may take a moment.")

    try:
        # Get processors
        img_proc, data_ext, _ = get_processors()

        # Download photo
        photo = await update.message.photo[-1].get_file()
        photo_path = f"/tmp/inventory_{update.effective_user.id}_{datetime.now().timestamp()}.jpg"
        await photo.download_to_drive(photo_path)

        # Process image with OCR
        logger.info(f"Processing image for user {update.effective_user.id}")
        ocr_result = img_proc.process_image(photo_path)

        ocr_text = ocr_result.get('text', '').strip()
        colors_detected = ocr_result.get('colors')

        logger.info(f"OCR extracted {len(ocr_text)} characters")
        logger.info(f"Colors detected: {colors_detected.get('detected_colors') if colors_detected else 'None'}")

        # Initialize extracted_data
        extracted_data = None

        # Check if we should try resistor color code detection
        # Priority: If colors detected AND (no text OR minimal text)
        if colors_detected and colors_detected.get('detected_colors'):
            detected_colors = colors_detected.get('detected_colors', [])
            logger.info(f"Processing {len(detected_colors)} detected colors: {detected_colors}")

            # If we have enough colors for a resistor (3+)
            if len(detected_colors) >= 3:
                # Try to calculate resistance from colors
                from .image_processor import calculate_resistor_value
                resistance = calculate_resistor_value(detected_colors)

                if resistance:
                    # Build component data for resistor
                    extracted_data = {
                        'component_type': 'resistor',
                        'name': f'{resistance} Resistor',
                        'part_number': None,
                        'specifications': {'resistance': resistance},
                        'description': f'Resistor identified by color bands: {", ".join(detected_colors[:4])}',
                        'tags': ['resistor', 'color-coded', 'through-hole'],
                        'recognition_confidence': 65,  # Medium confidence for color detection
                    }
                    logger.info(f"✅ Resistor detected by colors: {detected_colors} = {resistance}")
                else:
                    # Colors detected but couldn't calculate value
                    logger.warning(f"Colors detected but couldn't calculate: {detected_colors}")
                    await update.message.reply_text(
                        f"🎨 I detected possible resistor colors:\n{', '.join(detected_colors)}\n\n"
                        f"But I couldn't calculate the exact resistance value.\n\n"
                        f"💡 Tip: Please use /add to enter manually, or try:\n"
                        f"• Better lighting on the color bands\n"
                        f"• Straighter angle to the resistor\n"
                        f"• Closer photo showing the bands clearly"
                    )
                    return
            elif ocr_text and len(ocr_text) < 10:
                # Some colors but not enough, and minimal text
                logger.info("Insufficient data - minimal colors and text")
                await update.message.reply_text(
                    "⚠️ Could not extract enough information from the image.\n\n"
                    f"Detected: {len(detected_colors)} color(s), {len(ocr_text)} characters\n\n"
                    "Please try:\n"
                    "• Better lighting (avoid shadows and glare)\n"
                    "• Clearer focus on labels/markings\n"
                    "• Closer photo of the component\n"
                    "• Different angle if color bands are present\n\n"
                    "Or use /add for manual entry."
                )
                return

        # If we don't have extracted_data from color detection, try OCR + AI
        if not extracted_data:
            # First try: OCR + Groq AI
            if ocr_text and len(ocr_text) >= 3:
                logger.info(f"Sending OCR to Groq AI: '{ocr_text[:100]}...'")
                extracted_data = data_ext.extract_component_data(
                    ocr_text,
                    photo_path
                )

            # If OCR failed or gave low confidence, try Vision AI
            if not extracted_data or extracted_data.get('recognition_confidence', 0) < 25:
                logger.info("OCR failed or low confidence, trying Vision AI...")

                # Try to use vision recognition
                try:
                    from .vision_recognition import VisionRecognizer
                    vision = VisionRecognizer()

                    if vision.is_available():
                        logger.info("Using Vision AI for recognition...")
                        vision_result = vision.recognize_component(photo_path)

                        if vision_result and vision_result.get('recognition_confidence', 0) > 40:
                            extracted_data = vision_result
                            logger.info(f"✅ Vision AI succeeded: {vision_result.get('component_type')} with {vision_result.get('recognition_confidence')}% confidence")
                        else:
                            logger.warning("Vision AI gave low confidence result")
                    else:
                        logger.info("Vision AI not configured (OPENAI_API_KEY not set)")
                except Exception as e:
                    logger.warning(f"Vision AI failed: {e}")

            # If still no good data, show error
            if not extracted_data or extracted_data.get('recognition_confidence', 0) < 20:
                logger.warning(f"All recognition methods failed. OCR: {len(ocr_text)} chars")
                await update.message.reply_text(
                    "⚠️ Could not identify this component.\n\n"
                    "Please try:\n"
                    "• Better lighting (natural light works best)\n"
                    "• Clearer focus on any text/markings\n"
                    "• Closer photo of labels or part numbers\n"
                    "• Clean the component if dusty\n\n"
                    "💡 Or use /add to enter the component manually."
                )
                return

        # Check if we got useful data (confidence > 20% and valid type)
        confidence = extracted_data.get('recognition_confidence', 0) if extracted_data else 0
        comp_type = extracted_data.get('component_type', 'unknown') if extracted_data else 'unknown'

        if not extracted_data or confidence < 20 or comp_type in ['unknown', 'none', '']:
            # Low confidence or no detection - show what we got and suggest manual entry
            ocr_preview = ocr_result['text'][:300] if ocr_result['text'] else "No text detected"

            # Send without markdown to avoid parsing errors with special characters
            await update.message.reply_text(
                f"❓ Low confidence detection\n\n"
                f"I detected some text but couldn't confidently identify the component.\n\n"
                f"Detected text:\n{ocr_preview}\n\n"
                f"Please use /add to enter this component manually, or try:\n"
                f"• Better lighting\n"
                f"• Different angle\n"
                f"• Closer photo of labels/markings"
            )
            return

        # Store for confirmation
        context.user_data['component'] = extracted_data
        context.user_data['component']['ocr_text'] = ocr_result['text']
        context.user_data['component']['created_by'] = update.effective_user.id
        context.user_data['component']['last_modified_by'] = update.effective_user.id

        # Show extracted data for confirmation
        specs = extracted_data.get('specifications', {})
        if specs:
            # Format specs as readable text, avoiding special markdown characters
            specs_list = [f"{k}: {v}" for k, v in specs.items()]
            specs_str = ', '.join(specs_list) if specs_list else 'None detected'
        else:
            specs_str = 'None detected'

        # Escape special markdown characters to avoid parsing errors
        def escape_markdown(text):
            """Escape markdown special characters."""
            if text is None:
                return 'N/A'
            text = str(text)
            # Escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
            return text

        comp_type = escape_markdown(extracted_data.get('component_type', 'Unknown'))
        comp_name = escape_markdown(extracted_data.get('name', 'Unknown'))
        part_num = escape_markdown(extracted_data.get('part_number', 'None'))
        specs_str = escape_markdown(specs_str)

        summary = f"""
🤖 *AI\\-Detected Component:*

*Type:* {comp_type}
*Name:* {comp_name}
*Part Number:* {part_num}
*Specs:* {specs_str}
*Confidence:* {confidence}%

Please enter the quantity you have, or type 'skip' to cancel:
"""

        await update.message.reply_text(summary, parse_mode='MarkdownV2')
        context.user_data['awaiting_quantity_for_photo'] = True

        # Clean up temp file
        os.remove(photo_path)

    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await update.message.reply_text(
            f"❌ Error processing image: {str(e)}\n"
            "Please try again or use /add for manual entry."
        )


async def handle_photo_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quantity input after photo recognition."""
    if not is_authorized(update.effective_user):
        return

    # Check if we're waiting for quantity from photo
    if not context.user_data.get('awaiting_quantity_for_photo'):
        return

    text = update.message.text.strip().lower()

    # Handle skip
    if text == 'skip':
        await update.message.reply_text("❌ Component not saved. Cancelled.")
        context.user_data.clear()
        return

    # Try to parse quantity
    try:
        quantity = int(text)
        if quantity < 0:
            raise ValueError("Quantity must be positive")

        # Get component data from context
        component = context.user_data.get('component', {})
        component['quantity'] = quantity

        # Remove fields that don't exist in database schema
        # Vision AI adds these extra fields that we don't have columns for
        component.pop('recognition_method', None)
        component.pop('visual_features', None)

        # Save to database
        db = get_supabase()
        result = db.table('components').insert(component).execute()

        component_id = result.data[0]['id']
        comp_name = component.get('name', 'Unknown')

        await update.message.reply_text(
            f"✅ Component saved successfully!\n\n"
            f"📦 {comp_name}\n"
            f"🆔 ID: {component_id}\n"
            f"📊 Quantity: {quantity}\n\n"
            f"Use /view {component_id} to see full details or /status to see inventory."
        )

        # Clear context
        context.user_data.clear()

    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid number for quantity, or type 'skip' to cancel."
        )
    except Exception as e:
        logger.error(f"Error saving photo component: {e}")
        await update.message.reply_text(
            f"❌ Error saving component: {str(e)}\n"
            "Please try again or use /add for manual entry."
        )
        context.user_data.clear()


async def search_components(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for components."""
    if not is_authorized(update.effective_user):
        await update.message.reply_text("⛔ You are not authorized.")
        return

    if not context.args:
        await update.message.reply_text(
            "🔍 Usage: /search <query>\n\n"
            "Examples:\n"
            "/search resistor\n"
            "/search arduino\n"
            "/search 10k"
        )
        return

    query = " ".join(context.args)

    try:
        db = get_supabase()
        # Search in multiple fields
        result = db.table('components').select('*').or_(
            f"name.ilike.%{query}%,"
            f"part_number.ilike.%{query}%,"
            f"component_type.ilike.%{query}%,"
            f"description.ilike.%{query}%"
        ).limit(20).execute()

        if not result.data:
            await update.message.reply_text(f"❌ No components found matching '{query}'")
            return

        response = f"🔍 *Search Results for '{query}':*\n\n"

        for comp in result.data:
            response += f"📦 *ID {comp['id']}:* {comp['name']}\n"
            response += f"   Type: {comp['component_type']}\n"
            response += f"   Quantity: {comp['quantity']}\n"
            if comp.get('storage_location'):
                response += f"   Location: {comp['storage_location']}\n"
            response += "\n"

        response += f"\nUse /view <ID> to see full details"

        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Search error: {e}")
        await update.message.reply_text(f"❌ Search failed: {str(e)}")


async def view_component(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View detailed information about a component by ID."""
    if not is_authorized(update.effective_user):
        await update.message.reply_text("⛔ You are not authorized.")
        return

    try:
        # Extract component ID from command
        if not context.args or len(context.args) == 0:
            await update.message.reply_text(
                "❌ Please provide a component ID.\n\n"
                "Usage: /view <ID>\n"
                "Example: /view 5"
            )
            return

        component_id = int(context.args[0])

        db = get_supabase()
        result = db.table('components').select('*').eq('id', component_id).execute()

        if not result.data or len(result.data) == 0:
            await update.message.reply_text(f"❌ Component with ID {component_id} not found.")
            return

        comp = result.data[0]

        # Format specifications
        specs = comp.get('specifications', {})
        if specs and isinstance(specs, dict):
            specs_str = '\n'.join([f"  • {k}: {v}" for k, v in specs.items()])
        else:
            specs_str = "  None"

        # Format tags
        tags = comp.get('tags', [])
        tags_str = ', '.join(tags) if tags else 'None'

        # Build response
        response = f"""
📦 *Component Details*

*ID:* {comp['id']}
*Type:* {comp.get('component_type', 'N/A')}
*Name:* {comp.get('name', 'N/A')}

*Manufacturer:* {comp.get('manufacturer') or 'N/A'}
*Part Number:* {comp.get('part_number') or 'N/A'}

*Specifications:*
{specs_str}

*Inventory:*
  • Quantity: {comp.get('quantity', 0)}
  • Min Quantity: {comp.get('minimum_quantity', 0)}
  • Location: {comp.get('storage_location') or 'Not specified'}

*Tags:* {tags_str}

*Description:*
{comp.get('description') or 'No description'}

*Notes:*
{comp.get('notes') or 'No notes'}

*Recognition:*
  • Confidence: {comp.get('recognition_confidence') or 'N/A'}%
  • OCR Text: {comp.get('ocr_text')[:50] + '...' if comp.get('ocr_text') else 'N/A'}

*Created:* {comp.get('created_at', 'N/A')[:10]}
*Updated:* {comp.get('updated_at', 'N/A')[:10]}
"""

        await update.message.reply_text(response, parse_mode='Markdown')

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid component ID. Please provide a number.\n\n"
            "Usage: /view <ID>\n"
            "Example: /view 5"
        )
    except Exception as e:
        logger.error(f"View component error: {e}")
        await update.message.reply_text(f"❌ Error viewing component: {str(e)}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show inventory status and statistics."""
    if not is_authorized(update.effective_user):
        await update.message.reply_text("⛔ You are not authorized.")
        return

    try:
        db = get_supabase()
        # Get summary statistics
        summary = db.table('v_inventory_summary_by_type').select('*').execute()
        low_stock = db.table('v_low_stock_components').select('*').limit(10).execute()

        total_components = sum(item['unique_components'] for item in summary.data)
        total_quantity = sum(item['total_quantity'] for item in summary.data)

        response = f"""
📊 *Inventory Status*

*Overall Statistics:*
• Unique Components: {total_components}
• Total Items: {total_quantity}
• Low Stock Items: {len(low_stock.data)}

*By Component Type:*
"""

        for item in summary.data[:10]:
            response += f"\n• {item['component_type']}: {item['unique_components']} types, {item['total_quantity']} items"

        if low_stock.data:
            response += "\n\n⚠️ *Low Stock Alert:*\n"
            for comp in low_stock.data[:5]:
                response += f"• {comp['name']}: {comp['quantity']}/{comp['minimum_quantity']}\n"

        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Status error: {e}")
        await update.message.reply_text(f"❌ Error getting status: {str(e)}")


async def low_stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show low stock components."""
    if not is_authorized(update.effective_user):
        await update.message.reply_text("⛔ You are not authorized.")
        return

    try:
        db = get_supabase()
        result = db.table('v_low_stock_components').select('*').execute()

        if not result.data:
            await update.message.reply_text("✅ All components are well-stocked!")
            return

        response = "⚠️ *Low Stock Components:*\n\n"

        for comp in result.data:
            stock_pct = comp.get('stock_level_percentage', 0) or 0
            response += f"📦 *{comp['name']}*\n"
            response += f"   ID: {comp['id']} | Type: {comp['component_type']}\n"
            response += f"   Stock: {comp['quantity']}/{comp['minimum_quantity']} ({stock_pct:.0f}%)\n"
            if comp.get('storage_location'):
                response += f"   Location: {comp['storage_location']}\n"
            response += "\n"

        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Low stock error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current operation."""
    await update.message.reply_text(
        "❌ Operation cancelled.\n"
        "Use /help to see available commands."
    )
    context.user_data.clear()
    return ConversationHandler.END


def main():
    """Start the bot."""
    # Get bot token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

    # Create application
    application = Application.builder().token(token).build()

    # Add conversation handler for adding components
    add_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_component_start)],
        states={
            WAITING_FOR_MANUAL_TYPE: [CallbackQueryHandler(component_type_selected, pattern="^type_")],
            WAITING_FOR_MANUAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, component_name_entered)],
            WAITING_FOR_MANUAL_SPECS: [MessageHandler(filters.TEXT & ~filters.COMMAND, component_specs_entered)],
            WAITING_FOR_MANUAL_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, component_quantity_entered)],
            WAITING_FOR_MANUAL_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, component_location_entered)],
            CONFIRM_COMPONENT: [CallbackQueryHandler(confirm_component, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("myid", myid_command))
    application.add_handler(CommandHandler("view", view_component))
    application.add_handler(CommandHandler("search", search_components))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("low_stock", low_stock_command))
    application.add_handler(add_conv_handler)

    # Handler for quantity input after photo recognition (must be before photo handler)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_photo_quantity
    ))

    # Photo handler for image recognition
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Start bot
    logger.info("🤖 Inventory Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
