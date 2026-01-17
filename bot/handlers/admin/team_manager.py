import os
import json
import requests
import uuid
from io import BytesIO
from typing import Dict, Optional, List, Any
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from ..util.menus import ADMIN_MENU
from ..logger_config import get_logger, log_function

# Define conversation states
(
    TEAM_MENU,
    ADD_EMPLOYEE_NAME,
    ADD_EMPLOYEE_PHONE,
    ADD_EMPLOYEE_EMAIL,
    ADD_EMPLOYEE_POSITION,
    ADD_EMPLOYEE_COMMISSION,
    ADD_EMPLOYEE_CONFIRM,
    EMPLOYEE_LIST_VIEW,
    EMPLOYEE_DETAIL_VIEW,
    EMPLOYEE_EDIT_MENU,
    EMPLOYEE_EDIT_NAME,
    EMPLOYEE_EDIT_PHONE,
    EMPLOYEE_EDIT_EMAIL,
    EMPLOYEE_EDIT_POSITION,
    EMPLOYEE_EDIT_COMMISSION,
    EMPLOYEE_EDIT_STATUS,
    CONFIRM_DELETE_EMPLOYEE,
    CANCEL_CONFIRMATION,
) = range(18)

# API URL from environment variables
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://api:5000")

# Employee positions
EMPLOYEE_POSITIONS = ["Technician", "Senior Technician", "Team Lead", "Manager", "Other"]

# Employee status options
EMPLOYEE_STATUS = ["Active", "Inactive", "Pending Verification"]

# Initialize logger
logger = get_logger(__name__)


class EmployeeData:
    """Class to store employee data during conversation"""

    def __init__(self):
        self.employee_id = None
        self.name = ""
        self.phone = ""
        self.email = ""
        self.position = ""
        self.commission_rate = 0.0
        self.status = "Pending Verification"
        self.join_date = datetime.now().strftime("%Y-%m-%d")
        self.admin_notes = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert employee data to dictionary for API request"""
        data = {
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "position": self.position,
            "commission_rate": self.commission_rate,
            "status": self.status,
            "join_date": self.join_date,
        }
        if self.admin_notes:
            data["admin_notes"] = self.admin_notes
        if self.employee_id:
            data["employee_id"] = self.employee_id
        return data


def get_nav_keyboard(include_back: bool = True, include_cancel: bool = True) -> InlineKeyboardMarkup:
    """Generate navigation keyboard"""
    buttons = []
    if include_back:
        buttons.append(InlineKeyboardButton("⬅️ Back", callback_data="team_nav:back"))
    if include_cancel:
        buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="team_nav:cancel"))
    return InlineKeyboardMarkup([buttons])


@log_function()
async def handle_team_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger = get_logger(__name__)
    logger.debug(f"Raw callback data: {update.callback_query.data}")  # Add this line
    """Handles team manager navigation and admin menu return actions."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    parts = data.split(":")

    if len(parts) != 2:
        return TEAM_MENU

    prefix, action = parts

    # Handle team navigation
    if prefix == "team":
        if action == "back":
            return context.user_data.get("prev_state", TEAM_MENU)
        elif action == "cancel":
            context.user_data.pop("employee_data", None)
            return await team_manager_menu(update, context)

    # Handle admin-level navigation
    elif prefix == "admin":
        if action == "back_to_menu":
            await query.edit_message_text(
                ADMIN_MENU.text,
                reply_markup=ADMIN_MENU.get_keyboard_markup(),
                parse_mode='Markdown'
            )
            return ConversationHandler.END

    return TEAM_MENU



@log_function()
async def team_manager_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the team manager main menu"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        message_id = query.message.message_id
    else:
        chat_id = update.message.chat_id
        message_id = None

    context.user_data["prev_state"] = TEAM_MENU
    if "employee_data" in context.user_data:
        del context.user_data["employee_data"]

    keyboard = [
        [InlineKeyboardButton("➕ Add New Employee", callback_data="team:add_employee")],
        [InlineKeyboardButton("👥 View Employee List", callback_data="team:list_employees")],
        [InlineKeyboardButton("📊 Team Performance", callback_data="team:performance")],
        [InlineKeyboardButton("📧 Send Team Announcement", callback_data="team:announcement")],
        [InlineKeyboardButton("🔙 Return to Admin Menu", callback_data="admin:back_to_menu")]
    ]

    text = (
        "👥 *TEAM MANAGER*\n\n"
        "Manage your team members and their settings.\n"
        "What would you like to do?"
    )

    if message_id:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    return TEAM_MENU


