# handlers/employee/job_report.py
import os
import json
import requests
import uuid
from io import BytesIO
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
    ASKING_JOB_DESCRIPTION,
    ASKING_CLIENT_NAME,
    ASKING_CLIENT_CONTACT,
    ASKING_AMOUNT,
    ASKING_PAYMENT_METHOD,
    ASKING_PHOTO,
    ASKING_NOTES,
    CONFIRM_SUBMIT,
    CONFIRM_CANCEL,  # New state for cancel confirmation
) = range(9)

# State sequence for navigation
STATE_SEQUENCE = [
    ASKING_JOB_DESCRIPTION,
    ASKING_CLIENT_NAME,
    ASKING_CLIENT_CONTACT,
    ASKING_AMOUNT,
    ASKING_PAYMENT_METHOD,
    ASKING_PHOTO,
    ASKING_NOTES,
    CONFIRM_SUBMIT
]

# API URL from environment variables
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://api:5000")

# Payment method options
PAYMENT_METHODS = ["Cash", "Credit Card", "Check", "Bank Transfer", "Other"]

# Initialize logger
logger = get_logger(__name__)


class JobReportData:
    """Class to store job report data during conversation"""

    def __init__(self, account_id: str):
        self.account_id = account_id
        self.job_description = ""
        self.client_name = ""
        self.client_contact = ""
        self.amount_received_dollars = 0.0
        self.payment_method = ""
        self.latitude = None
        self.longitude = None
        self.notes = ""
        self.job_status = "completed"
        self.photos: List[BytesIO] = []
        self.photo_filenames: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert job report data to dictionary for API request"""
        data = {
            "account_id": self.account_id,
            "job_description": self.job_description,
            "client_name": self.client_name,
            "client_contact": self.client_contact,
            "amount_received_dollars": self.amount_received_dollars,
            "payment_method": self.payment_method,
            "job_status": self.job_status
        }

        # Add optional fields if available
        if self.latitude is not None:
            data["latitude"] = self.latitude
        if self.longitude is not None:
            data["longitude"] = self.longitude
        if self.notes:
            data["notes"] = self.notes

        return data


def get_nav_keyboard(current_state: int, include_cancel: bool = True) -> InlineKeyboardMarkup:
    """Generate navigation keyboard based on current state"""
    buttons = []

    # Only add Back button if not in first state
    if current_state > ASKING_JOB_DESCRIPTION:
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
async def start_job_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the job report submission process"""
    user_id = update.effective_user.id
    logger.info(f"Starting job report submission for user {user_id}")

    # Initialize or reset data storage in context
    context.user_data["job_report"] = JobReportData(str(user_id))

    # Keep track of current state for navigation
    context.user_data["current_state"] = ASKING_JOB_DESCRIPTION

    # Handle callback query if this was triggered by a button
    if update.callback_query:
        await update.callback_query.answer()
        query = update.callback_query
        await query.message.reply_text(
            "📋 *New Job Report*\n\n"
            "Let's collect the details about this job.\n\n"
            "Please describe the job you completed:",
            parse_mode='Markdown',
            reply_markup=get_nav_keyboard(ASKING_JOB_DESCRIPTION)
        )
    else:
        await update.message.reply_text(
            "📋 *New Job Report*\n\n"
            "Let's collect the details about this job.\n\n"
            "Please describe the job you completed:",
            parse_mode='Markdown',
            reply_markup=get_nav_keyboard(ASKING_JOB_DESCRIPTION)
        )

    return ASKING_JOB_DESCRIPTION


@log_function()
async def job_description_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the job description input"""
    user_data = context.user_data["job_report"]
    user_data.job_description = update.message.text

    # Update current state
    context.user_data["current_state"] = ASKING_CLIENT_NAME

    await update.message.reply_text(
        "Thanks! What is the client's name?",
        reply_markup=get_nav_keyboard(ASKING_CLIENT_NAME)
    )

    return ASKING_CLIENT_NAME


@log_function()
async def client_name_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the client name input"""
    user_data = context.user_data["job_report"]
    user_data.client_name = update.message.text

    # Update current state
    context.user_data["current_state"] = ASKING_CLIENT_CONTACT

    await update.message.reply_text(
        "Great! What is the client's contact information (phone or email)?",
        reply_markup=get_nav_keyboard(ASKING_CLIENT_CONTACT)
    )

    return ASKING_CLIENT_CONTACT


