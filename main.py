import config
import logging
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto
from base import SQL
from datetime import datetime

db = SQL('db.db')  # соединение с БД

bot = Bot(token=config.TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Меню администратора
kb_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить товар", callback_data="add")]
])

# Главное меню
kb_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Посмотреть все товары", callback_data="items")],
    [InlineKeyboardButton(text="Моя корзина", callback_data="basket")],
    [InlineKeyboardButton(text="Мои заказы", callback_data="orders")],
    [InlineKeyboardButton(text="Сделать покупку", callback_data="buy")],
    [InlineKeyboardButton(text="Пополнить баланс (+100)", callback_data="up_balance")]
])

#статусы пользователя
# 0 - статус покоя
# 1 -
# 2 -
# 3 -
# 4 -
# 5 - введи название товара
# 6 - введи цену
# 7 - отправь фото

#статусы заказа
# 0 - в корзине
# 1 - заказан
#временные переменные для добавления товара
name = ''
price = 0

@dp.message(F.photo)
async def photo_handler(message):
    """Обработка загрузки фото товара."""
    global name, price
    user_id = message.from_user.id
    status = db.get_field("users", user_id, "status")  # получаем статус пользователя
    if status == 7:
        db.add_item(name, price)
        item_id = db.get_item_id(name)
        await message.answer("Товар успешно добавлен!")
        await bot.download(message.photo[-1], destination=f"images/{item_id}.png")
        db.update_field("users", user_id, "status", 0)

#когда пользователь написал сообщение
@dp.message()
async def start(message):
    global name, price
    user_id = message.from_user.id
    if not db.user_exist(user_id):#если пользователя нет в бд
        db.add_user(user_id)#добавляем
    status = db.get_field("users", user_id, "status")  # получаем статус пользователя
    admin = db.get_field("users", user_id, "admin")
    if not admin:
        await message.answer("Главное меню:", reply_markup=kb_main)
        return
    if admin and status==0:
        await message.answer("Меню администратора:", reply_markup=kb_admin)
        return
    if status == 5:
        name = message.text
        db.update_field("users", user_id, "status", 6)
        await message.answer("Введите цену товара!")
        return
    if status == 6:
        try:
            price = float(message.text)
            await message.answer("Отправьте фото товара!")
            db.update_field("users", user_id, "status", 7)
        except ValueError:
            await message.answer("Пожалуйста, введите корректную цену (число).")
        return
   

