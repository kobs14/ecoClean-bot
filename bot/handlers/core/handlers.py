import time

from telegram import Update
from telegram.ext import ContextTypes

from ..util.menus import EMPLOYEE_MENU, ADMIN_MENU, STATUS_MENU
from ..logger_config import get_logger


logger = get_logger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    start_time = time.time()  # Track execution time

    user = update.effective_user
    user_id = user.id if user else "Unknown"
    username = user.username if user else "Unknown"

    logger.info(f"Received /start command from user {user_id} (@{username})")

    query = update.message
    await query.reply_text(
        "🔄 EcoClean Bot is initializing...",
        parse_mode='Markdown'
    )

    # Temporary - replace with actual role-based menu selection
    # await show_employee_menu(update, context)
    await show_admin_menu(update, context)
    # await show_status_menu(update, context)
    execution_time = time.time() - start_time
    logger.info(f"Completed handling /start command for user {user_id} in {execution_time:.4f}s")


async def show_employee_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the employee menu"""
    query = update.message or update.callback_query

    # If it's a callback query, answer it to remove the loading spinner
    if update.callback_query:
        await update.callback_query.answer()

    await (query.message if update.callback_query else query).reply_text(
        EMPLOYEE_MENU.text,
        reply_markup=EMPLOYEE_MENU.get_keyboard_markup(),
        parse_mode='Markdown'
    )


async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the admin menu"""
    user_id = update.effective_user.id
    logger.info(f"Showing admin menu to user {user_id}")

    query = update.message or update.callback_query

    # If it's a callback query, answer it to remove the loading spinner
    if update.callback_query:
        await update.callback_query.answer()

    await (query.message if update.callback_query else query).reply_text(
        ADMIN_MENU.text,
        reply_markup=ADMIN_MENU.get_keyboard_markup(),
        parse_mode='Markdown'
    )


async def show_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the status update menu"""
    user_id = update.effective_user.id
    logger.info(f"Showing status menu to user {user_id}")

    query = update.message or update.callback_query

    # If it's a callback query, answer it to remove the loading spinner
    if update.callback_query:
        await update.callback_query.answer()

    await (query.message if update.callback_query else query).reply_text(
        STATUS_MENU.text,
        reply_markup=STATUS_MENU.get_keyboard_markup(),
        parse_mode='Markdown'
    )


# async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle inline button callbacks"""
#     query = update.callback_query
#     await query.answer()
#
#     data = query.data.split(':')
#     action, value = data[0], data[1] if len(data) > 1 else None
#
#     # Routing logic for different callback actions
#     if action == 'admin' and value == 'team':
#         await query.message.reply_text("Team management coming soon!")
#     elif action == 'status':
#         # Placeholder for status update logic
#         await query.message.reply_text(f"Status updated to: {value}")
#     elif action == 'report':
#         await query.message.reply_text("Job report submission coming soon!")
#     else:
#         await query.message.reply_text("Unhandled action")