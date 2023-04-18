import logging
from typing import Dict

from aiogram import Bot, Dispatcher, types
from aiogram.types import CallbackQuery
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

bot = Bot(token="5999890636:AAF3aSLtWBBJ2J9mTnrIl6e21rJhNGDGS1I")
dp = Dispatcher(bot)

# A dictionary to store the current order of each user
store_orders = {}


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    store_orders[user_id] = {}
    await message.reply("Welcome to the store! You can use the following commands:\n"
                        "/add - Add items to your order\n"
                        "/remove - Remove items from your order\n"
                        "/view - View your current order\n"
                        "/checkout - Place your order")


@dp.message_handler(commands=['add'])
async def add_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('🍔 Burger', callback_data='add burger'))
    keyboard.add(InlineKeyboardButton('🍟 Fries', callback_data='add fries'))
    keyboard.add(InlineKeyboardButton('🍦 Ice cream', callback_data='add ice cream'))
    keyboard.add(InlineKeyboardButton('🥪 Sandwich', callback_data='add sandwich'))
    keyboard.add(InlineKeyboardButton('🍕 Pizza', callback_data='add pizza'))
    keyboard.add(InlineKeyboardButton('🌮 Taco', callback_data='add taco'))
    keyboard.add(InlineKeyboardButton('🍩 Donut', callback_data='add donut'))
    keyboard.add(InlineKeyboardButton('🥨 Pretzel', callback_data='add pretzel'))
    keyboard.add(InlineKeyboardButton('🍺 Beer', callback_data='add beer'))
    keyboard.add(InlineKeyboardButton('🍷 Wine', callback_data='add wine'))
    await message.reply("Please select an item to add to your order:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('add'))
async def process_add_callback(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    item = callback_query.data.split(' ')[1]
    store_order = store_orders.get(user_id)
    if not store_order:
        store_order = {}
        store_orders[user_id] = store_order
    store_order[item] = store_order.get(item, 0) + 1
    message_text = f"Added 1 {item} to your order"
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, text=message_text)
    await bot.answer_callback_query(callback_query.id)


@dp.message_handler(commands=['remove'])
async def remove_handler(message: types.Message):
    user_id = message.from_user.id
    store_order = store_orders.get(user_id)
    if not store_order:
        await message.reply("You have not placed an order yet!")
        return
    keyboard = InlineKeyboardMarkup()
    for item, quantity in store_order.items():
        keyboard.add(InlineKeyboardButton(f"{item} ({quantity})", callback_data=f"remove {item}"))
    await message.reply("Please select an item to remove from your order:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('remove'))
async def process_remove_callback(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    item = callback_query.data.split(' ')[1]
    store_order = store_orders.get(user_id)
    if not store_order or item not in store_order:
        message_text = f"You do not have {item} in your order"
    else:
        store_order[item] -= 1
        if store_order[item] == 0:
            del store_order[item]
        message_text = f"Removed 1 {item} from your order"
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, text=message_text)
    await bot.answer_callback_query(callback_query.id)


@dp.message_handler(commands=['view'])
async def view_handler(message: types.Message):
    user_id = message.from_user.id
    store_order = store_orders.get(user_id)
    if not store_order:
        await message.reply("You have not placed an order yet!")
    else:
        order_text = "Your current order:\n"
    for item, quantity in store_order.items():
            order_text += f"{item} ({quantity})\n"
            await message.reply(order_text)

# @dp.message_handler(commands=['checkout'])
# async def checkout_handler(message: types.Message):
#     user_id = message.from_user.id
#     store_order = store_orders.get(user_id)
#     if not store_order:
#         await message.reply("You have not placed an order yet!")
#     else:
#         total_price = calculate_total_price(store_order)
#     await message.reply(f"Your total order price is {total_price}. "
#     f"Please pay using one of the following methods: "
#     f"credit card, PayPal, or Bitcoin. "
#     f"Your order will be delivered in 30 minutes.")
#     store_orders[user_id] = {} 


@dp.message_handler(commands=['checkout'])
async def checkout_handler(message: types.Message):
    user_id = message.from_user.id
    store_order = store_orders.get(user_id)
    if not store_order:
        await message.reply("You have not placed an order yet!")
        return

    total_price = calculate_total_price(store_order)
    order_text = "New order:\n"
    for item, quantity in store_order.items():
        order_text += f"{item} ({quantity})\n"
    order_text += f"Total price: {total_price}"

    owner_chat_id = '1040911351'

    # Send a notification to the owner
    keyboard = InlineKeyboardMarkup()
    confirm_button = InlineKeyboardButton('Confirm', callback_data=f"confirm {user_id}")
    reject_button = InlineKeyboardButton('Reject', callback_data=f"reject {user_id}")
    keyboard.add(confirm_button, reject_button)
    await bot.send_message(owner_chat_id, order_text, reply_markup=keyboard)

    # Clear the user's order
    store_orders[user_id] = {}


@dp.callback_query_handler(lambda c: c.data.startswith(('confirm', 'reject')))
async def process_order_callback(callback_query: CallbackQuery):
    action, user_id = callback_query.data.split(' ')
    store_order = store_orders.get(int(user_id))

    if not store_order:
        message_text = "Order already processed."
    elif action == 'confirm':
        total_price = calculate_total_price(store_order)
        message_text = f"Confirmed order for user {user_id}. Total price: {total_price}"
        store_orders[int(user_id)] = {}
    else:
        message_text = f"Rejected order for user {user_id}"
        store_orders[int(user_id)] = {}

    await bot.send_message(callback_query.from_user.id, message_text)
    await bot.answer_callback_query(callback_query.id)




# clear the order

def calculate_total_price(store_order: Dict[str, int]) -> float:
    prices = {"burger": 5.99, "fries": 2.99, "ice cream": 3.49, "sandwich": 6.99, 
    "pizza": 8.99, "taco": 4.99, "donut": 1.49, "pretzel": 2.49, "beer": 4.99, "wine": 9.99}
    total = 0.0
    for item, quantity in store_order.items():
        price = prices.get(item, 0.0)
        total += price * quantity
    return round(total, 2)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
