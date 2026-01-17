import os
import json
import requests
import uuid
from typing import Dict, Optional, List, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from ..util.menus import EMPLOYEE_MENU
from ..logger_config import get_logger, log_function

# Define conversation states
(
    ASKING_MATERIAL_TYPE,
    ASKING_MATERIAL_QUANTITY,
    ASKING_PRIORITY,
    ASKING_NOTES,
    CONFIRM_SUBMIT,
    CONFIRM_CANCEL,
) = range(6)

# State sequence for navigation
STATE_SEQUENCE = [
    ASKING_MATERIAL_TYPE,
    ASKING_MATERIAL_QUANTITY,
    ASKING_PRIORITY,
    ASKING_NOTES,
    CONFIRM_SUBMIT
]

# API URL from environment variables
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://api:5000")

# Material type options
MATERIAL_TYPES = [
    "Cleaning Solution",
    "Disinfectant",
    "Vacuum Parts",
    "Scrubber Parts",
    "Floor Pads",
    "Mops/Brushes",
    "Safety Equipment",
    "Other"
]

# Priority levels
PRIORITY_LEVELS = ["Low", "Medium", "High", "Urgent"]

# Initialize logger
logger = get_logger(__name__)


class MaterialRequestData:
    """Class to store material request data during conversation"""

    def __init__(self, account_id: str):
        self.account_id = account_id
        self.material_type = ""
        self.material_quantity = ""
        self.priority = ""
        self.notes = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert material request data to dictionary for API request"""
        data = {
            "account_id": self.account_id,
            "material_type": self.material_type,
            "material_quantity": self.material_quantity,
            "priority": self.priority,
        }

        # Add optional fields if available
        if self.notes:
            data["notes"] = self.notes

        return data


def get_nav_keyboard(current_state: int, include_cancel: bool = True) -> InlineKeyboardMarkup:
    """Generate navigation keyboard based on current state"""
    buttons = []

    # Only add Back button if not in first state
    if current_state > ASKING_MATERIAL_TYPE:
        back_button = InlineKeyboardButton("⬅️ Back", callback_data="nav:back")
        buttons.append(back_button)

    # Always add Cancel button
    if include_cancel:
        cancel_button = InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")
        buttons.append(cancel_button)

    # Create row of buttons
    keyboard = [buttons]
    return InlineKeyboardMarkup(keyboard)


@log_function()
async def start_material_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the material request submission process"""
    user_id = update.effective_user.id
    logger.info(f"Starting material request submission for user {user_id}")

    # Initialize or reset data storage in context
    context.user_data["material_request"] = MaterialRequestData(str(user_id))

    # Keep track of current state for navigation
    context.user_data["current_state"] = ASKING_MATERIAL_TYPE

    # Create material type keyboard
    material_keyboard = []
    for i in range(0, len(MATERIAL_TYPES), 2):
        row = []
        row.append(InlineKeyboardButton(MATERIAL_TYPES[i], callback_data=f"material:{MATERIAL_TYPES[i]}"))
        if i + 1 < len(MATERIAL_TYPES):
            row.append(InlineKeyboardButton(MATERIAL_TYPES[i + 1], callback_data=f"material:{MATERIAL_TYPES[i + 1]}"))
        material_keyboard.append(row)

    # Add navigation buttons
    nav_buttons = []
    nav_buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel"))
    material_keyboard.append(nav_buttons)

    # Handle callback query if this was triggered by a button
    if update.callback_query:
        await update.callback_query.answer()
        query = update.callback_query
        await query.message.reply_text(
            "📦 *New Material Request*\n\n"
            "Let's collect the details about the materials you need.\n\n"
            "Please select the type of material:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(material_keyboard)
        )
    else:
        await update.message.reply_text(
            "📦 *New Material Request*\n\n"
            "Let's collect the details about the materials you need.\n\n"
            "Please select the type of material:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(material_keyboard)
        )

    return ASKING_MATERIAL_TYPE


