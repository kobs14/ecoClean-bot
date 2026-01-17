
import os
import requests
import uuid


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

# Initialize logger
logger = get_logger(__name__)

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://api:5000")



# Define conversation states for the estimate flow
(
    SELECTING_CATEGORY,    # Choosing item category
    SELECTING_SPECIFICS,   # Selecting size/type within category
    ADDING_QUANTITY,       # Adding quantity for the selected item
    REVIEWING_ITEMS,       # Reviewing current items in estimate
    CONFIRMING_ESTIMATE,   # Final confirmation before submission
    CONFIRM_CANCEL,         # Confirm cancellation
    ASKING_CLIENT_NAME,
    ASKING_CLIENT_CONTACT,
    ADDING_NOTES
) = range(9)

# Define cleaning categories and their options
CLEANING_CATEGORIES = {
    "room": ["Small Room ($50)", "Medium Room ($75)", "Large Room ($100)"],
    "hallway": ["Small Hallway ($30)", "Large Hallway ($45)"],
    "bathroom": ["Half Bath ($35)", "Full Bath ($60)"],
    "kitchen": ["Small Kitchen ($65)", "Large Kitchen ($90)"],
    "furniture": ["Sofa ($60)", "Loveseat ($45)", "Armchair ($30)"],
    "patio": ["Small Patio ($40)", "Large Patio ($70)"],
    "other": ["Carpet Stain Treatment ($25)", "Window Cleaning ($15/window)"]
}

# Price lookup for each item (in dollars)
ITEM_PRICES = {
    "Small Room": 50,
    "Medium Room": 75,
    "Large Room": 100,
    "Small Hallway": 30,
    "Large Hallway": 45,
    "Half Bath": 35,
    "Full Bath": 60,
    "Small Kitchen": 65,
    "Large Kitchen": 90,
    "Sofa": 60,
    "Loveseat": 45,
    "Armchair": 30,
    "Small Patio": 40,
    "Large Patio": 70,
    "Carpet Stain Treatment": 25,
    "Window Cleaning": 15
}

class EstimateData:
    """Class to store estimate data during conversation"""

    def __init__(self, account_id: str):
        self.account_id = account_id
        self.client_name = ""
        self.client_contact = ""
        self.items = []  # List of {name, quantity, price_per_unit, total_price}
        self.total_price = 0.0
        self.notes = ""

    def add_item(self, name, quantity, price_per_unit):
        """Add an item to the estimate"""
        total_price = quantity * price_per_unit
        self.items.append({
            "name": name,
            "quantity": quantity,
            "price_per_unit": price_per_unit,
            "total_price": total_price
        })
        self.total_price += total_price

    def remove_item(self, index):
        """Remove an item from the estimate"""
        if 0 <= index < len(self.items):
            item = self.items.pop(index)
            self.total_price -= item["total_price"]

    def to_dict(self):
        """Convert estimate data to dictionary for API request"""
        return {
            "account_id": self.account_id,
            "client_name": self.client_name,
            "client_contact": self.client_contact,
            "items": self.items,
            "total_price": self.total_price,
            "notes": self.notes
        }

@log_function()
async def start_estimate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the estimate creation process"""
    user_id = update.effective_user.id
    logger.info(f"Starting estimate creation for user {user_id}")

    # Initialize data storage in context
    context.user_data["estimate"] = EstimateData(str(user_id))

    # Handle callback query if triggered by button
    if update.callback_query:
        await update.callback_query.answer()
        query = update.callback_query

        # Ask for client info first
        await query.message.reply_text(
            "📝 *New Cleaning Estimate*\n\n"
            "Let's create a cleaning estimate for your client.\n\n"
            "What is the client's name?",
            parse_mode='Markdown',
            reply_markup=get_nav_keyboard(include_cancel=True)
        )

        return ASKING_CLIENT_NAME
    else:
        await update.message.reply_text(
            "📝 *New Cleaning Estimate*\n\n"
            "Let's create a cleaning estimate for your client.\n\n"
            "What is the client's name?",
            parse_mode='Markdown',
            reply_markup=get_nav_keyboard(include_cancel=True)
        )

        return ASKING_CLIENT_NAME


@log_function()
async def client_name_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the client name input"""
    user_data = context.user_data["estimate"]
    user_data.client_name = update.message.text

    await update.message.reply_text(
        "Great! What is the client's contact information (phone or email)?",
        reply_markup=get_nav_keyboard(include_cancel=True)
    )

    return ASKING_CLIENT_CONTACT


