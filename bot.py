import os
from telegram import Update
import sqlite3
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes
)

BOT_TOKEN = os.environ.get('TRACKER_TELEGRAM_TOKEN')
DB_NAME = "expense_tracker.db"

def init_database():
    """Initialize the database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT,
            budget INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_categories():
    """Get all categories from the database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row  # To access columns by name

        cursor.execute("SELECT name, budget FROM categories ORDER BY name")
        
        # Convert to list of dictionaries
        categories = [{'name': row['name'], 'budget': row['budget']} for row in cursor.fetchall()]
        return {'categories': categories}
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to the Expense Tracker Bot! Use /expenses to calculate your daily expenses."
    )

async def compute_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = [arg for arg in context.args if arg.isdigit()]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Your expenses today is: {sum(map(int, result))} JPY.")
    
async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Usage: /add_category <category_name> <budget>"
        )
        return

    category_name = context.args[0]
    budget = context.args[1]

    try:
        budget_value = int(budget)
    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Budget must be a number."
        )
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO categories (name, budget) VALUES (?, ?)", (category_name, budget_value))
    conn.commit()
    conn.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Category '{category_name}' with budget {budget_value} JPY added successfully."
    )

async def get_categories_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = get_categories()
    if not categories or not categories['categories']:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No categories found. Please add a category using /add_category."
        )
        return

    response = "Categories:\n"
    for category in categories['categories']:
        response += f"{category['name']}: {category['budget']} JPY\n"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response
    )
    
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please use the /expenses command followed by your expenses in JPY."
    )

def run_telegram_bot():
    init_database()
    print ("Starting telegram bot...")
    application = Application.builder().token(BOT_TOKEN).build()

    start_handler = CommandHandler("start", send_welcome)
    application.add_handler(start_handler)
    application.add_handler(CommandHandler("expenses", compute_expenses))
    application.add_handler(CommandHandler("add_category", add_category))
    application.add_handler(CommandHandler("categories", get_categories_handler))

    application.run_polling()

if __name__ == "__main__":
    if BOT_TOKEN:
        run_telegram_bot()
    else:
        print("Please set the TRACKER_TELEGRAM_TOKEN environment variable.")