@log_function()
async def material_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle material type selection"""
    query = update.callback_query
    await query.answer()

    user_data = context.user_data["material_request"]
    material_type = query.data.split(':')[1]
    user_data.material_type = material_type

    # Handle "Other" option - ask for specific type
    if material_type == "Other":
        await query.message.reply_text(
            "Please specify the type of material you need:",
            reply_markup=get_nav_keyboard(ASKING_MATERIAL_TYPE)
        )
        return ASKING_MATERIAL_TYPE

    # Update current state and move to quantity
    context.user_data["current_state"] = ASKING_MATERIAL_QUANTITY

    await query.message.reply_text(
        f"You selected: {material_type}\n\n"
        "Please specify the quantity needed (e.g., '5 bottles', '2 boxes', '1 set'):",
        reply_markup=get_nav_keyboard(ASKING_MATERIAL_QUANTITY)
    )

    return ASKING_MATERIAL_QUANTITY


@log_function()
async def material_type_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom material type input for 'Other' option"""
    user_data = context.user_data["material_request"]
    user_data.material_type = f"Other: {update.message.text}"

    # Update current state
    context.user_data["current_state"] = ASKING_MATERIAL_QUANTITY

    await update.message.reply_text(
        f"Custom material type: {user_data.material_type}\n\n"
        "Please specify the quantity needed (e.g., '5 bottles', '2 boxes', '1 set'):",
        reply_markup=get_nav_keyboard(ASKING_MATERIAL_QUANTITY)
    )

    return ASKING_MATERIAL_QUANTITY


@log_function()
async def material_quantity_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the material quantity input"""
    user_data = context.user_data["material_request"]
    user_data.material_quantity = update.message.text

    # Update current state
    context.user_data["current_state"] = ASKING_PRIORITY

    # Create priority keyboard
    priority_keyboard = []
    for i in range(0, len(PRIORITY_LEVELS), 2):
        row = []
        row.append(InlineKeyboardButton(PRIORITY_LEVELS[i], callback_data=f"priority:{PRIORITY_LEVELS[i]}"))
        if i + 1 < len(PRIORITY_LEVELS):
            row.append(InlineKeyboardButton(PRIORITY_LEVELS[i + 1], callback_data=f"priority:{PRIORITY_LEVELS[i + 1]}"))
        priority_keyboard.append(row)

    # Add navigation buttons
    nav_buttons = []
    nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data="nav:back"))
    nav_buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel"))
    priority_keyboard.append(nav_buttons)

    await update.message.reply_text(
        "What priority level would you assign to this request?",
        reply_markup=InlineKeyboardMarkup(priority_keyboard)
    )

    return ASKING_PRIORITY


@log_function()
async def priority_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle priority level selection"""
    query = update.callback_query
    await query.answer()

    user_data = context.user_data["material_request"]
    priority = query.data.split(':')[1]
    user_data.priority = priority

    # Update current state
    context.user_data["current_state"] = ASKING_NOTES

    # Create notes keyboard with Continue option
    notes_keyboard = [
        [InlineKeyboardButton("Continue Without Notes", callback_data="notes:skip")],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="nav:back"),
            InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")
        ]
    ]

    await query.message.reply_text(
        "Any additional notes about this material request? (e.g., specific brand, urgency reason)\n\n"
        "Type your notes or click 'Continue Without Notes':",
        reply_markup=InlineKeyboardMarkup(notes_keyboard)
    )

    return ASKING_NOTES


@log_function()
async def notes_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle notes input"""
    user_data = context.user_data["material_request"]

    # Check if this is a text message or callback query
    if update.message:
        notes = update.message.text
        user_data.notes = notes
    # No else needed as callback handler will be separate

    # Update current state
    context.user_data["current_state"] = CONFIRM_SUBMIT

    # Show summary for confirmation
    report_data = user_data.to_dict()
    summary = (
        "📦 *Material Request Summary*\n\n"
        f"🧹 *Material Type:* {report_data['material_type']}\n"
        f"🔢 *Quantity:* {report_data['material_quantity']}\n"
        f"⚠️ *Priority:* {report_data['priority']}\n"
    )

    if user_data.notes:
        summary += f"📌 *Notes:* {user_data.notes}\n"

    summary += "\nIs this information correct? Submit your request or make changes:"

    confirmation_keyboard = [
        [InlineKeyboardButton("✅ Submit Request", callback_data="request:submit")],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="nav:back"),
            InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")
        ]
    ]

    if update.message:
        await update.message.reply_text(
            summary,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(confirmation_keyboard)
        )
    else:
        # For callback queries
        await update.callback_query.message.reply_text(
            summary,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(confirmation_keyboard)
        )

    return CONFIRM_SUBMIT


@log_function()
async def notes_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle notes skip button"""
    query = update.callback_query
    await query.answer()

    choice = query.data.split(':')[1]

    if choice == "skip":
        user_data = context.user_data["material_request"]
        user_data.notes = ""  # Empty notes

        # Proceed to confirmation
        context.user_data["current_state"] = CONFIRM_SUBMIT

        # Show summary for confirmation
        report_data = user_data.to_dict()
        summary = (
            "📦 *Material Request Summary*\n\n"
            f"🧹 *Material Type:* {report_data['material_type']}\n"
            f"🔢 *Quantity:* {report_data['material_quantity']}\n"
            f"⚠️ *Priority:* {report_data['priority']}\n"
        )

        summary += "\nIs this information correct? Submit your request or make changes:"

        confirmation_keyboard = [
            [InlineKeyboardButton("✅ Submit Request", callback_data="request:submit")],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="nav:back"),
                InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")
            ]
        ]

        await query.message.reply_text(
            summary,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(confirmation_keyboard)
        )

        return CONFIRM_SUBMIT

    return ASKING_NOTES


