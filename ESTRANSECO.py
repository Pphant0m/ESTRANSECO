import os
import csv
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# === Налаштування ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "123456789"))

# === Стани ===
(
    CHOOSING, DATE, CURRENCY, CAR_RENTAL, MAINTENANCE, CLIENT_PURCHASES,
    ROAD_FUEL, FERRY, PHONE, ADVERTISING, FOOD_HOME,
    SHOPPING_HOME, BORDER, NOVA_POSHTA, TOTAL_INCOME
) = range(15)

MAIN_MENU = ReplyKeyboardMarkup(
    [["Внести витрати/дохід"]],
    resize_keyboard=True
)

# === Обробники ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Оберіть дію:", reply_markup=MAIN_MENU)
    return CHOOSING

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Внести витрати/дохід":
        await update.message.reply_text("Введіть дату поїздки (напр. 2025-04-30):")
        return DATE
    await update.message.reply_text("Невідома дія.")
    return CHOOSING

async def get_field(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str, next_state: int, prompt: str):
    context.user_data[key] = float(update.message.text.replace(',', '.'))
    await update.message.reply_text(prompt)
    return next_state

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text.strip()
    await update.message.reply_text("Введіть валюту доходу (USD, EUR, SEK, NOK):")
    return CURRENCY

async def get_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    currency = update.message.text.strip().upper()
    if currency not in ["USD", "EUR", "SEK", "NOK"]:
        await update.message.reply_text("Валюта має бути одна з: USD, EUR, SEK, NOK. Спробуйте ще раз.")
        return CURRENCY
    context.user_data['currency'] = currency
    await update.message.reply_text("Оренда авто (грн):")
    return CAR_RENTAL

async def get_car_rental(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await get_field(update, context, 'car_rental', MAINTENANCE, "Обслуговування авто (грн):")

async def get_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await get_field(update, context, 'maintenance', CLIENT_PURCHASES, "Покупки клієнтам (грн):")

async def get_client_purchases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await get_field(update, context, 'client_purchases', ROAD_FUEL, "Витрати на дорогу і паливо (грн):")

async def get_road_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await get_field(update, context, 'road_fuel', FERRY, "Паром (грн):")

async def get_ferry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await get_field(update, context, 'ferry', PHONE, "Телефон (грн):")

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await get_field(update, context, 'phone', ADVERTISING, "Реклама (грн):")

async def get_advertising(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await get_field(update, context, 'advertising', FOOD_HOME, "Продукти додому (грн):")

async def get_food_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await get_field(update, context, 'food_home', SHOPPING_HOME, "Покупки додому (грн):")

async def get_shopping_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await get_field(update, context, 'shopping_home', BORDER, "Кордон (грн):")

async def get_border(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await get_field(update, context, 'border', NOVA_POSHTA, "Нова Пошта (грн):")

async def get_nova_poshta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await get_field(update, context, 'nova_poshta', TOTAL_INCOME, "Загальний прибуток (грн):")

async def get_total_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['total_income'] = float(update.message.text.replace(',', '.'))

    # Підрахунок витрат і чистого доходу
    expenses = sum([
        context.user_data[key] for key in (
            'car_rental', 'maintenance', 'client_purchases', 'road_fuel', 'ferry',
            'phone', 'advertising', 'food_home', 'shopping_home', 'border', 'nova_poshta'
        )
    ])
    income = context.user_data['total_income']
    net_income = income - expenses

    # Збереження у файл
    trip_date = context.user_data['date']
    currency = context.user_data['currency']
    filename = f"finance_{trip_date}.csv"
    file_exists = os.path.exists(filename)

    with open(filename, 'a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                "Дата", "Валюта", "Оренда авто", "Обслуговування", "Клієнтські покупки",
                "Дорога+паливо", "Паром", "Телефон", "Реклама", "Продукти додому",
                "Покупки додому", "Кордон", "Нова Пошта", "Прибуток",
                "Витрати", "Чистий дохід", "Дата запису"
            ])
        writer.writerow([
            trip_date, currency, context.user_data['car_rental'], context.user_data['maintenance'],
            context.user_data['client_purchases'], context.user_data['road_fuel'],
            context.user_data['ferry'], context.user_data['phone'], context.user_data['advertising'],
            context.user_data['food_home'], context.user_data['shopping_home'],
            context.user_data['border'], context.user_data['nova_poshta'],
            income, expenses, net_income, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])

    await update.message.reply_text(
        f"✅ Записано!\nВалюта: {currency}\n"
        f"Загальні витрати: {expenses:.2f} {currency}\n"
        f"Загальний прибуток: {income:.2f} {currency}\n"
        f"Чистий дохід: {net_income:.2f} {currency}"
    )

    await context.bot.send_document(
        chat_id=ADMIN_CHAT_ID,
        document=open(filename, "rb"),
        caption=f"📊 Звіт поїздки: {trip_date}"
    )

    await update.message.reply_text("Готово! Оберіть наступну дію:", reply_markup=MAIN_MENU)
    return CHOOSING

# === Запуск бота ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_currency)],
            CAR_RENTAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_car_rental)],
            MAINTENANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_maintenance)],
            CLIENT_PURCHASES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_purchases)],
            ROAD_FUEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_road_fuel)],
            FERRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ferry)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ADVERTISING: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_advertising)],
            FOOD_HOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_food_home)],
            SHOPPING_HOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_shopping_home)],
            BORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_border)],
            NOVA_POSHTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nova_poshta)],
            TOTAL_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_total_income)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    print("🟢 Finance Bot is running...")
    app.run_polling()