@log_function()
async def client_contact_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the client contact input"""
    user_data = context.user_data["job_report"]
    user_data.client_contact = update.message.text

    # Update current state
    context.user_data["current_state"] = ASKING_AMOUNT

    await update.message.reply_text(
        "How much payment did you receive? (Enter amount in dollars, e.g. 150.00)",
        reply_markup=get_nav_keyboard(ASKING_AMOUNT)
    )

    return ASKING_AMOUNT


@log_function()
async def amount_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the payment amount input"""
    try:
        amount = float(update.message.text.replace('$', '').strip())
        user_data = context.user_data["job_report"]
        user_data.amount_received_dollars = amount

        # Update current state
        context.user_data["current_state"] = ASKING_PAYMENT_METHOD

        # Create payment method keyboard with navigation buttons
        payment_keyboard = []
        for i in range(0, len(PAYMENT_METHODS), 2):
            row = []
            row.append(InlineKeyboardButton(PAYMENT_METHODS[i], callback_data=f"payment:{PAYMENT_METHODS[i]}"))
            if i + 1 < len(PAYMENT_METHODS):
                row.append(
                    InlineKeyboardButton(PAYMENT_METHODS[i + 1], callback_data=f"payment:{PAYMENT_METHODS[i + 1]}"))
            payment_keyboard.append(row)

        # Add navigation buttons
        nav_buttons = []
        if ASKING_PAYMENT_METHOD > ASKING_JOB_DESCRIPTION:
            nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data="nav:back"))
        nav_buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel"))
        payment_keyboard.append(nav_buttons)

        reply_markup = InlineKeyboardMarkup(payment_keyboard)

        await update.message.reply_text(
            "What was the payment method?",
            reply_markup=reply_markup
        )

        return ASKING_PAYMENT_METHOD

    except ValueError:
        await update.message.reply_text(
            "Please enter a valid amount (e.g. 150.00). Try again:",
            reply_markup=get_nav_keyboard(ASKING_AMOUNT)
        )
        return ASKING_AMOUNT


@log_function()
async def payment_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment method selection"""
    query = update.callback_query
    await query.answer()

    user_data = context.user_data["job_report"]
    payment_method = query.data.split(':')[1]
    user_data.payment_method = payment_method

    # Update current state
    context.user_data["current_state"] = ASKING_PHOTO

    # Ask for location if available
    if update.effective_message.location:
        user_data.latitude = update.effective_message.location.latitude
        user_data.longitude = update.effective_message.location.longitude

    # Photo upload keyboard with Skip option
    photo_keyboard = [
        [InlineKeyboardButton("Skip Photos", callback_data="photo:skip")],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="nav:back"),
            InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")
        ]
    ]

    # Request photo
    await query.message.reply_text(
        "Would you like to add photos of the job?\n\n"
        "Send me photos or use the buttons below to continue.",
        reply_markup=InlineKeyboardMarkup(photo_keyboard)
    )

    return ASKING_PHOTO


@log_function()
async def photo_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle uploaded photos"""
    user_data = context.user_data["job_report"]

    # Get largest photo for best quality
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = BytesIO()
    await photo_file.download_to_memory(photo_bytes)
    photo_bytes.seek(0)  # Reset position to beginning of file

    # Save photo data for later upload
    user_data.photos.append(photo_bytes)
    user_data.photo_filenames.append(f"photo_{len(user_data.photos)}.jpg")

    photo_keyboard = [
        [InlineKeyboardButton("Done with Photos", callback_data="photo:done")],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="nav:back"),
            InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")
        ]
    ]

    await update.message.reply_text(
        f"Photo #{len(user_data.photos)} received! Send another photo or click one of the options below:",
        reply_markup=InlineKeyboardMarkup(photo_keyboard)
    )

    return ASKING_PHOTO


