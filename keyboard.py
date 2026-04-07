from telebot import types
from menu import *
from json_core import read_json

ITEMS_PER_PAGE = 5

def start_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('Меню 🍕')  # Исправлена опечатка в тексте
    btn2 = types.KeyboardButton('Корзина 🛒')  # Изменен эмодзи для корзины
    btn3 = types.KeyboardButton('Заказать 🍽')
    markup.add(btn1, btn2, btn3)
    return markup

def menu_keyboard(page=0):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    
    # Создаем кнопки для элементов текущей страницы
    for i, item in enumerate(menu_items[start_index:end_index], start=start_index):
        # Исправлено: передаем название блюда вместо индекса
        button = types.InlineKeyboardButton(
            text=f"{item['name']} - {item['price']}", 
            callback_data=f"item_{item['name']}"  # Теперь передаем название, а не индекс
        )    
        keyboard.add(button)    
    
    # Навигационные кнопки
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"page_{page - 1}"))
    if end_index < len(menu_items):
        nav_buttons.append(types.InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"page_{page + 1}"))
    
    if nav_buttons:
        keyboard.row(*nav_buttons)
        
    return keyboard

def cart_keyboard(client_id):
    user_data = read_json()
    # Исправлено: проверяем существование пользователя и корзины
    if str(client_id) not in user_data["clients"] or "cart" not in user_data["clients"][str(client_id)]:
        cart = {}
    else:
        cart = user_data["clients"][str(client_id)]["cart"]
        
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    
    if not cart:
        keyboard.add(types.InlineKeyboardButton("Корзина пуста", callback_data="empty"))
    else:
        for name, quantity in cart.items():
            button_text = f"{name} × {quantity}"
            button_plus = types.InlineKeyboardButton("➕", callback_data=f"plus_{name}") 
            button_minus = types.InlineKeyboardButton("➖", callback_data=f"minus_{name}")
            keyboard.row(button_minus, types.InlineKeyboardButton(button_text, callback_data='...'), button_plus)
    
    return keyboard

def accept_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
    btn2 = types.InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm")
    keyboard.add(btn1, btn2)
    return keyboard

def location_keyboard():
    """Новая клавиатура для запроса местоположения"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("📍 Отправить местоположение", request_location=True)
    keyboard.add(btn)
    return keyboard
