import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from ..util.menus import ADMIN_MENU
from ..logger_config import get_logger, log_function

logger = get_logger(__name__)

# Define conversation states for reports
(
    REPORT_TYPE_SELECTION,
    REPORT_DATE_RANGE,
    REPORT_CONFIRMATION,
    REPORT_GENERATING,
) = range(4)

# Report types
REPORT_TYPES = [
    "Daily Performance",
    "Weekly Summary",
    "Material Usage",
    "Team Productivity",
    "Financial Overview",
    "Customer Feedback"
]


class ReportGenerator:
    """Class to store report generation data during conversation"""

    def __init__(self, admin_id: str):
        self.admin_id = admin_id
        self.report_type = ""
        self.date_range = ""
        self.custom_filters = {}

    def to_dict(self) -> dict:
        """Convert to API-compatible format"""
        return {
            "admin_id": self.admin_id,
            "report_type": self.report_type,
            "date_range": self.date_range,
            **self.custom_filters
        }


@log_function()
async def start_report_generation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for report generation"""
    query = update.callback_query
    await query.answer()

    # Initialize report data
    context.user_data["report_data"] = ReportGenerator(str(update.effective_user.id))

    # Create report type selection keyboard
    keyboard = []
    for i in range(0, len(REPORT_TYPES), 2):
        row = []
        row.append(InlineKeyboardButton(REPORT_TYPES[i], callback_data=f"report_type:{REPORT_TYPES[i]}"))
        if i + 1 < len(REPORT_TYPES):
            row.append(InlineKeyboardButton(REPORT_TYPES[i + 1], callback_data=f"report_type:{REPORT_TYPES[i + 1]}"))
        keyboard.append(row)

    # Add navigation
    keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data="admin:back_to_menu"),
        InlineKeyboardButton("❌ Cancel", callback_data="admin:cancel")
    ])

    await query.edit_message_text(
        "📊 *Report Generation*\n\n"
        "Select the type of report you want to generate:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return REPORT_TYPE_SELECTION


@log_function()
async def select_report_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle report type selection"""
    query = update.callback_query
    await query.answer()

    report_type = query.data.split(':')[1]
    context.user_data["report_data"].report_type = report_type

    # Date range selection keyboard
    date_ranges = [
        "Today",
        "Yesterday",
        "This Week",
        "Last Week",
        "This Month",
        "Custom Range"
    ]

    keyboard = []
    for i in range(0, len(date_ranges), 2):
        row = []
        row.append(InlineKeyboardButton(date_ranges[i], callback_data=f"date_range:{date_ranges[i]}"))
        if i + 1 < len(date_ranges):
            row.append(InlineKeyboardButton(date_ranges[i + 1], callback_data=f"date_range:{date_ranges[i + 1]}"))
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data="report:back"),
        InlineKeyboardButton("❌ Cancel", callback_data="admin:cancel")
    ])

    await query.edit_message_text(
        f"📋 *{report_type} Report*\n\n"
        "Select the time period for the report:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard))

    return REPORT_DATE_RANGE


@log_function()
async def handle_custom_date_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom date range input"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "Please enter the date range in format:\n"
        "`YYYY-MM-DD to YYYY-MM-DD`\n\n"
        "Example: `2023-01-01 to 2023-01-31`",
        parse_mode='Markdown'
    )

    return REPORT_DATE_RANGE


@log_function()
async def process_date_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process date range selection (both buttons and custom input)"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        if query.data.startswith("date_range:Custom"):
            return await handle_custom_date_range(update, context)

        date_range = query.data.split(':')[1]
        context.user_data["report_data"].date_range = date_range
    else:
        # Handle custom date range input
        date_range = update.message.text
        if not validate_date_range(date_range):
            await update.message.reply_text(
                "Invalid date format. Please use `YYYY-MM-DD to YYYY-MM-DD`",
                parse_mode='Markdown'
            )
            return REPORT_DATE_RANGE
        context.user_data["report_data"].date_range = date_range

    return await show_report_confirmation(update, context)


def validate_date_range(date_range: str) -> bool:
    """Simple date range validation"""
    try:
        dates = date_range.split(" to ")
        if len(dates) != 2:
            return False
        # Add actual date parsing logic here
        return True
    except:
        return False