#когда пользователь нажал на inline кнопку
@dp.callback_query()
async def start_call(call):
    user_id = call.from_user.id
    if not db.user_exist(user_id):#если пользователя нет в бд
        db.add_user(user_id)#добавляем
    if call.data == "add":
        await call.answer("Введите название товара.")
        db.update_field("users", user_id, "status", 5)
    if call.data == "basket":
        items_list = db.get_orders(user_id, 0)
        if not items_list:
            await call.answer("Нет товаров в корзине!")
            return
        await call.message.answer("Ваша корзина:")
        for i in range(len(items_list)):
            order_id, item_id, _, count, _, _, _, name, price, _ = items_list[i]
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="-", callback_data=f"minus_{item_id}"),
                InlineKeyboardButton(text=f"{count}", callback_data="number"),
                InlineKeyboardButton(text="+", callback_data=f"plus_{item_id}")]
            ])
            await call.message.answer(f"Название: {name}\nЦена: {price}", reply_markup=kb)
    if call.data == "orders":
        items_list = db.get_orders(user_id, 1)
        if not items_list:
            await call.answer("Вы ещё ничего не заказывали!")
            return
        await call.message.answer("Ваша история заказов:")
        for i in range(len(items_list)):
            order_id, _, item_id, count, _, date, _, name, price, _ = items_list[i]
            await call.message.answer(f"Название: {name}\nЦена: {price} Количество: {count} Дата: {date}")
    if call.data == "items":
        items = db.get_items_by_status(1)
        if not items:
            await call.answer("Нет доступных товаров!")
            return
        await call.message.answer("Доступные товары:")
        for i in range(len(items)):
            item_id, name, price, item_status = items[i]
            try:
                image = FSInputFile(f"images/{item_id}.png")
                await bot.send_photo(call.message.chat.id, image)
            except:
                await call.message.answer("Фото для этого товара не найдено.")
            count = db.get_count(item_id, user_id, 0)
            if count == 0:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Добавить в корзину", callback_data=f"add_{item_id}")],
                ])
            else:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="-", callback_data=f"minus_{item_id}"),
                     InlineKeyboardButton(text=f"{count}", callback_data="number"),
                     InlineKeyboardButton(text="+", callback_data=f"plus_{item_id}")]
                ])
            await call.message.answer(f"Название: {name}\nЦена: {price}", reply_markup=kb)
    if "add_" in call.data:
        item_id = int(call.data[4:])
        db.add_order(user_id, item_id)
        count = 1
        await call.answer("Товар добавлен в корзину!")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="-", callback_data=f"minus_{item_id}"),
             InlineKeyboardButton(text=f"{count}", callback_data="number"),
             InlineKeyboardButton(text="+", callback_data=f"plus_{item_id}")]
        ])
        await call.message.edit_text(call.message.text, reply_markup=kb)
    if "plus_" in call.data:
        item_id = int(call.data[5:])
        order_id = db.get_order_id(item_id, user_id, 0)
        if order_id == 0:
            await call.answer("Заказ не найден!")
            return
        count = db.get_field("orders", order_id, "count")
        count += 1
        db.update_field("orders", order_id, "count", count)
        kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="-", callback_data=f"minus_{item_id}"),
                InlineKeyboardButton(text=f"{count}", callback_data="number"),
                InlineKeyboardButton(text="+", callback_data=f"plus_{item_id}")]
            ])
        await call.message.edit_text(call.message.text,  reply_markup=kb)
    if "minus_" in call.data:
        item_id = int(call.data[6:])
        order_id = db.get_order_id(item_id, user_id, 0)
        if order_id == 0:
            await call.answer("Заказ не найден!")
            return
        count = db.get_field("orders", order_id, "count")
        count -= 1
        if count < 1:
            db.delete_order(user_id, item_id)
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Добавить в корзину", callback_data=f"add_{item_id}")]])
            await call.message.edit_text(call.message.text,  reply_markup=kb)
            return
        db.update_field("orders", order_id, "count", count)
        kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="-", callback_data=f"minus_{item_id}"),
                InlineKeyboardButton(text=f"{count}", callback_data="number"),
                InlineKeyboardButton(text="+", callback_data=f"plus_{item_id}")]
            ])
        await call.message.edit_text(call.message.text,  reply_markup=kb)
    if call.data == "buy":
        orders = db.get_orders(user_id, 0)
        if not orders:
            await call.answer("Ваша корзина пуста!")
            return
        total_cost = 0
        for i in range(len(orders)):
            total_cost += orders[i][-2]*orders[i][3]
        balance = db.get_field("users", user_id, "balance")
        if balance < total_cost:
            await call.answer(f"Недостаточно средств! Итоговая сумма: {total_cost}")
            return
        #если денег хватает
        db.update_field("users", user_id, "balance", balance - total_cost)
        for i in range(len(orders)):
            order_id = orders[i][0]
            current_time = datetime.now()
            formatted_time = current_time.strftime("%d.%m.%Y %H:%M")
            db.update_field('orders', order_id, 'status',1)
            db.update_field('orders', order_id, 'data', formatted_time)
        await call.answer(f"Покупка совершена! Итоговая сумма: {total_cost}")
    if call.data == "up_balance":
        balance = db.get_field("users", user_id, "balance")
        balance += 100
        db.update_field("users", user_id, "balance", balance)
        await call.answer(f"Ваш новый баланс: {balance}")
        
        
            
    await bot.answer_callback_query(call.id)#ответ на запрос, чтобы бот не зависал

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