@log_function()
async def client_contact_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the client contact input"""
    user_data = context.user_data["estimate"]
    user_data.client_contact = update.message.text

    # Now let's start building the estimate
    return await show_category_selection(update, context)


@log_function()
async def show_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the cleaning categories selection"""
    # Create category selection keyboard
    category_keyboard = []

    for category in CLEANING_CATEGORIES:
        category_keyboard.append([InlineKeyboardButton(
            category.capitalize(),
            callback_data=f"category:{category}"
        )])

    # Add navigation buttons
    nav_row = []
    if context.user_data["estimate"].items:  # Only show review button if items exist
        nav_row.append(InlineKeyboardButton("📋 Review Estimate", callback_data="estimate:review"))
    nav_row.append(InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel"))
    category_keyboard.append(nav_row)

    if isinstance(update, Update) and update.message:  # Coming from a text handler
        await update.message.reply_text(
            "Please select a cleaning category to add to the estimate:",
            reply_markup=InlineKeyboardMarkup(category_keyboard)
        )
    else:  # Coming from callback query
        if hasattr(update, 'callback_query'):
            query = update.callback_query
            await query.message.reply_text(
                "Please select a cleaning category to add to the estimate:",
                reply_markup=InlineKeyboardMarkup(category_keyboard)
            )
        else:
            # Handle the context.bot.send_message case
            chat_id = update.effective_chat.id
            await context.bot.send_message(
                chat_id=chat_id,
                text="Please select a cleaning category to add to the estimate:",
                reply_markup=InlineKeyboardMarkup(category_keyboard)
            )

    return SELECTING_CATEGORY


@log_function()
async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category selection"""
    query = update.callback_query
    await query.answer()

    selected_category = query.data.split(':')[1]
    context.user_data["current_category"] = selected_category

    # Show options for this category
    options = CLEANING_CATEGORIES[selected_category]
    option_keyboard = []

    for option in options:
        option_keyboard.append([InlineKeyboardButton(option, callback_data=f"option:{option}")])

    # Add back button
    option_keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data="nav:categories"),
        InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")
    ])

    await query.message.reply_text(
        f"Select a {selected_category.capitalize()} option:",
        reply_markup=InlineKeyboardMarkup(option_keyboard)
    )

    return SELECTING_SPECIFICS


@log_function()
async def option_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle specific option selection"""
    query = update.callback_query
    await query.answer()

    selected_option = query.data.split(':')[1]
    # Extract the name part without the price
    option_name = selected_option.split('(')[0].strip()

    context.user_data["current_option"] = option_name
    context.user_data["current_price"] = ITEM_PRICES[option_name]

    # Ask for quantity
    quantity_keyboard = []
    # Quick selection for common quantities
    quantity_row = []
    for qty in [1, 2, 3]:
        quantity_row.append(InlineKeyboardButton(str(qty), callback_data=f"qty:{qty}"))
    quantity_keyboard.append(quantity_row)

    # Add navigation buttons
    quantity_keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data="nav:options"),
        InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")
    ])

    await query.message.reply_text(
        f"How many {option_name}(s) would you like to add? (${context.user_data['current_price']} each)\n\n"
        f"Select a quantity or type a number:",
        reply_markup=InlineKeyboardMarkup(quantity_keyboard)
    )

    return ADDING_QUANTITY