@log_function()
async def submit_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle material request submission"""
    query = update.callback_query
    await query.answer()

    action = query.data.split(':')[1]

    if action == "cancel":
        # Confirm cancellation
        await confirm_cancellation(update, context)
        return CONFIRM_CANCEL

    # Proceed with submission
    user_data = context.user_data["material_request"]

    progress_message = await query.message.reply_text("Submitting your material request... Please wait.")

    try:
        # Submit request to backend API
        logger.info(f"Submitting material request to API: {BACKEND_API_URL}/material-request/")

        # Convert data to API format
        api_data = user_data.to_dict()

        # Send request to create material request
        response = requests.post(
            f"{BACKEND_API_URL}/material-request/",
            json=api_data
        )

        if response.status_code != 201:
            logger.error(f"API error: {response.status_code} - {response.text}")
            await progress_message.edit_text(
                "❌ Error submitting request. Please try again later.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Return to Menu", callback_data="menu:employee")]
                ])
            )
            return ConversationHandler.END

        # Get request ID from response
        request_id = response.json().get("request_id", str(uuid.uuid4()))  # Fallback for demo

        # Success message
        success_message = (
            "✅ *Material Request Submitted Successfully!*\n\n"
            f"Thank you for submitting your request for {user_data.material_type}.\n"
            f"Your request ID is: {request_id}\n"
            f"Priority level: {user_data.priority}\n\n"
            "You will be notified when your request is processed."
        )

        await progress_message.edit_text(
            success_message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Return to Menu", callback_data="menu:employee")]
            ])
        )

        # Clear data
        if "material_request" in context.user_data:
            del context.user_data["material_request"]
        if "current_state" in context.user_data:
            del context.user_data["current_state"]

        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error during request submission: {str(e)}")
        await progress_message.edit_text(
            "❌ Error submitting request. Please try again later.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Return to Menu", callback_data="menu:employee")]
            ])
        )
        return ConversationHandler.END


@log_function()
async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle navigation buttons (back/cancel)"""
    query = update.callback_query
    await query.answer()

    action = query.data.split(':')[1]

    if action == "cancel":
        # Confirm cancellation
        return await confirm_cancellation(update, context)

    elif action == "back":
        # Go back to previous state
        current_state = context.user_data.get("current_state", ASKING_MATERIAL_TYPE)
        current_index = STATE_SEQUENCE.index(current_state)

        if current_index > 0:
            new_state = STATE_SEQUENCE[current_index - 1]
            context.user_data["current_state"] = new_state

            # Display appropriate message for new state
            return await go_to_state(update, context, new_state)

    # Default fallback
    return context.user_data.get("current_state", ASKING_MATERIAL_TYPE)


