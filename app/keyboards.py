from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup 
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import get_masters, get_services, get_categories

contact = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отправить контакт', request_contact=True) ]
], resize_keyboard=True, input_field_placeholder='Нажмите книпку ниже.')

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Меню')]
], resize_keyboard=True)

menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Посмотреть цены', callback_data='view_prices')],
    [InlineKeyboardButton(text='Записаться на услугу', callback_data='book_service')],
    [InlineKeyboardButton(text='Просмотреть / Отменить запись', callback_data='view_or_reschedule')],
    [InlineKeyboardButton(text='Посмотреть работы', callback_data='view_works')],
    [InlineKeyboardButton(text='Задать вопрос боту', callback_data='ask_bot')],
    [InlineKeyboardButton(text='Связаться с мастером', callback_data='contact_master')]
])

back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='back')]
])

async def masters():
    all_masters = await get_masters()
    keyboard = InlineKeyboardBuilder()
    for master in all_masters:
        keyboard.add(InlineKeyboardButton(text=master.name, callback_data=f'master_{master.id}'))
    keyboard.add(back.inline_keyboard[0][0])
    return keyboard.adjust(1).as_markup()

async def categories():
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f'category_{category.id}'))
    keyboard.add(back.inline_keyboard[0][0])
    return keyboard.adjust(1).as_markup()

async def services(category):
    all_services = await get_services(category)
    keyboard = InlineKeyboardBuilder()
    for service in all_services:
        keyboard.add(InlineKeyboardButton(text=service.name, callback_data=f'service_{service.id}'))
    keyboard.add(back.inline_keyboard[0][0])
    return keyboard.adjust(1).as_markup()