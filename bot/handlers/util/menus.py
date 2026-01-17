
from dataclasses import dataclass
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

@dataclass
class MenuTemplate:
    text: str
    buttons: list[list[InlineKeyboardButton]]

    def get_keyboard_markup(self):
        return InlineKeyboardMarkup(self.buttons)


# ---- Employee Menu ----
EMPLOYEE_MENU = MenuTemplate(
    text="🌟 *WELCOME BACK, CHAMP!* 🌟\n"
         "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
         "🔥 *Today’s Mission*\n"
         "» Deliver 5-star service\n"
         "» Log jobs in real-time\n"
         "» Keep safety first\n\n"
         "💡 *Pro Tip*: Use ‘📋 Job Report’ to\n"
         "automatically track your efficiency!\n\n"
         "🚀 *Ready to make today count?*",
    buttons=[
        # First row - core workflow
        [
            InlineKeyboardButton("📋 JOB REPORT", callback_data="report:start"),
            InlineKeyboardButton("🕒 UPDATE STATUS", callback_data="status:change")
        ],
        # Second row - resources
        [
            InlineKeyboardButton("📦 MATERIAL REQUEST", callback_data="material:request"),
            InlineKeyboardButton("💵 CREATE ESTIMATE", callback_data="quote:generate")
        ],
        # Third row - performance
        [
            InlineKeyboardButton("👥 CONTACT SUPERVISOR", callback_data="contact:supervisor"),
            InlineKeyboardButton("❓ HELP & TRAINING", callback_data="employee:help")
        ],
        # Fourth row - account
        [
            InlineKeyboardButton("⚙️ ACCOUNT SETTINGS", callback_data="employee:settings"),
            InlineKeyboardButton("📊 MY PERFORMANCE", callback_data="employee:performance")
        ],
        # Fifth row - notifications
        [
            InlineKeyboardButton("🔔 NOTIFICATIONS", callback_data="employee:notifications"),
            InlineKeyboardButton("ℹ️ COMPANY INFO", callback_data="company:info")
        ]
    ]
)


# ---- Admin Menu ----
ADMIN_MENU = MenuTemplate(
    text="🔷 *ECO CLEAN ADMIN COMMAND CENTER* 🔷\n"
         "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
         "👑 *Live Team Dashboard*\n"
         "🟢 3 Available | 🟠 2 On Job | 🔴 1 Offline\n"
         "📊 12 Jobs Today | ⚠️ 2 Pending Issues\n\n"
         "📌 *Quick Stats*\n"
         "• 📈 78% Efficiency (▲2%)\n"
         "• 💰 $4,850 Today\n"
         "• ⏱ 6.2h Avg. Job Time\n\n"
         "🛠️ *Management Tools*",
    buttons=[
        # Row 1 - Team Control
        [
            InlineKeyboardButton("👥 TEAM MANAGER", callback_data="admin:team_status"),
            InlineKeyboardButton("📊 LIVE METRICS", callback_data="admin:performance")
        ],
        # Row 2 - Data
        [
            InlineKeyboardButton("📤 EXPORT DATA", callback_data="admin:export_data"),
            InlineKeyboardButton("📄 REPORTS", callback_data="admin:generate_reports")
        ],
        # Row 3 - TOperations
        [
            InlineKeyboardButton("📦 INVENTORY", callback_data="admin:inventory"),
            InlineKeyboardButton("📝 JOB DISPATCH", callback_data="admin:dispatch")
        ],
        # Row 4 - System
        [
            InlineKeyboardButton("🚨 ALERT CENTER", callback_data="admin:alerts"),
            InlineKeyboardButton("⚙️ SYSTEM SETTINGS", callback_data="admin:settings")
        ],
        # Row 5 - Financial
        [
            InlineKeyboardButton("💸 PAYROLL", callback_data="admin:payroll"),
            InlineKeyboardButton("📅 SCHEDULER", callback_data="admin:scheduler")
        ]
    ]
)


# ---- Status Menu ----
STATUS_MENU = MenuTemplate(
    text="🔄 *Update Your Status*\n\n"
         "Select your current availability status:",
    buttons=[
        [
            InlineKeyboardButton("🟢 Available", callback_data="status:available"),
            InlineKeyboardButton("🟠 On Job", callback_data="status:on_job")
        ],
        [
            InlineKeyboardButton("🔴 Offline", callback_data="status:offline"),
            InlineKeyboardButton("🍃 Break", callback_data="status:break")
        ],
        [
            InlineKeyboardButton("📅 Set Custom", callback_data="status:custom"),
            InlineKeyboardButton("🔙 Back", callback_data="menu:employee")
        ]
    ]
)

# ---- Report Menu ----
REPORT_MENU = MenuTemplate(
    text="📋 *New Job Report*\n\n"
         "How would you like to submit your report?",
    buttons=[
        [
            InlineKeyboardButton("✍️ Text Entry", callback_data="report:text"),
            InlineKeyboardButton("🎙 Voice Note", callback_data="report:voice")
        ],
        [
            InlineKeyboardButton("📸 Photo", callback_data="report:photo"),
            InlineKeyboardButton("📹 Video", callback_data="report:video")
        ],
        [
            InlineKeyboardButton("📁 From Template", callback_data="report:template"),
            InlineKeyboardButton("🔙 Back", callback_data="menu:employee")
        ]
    ]
)