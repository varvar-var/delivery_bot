import json
from menu import *

def read_json():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"clients": {}}  # Исправлено: возвращаем структуру с clients
    
def write_json(data):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_to_cart(client_id, item):
    user_data = read_json()
    # Исправлено: проверяем существование структуры данных
    if str(client_id) not in user_data["clients"]:
        user_data["clients"][str(client_id)] = {"cart": {}}
    
    cart = user_data["clients"][str(client_id)]["cart"]
    if item in cart:
        cart[item] += 1
    else:
        cart[item] = 1    
    user_data["clients"][str(client_id)]["cart"] = cart
    write_json(user_data) 

def del_from_cart(client_id, item):
    user_data = read_json()
    cart = user_data["clients"][str(client_id)]["cart"]
    if item in cart:  # Добавлена проверка существования элемента
        if cart[item] == 1:
            del cart[item]
        else:
            cart[item] -= 1 
        user_data["clients"][str(client_id)]["cart"] = cart
        write_json(user_data)  

def calculate_cart_total(client_id):
    user_data = read_json()
    # Исправлено: проверяем существование пользователя и корзины
    if str(client_id) not in user_data["clients"] or "cart" not in user_data["clients"][str(client_id)]:
        return 0
        
    cart = user_data["clients"][str(client_id)]["cart"]
    total = 0
    for name, quantity in cart.items():
        for item in menu_items:
            if name == item['name']:
                price = int(item['price'].split()[0])
                total += price * quantity
    return total