@log_function()
async def quantity_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity input"""
    # Check if this is a button press or text input
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        quantity = int(query.data.split(':')[1])
    else:
        # Handle text input
        try:
            quantity = int(update.message.text.strip())
            if quantity <= 0:
                await update.message.reply_text(
                    "Please enter a positive number. Try again:"
                )
                return ADDING_QUANTITY
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid number. Try again:"
            )
            return ADDING_QUANTITY

    # Add the item to the estimate
    option_name = context.user_data["current_option"]
    price = context.user_data["current_price"]

    user_data = context.user_data["estimate"]
    user_data.add_item(option_name, quantity, price)

    # Provide feedback and ask if they want to add more
    total_price = quantity * price

    more_items_keyboard = [
        [InlineKeyboardButton("➕ Add More Items", callback_data="estimate:add_more")],
        [InlineKeyboardButton("📋 Review Estimate", callback_data="estimate:review")],
        [InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")]
    ]

    if update.callback_query:
        await query.message.reply_text(
            f"Added {quantity} {option_name}(s) to the estimate (${total_price:.2f}).\n\n"
            f"Would you like to add more items or review your estimate?",
            reply_markup=InlineKeyboardMarkup(more_items_keyboard)
        )
    else:
        await update.message.reply_text(
            f"Added {quantity} {option_name}(s) to the estimate (${total_price:.2f}).\n\n"
            f"Would you like to add more items or review your estimate?",
            reply_markup=InlineKeyboardMarkup(more_items_keyboard)
        )

    return REVIEWING_ITEMS


@log_function()
async def review_estimate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Review the current estimate"""
    query = update.callback_query
    await query.answer()

    user_data = context.user_data["estimate"]

    if not user_data.items:
        await query.message.reply_text(
            "Your estimate is empty. Let's add some items first."
        )
        return await show_category_selection(update, context)

    # Build the estimate summary
    summary = f"📋 *Estimate for {user_data.client_name}*\n\n"
    summary += f"👤 *Client:* {user_data.client_name}\n"
    summary += f"📞 *Contact:* {user_data.client_contact}\n\n"
    summary += "*Items:*\n"

    for idx, item in enumerate(user_data.items):
        summary += f"{idx + 1}. {item['name']} x {item['quantity']} = ${item['total_price']:.2f}\n"

    summary += f"\n💰 *Total Estimate:* ${user_data.total_price:.2f}\n\n"

    # Create review keyboard
    review_keyboard = [
        [InlineKeyboardButton("➕ Add More Items", callback_data="estimate:add_more")],
        [InlineKeyboardButton("✏️ Edit Items", callback_data="estimate:edit")],
        [InlineKeyboardButton("📝 Add Notes", callback_data="estimate:add_notes")],
        [InlineKeyboardButton("✅ Submit Estimate", callback_data="estimate:submit")],
        [InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")]
    ]

    await query.message.reply_text(
        summary,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(review_keyboard)
    )

    return CONFIRMING_ESTIMATE


@log_function()
async def edit_estimate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Edit the current estimate items"""
    query = update.callback_query
    await query.answer()

    user_data = context.user_data["estimate"]

    if not user_data.items:
        await query.message.reply_text("There are no items to edit.")
        return await show_category_selection(update, context)

    # Create a keyboard with options to remove items
    edit_keyboard = []

    for idx, item in enumerate(user_data.items):
        edit_keyboard.append([
            InlineKeyboardButton(
                f"❌ Remove: {item['name']} x {item['quantity']}",
                callback_data=f"remove:{idx}"
            )
        ])

    # Add navigation buttons
    edit_keyboard.append([
        InlineKeyboardButton("⬅️ Back to Review", callback_data="estimate:review"),
        InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")
    ])

    await query.message.reply_text(
        "Select an item to remove from the estimate:",
        reply_markup=InlineKeyboardMarkup(edit_keyboard)
    )

    return REVIEWING_ITEMS


# First, let's create the missing functions and constants

def get_nav_keyboard(include_cancel=True):
    """Create a navigation keyboard with optional cancel button"""
    keyboard = []
    if include_cancel:
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")])
    return InlineKeyboardMarkup(keyboard)


# Define state sequence for navigation
STATE_SEQUENCE = [
    ASKING_CLIENT_NAME,
    ASKING_CLIENT_CONTACT,
    SELECTING_CATEGORY,
    SELECTING_SPECIFICS,
    ADDING_QUANTITY,
    REVIEWING_ITEMS,
    CONFIRMING_ESTIMATE
]


@log_function()
async def confirm_cancellation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask for confirmation before cancelling the estimate process"""
    query = update.callback_query

    confirm_keyboard = [
        [
            InlineKeyboardButton("Yes, Cancel", callback_data="cancel:confirm"),
            InlineKeyboardButton("No, Continue", callback_data="cancel:continue")
        ]
    ]

    await query.message.reply_text(
        "Are you sure you want to cancel creating this estimate? All entered information will be lost.",
        reply_markup=InlineKeyboardMarkup(confirm_keyboard)
    )

    return CONFIRM_CANCEL


async def handle_cancel_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the cancel confirmation response"""
    query = update.callback_query
    await query.answer()

    choice = query.data.split(':')[1]

    if choice == "confirm":
        # Clear user data
        if "estimate" in context.user_data:
            del context.user_data["estimate"]

        # Use EMPLOYEE_MENU.buttons instead of EMPLOYEE_MENU
        await query.message.reply_text(
            "Estimate creation cancelled. Returning to the main menu.",
            reply_markup=EMPLOYEE_MENU.get_keyboard_markup(),
            parse_mode='Markdown'
        )
        # await query.message.reply_text(
        #     EMPLOYEE_MENU.text,
        #     reply_markup=EMPLOYEE_MENU.get_keyboard_markup(),
        #     parse_mode='Markdown'
        # )
        return ConversationHandler.END
    else:
        # Continue with the process - return to previous state
        previous_state = context.user_data.get("current_state", REVIEWING_ITEMS)
        await query.message.reply_text("Let's continue creating the estimate.")
        return await go_to_state(update, context, previous_state)


@log_function()
async def go_to_state(update: Update, context: ContextTypes.DEFAULT_TYPE, state: int) -> int:
    """Navigate to a specific state in the conversation"""
    context.user_data["current_state"] = state

    if state == ASKING_CLIENT_NAME:
        await update.callback_query.message.reply_text(
            "What is the client's name?",
            reply_markup=get_nav_keyboard(include_cancel=True)
        )
        return ASKING_CLIENT_NAME

    elif state == ASKING_CLIENT_CONTACT:
        await update.callback_query.message.reply_text(
            "What is the client's contact information (phone or email)?",
            reply_markup=get_nav_keyboard(include_cancel=True)
        )
        return ASKING_CLIENT_CONTACT

    elif state == SELECTING_CATEGORY:
        return await show_category_selection(update, context)

    elif state == REVIEWING_ITEMS:
        # Create a mock callback query for review_estimate
        return await review_estimate(update, context)

    # Default fallback
    return await show_category_selection(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /cancel command"""
    if update.message:
        await update.message.reply_text(
            "Estimate creation cancelled. Returning to the main menu.",
            reply_markup=EMPLOYEE_MENU.get_keyboard_markup(),
            parse_mode='Markdown'
        )
    else:
        await update.callback_query.message.reply_text(
            "Estimate creation cancelled. Returning to the main menu.",
            reply_markup=EMPLOYEE_MENU.get_keyboard_markup(),
            parse_mode='Markdown'
        )


    # Clear user data
    if "estimate" in context.user_data:
        del context.user_data["estimate"]

    return ConversationHandler.END


# Now, let's fix the handle_navigation function for the estimate flow

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
        current_state = context.user_data.get("current_state", SELECTING_CATEGORY)
        current_index = STATE_SEQUENCE.index(current_state)

        if current_index > 0:
            new_state = STATE_SEQUENCE[current_index - 1]
            context.user_data["current_state"] = new_state

            # Display appropriate message for new state
            return await go_to_state(update, context, new_state)

    elif action == "categories":
        # Go back to category selection
        return await show_category_selection(update, context)

    elif action == "options":
        # Go back to the options for the current category
        selected_category = context.user_data.get("current_category")
        if selected_category:
            # Re-create a callback query data
            context.update = update
            query.data = f"category:{selected_category}"
            return await category_selected(update, context)

    # Default fallback
    return context.user_data.get("current_state", SELECTING_CATEGORY)



@log_function()
async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Remove an item from the estimate"""
    query = update.callback_query
    await query.answer()

    item_idx = int(query.data.split(':')[1])
    user_data = context.user_data["estimate"]

    # Get item name before removing
    item_name = user_data.items[item_idx]["name"]
    quantity = user_data.items[item_idx]["quantity"]

    # Remove the item
    user_data.remove_item(item_idx)

    await query.message.reply_text(
        f"Removed {quantity} {item_name}(s) from the estimate."
    )

    # Return to the review
    context.update = update  # Pass update through context for the next function
    return await review_estimate(update, context)


@log_function()
async def add_notes_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt for adding notes to the estimate"""
    query = update.callback_query
    await query.answer()

    user_data = context.user_data["estimate"]

    # Create keyboard with option to skip notes
    notes_keyboard = [
        [InlineKeyboardButton("Skip Notes", callback_data="notes:skip")],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="estimate:review"),
            InlineKeyboardButton("❌ Cancel", callback_data="nav:cancel")
        ]
    ]

    current_notes = f"\n\nCurrent notes: {user_data.notes}" if user_data.notes else ""

    await query.message.reply_text(
        f"Please enter any notes for this estimate (discounts, special instructions, etc.){current_notes}",
        reply_markup=InlineKeyboardMarkup(notes_keyboard)
    )

    return ADDING_NOTES