@log_function()
async def start_add_employee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process of adding a new employee"""
    query = update.callback_query
    await query.answer()

    # Store previous state for navigation
    context.user_data["prev_state"] = TEAM_MENU

    # Initialize employee data
    context.user_data["employee_data"] = EmployeeData()

    await query.message.edit_text(
        text="➕ *Add New Employee*\n\n"
             "Please enter the employee's full name:",
        parse_mode='Markdown',
        reply_markup=get_nav_keyboard()
    )

    return ADD_EMPLOYEE_NAME


@log_function()
async def employee_name_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the employee name and ask for phone number"""
    # Store previous state for navigation
    context.user_data["prev_state"] = ADD_EMPLOYEE_NAME

    # Get the employee data
    employee_data = context.user_data.get("employee_data", EmployeeData())
    employee_data.name = update.message.text.strip()
    context.user_data["employee_data"] = employee_data

    # Ask for phone number
    await update.message.reply_text(
        text="📱 *Add New Employee*\n\n"
             f"Name: *{employee_data.name}*\n\n"
             "Please enter the employee's phone number:",
        parse_mode='Markdown',
        reply_markup=get_nav_keyboard()
    )

    return ADD_EMPLOYEE_PHONE


@log_function()
async def employee_phone_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the employee phone and ask for email"""
    # Store previous state for navigation
    context.user_data["prev_state"] = ADD_EMPLOYEE_PHONE

    # Get the employee data
    employee_data = context.user_data.get("employee_data", EmployeeData())
    employee_data.phone = update.message.text.strip()
    context.user_data["employee_data"] = employee_data

    # Ask for email
    await update.message.reply_text(
        text="📧 *Add New Employee*\n\n"
             f"Name: *{employee_data.name}*\n"
             f"Phone: *{employee_data.phone}*\n\n"
             "Please enter the employee's email address:",
        parse_mode='Markdown',
        reply_markup=get_nav_keyboard()
    )

    return ADD_EMPLOYEE_EMAIL


@log_function()
async def employee_email_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the employee email and ask for position"""
    return ADD_EMPLOYEE_POSITION

@log_function()
async def employee_position_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the employee position selection and ask for commission"""
    return ADD_EMPLOYEE_COMMISSION

@log_function()
async def employee_commission_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the employee commission rate and show confirmation"""
    return ADD_EMPLOYEE_CONFIRM

@log_function()
async def confirm_add_employee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and save the new employee"""
    return TEAM_MENU

@log_function()
async def start_edit_employee_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start editing employee name"""
    return EMPLOYEE_EDIT_NAME

@log_function()
async def start_edit_employee_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start editing employee phone"""
    return EMPLOYEE_EDIT_PHONE

@log_function()
async def start_edit_employee_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start editing employee email"""
    return EMPLOYEE_EDIT_EMAIL

