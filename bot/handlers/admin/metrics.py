from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    filters
)
import requests
from datetime import datetime
from ..util.menus import ADMIN_MENU
from ..util.mock_api import mock_api
from ..logger_config import get_logger, log_function

logger = get_logger(__name__)

# Define metrics refresh intervals (in seconds)
REFRESH_INTERVALS = {
    "Realtime (10s)": 10,
    "Standard (30s)": 30,
    "Economy (60s)": 60
}

# Metrics categories
METRICS_CATEGORIES = [
    "Team Performance",
    "Job Progress",
    "Equipment Status",
    "Customer Feedback",
    "Financial Metrics"
]


# Define states
SHOWING_METRICS_MENU, VIEWING_METRICS, METRICS_SETTINGS = range(3)


class LiveMetricsViewer:
    """Class to manage live metrics viewing session"""

    def __init__(self, admin_id: str):
        self.admin_id = admin_id
        self.current_category = ""
        self.refresh_interval = 30  # Default
        self.last_update = None
        self.active = True


@log_function()
async def start_live_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for live metrics"""
    query = update.callback_query
    await query.answer()

    # Initialize metrics session
    context.user_data["metrics_session"] = LiveMetricsViewer(str(update.effective_user.id))

    # Create category selection keyboard
    keyboard = []
    for i in range(0, len(METRICS_CATEGORIES), 2):
        row = []
        row.append(
            InlineKeyboardButton(METRICS_CATEGORIES[i], callback_data=f"metrics_category:{METRICS_CATEGORIES[i]}"))
        if i + 1 < len(METRICS_CATEGORIES):
            row.append(InlineKeyboardButton(METRICS_CATEGORIES[i + 1],
                                            callback_data=f"metrics_category:{METRICS_CATEGORIES[i + 1]}"))
        keyboard.append(row)

    # Add navigation
    keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data="admin:back_to_menu"),
        InlineKeyboardButton("❌ Close", callback_data="metrics:close")
    ])

    await query.edit_message_text(
        "📊 *Live Metrics Dashboard*\n\n"
        "Select a category to monitor:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return SHOWING_METRICS_MENU  # Return appropriate state constant


@log_function()
async def show_metrics_category_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the metrics category selection menu"""
    # Create refresh interval selection keyboard
    interval_buttons = []
    for interval in REFRESH_INTERVALS:
        interval_buttons.append(
            InlineKeyboardButton(interval, callback_data=f"metrics_interval:{interval}"))

    keyboard = [
        [InlineKeyboardButton("🔄 Refresh Now", callback_data="metrics:refresh")],
        interval_buttons[:2],  # First two interval options
        interval_buttons[2:],  # Remaining interval options
        [
            InlineKeyboardButton("📊 All Metrics", callback_data="metrics_category:all"),
            InlineKeyboardButton("⬅️ Back", callback_data="admin:back_to_menu")
        ],
        [InlineKeyboardButton("❌ Close Dashboard", callback_data="metrics:close")]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "📊 *Live Metrics Dashboard*\n\n"
            "Select a category or configure refresh:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(
            "📊 *Live Metrics Dashboard*\n\n"
            "Select a category or configure refresh:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard))

    return SHOWING_METRICS_MENU  # Return appropriate state constant



@log_function()
async def handle_metrics_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle metrics category or interval selection"""
    query = update.callback_query
    await query.answer()

    if not context.user_data.get("metrics_session"):
        context.user_data["metrics_session"] = LiveMetricsViewer(str(update.effective_user.id))

    session = context.user_data["metrics_session"]

    if query.data.startswith("metrics_category:"):
        # Category selected
        category = query.data.split(':')[1]
        session.current_category = category
        await display_metrics(update, context, category)
        return VIEWING_METRICS  # Return viewing metrics state

    elif query.data.startswith("metrics_interval:"):
        # Refresh interval changed
        interval_name = query.data.split(':')[1]
        session.refresh_interval = REFRESH_INTERVALS[interval_name]
        await query.answer(f"Refresh interval set to {interval_name}")
        await show_metrics_category_menu(update, context)
        return SHOWING_METRICS_MENU  # Return menu state

    elif query.data == "metrics:refresh":
        # Manual refresh
        if session.current_category:
            await display_metrics(update, context, session.current_category)
            return VIEWING_METRICS  # Return viewing metrics state
        else:
            await query.answer("Please select a category first")
            await show_metrics_category_menu(update, context)
            return SHOWING_METRICS_MENU  # Return to menu

    return SHOWING_METRICS_MENU  # Default return to menu


# @log_function()
# async def display_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> int:
#     """Fetch and display the requested metrics"""
#     query = update.callback_query
#     await query.answer()
#
#     session = context.user_data["metrics_session"]
#     session.last_update = datetime.now()
#
#     try:
#         #TODO Call API
#         # Fetch metrics from API
#         response = requests.get(
#             f"BACKEND_API_URL/admin/metrics",
#             params={
#                 "category": category,
#                 "admin_id": session.admin_id
#             },
#             timeout=10
#         )
#
#         if response.status_code != 200:
#             raise Exception("API error")
#
#         metrics_data = response.json()
#
#         # Format the metrics display
#         message = format_metrics_message(category, metrics_data)
#
#         # Create navigation keyboard
#         keyboard = [
#             [InlineKeyboardButton("🔄 Refresh", callback_data="metrics:refresh")],
#             [
#                 InlineKeyboardButton("⚙️ Settings", callback_data="metrics:settings"),
#                 InlineKeyboardButton("📊 All Categories", callback_data="metrics_category:all")
#             ],
#             [InlineKeyboardButton("❌ Close", callback_data="metrics:close")]
#         ]
#
#         if query.message.text != message:  # Only edit if content changed
#             await query.edit_message_text(
#                 message,
#                 parse_mode='Markdown',
#                 reply_markup=InlineKeyboardMarkup(keyboard))
#
#         # Schedule auto-refresh if session is active
#         if session.active:
#             context.job_queue.run_once(
#                 callback=auto_refresh_metrics,
#                 when=session.refresh_interval,
#                 data=(update.effective_chat.id, query.message.message_id, category),
#                 name=f"metrics_refresh_{session.admin_id}"
#             )
#
#         return await handle_metrics_interaction(update, context)
#
#     except Exception as e:
#         logger.error(f"Error fetching metrics: {str(e)}")
#         await query.edit_message_text(
#             "⚠️ Could not fetch metrics data. Please try again.",
#             reply_markup=InlineKeyboardMarkup([
#                 [InlineKeyboardButton("🔄 Retry", callback_data=f"metrics_category:{category}")],
#                 [InlineKeyboardButton("⬅️ Back", callback_data="metrics:back")]
#             ]))
#         return await handle_metrics_interaction(update, context)


@log_function()
async def display_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> int:
    """Fetch and display the requested metrics"""
    query = update.callback_query
    await query.answer()

    session = context.user_data["metrics_session"]
    session.last_update = datetime.now()

    try:
        # Use mock API instead of real API for testing
        metrics_data = mock_api.get_metrics(category, session.admin_id)

        # Format the metrics display
        message = format_metrics_message(category, metrics_data)

        # Create navigation keyboard
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="metrics:refresh")],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="metrics:settings"),
                InlineKeyboardButton("📊 All Categories", callback_data="metrics_category:all")
            ],
            [InlineKeyboardButton("❌ Close", callback_data="metrics:close")]
        ]

        # When using query.edit_message_text, wrap with try/except
        # to handle 'message is not modified' exceptions
        try:
            await query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                # Only log errors that aren't about unchanged messages
                logger.error(f"Error updating message: {str(e)}")

        # Schedule auto-refresh if session is active
        if session.active:
            # Remove any existing jobs first to prevent duplicates
            current_jobs = context.job_queue.get_jobs_by_name(f"metrics_refresh_{session.admin_id}")
            for job in current_jobs:
                job.schedule_removal()

            # Schedule new job
            context.job_queue.run_once(
                callback=auto_refresh_metrics,
                when=session.refresh_interval,
                data=(update.effective_chat.id, query.message.message_id, category),
                name=f"metrics_refresh_{session.admin_id}"
            )

        return VIEWING_METRICS  # Return the viewing metrics state

    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}")
        await query.edit_message_text(
            "⚠️ Could not fetch metrics data. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Retry", callback_data=f"metrics_category:{category}")],
                [InlineKeyboardButton("⬅️ Back", callback_data="metrics:back")]
            ]))
        return VIEWING_METRICS



def format_metrics_message(category: str, data: dict) -> str:
    """Format metrics data into a readable message"""
    base_msg = f"📊 *{category} Metrics*\n"
    base_msg += f"_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n"

    if category == "Team Performance":
        return base_msg + (
            "👥 *Team Stats*\n"
            f"• Online: {data.get('online', 0)} | On Job: {data.get('on_job', 0)}\n"
            f"• Avg. Rating: {data.get('avg_rating', 0)}/5\n"
            f"• Efficiency: {data.get('efficiency', 0)}%\n\n"
            "🏆 *Top Performers*\n"
            f"1. {data.get('top_performers', [''])[0]}\n"
            f"2. {data.get('top_performers', [''])[1]}\n"
            f"3. {data.get('top_performers', [''])[2]}"
        )
    elif category == "Job Progress":
        return base_msg + (
            "🧹 *Job Status*\n"
            f"• Completed: {data.get('completed', 0)}\n"
            f"• In Progress: {data.get('in_progress', 0)}\n"
            f"• Scheduled: {data.get('scheduled', 0)}\n\n"
            "⏱ *Timing*\n"
            f"• Avg. Duration: {data.get('avg_duration', 0)} mins\n"
            f"• On Time: {data.get('on_time_rate', 0)}%"
        )
    elif category == "all":
        return base_msg + (
            "🌐 *System Overview*\n"
            f"• Teams Active: {data.get('teams_active', 0)}/{data.get('teams_total', 0)}\n"
            f"• Jobs Today: {data.get('jobs_today', 0)}\n"
            f"• Revenue Today: ${data.get('revenue_today', 0)}\n\n"
            "⚡ *Efficiency*\n"
            f"• Overall: {data.get('efficiency', 0)}%\n"
            f"• This Week: {data.get('efficiency_week', 0)}%"
        )
    else:
        return base_msg + "No data available for this category."


# @log_function()
# async def auto_refresh_metrics(context: ContextTypes.DEFAULT_TYPE):
#     """Auto-refresh metrics based on selected interval"""
#     job = context.job
#     chat_id, message_id, category = job.data
#
#     try:
#         # Check if session is still active
#         if not context.user_data.get("metrics_session") or not context.user_data["metrics_session"].active:
#             return
#         # TODO Call API
#         # Fetch fresh metrics
#         response = requests.get(
#             f"BACKEND_API_URL/admin/metrics",
#             params={
#                 "category": category,
#                 "admin_id": context.user_data["metrics_session"].admin_id
#             },
#             timeout=10
#         )
#
#         if response.status_code == 200:
#             metrics_data = response.json()
#             message = format_metrics_message(category, metrics_data)
#
#             # Edit the existing message
#             await context.bot.edit_message_text(
#                 message,
#                 chat_id=chat_id,
#                 message_id=message_id,
#                 parse_mode='Markdown',
#                 reply_markup=InlineKeyboardMarkup([
#                     [InlineKeyboardButton("🔄 Refresh", callback_data="metrics:refresh")],
#                     [
#                         InlineKeyboardButton("⚙️ Settings", callback_data="metrics:settings"),
#                         InlineKeyboardButton("📊 All Categories", callback_data="metrics_category:all")
#                     ],
#                     [InlineKeyboardButton("❌ Close", callback_data="metrics:close")]
#                 ])
#             )
#
#             # Schedule next refresh
#             context.job_queue.run_once(
#                 callback=auto_refresh_metrics,
#                 when=context.user_data["metrics_session"].refresh_interval,
#                 data=job.data,
#                 name=f"metrics_refresh_{context.user_data['metrics_session'].admin_id}"
#             )
#
#     except Exception as e:
#         logger.error(f"Auto-refresh failed: {str(e)}")


@log_function()
async def auto_refresh_metrics(context: ContextTypes.DEFAULT_TYPE):
    """Auto-refresh metrics based on selected interval"""
    job = context.job
    chat_id, message_id, category = job.data

    try:
        # Check if session is still active
        if not context.user_data.get("metrics_session") or not context.user_data["metrics_session"].active:
            return

        # Use mock API instead of real API
        metrics_data = mock_api.get_metrics(category, context.user_data["metrics_session"].admin_id)
        message = format_metrics_message(category, metrics_data)

        # Edit the existing message
        try:
            await context.bot.edit_message_text(
                message,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="metrics:refresh")],
                    [
                        InlineKeyboardButton("⚙️ Settings", callback_data="metrics:settings"),
                        InlineKeyboardButton("📊 All Categories", callback_data="metrics_category:all")
                    ],
                    [InlineKeyboardButton("❌ Close", callback_data="metrics:close")]
                ])
            )
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                # Only log errors that aren't about unchanged messages
                logger.error(f"Error updating message: {str(e)}")

        # Schedule next refresh
        context.job_queue.run_once(
            callback=auto_refresh_metrics,
            when=context.user_data["metrics_session"].refresh_interval,
            data=job.data,
            name=f"metrics_refresh_{context.user_data['metrics_session'].admin_id}"
        )

    except Exception as e:
        logger.error(f"Auto-refresh failed: {str(e)}")


@log_function()
async def handle_metrics_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle interactions while viewing metrics"""
    query = update.callback_query
    await query.answer()

    if query.data == "metrics:back":
        await show_metrics_category_menu(update, context)
        return SHOWING_METRICS_MENU

    elif query.data == "metrics:settings":
        await show_metrics_settings(update, context)
        return METRICS_SETTINGS

    elif query.data == "metrics:close" or query.data == "admin:back_to_menu":
        await close_metrics_session(update, context)
        return ConversationHandler.END

    elif query.data.startswith("metrics_category:"):
        category = query.data.split(':')[1]
        context.user_data["metrics_session"].current_category = category
        await display_metrics(update, context, category)
        return VIEWING_METRICS

    elif query.data == "metrics:refresh":
        if context.user_data.get("metrics_session") and context.user_data["metrics_session"].current_category:
            await display_metrics(
                update,
                context,
                context.user_data["metrics_session"].current_category)
            return VIEWING_METRICS

    # Default - stay in the same state
    return VIEWING_METRICS


@log_function()
async def show_metrics_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show metrics display settings"""
    query = update.callback_query
    await query.answer()

    session = context.user_data["metrics_session"]

    # Create interval selection keyboard
    interval_buttons = []
    for interval_name, interval_sec in REFRESH_INTERVALS.items():
        is_selected = (interval_sec == session.refresh_interval)
        prefix = "✅" if is_selected else "⚪"
        interval_buttons.append(
            [InlineKeyboardButton(f"{prefix} {interval_name}",
                                  callback_data=f"metrics_set_interval:{interval_name}")])

    keyboard = interval_buttons + [
        [
            InlineKeyboardButton("⬅️ Back", callback_data=f"metrics_category:{session.current_category}"),
            InlineKeyboardButton("❌ Close", callback_data="metrics:close")
        ]
    ]

    await query.edit_message_text(
        "⚙️ *Metrics Display Settings*\n\n"
        "Configure how often the metrics automatically refresh:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard))

    return METRICS_SETTINGS  # Return settings state


@log_function()
async def close_metrics_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Clean up and close the metrics session"""
    query = update.callback_query
    await query.answer()

    # Cancel any pending refresh jobs
    if "metrics_session" in context.user_data:
        admin_id = context.user_data["metrics_session"].admin_id
        current_jobs = context.job_queue.get_jobs_by_name(f"metrics_refresh_{admin_id}")
        for job in current_jobs:
            job.schedule_removal()

        del context.user_data["metrics_session"]

    # Return to admin menu
    await query.edit_message_text(
        ADMIN_MENU.text,
        reply_markup=ADMIN_MENU.get_keyboard_markup(),
        parse_mode='Markdown')

    return ConversationHandler.END  # End the conversation properly


metrics_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_live_metrics, pattern=r"^admin:performance$")
    ],
    states={
        SHOWING_METRICS_MENU: [
            CallbackQueryHandler(handle_metrics_selection, pattern=r"^metrics_")
        ],
        VIEWING_METRICS: [
            CallbackQueryHandler(handle_metrics_interaction, pattern=r"^metrics_"),
            CallbackQueryHandler(handle_metrics_interaction, pattern=r"^metrics:")
        ],
        METRICS_SETTINGS: [
            CallbackQueryHandler(handle_metrics_interaction, pattern=r"^metrics_"),
            CallbackQueryHandler(handle_metrics_interaction, pattern=r"^metrics:")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(close_metrics_session, pattern=r"^admin:back_to_menu$"),
        CallbackQueryHandler(close_metrics_session, pattern=r"^metrics:close$")
    ],
    map_to_parent={
        ConversationHandler.END: ADMIN_MENU  # This should be a state in your parent handler
    }
)