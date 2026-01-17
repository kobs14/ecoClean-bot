import os
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from ..util.menus import STATUS_MENU, EMPLOYEE_MENU
from ..logger_config import get_logger, log_function

# Initialize logger
logger = get_logger(__name__)

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://api:5000")

# Define conversation states
(
    SELECTING_STATUS,
    CUSTOM_STATUS_MESSAGE,
    CUSTOM_STATUS_DURATION,
    CONFIRMING_STATUS
) = range(4)


@log_function()
async def start_status_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the status update process"""
    user_id = update.effective_user.id
    logger.info(f"Starting status update for user {user_id}")

    # Set up storage for status data
    if "status_data" not in context.user_data:
        context.user_data["status_data"] = {
            "current_status": "unknown",
            "status_message": "",
            "status_until": None
        }

    # Handle callback query
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            STATUS_MENU.text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(STATUS_MENU.buttons)
        )
    else:
        await update.message.reply_text(
            STATUS_MENU.text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(STATUS_MENU.buttons)
        )

    return SELECTING_STATUS


@log_function()
async def handle_status_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the selected status"""
    query = update.callback_query
    await query.answer()

    # Extract status from callback data
    status_type = query.data.split(':')[1]

    # Store the status
    context.user_data["status_data"]["current_status"] = status_type

    if status_type == "custom":
        await query.message.reply_text(
            "Please enter a custom status message (e.g., 'In a meeting', 'Out for supplies'):",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Cancel", callback_data="status:cancel")
            ]])
        )
        return CUSTOM_STATUS_MESSAGE

    # Set default messages for standard statuses
    status_messages = {
        "available": "I'm available for new assignments",
        "on_job": "Currently working on a job",
        "offline": "Offline - not available",
        "break": "On break"
    }

    context.user_data["status_data"]["status_message"] = status_messages.get(status_type, "")

    # For standard statuses, ask for confirmation right away
    return await show_status_confirmation(update, context)


@log_function()
async def handle_custom_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process custom status message input"""
    # Handle cancel button
    if update.callback_query and update.callback_query.data == "status:cancel":
        await update.callback_query.answer()
        return await start_status_update(update, context)

    # Store custom message
    context.user_data["status_data"]["status_message"] = update.message.text

    # Ask for duration
    duration_keyboard = [
        [
            InlineKeyboardButton("1 hour", callback_data="duration:1"),
            InlineKeyboardButton("2 hours", callback_data="duration:2"),
            InlineKeyboardButton("4 hours", callback_data="duration:4")
        ],
        [
            InlineKeyboardButton("Rest of day", callback_data="duration:eod"),
            InlineKeyboardButton("Custom", callback_data="duration:custom")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="status:back_to_message")
        ]
    ]

    await update.message.reply_text(
        "How long will you be in this status?",
        reply_markup=InlineKeyboardMarkup(duration_keyboard)
    )

    return CUSTOM_STATUS_DURATION


@log_function()
async def handle_duration_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the selected duration for custom status"""
    query = update.callback_query
    await query.answer()

    duration_type = query.data.split(':')[1]

    now = datetime.now()

    if duration_type == "eod":
        # Set until end of day (5pm or current time if after 5pm)
        eod = now.replace(hour=17, minute=0, second=0, microsecond=0)
        if now > eod:
            eod = eod + timedelta(days=1)
        context.user_data["status_data"]["status_until"] = eod
    elif duration_type == "custom":
        await query.message.reply_text(
            "Please enter how many hours this status should last (e.g., '3.5'):",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Cancel", callback_data="duration:cancel")
            ]])
        )
        return CUSTOM_STATUS_DURATION
    elif duration_type == "back_to_message":
        await query.message.reply_text(
            "Please enter a custom status message:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Cancel", callback_data="status:cancel")
            ]])
        )
        return CUSTOM_STATUS_MESSAGE
    else:
        # Convert to hours and add to current time
        try:
            hours = float(duration_type)
            context.user_data["status_data"]["status_until"] = now + timedelta(hours=hours)
        except ValueError:
            # Handle invalid input
            await query.message.reply_text("Invalid duration. Please try again.")
            return CUSTOM_STATUS_DURATION

    return await show_status_confirmation(update, context)


