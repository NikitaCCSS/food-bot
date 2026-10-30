import telebot
from telebot import types
import json
import datetime
import matplotlib.pyplot as plt
import io

bot = telebot.TeleBot("YOUR_TOKEN_HERE")

FILE_NAME = "food.json"

def load_data():
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Добавить покупку")
    btn2 = types.KeyboardButton("Мои расходы")
    btn3 = types.KeyboardButton("Что покупаю чаще")
    btn4 = types.KeyboardButton("Удалить покупку")
    btn5 = types.KeyboardButton("Расходы за сегодня") 
    btn6 = types.KeyboardButton("График расходов")    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}! Я твой помощник по продуктам.", reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "Добавить покупку":
        bot.send_message(message.chat.id, "Напиши, что купил и за сколько (через запятую, например: Хлеб 50, Молоко 80).")
        bot.register_next_step_handler(message, add_purchase)
    elif message.text == "Мои расходы":
        show_expenses(message)
    elif message.text == "Что покупаю чаще":
        show_top_products(message)
    elif message.text == "Удалить покупку":
        bot.send_message(message.chat.id, "Напиши название товара, который хочешь удалить (например: Хлеб).")
        bot.register_next_step_handler(message, delete_purchase)
    elif message.text == "Расходы за сегодня": 
        show_today_expenses(message)
    elif message.text == "График расходов":    
        show_chart(message)
    else:
        bot.send_message(message.chat.id, "Нажми на кнопку ниже.")

def add_purchase(message):
    items = message.text.split(",")
    added_items = []
    today = datetime.date.today().strftime("%d.%m.%Y")
    data = load_data()
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    for item_str in items:
        parts = item_str.strip().split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, f"⚠️ Пропущено: '{item_str.strip()}'. Формат: Название Цена.")
            continue
        product_name = parts[0]
        try:
            product_price = int(parts[1])
        except ValueError:
            bot.send_message(message.chat.id, f"⚠️ Ошибка в цене для '{product_name}'. Цена должна быть числом.")
            continue

        purchase = {"user_id": user_id, "user_name": user_name, "name": product_name, "price": product_price, "date": today}
        data.append(purchase)
        added_items.append(f"{product_name} ({product_price} руб.)")

    if added_items:
        save_data(data)
        bot.send_message(message.chat.id, f"✅ Записал: {', '.join(added_items)}")
    else:
        bot.send_message(message.chat.id, "❌ Ничего не добавлено. Проверь формат.")

def show_expenses(message):
    data = load_data()
    user_id = message.from_user.id
    user_data = [item for item in data if item.get("user_id") == user_id]
    if not user_data:
        bot.send_message(message.chat.id, "У тебя пока нет покупок.")
        return
    total = sum(item["price"] for item in user_data)
    last_five = user_data[-5:]
    text = "📊 *Твои последние покупки:*\n\n"
    for item in last_five:
        text += f"• {item['name']} — {item['price']} руб. ({item['date']})\n"
    text += f"\n💰 *Общая сумма: {total} руб.*"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

def show_top_products(message):
    data = load_data()
    user_id = message.from_user.id
    user_data = [item for item in data if item.get("user_id") == user_id]
    if not user_data:
        bot.send_message(message.chat.id, "Пока нет покупок для анализа.")
        return
    counts = {}
    for item in user_data:
        name = item["name"]
        counts[name] = counts.get(name, 0) + 1
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    text = "🏆 *Топ-3 самых частых покупок:*\n\n"
    for i, (name, count) in enumerate(sorted_items[:3], 1):
        text += f"{i}. {name} — {count} раз(а)\n"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

def delete_purchase(message):
    product_to_delete = message.text.strip()
    data = load_data()
    user_id = message.from_user.id
    new_data = [item for item in data if not (item["name"].lower() == product_to_delete.lower() and item.get("user_id") == user_id)]
    if len(new_data) == len(data):
        bot.send_message(message.chat.id, f"❌ У тебя нет товара '{product_to_delete}'.")
    else:
        save_data(new_data)
        deleted_count = len(data) - len(new_data)
        bot.send_message(message.chat.id, f"🗑️ Удалено {deleted_count} записей о товаре '{product_to_delete}'.")

def show_today_expenses(message):
    data = load_data()
    user_id = message.from_user.id
    today = datetime.date.today().strftime("%d.%m.%Y")
    
    today_data = [item for item in data if item.get("user_id") == user_id and item.get("date") == today]
    
    if not today_data:
        bot.send_message(message.chat.id, "Сегодня ты еще ничего не покупал.")
        return
        
    total = sum(item["price"] for item in today_data)
    text = f"📅 *Твои покупки за сегодня ({today}):*\n\n"
    for item in today_data:
        text += f"• {item['name']} — {item['price']} руб.\n"
    text += f"\n💰 *Потрачено за сегодня: {total} руб.*"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

def show_chart(message):
    data = load_data()
    user_id = message.from_user.id
    user_data = [item for item in data if item.get("user_id") == user_id]
    
    if not user_data:
        bot.send_message(message.chat.id, "Нет данных для графика.")
        return
        
    expenses_by_product = {}
    for item in user_data:
        name = item["name"]
        price = item["price"]
        expenses_by_product[name] = expenses_by_product.get(name, 0) + price
        
    sorted_expenses = sorted(expenses_by_product.items(), key=lambda x: x[1], reverse=True)[:5]
    
    labels = [item[0] for item in sorted_expenses]
    sizes = [item[1] for item in sorted_expenses]
    

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title("Твои расходы (Топ-5)")
    plt.axis('equal') 
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close() 
    
    bot.send_photo(message.chat.id, buf)

print("Бот запущен...")
bot.polling(none_stop=True) 