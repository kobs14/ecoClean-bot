import os
import sys

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler
)

from handlers.logger_config import get_logger, log_function

# Get module-level logger
logger = get_logger(__name__)


@log_function()
def run_bot():
    """Initialize and run the Telegram bot"""
    logger.info("Starting EcoClean Bot...")

    from handlers.core.handlers import (
        start,
        show_employee_menu,
        # handle_callback
    )

    from handlers.employee.job_report import job_report_conv_handler
    from handlers.employee.estimate import estimate_conv_handler
    from handlers.employee.update_status import status_conv_handler
    from handlers.employee.material_request import material_request_conv_handler
    from handlers.admin.reports import report_conv_handler
    from handlers.admin.metrics import metrics_conv_handler
    from handlers.admin.team_manager import team_manager_conv_handler
    # from handlers.admin.team_manager1 import team_manager_conv_handler

    try:
        # Log token length to verify it's available
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.critical("No Telegram token found in environment variables!")
            sys.exit(1)

        # Build application
        app = ApplicationBuilder().token(token).build()

        # Add handlers
        logger.debug("Registering command handlers")
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("menu", show_employee_menu))

        # Add job report conversation handler
        logger.debug("Registering job report conversation handler")
        app.add_handler(job_report_conv_handler)

        # Add estimate conversation handler
        logger.debug("Registering job report conversation handler")
        app.add_handler(estimate_conv_handler)

        # Add update_status conversation handler
        logger.debug("Update status conversation handler")
        app.add_handler(status_conv_handler)

        # Add material_request conversation handler
        logger.debug("Request materials conversation handler")
        app.add_handler(material_request_conv_handler)

        # Add live_metrics_handler conversation handler (ADMIN)
        logger.debug("Live metrics conversation handler")
        app.add_handler(metrics_conv_handler)

        # Add reports conversation handler (ADMIN)
        logger.debug("Reports conversation handler")
        app.add_handler(report_conv_handler)

        # Add Team Manager conversation handler (ADMIN)
        logger.debug("Team Manager conversation handler")
        app.add_handler(team_manager_conv_handler)

        # logger.debug("Registering callback query handler")
        # app.add_handler(CallbackQueryHandler(handle_callback))

        logger.info("🤖 EcoClean Bot is starting polling...")
        app.run_polling()

    except Exception as e:
        logger.critical(f"Failed to start bot: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_bot()