@log_function()
async def start_edit_employee_position(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start editing employee position"""
    return EMPLOYEE_EDIT_POSITION

@log_function()
async def start_edit_employee_commission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start editing employee commission rate"""
    return EMPLOYEE_EDIT_COMMISSION

@log_function()
async def start_edit_employee_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start editing employee status"""
    return EMPLOYEE_EDIT_STATUS

@log_function()
async def confirm_delete_employee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show confirmation for employee deletion"""
    return CONFIRM_DELETE_EMPLOYEE


@log_function()
async def list_employees(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display list of employees"""
    query = update.callback_query
    await query.answer()

    # Store previous state for navigation
    context.user_data["prev_state"] = TEAM_MENU

    # This would normally fetch data from API, but for now we'll use dummy data
    try:
        # Make API request to get employees
        response = requests.get(f"{BACKEND_API_URL}/api/employees")
        if response.status_code == 200:
            employees = response.json()
        else:
            # Fallback to dummy data if API fails
            employees = [
                {"employee_id": "1", "name": "John Doe", "position": "Technician", "status": "Active"},
                {"employee_id": "2", "name": "Jane Smith", "position": "Team Lead", "status": "Active"},
                {"employee_id": "3", "name": "Bob Johnson", "position": "Manager", "status": "Inactive"}
            ]
    except Exception as e:
        logger.error(f"Error fetching employees: {e}")
        employees = [
            {"employee_id": "1", "name": "John Doe", "position": "Technician", "status": "Active"},
            {"employee_id": "2", "name": "Jane Smith", "position": "Team Lead", "status": "Active"},
            {"employee_id": "3", "name": "Bob Johnson", "position": "Manager", "status": "Inactive"}
        ]

    # Create keyboard with employee list
    keyboard = []
    for employee in employees:
        status_emoji = "🟢" if employee["status"] == "Active" else "🔴"
        keyboard.append([
            InlineKeyboardButton(
                f"{status_emoji} {employee['name']} - {employee['position']}",
                callback_data=f"employee:view:{employee['employee_id']}"
            )
        ])

    # Add navigation buttons
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="team_nav:back")])

    await query.message.edit_text(
        text="👥 *Employee List*\n\n"
             "Select an employee to view details:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return EMPLOYEE_LIST_VIEW


@log_function()
async def view_employee_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display details for a specific employee"""
    query = update.callback_query
    await query.answer()

    # Store previous state for navigation
    context.user_data["prev_state"] = EMPLOYEE_LIST_VIEW

    # Get employee ID from callback data
    _, _, employee_id = query.data.split(":")

    # This would normally fetch data from API, but for now we'll use dummy data
    try:
        # Make API request to get employee details
        response = requests.get(f"{BACKEND_API_URL}/api/employees/{employee_id}")
        if response.status_code == 200:
            employee = response.json()
        else:
            # Fallback to dummy data if API fails
            employee = {
                "employee_id": employee_id,
                "name": "John Doe" if employee_id == "1" else "Jane Smith" if employee_id == "2" else "Bob Johnson",
                "phone": "123-456-7890",
                "email": f"employee{employee_id}@ecocompany.com",
                "position": "Technician" if employee_id == "1" else "Team Lead" if employee_id == "2" else "Manager",
                "status": "Active" if employee_id in ["1", "2"] else "Inactive",
                "join_date": "2023-01-15",
                "commission_rate": 10.5
            }
    except Exception as e:
        logger.error(f"Error fetching employee details: {e}")
        employee = {
            "employee_id": employee_id,
            "name": "John Doe" if employee_id == "1" else "Jane Smith" if employee_id == "2" else "Bob Johnson",
            "phone": "123-456-7890",
            "email": f"employee{employee_id}@ecocompany.com",
            "position": "Technician" if employee_id == "1" else "Team Lead" if employee_id == "2" else "Manager",
            "status": "Active" if employee_id in ["1", "2"] else "Inactive",
            "join_date": "2023-01-15",
            "commission_rate": 10.5
        }

    # Save employee data for later use
    context.user_data["employee_data"] = EmployeeData()
    for key, value in employee.items():
        if hasattr(context.user_data["employee_data"], key):
            setattr(context.user_data["employee_data"], key, value)

    # Create status emoji
    status_emoji = "🟢" if employee["status"] == "Active" else "🔴" if employee["status"] == "Inactive" else "🟠"

    # Create keyboard for employee actions
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Employee", callback_data=f"employee:edit:{employee_id}")],
        [
            InlineKeyboardButton("🔙 Back to List", callback_data="team:list_employees"),
            InlineKeyboardButton("🔝 Main Menu", callback_data="admin:team_status")
        ]
    ]

    # Display employee details
    text = (
        f"👤 *Employee Details*\n\n"
        f"*Name:* {employee['name']}\n"
        f"*Position:* {employee['position']}\n"
        f"*Status:* {status_emoji} {employee['status']}\n"
        f"*Phone:* {employee['phone']}\n"
        f"*Email:* {employee['email']}\n"
        f"*Join Date:* {employee['join_date']}\n"
        f"*Commission Rate:* {employee['commission_rate']}%\n"
    )

    await query.message.edit_text(
        text=text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return EMPLOYEE_DETAIL_VIEW


@log_function()
async def edit_employee_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display menu for editing employee details"""
    query = update.callback_query
    await query.answer()

    # Store previous state for navigation
    context.user_data["prev_state"] = EMPLOYEE_DETAIL_VIEW

    # Get employee ID from callback data
    _, _, employee_id = query.data.split(":")

    # Get employee data
    employee_data = context.user_data.get("employee_data")
    if not employee_data:
        # If no employee data found, go back to list
        return await list_employees(update, context)

    # Create keyboard for edit options
    keyboard = [
        [InlineKeyboardButton("📝 Edit Name", callback_data=f"employee:edit_name:{employee_id}")],
        [InlineKeyboardButton("📱 Edit Phone", callback_data=f"employee:edit_phone:{employee_id}")],
        [InlineKeyboardButton("📧 Edit Email", callback_data=f"employee:edit_email:{employee_id}")],
        [InlineKeyboardButton("👤 Edit Position", callback_data=f"employee:edit_position:{employee_id}")],
        [InlineKeyboardButton("💰 Edit Commission", callback_data=f"employee:edit_commission:{employee_id}")],
        [InlineKeyboardButton("🔄 Change Status", callback_data=f"employee:edit_status:{employee_id}")],
        [InlineKeyboardButton("❌ Delete Employee", callback_data=f"employee:delete:{employee_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="team_nav:back")]
    ]

    await query.message.edit_text(
        text=f"✏️ *Edit Employee: {employee_data.name}*\n\n"
             "Select what you'd like to edit:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return EMPLOYEE_EDIT_MENU


@log_function()
async def return_to_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to the main admin menu"""
    query = update.callback_query
    await query.answer()

    # Call the show_admin_menu function from your core/handlers.py
    from ..core.handlers import show_admin_menu
    await show_admin_menu(update, context)

    return ConversationHandler.END  # End the conversation



team_manager_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(team_manager_menu, pattern=r"^admin:team_status$")
    ],
    states={
        TEAM_MENU: [
            CallbackQueryHandler(start_add_employee, pattern=r"^team:add_employee$"),
            CallbackQueryHandler(list_employees, pattern=r"^team:list_employees$"),
            CallbackQueryHandler(handle_team_navigation, pattern=r"^(admin|team):"),
        ],
        ADD_EMPLOYEE_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, employee_name_provided),
            CallbackQueryHandler(handle_team_navigation, pattern=r"^(admin|team):")
        ],
        ADD_EMPLOYEE_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, employee_phone_provided),
            CallbackQueryHandler(handle_team_navigation, pattern=r"^(admin|team):")
        ],
        ADD_EMPLOYEE_EMAIL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, employee_email_provided),
            CallbackQueryHandler(handle_team_navigation, pattern=r"^(admin|team):")
        ],
        ADD_EMPLOYEE_POSITION: [
            CallbackQueryHandler(employee_position_selected, pattern=r"^position:"),
            CallbackQueryHandler(handle_team_navigation, pattern=r"^(admin|team):")
        ],
        ADD_EMPLOYEE_COMMISSION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, employee_commission_provided),
            CallbackQueryHandler(handle_team_navigation, pattern=r"^(admin|team):")
        ],
        ADD_EMPLOYEE_CONFIRM: [
            CallbackQueryHandler(confirm_add_employee, pattern=r"^team:confirm$"),
            CallbackQueryHandler(handle_team_navigation, pattern=r"^(admin|team):")
        ],
        EMPLOYEE_LIST_VIEW: [
            CallbackQueryHandler(view_employee_detail, pattern=r"^employee:view:"),
            CallbackQueryHandler(handle_team_navigation, pattern=r"^(admin|team):")
        ],
        EMPLOYEE_DETAIL_VIEW: [
            CallbackQueryHandler(edit_employee_menu, pattern=r"^employee:edit:"),
            CallbackQueryHandler(list_employees, pattern=r"^team:list_employees$"),
            CallbackQueryHandler(handle_team_navigation, pattern=r"^(admin|team):")
        ],
        EMPLOYEE_EDIT_MENU: [
            CallbackQueryHandler(start_edit_employee_name, pattern=r"^employee:edit_name:"),
            CallbackQueryHandler(start_edit_employee_phone, pattern=r"^employee:edit_phone:"),
            CallbackQueryHandler(start_edit_employee_email, pattern=r"^employee:edit_email:"),
            CallbackQueryHandler(start_edit_employee_position, pattern=r"^employee:edit_position:"),
            CallbackQueryHandler(start_edit_employee_commission, pattern=r"^employee:edit_commission:"),
            CallbackQueryHandler(start_edit_employee_status, pattern=r"^employee:edit_status:"),
            CallbackQueryHandler(confirm_delete_employee, pattern=r"^employee:delete:"),
            CallbackQueryHandler(handle_team_navigation, pattern=r"^(admin|team):")
        ],
        # Add other edit states as needed...
    },
    fallbacks=[
        CommandHandler("cancel", handle_team_navigation),
        CallbackQueryHandler(handle_team_navigation, pattern=r"^(admin|team):")
    ],
    map_to_parent={
        TEAM_MENU: ADMIN_MENU
    }
)