@log_function()
async def notes_provided(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle notes input"""
    user_data = context.user_data["estimate"]

    # Check if this is a text message or callback query
    if update.message:
        notes = update.message.text
        user_data.notes = notes

        # Return to review
        await update.message.reply_text("Notes added! Returning to estimate review.")
        update.callback_query = None  # Clear callback_query to use different branch in review_estimate
        context.update = update

    elif update.callback_query:
        query = update.callback_query
        await query.answer()

        if query.data == "notes:skip":
            user_data.notes = ""
            await query.message.reply_text("No notes added. Returning to estimate review.")

        context.update = update

    # Call review_estimate with the current update
    return await review_estimate(context.update, context)


@log_function()
async def submit_estimate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle estimate submission"""
    query = update.callback_query
    await query.answer()

    user_data = context.user_data["estimate"]

    progress_message = await query.message.reply_text(
        "Submitting your estimate... Please wait."
    )

    try:
        # Submit estimate to backend API
        logger.info(f"Submitting estimate to API: {BACKEND_API_URL}/estimates/")

        # Convert data to API format
        api_data = user_data.to_dict()

        # Send request to create estimate
        response = requests.post(
            f"{BACKEND_API_URL}/estimates/",
            json=api_data
        )

        if response.status_code != 201:
            logger.error(f"API error: {response.status_code} - {response.text}")
            await progress_message.edit_text(
                "❌ Error submitting estimate. Please try again later.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Return to Menu", callback_data="menu:employee")]
                ])
            )
            return ConversationHandler.END

        # Get estimate ID from response
        estimate_id = response.json().get("estimate_id", str(uuid.uuid4()))

        # Success message
        success_message = (
            "✅ *Estimate Created Successfully!*\n\n"
            f"Estimate for {user_data.client_name} has been created.\n"
            f"Total amount: ${user_data.total_price:.2f}\n\n"
            f"Estimate ID: {estimate_id}"
        )

        await progress_message.edit_text(
            success_message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Return to Menu", callback_data="menu:employee")]
            ])
        )

        # Clear data
        if "estimate" in context.user_data:
            del context.user_data["estimate"]

        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error during estimate submission: {str(e)}")

        await progress_message.edit_text(
            "❌ Error submitting estimate. Please try again later.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Return to Menu", callback_data="menu:employee")]
            ])
        )

        return ConversationHandler.END