@log_function()
async def photo_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle photo upload choices"""
    query = update.callback_query
    await query.answer()

    choice = query.data.split(':')[1]

    if choice in ["done", "skip"]:
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
            "Any additional notes about this job? Type your notes or click 'Continue Without Notes':",
            reply_markup=InlineKeyboardMarkup(notes_keyboard)
        )
        return ASKING_NOTES

    return ASKING_PHOTO


@log_function()
async def notes_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle notes input"""
    user_data = context.user_data["job_report"]

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
        "📋 *Job Report Summary*\n\n"
        f"📝 *Description:* {report_data['job_description']}\n"
        f"👤 *Client:* {report_data['client_name']}\n"
        f"📞 *Contact:* {report_data['client_contact']}\n"
        f"💰 *Amount:* ${report_data['amount_received_dollars']:.2f}\n"
        f"💳 *Payment Method:* {report_data['payment_method']}\n"
    )

    if user_data.notes:
        summary += f"📌 *Notes:* {user_data.notes}\n"

    summary += f"\n📸 *Photos:* {len(user_data.photos)} attached\n\n"
    summary += "Is this information correct? Submit your report or make changes:"

    confirmation_keyboard = [
        [InlineKeyboardButton("✅ Submit Report", callback_data="report:submit")],
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
        user_data = context.user_data["job_report"]
        user_data.notes = ""  # Empty notes

        # Proceed to confirmation
        context.user_data["current_state"] = CONFIRM_SUBMIT

        # Show summary for confirmation
        report_data = user_data.to_dict()
        summary = (
            "📋 *Job Report Summary*\n\n"
            f"📝 *Description:* {report_data['job_description']}\n"
            f"👤 *Client:* {report_data['client_name']}\n"
            f"📞 *Contact:* {report_data['client_contact']}\n"
            f"💰 *Amount:* ${report_data['amount_received_dollars']:.2f}\n"
            f"💳 *Payment Method:* {report_data['payment_method']}\n"
        )

        summary += f"\n📸 *Photos:* {len(user_data.photos)} attached\n\n"
        summary += "Is this information correct? Submit your report or make changes:"

        confirmation_keyboard = [
            [InlineKeyboardButton("✅ Submit Report", callback_data="report:submit")],
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
async def submit_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle report submission"""
    query = update.callback_query
    await query.answer()

    action = query.data.split(':')[1]

    if action == "cancel":
        # Confirm cancellation
        await confirm_cancellation(update, context)
        return CONFIRM_CANCEL

    # Proceed with submission
    user_data = context.user_data["job_report"]

    progress_message = await query.message.reply_text("Submitting your report... Please wait.")

    try:
        # Submit report to backend API
        logger.info(f"Submitting job report to API: {BACKEND_API_URL}/job-report/")

        # Convert data to API format
        api_data = user_data.to_dict()

        # Send request to create job report
        response = requests.post(
            f"{BACKEND_API_URL}/job-report/",
            json=api_data
        )

        if response.status_code != 201:
            logger.error(f"API error: {response.status_code} - {response.text}")
            await progress_message.edit_text(
                "❌ Error submitting report. Please try again later.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Return to Menu", callback_data="menu:employee")]
                ])
            )
            return ConversationHandler.END

        # Get job report ID from response
        job_report_id = response.json().get("job_report_id", str(uuid.uuid4()))  # Fallback for demo

        # Upload photos if any
        photos_uploaded = 0
        if user_data.photos:
            await progress_message.edit_text(
                f"Report submitted! Uploading photos ({len(user_data.photos)} remaining)...")

            for i, (photo_bytes, filename) in enumerate(zip(user_data.photos, user_data.photo_filenames)):
                try:
                    await progress_message.edit_text(f"Uploading photo {i + 1}/{len(user_data.photos)}...")

                    photo_response = requests.post(
                        f"{BACKEND_API_URL}/job-report/{job_report_id}/photos",
                        files={"file": (filename, photo_bytes, "image/jpeg")}
                    )

                    if photo_response.status_code == 201:
                        photos_uploaded += 1
                    else:
                        logger.error(f"Photo upload error: {photo_response.status_code} - {photo_response.text}")

                except Exception as e:
                    logger.error(f"Error uploading photo {i + 1}: {str(e)}")

        # Success message
        success_message = (
            "✅ *Job Report Submitted Successfully!*\n\n"
            f"Thank you for submitting your job report for {user_data.client_name}.\n"
        )

        if photos_uploaded > 0:
            success_message += f"\n{photos_uploaded} photos were uploaded."

        await progress_message.edit_text(
            success_message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Return to Menu", callback_data="menu:employee")]
            ])
        )

        # Clear data
        if "job_report" in context.user_data:
            del context.user_data["job_report"]
        if "current_state" in context.user_data:
            del context.user_data["current_state"]

        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error during report submission: {str(e)}")
        await progress_message.edit_text(
            "❌ Error submitting report. Please try again later.",
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
        current_state = context.user_data.get("current_state", ASKING_JOB_DESCRIPTION)
        current_index = STATE_SEQUENCE.index(current_state)

        if current_index > 0:
            new_state = STATE_SEQUENCE[current_index - 1]
            context.user_data["current_state"] = new_state

            # Display appropriate message for new state
            return await go_to_state(update, context, new_state)

    # Default fallback
    return context.user_data.get("current_state", ASKING_JOB_DESCRIPTION)


@log_function()
async def go_to_state(update: Update, context: ContextTypes.DEFAULT_TYPE, state: int) -> int:
    """Navigate to a specific state with appropriate prompts"""
    query = update.callback_query
    user_data = context.user_data["job_report"]

    if state == ASKING_JOB_DESCRIPTION:
        await query.message.reply_text(
            f"Let's edit the job description.\n\nCurrent value: {user_data.job_description or 'Not set'}\n\nPlease enter a new description:",
            reply_markup=get_nav_keyboard(state)
        )
        return ASKING_JOB_DESCRIPTION

    elif state == ASKING_CLIENT_NAME:
        await query.message.reply_text(
            f"Let's edit the client name.\n\nCurrent value: {user_data.client_name or 'Not set'}\n\nPlease enter the client name:",
            reply_markup=get_nav_keyboard(state)
        )
        return ASKING_CLIENT_NAME

    elif state == ASKING_CLIENT_CONTACT:
        await query.message.reply_text(
            f"Let's edit the client contact.\n\nCurrent value: {user_data.client_contact or 'Not set'}\n\nPlease enter the client's contact information:",
            reply_markup=get_nav_keyboard(state)
        )
        return ASKING_CLIENT_CONTACT

    elif state == ASKING_AMOUNT:
        await query.message.reply_text(
            f"Let's edit the payment amount.\n\nCurrent value: ${user_data.amount_received_dollars:.2f if user_data.amount_received_dollars else 'Not set'}\n\nPlease enter the amount received:",
            reply_markup=get_nav_keyboard(state)
        )
        return ASKING_AMOUNT

    elif state == ASKING_PAYMENT_METHOD:
        # Create payment method keyboard
        payment_keyboard = []
        for i in range(0, len(PAYMENT_METHODS), 2):
            row = []
            row.append(InlineKeyboardButton(PAYMENT_METHODS[i], callback_data=f"payment:{PAYMENT_METHODS[i]}"))
            if i + 1 < len(PAYMENT_METHODS):
                row.append(
                    InlineKeyboardButton(PAYMENT_METHODS[i + 1], callback_data=f"payment:{PAYMENT_METHODS[i + 1]}"))
            payment_keyboard.append(row)

        # Add navigation buttons
        nav_buttons = []
        nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data="nav:back"))
        nav_buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel"))
        payment_keyboard.append(nav_buttons)

        await query.message.reply_text(
            f"Let's change the payment method.\n\nCurrent method: {user_data.payment_method or 'Not set'}\n\nSelect a payment method:",
            reply_markup=InlineKeyboardMarkup(payment_keyboard)
        )
        return ASKING_PAYMENT_METHOD

    elif state == ASKING_PHOTO:
        photo_keyboard = [
            [InlineKeyboardButton("Skip Photos", callback_data="photo:skip")],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="nav:back"),
                InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")
            ]
        ]

        if user_data.photos:
            msg = f"You've uploaded {len(user_data.photos)} photos. Upload additional photos or continue."
        else:
            msg = "Would you like to add photos of the job? Send photos or click Skip to continue."

        await query.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup(photo_keyboard)
        )
        return ASKING_PHOTO


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
    """Ask user to confirm they want to cancel the report"""
    query = update.callback_query

    confirmation_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Yes, Cancel Report", callback_data="cancel:confirm"),
            InlineKeyboardButton("No, Continue Report", callback_data="cancel:continue")
        ]
    ])

    await query.message.reply_text(
        "❓ *Are you sure you want to cancel this report?*\n\n"
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
        if "job_report" in context.user_data:
            del context.user_data["job_report"]
        if "current_state" in context.user_data:
            del context.user_data["current_state"]

        await query.message.reply_text(
            "Report cancelled. Returning to main menu."
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
        current_state = context.user_data.get("current_state", ASKING_JOB_DESCRIPTION)
        await query.message.reply_text(
            "Let's continue with your report."
        )
        return await go_to_state(update, context, current_state)


@log_function()
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command"""
    # Clear data
    if "job_report" in context.user_data:
        del context.user_data["job_report"]
    if "current_state" in context.user_data:
        del context.user_data["current_state"]

    await update.message.reply_text(
        "Report cancelled. Returning to main menu."
    )

    # Return to menu
    await update.message.reply_text(
        EMPLOYEE_MENU.text,
        reply_markup=EMPLOYEE_MENU.get_keyboard_markup(),
        parse_mode='Markdown'
    )

    return ConversationHandler.END


# Create the conversation handler
job_report_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_job_report, pattern=r"^report:start$"),
        CommandHandler("report", start_job_report)
    ],
    states={
        ASKING_JOB_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, job_description_provided),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        ASKING_CLIENT_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, client_name_provided),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        ASKING_CLIENT_CONTACT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, client_contact_provided),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        ASKING_AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, amount_provided),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        ASKING_PAYMENT_METHOD: [
            CallbackQueryHandler(payment_method_selected, pattern=r"^payment:"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        ASKING_PHOTO: [
            MessageHandler(filters.PHOTO, photo_provided),
            CallbackQueryHandler(photo_choice, pattern=r"^photo:"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        ASKING_NOTES: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, notes_provided),
            CallbackQueryHandler(notes_choice, pattern=r"^notes:"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        CONFIRM_SUBMIT: [
            CallbackQueryHandler(submit_report, pattern=r"^report:"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        CONFIRM_CANCEL: [
            CallbackQueryHandler(handle_cancel_confirmation, pattern=r"^cancel:")
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)