@log_function()
async def go_to_state(update: Update, context: ContextTypes.DEFAULT_TYPE, state: int) -> int:
    """Navigate to a specific state with appropriate prompts"""
    query = update.callback_query
    user_data = context.user_data["material_request"]

    if state == ASKING_MATERIAL_TYPE:
        # Create material type keyboard
        material_keyboard = []
        for i in range(0, len(MATERIAL_TYPES), 2):
            row = []
            row.append(InlineKeyboardButton(MATERIAL_TYPES[i], callback_data=f"material:{MATERIAL_TYPES[i]}"))
            if i + 1 < len(MATERIAL_TYPES):
                row.append(
                    InlineKeyboardButton(MATERIAL_TYPES[i + 1], callback_data=f"material:{MATERIAL_TYPES[i + 1]}"))
            material_keyboard.append(row)

        # Add navigation buttons
        nav_buttons = []
        nav_buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel"))
        material_keyboard.append(nav_buttons)

        await query.message.reply_text(
            f"Let's edit the material type.\n\nCurrent type: {user_data.material_type or 'Not set'}\n\nPlease select a material type:",
            reply_markup=InlineKeyboardMarkup(material_keyboard)
        )
        return ASKING_MATERIAL_TYPE

    elif state == ASKING_MATERIAL_QUANTITY:
        await query.message.reply_text(
            f"Let's edit the quantity.\n\nCurrent quantity: {user_data.material_quantity or 'Not set'}\n\nPlease specify the quantity needed:",
            reply_markup=get_nav_keyboard(state)
        )
        return ASKING_MATERIAL_QUANTITY

    elif state == ASKING_PRIORITY:
        # Create priority keyboard
        priority_keyboard = []
        for i in range(0, len(PRIORITY_LEVELS), 2):
            row = []
            row.append(InlineKeyboardButton(PRIORITY_LEVELS[i], callback_data=f"priority:{PRIORITY_LEVELS[i]}"))
            if i + 1 < len(PRIORITY_LEVELS):
                row.append(
                    InlineKeyboardButton(PRIORITY_LEVELS[i + 1], callback_data=f"priority:{PRIORITY_LEVELS[i + 1]}"))
            priority_keyboard.append(row)

        # Add navigation buttons
        nav_buttons = []
        nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data="nav:back"))
        nav_buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel"))
        priority_keyboard.append(nav_buttons)

        await query.message.reply_text(
            f"Let's change the priority level.\n\nCurrent priority: {user_data.priority or 'Not set'}\n\nSelect a priority level:",
            reply_markup=InlineKeyboardMarkup(priority_keyboard)
        )
        return ASKING_PRIORITY

    elif state == ASKING_NOTES:
        # Create notes keyboard with Continue option
        notes_keyboard = [
            [InlineKeyboardButton("Continue Without Notes", callback_data="notes:skip")],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="nav:back"),
                InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")
            ]
        ]

        await query.message.reply_text(
            f"Let's edit the notes.\n\nCurrent notes: {user_data.notes or 'None'}\n\nPlease enter any additional notes or click 'Continue Without Notes':",
            reply_markup=InlineKeyboardMarkup(notes_keyboard)
        )
        return ASKING_NOTES

    # Default
    return state


@log_function()
async def confirm_cancellation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask user to confirm they want to cancel the request"""
    query = update.callback_query

    confirmation_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Yes, Cancel Request", callback_data="cancel:confirm"),
            InlineKeyboardButton("No, Continue Request", callback_data="cancel:continue")
        ]
    ])

    await query.message.reply_text(
        "❓ *Are you sure you want to cancel this material request?*\n\n"
        "All entered information will be lost.",
        parse_mode='Markdown',
        reply_markup=confirmation_keyboard
    )

    return CONFIRM_CANCEL


@log_function()
async def handle_cancel_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the cancellation confirmation response"""
    query = update.callback_query
    await query.answer()

    choice = query.data.split(':')[1]

    if choice == "confirm":
        # Clear data
        if "material_request" in context.user_data:
            del context.user_data["material_request"]
        if "current_state" in context.user_data:
            del context.user_data["current_state"]

        await query.message.reply_text(
            "Material request cancelled. Returning to main menu."
        )

        # Return to menu
        await query.message.reply_text(
            EMPLOYEE_MENU.text,
            reply_markup=EMPLOYEE_MENU.get_keyboard_markup(),
            parse_mode='Markdown'
        )

        return ConversationHandler.END

    else:  # Continue
        # Return to previous state
        current_state = context.user_data.get("current_state", ASKING_MATERIAL_TYPE)
        await query.message.reply_text(
            "Let's continue with your material request."
        )
        return await go_to_state(update, context, current_state)


@log_function()
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command"""
    # Clear data
    if "material_request" in context.user_data:
        del context.user_data["material_request"]
    if "current_state" in context.user_data:
        del context.user_data["current_state"]

    await update.message.reply_text(
        "Material request cancelled. Returning to main menu."
    )

    # Return to menu
    await update.message.reply_text(
        EMPLOYEE_MENU.text,
        reply_markup=EMPLOYEE_MENU.get_keyboard_markup(),
        parse_mode='Markdown'
    )

    return ConversationHandler.END


# Create the conversation handler
material_request_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_material_request, pattern=r"^material:request$"),
        CommandHandler("material", start_material_request)
    ],
    states={
        ASKING_MATERIAL_TYPE: [
            CallbackQueryHandler(material_type_selected, pattern=r"^material:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, material_type_provided),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        ASKING_MATERIAL_QUANTITY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, material_quantity_provided),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        ASKING_PRIORITY: [
            CallbackQueryHandler(priority_selected, pattern=r"^priority:"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        ASKING_NOTES: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, notes_provided),
            CallbackQueryHandler(notes_choice, pattern=r"^notes:"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        CONFIRM_SUBMIT: [
            CallbackQueryHandler(submit_request, pattern=r"^request:"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        CONFIRM_CANCEL: [
            CallbackQueryHandler(handle_cancel_confirmation, pattern=r"^cancel:")
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)