@log_function()
async def handle_custom_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process custom duration input"""
    # Handle cancel button
    if update.callback_query and update.callback_query.data == "duration:cancel":
        await update.callback_query.answer()
        # Go back to the duration selection
        duration_keyboard = [
            [
                InlineKeyboardButton("1 hour", callback_data="duration:1"),
                InlineKeyboardButton("2 hours", callback_data="duration:2"),
                InlineKeyboardButton("4 hours", callback_data="duration:4")
            ],
            [
                InlineKeyboardButton("Rest of day", callback_data="duration:eod"),
                InlineKeyboardButton("Custom", callback_data="duration:custom")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="status:back_to_message")
            ]
        ]

        await update.callback_query.message.reply_text(
            "How long will you be in this status?",
            reply_markup=InlineKeyboardMarkup(duration_keyboard)
        )
        return CUSTOM_STATUS_DURATION

    try:
        # Parse the hours
        hours = float(update.message.text)
        if hours <= 0:
            await update.message.reply_text("Please enter a positive number. Try again:")
            return CUSTOM_STATUS_DURATION

        # Calculate end time
        now = datetime.now()
        context.user_data["status_data"]["status_until"] = now + timedelta(hours=hours)

        # Show confirmation
        return await show_status_confirmation(update, context)

    except ValueError:
        await update.message.reply_text("Please enter a valid number of hours:")
        return CUSTOM_STATUS_DURATION


@log_function()
async def show_status_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show status confirmation screen"""
    status_data = context.user_data["status_data"]
    status_type = status_data["current_status"]
    status_message = status_data["status_message"]
    status_until = status_data["status_until"]

    # Format status for display
    status_labels = {
        "available": "🟢 Available",
        "on_job": "🟠 On Job",
        "offline": "🔴 Offline",
        "break": "🍃 Break",
        "custom": "📅 Custom"
    }

    status_label = status_labels.get(status_type, "Unknown")

    # Create confirmation message
    if status_type == "custom":
        confirmation = (
            f"*Status Update Confirmation*\n\n"
            f"Status: {status_label}\n"
            f"Message: \"{status_message}\"\n"
        )

        if status_until:
            confirmation += f"Duration: Until {status_until.strftime('%I:%M %p')}\n"
    else:
        confirmation = (
            f"*Status Update Confirmation*\n\n"
            f"Status: {status_label}\n"
        )

    confirmation += "\nConfirm this status update?"

    # Create confirmation keyboard
    confirm_keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="status_confirm:yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="status_confirm:no")
        ]
    ]

    # Handle different update types
    if update.callback_query:
        await update.callback_query.message.reply_text(
            confirmation,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(confirm_keyboard)
        )
    else:
        await update.message.reply_text(
            confirmation,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(confirm_keyboard)
        )

    return CONFIRMING_STATUS


@log_function()
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the status confirmation"""
    query = update.callback_query
    await query.answer()

    choice = query.data.split(':')[1]

    if choice == "no":
        # User cancelled the status update
        await query.message.reply_text(
            "Status update cancelled. Returning to the main menu.",
            reply_markup=InlineKeyboardMarkup(EMPLOYEE_MENU.buttons)
        )
        return ConversationHandler.END

    # User confirmed the status update
    status_data = context.user_data["status_data"]

    try:
        # Here you would update the status in your backend
        user_id = update.effective_user.id
        status_type = status_data["current_status"]
        status_message = status_data["status_message"]
        status_until = status_data["status_until"]

        logger.info(f"Updating status for user {user_id}: {status_type} - {status_message}")

        # Create API request body
        api_data = {
            "user_id": str(user_id),
            "status": status_type,
            "message": status_message,
            "valid_until": status_until.isoformat() if status_until else None
        }

        # Here you would make an API call to your backend
        # Example (commented out):
        # response = requests.post(f"{BACKEND_API_URL}/status/update", json=api_data)
        # if response.status_code != 200:
        #     logger.error(f"API error: {response.status_code} - {response.text}")
        #     raise Exception("API Error")

        # Status emoji for display
        status_emojis = {
            "available": "🟢",
            "on_job": "🟠",
            "offline": "🔴",
            "break": "🍃",
            "custom": "📅"
        }

        status_emoji = status_emojis.get(status_type, "")

        # Show success message
        success_message = f"✅ Status updated successfully to {status_emoji} "

        if status_type == "custom":
            success_message += f"Custom: \"{status_message}\""
        else:
            status_labels = {
                "available": "Available",
                "on_job": "On Job",
                "offline": "Offline",
                "break": "On Break"
            }
            success_message += status_labels.get(status_type, "Unknown")

        if status_until:
            success_message += f"\nActive until: {status_until.strftime('%I:%M %p')}"

        await query.message.reply_text(
            success_message,
            reply_markup=InlineKeyboardMarkup(EMPLOYEE_MENU.buttons)
        )

        # Clean up user data
        if "status_data" in context.user_data:
            del context.user_data["status_data"]

        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error updating status: {str(e)}")
        await query.message.reply_text(
            "❌ There was an error updating your status. Please try again later.",
            reply_markup=InlineKeyboardMarkup(EMPLOYEE_MENU.buttons)
        )
        return ConversationHandler.END


@log_function()
async def cancel_status_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the status update process"""
    # Clear user data
    if "status_data" in context.user_data:
        del context.user_data["status_data"]

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            "Status update cancelled. Returning to the main menu.",
            reply_markup=EMPLOYEE_MENU.get_keyboard_markup(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "Status update cancelled. Returning to the main menu.",
            reply_markup=EMPLOYEE_MENU.get_keyboard_markup(),
            parse_mode='Markdown'
        )

    return ConversationHandler.END


# Create the conversation handler for status updates
status_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_status_update, pattern=r"^status:change$"),
        CommandHandler("status", start_status_update)
    ],
    states={
        SELECTING_STATUS: [
            CallbackQueryHandler(handle_status_selection, pattern=r"^status:"),
            CallbackQueryHandler(cancel_status_update, pattern=r"^menu:employee$")
        ],
        CUSTOM_STATUS_MESSAGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_message),
            CallbackQueryHandler(start_status_update, pattern=r"^status:cancel$")
        ],
        CUSTOM_STATUS_DURATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_duration),
            CallbackQueryHandler(handle_duration_selection, pattern=r"^duration:"),
            CallbackQueryHandler(handle_custom_message, pattern=r"^status:back_to_message$")
        ],
        CONFIRMING_STATUS: [
            CallbackQueryHandler(handle_confirmation, pattern=r"^status_confirm:")
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel_status_update),
        CallbackQueryHandler(cancel_status_update, pattern=r"^menu:employee$")
    ]
)