import telebot
from telebot import types
from keyboard import start_keyboard, menu_keyboard, cart_keyboard, accept_keyboard, location_keyboard
from json_core import write_json, read_json, add_to_cart, del_from_cart, calculate_cart_total
from menu import *
from dotenv import load_dotenv
import os


load_dotenv()

TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}! 👋', reply_markup=start_keyboard())
    user_data = read_json()
    if str(message.chat.id) not in user_data["clients"]:
        user_data["clients"][str(message.chat.id)] = {"cart": {}}
        write_json(user_data)
        bot.send_message(message.chat.id, "Для завершения регистрации введите /add_info")

@bot.message_handler(commands=['add_info'])
def add_info(message):
    bot.send_message(message.chat.id, "Введите свое имя")
    bot.register_next_step_handler(message, process_info)

def process_info(message):
    user_data = read_json()
    if str(message.chat.id) not in user_data["clients"]:
        user_data["clients"][str(message.chat.id)] = {"cart": {}}
    user_data["clients"][str(message.chat.id)]["name"] = message.text
    write_json(user_data)
    bot.send_message(message.chat.id, "Введите свой номер телефона")
    bot.register_next_step_handler(message, save_info)

def save_info(message):
    user_data = read_json()
    # Более гибкая проверка номера телефона
    phone = ''.join(filter(str.isdigit, message.text))
    if len(phone) >= 10:
        user_data["clients"][str(message.chat.id)]["phone"] = phone
        write_json(user_data)
        bot.send_message(message.chat.id, "✅ Ваши данные сохранены!") 
    else:
        bot.send_message(message.chat.id, "❌ Введите корректный номер телефона!")  
        bot.register_next_step_handler(message, save_info)   

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    try:
        if call.data.startswith("page_"):
            _, page = call.data.split("_")
            keyboard = menu_keyboard(int(page))
            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text="🍽️ **Меню**\nВыберите блюдо:", 
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        elif call.data.startswith("item_"):
            # Исправлено: получаем название блюда напрямую из callback_data
            item_name = call.data[5:]  # Убираем префикс "item_"
            add_to_cart(call.message.chat.id, item_name)
            bot.answer_callback_query(call.id, f"✅ {item_name} добавлено в заказ!")
        elif call.data.startswith("minus_"):
            _, item = call.data.split('_', 1)  # Исправлено: разбиваем только по первому '_'
            del_from_cart(call.message.chat.id, item)
            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text="🛒 **Ваша корзина**", 
                parse_mode='Markdown',
                reply_markup=cart_keyboard(str(call.message.chat.id))
            )
        elif call.data.startswith("plus_"):
            _, item = call.data.split('_', 1)  # Исправлено: разбиваем только по первому '_'
            add_to_cart(call.message.chat.id, item) 
            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text="🛒 **Ваша корзина**", 
                parse_mode='Markdown',
                reply_markup=cart_keyboard(str(call.message.chat.id))
            ) 
        elif call.data == "cancel":
            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text="❌ Заказ отменен. Вы можете изменить заказ."
            )    
        elif call.data == "confirm":
            user_data = read_json()
            client_id = str(call.message.chat.id)
    # Проверяем, что корзина не пуста
            if client_id not in user_data["clients"] or not user_data["clients"][client_id].get("cart"):
                bot.send_message(call.message.chat.id, "❌ Ваша корзина пуста!")
                return
                
            total_price = calculate_cart_total(call.message.chat.id)
            bot.send_message(
                call.message.chat.id, 
                f"📍 Куда доставить заказ?\n\nВы можете:\n• Написать адрес текстом\n• Или отправить местоположение", 
                reply_markup=location_keyboard()
            )
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: create_order(m, total_price))
            
    except Exception as e:
        print(f"Error in callback handler: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")

def create_order(message, price):
    if message.content_type == 'text':
        address = message.text
    elif message.content_type == 'location':
        coord1 = message.location.latitude
        coord2 = message.location.longitude 
        address = f"📍 Координаты: {coord1:.6f}, {coord2:.6f}"  
    else:
        bot.send_message(message.chat.id, '❌ Неверный формат адреса')  
        return
        
    # Формируем красивое сообщение о заказе
    user_data = read_json()
    client_id = str(message.chat.id)
    cart = user_data["clients"][client_id]["cart"]
    
    order_details = "🍽️ **Ваш заказ:**\n"
    for name, quantity in cart.items():
        order_details += f"• {name} × {quantity}\n"
    
    order_details += f"\n💰 **Итого:** {price} руб."
    order_details += f"\n📍 **Адрес:** {address}"
    order_details += f"\n💵 **Оплата:** наличными курьеру"
    
    bot.send_message(message.chat.id, order_details, parse_mode='Markdown')
    bot.send_message(message.chat.id, "✅ Заказ принят в работу! 🚀")
    
    # Очищаем корзину после заказа
    user_data["clients"][client_id]["cart"] = {}
    write_json(user_data)

@bot.message_handler(func=lambda message: True)  
def handle_all(message):
    if message.text == 'Меню 🍕':
        bot.send_message(message.chat.id, '🍽️ **Выберите блюдо из меню:**', parse_mode='Markdown', reply_markup=menu_keyboard())
    elif message.text == 'Корзина 🛒':
        user_data = read_json()
        client_id = str(message.chat.id)
        
        if client_id not in user_data["clients"] or not user_data["clients"][client_id].get("cart"):
            bot.send_message(message.chat.id, "🛒 Ваша корзина пуста")
        else:
            total_price = calculate_cart_total(message.chat.id)
            cart_text = f"🛒 **Ваша корзина**\n\n"
            
            cart = user_data["clients"][client_id]["cart"]
            for name, quantity in cart.items():
                cart_text += f"• {name} × {quantity}\n"
            
            cart_text += f"\n💰 **Общая стоимость:** {total_price} руб."
            bot.send_message(message.chat.id, cart_text, parse_mode='Markdown', reply_markup=cart_keyboard(client_id))
            
    elif message.text == "Заказать 🍽":
        user_data = read_json()
        client_id = str(message.chat.id)
        
        if client_id not in user_data["clients"] or not user_data["clients"][client_id].get("cart"):
            bot.send_message(message.chat.id, "❌ Ваша корзина пуста!")
            return
            
        cart = user_data["clients"][client_id]["cart"]
        total_price = calculate_cart_total(message.chat.id)
        
        msg = "🍽️ **Ваш заказ:**\n\n"
        for name, quantity in cart.items():   
            msg += f"• {name} × {quantity}\n"
        msg += f"\n💰 **Общая стоимость:** {total_price} руб."
        
        bot.send_message(message.chat.id, msg, parse_mode='Markdown')
        bot.send_message(message.chat.id, "✅ Подтвердите правильность заказа:", reply_markup=accept_keyboard())
    else:
        bot.send_message(message.chat.id, '❓ Я вас не понял. Используйте кнопки меню.')

if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)