# Create the conversation handler for estimate creation
estimate_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_estimate, pattern=r"^quote:generate$"),
        CommandHandler("estimate", start_estimate)
    ],
    states={
        ASKING_CLIENT_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, client_name_provided),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        ASKING_CLIENT_CONTACT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, client_contact_provided),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        SELECTING_CATEGORY: [
            CallbackQueryHandler(category_selected, pattern=r"^category:"),
            CallbackQueryHandler(review_estimate, pattern=r"^estimate:review$"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        SELECTING_SPECIFICS: [
            CallbackQueryHandler(option_selected, pattern=r"^option:"),
            CallbackQueryHandler(show_category_selection, pattern=r"^nav:categories$"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        ADDING_QUANTITY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_provided),
            CallbackQueryHandler(quantity_provided, pattern=r"^qty:"),
            CallbackQueryHandler(option_selected, pattern=r"^nav:options$"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        REVIEWING_ITEMS: [
            CallbackQueryHandler(show_category_selection, pattern=r"^estimate:add_more$"),
            CallbackQueryHandler(review_estimate, pattern=r"^estimate:review$"),
            CallbackQueryHandler(edit_estimate, pattern=r"^estimate:edit$"),
            CallbackQueryHandler(remove_item, pattern=r"^remove:"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        ADDING_NOTES: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, notes_provided),
            CallbackQueryHandler(notes_provided, pattern=r"^notes:"),
            CallbackQueryHandler(review_estimate, pattern=r"^estimate:review$"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        CONFIRMING_ESTIMATE: [
            CallbackQueryHandler(show_category_selection, pattern=r"^estimate:add_more$"),
            CallbackQueryHandler(edit_estimate, pattern=r"^estimate:edit$"),
            CallbackQueryHandler(add_notes_prompt, pattern=r"^estimate:add_notes$"),
            CallbackQueryHandler(submit_estimate, pattern=r"^estimate:submit$"),
            CallbackQueryHandler(handle_navigation, pattern=r"^nav:")
        ],
        CONFIRM_CANCEL: [
            CallbackQueryHandler(handle_cancel_confirmation, pattern=r"^cancel:")
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)