@log_function()
async def show_report_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show confirmation before generating report"""
    report_data = context.user_data["report_data"]

    confirmation_text = (
        f"📄 *Report Summary*\n\n"
        f"🔹 Type: {report_data.report_type}\n"
        f"📅 Period: {report_data.date_range}\n\n"
        "Would you like to generate this report now?"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Generate Report", callback_data="report:generate"),
            InlineKeyboardButton("🔄 Change Parameters", callback_data="report:back")
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="admin:cancel")
        ]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            confirmation_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(
            confirmation_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard))

    return REPORT_CONFIRMATION


@log_function()
async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate and send the actual report"""
    query = update.callback_query
    await query.answer()

    report_data = context.user_data["report_data"]

    # Show generating message
    await query.edit_message_text(
        f"⏳ Generating {report_data.report_type} report for {report_data.date_range}...",
        parse_mode='Markdown'
    )

    try:
        # Call your backend API to generate the report
        # This is a placeholder - implement your actual API call
        #TODO: Call API
        api_response = requests.post(
            f"BACKEND_API_URL/admin/generate-report",
            json=report_data.to_dict()
        )

        if api_response.status_code != 200:
            raise Exception("API error")

        report_url = api_response.json().get("report_url")

        # Send the report to the admin
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=report_url,
            caption=f"📊 *{report_data.report_type} Report* ({report_data.date_range})",
            parse_mode='Markdown'
        )

        # Clean up
        del context.user_data["report_data"]

        # Return to admin menu
        await query.message.reply_text(
            ADMIN_MENU.text,
            reply_markup=ADMIN_MENU.get_keyboard_markup(),
            parse_mode='Markdown'
        )

        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        await query.edit_message_text(
            "❌ Failed to generate report. Please try again later.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Retry", callback_data="report:generate")],
                [InlineKeyboardButton("⬅️ Admin Menu", callback_data="admin:back_to_menu")]
            ])
        )
        return REPORT_GENERATING


@log_function()
async def handle_report_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle back/cancel navigation during report generation"""
    query = update.callback_query
    await query.answer()

    action = query.data.split(':')[1]

    if action == "back_to_menu":
        # Return to admin menu
        await query.edit_message_text(
            ADMIN_MENU.text,
            reply_markup=ADMIN_MENU.get_keyboard_markup(),
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    elif action == "back":
        # Go back one step
        current_text = query.message.text

        if "Select the type of report" in current_text:
            return REPORT_TYPE_SELECTION
        elif "Select the time period" in current_text:
            return await start_report_generation(update, context)
        elif "Report Summary" in current_text:
            return await select_report_type(update, context)

    elif action == "cancel":
        # Clean up and return to menu
        if "report_data" in context.user_data:
            del context.user_data["report_data"]

        await query.edit_message_text(
            ADMIN_MENU.text,
            reply_markup=ADMIN_MENU.get_keyboard_markup(),
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    return REPORT_TYPE_SELECTION


# Create the conversation handler
report_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_report_generation, pattern=r"^admin:generate_reports$")
    ],
    states={
        REPORT_TYPE_SELECTION: [
            CallbackQueryHandler(select_report_type, pattern=r"^report_type:"),
            CallbackQueryHandler(handle_report_navigation, pattern=r"^(admin|report):")
        ],
        REPORT_DATE_RANGE: [
            CallbackQueryHandler(process_date_range, pattern=r"^date_range:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_date_range),
            CallbackQueryHandler(handle_report_navigation, pattern=r"^(admin|report):")
        ],
        REPORT_CONFIRMATION: [
            CallbackQueryHandler(generate_report, pattern=r"^report:generate"),
            CallbackQueryHandler(handle_report_navigation, pattern=r"^(admin|report):")
        ],
        REPORT_GENERATING: [
            CallbackQueryHandler(generate_report, pattern=r"^report:generate"),
            CallbackQueryHandler(handle_report_navigation, pattern=r"^admin:")
        ]
    },
    fallbacks=[
        CommandHandler("cancel", handle_report_navigation),
        CallbackQueryHandler(handle_report_navigation, pattern=r"^admin:")
    ]
)