from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup 
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import get_masters, get_services, get_categories

contact = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отправить контакт', request_contact=True) ]
], resize_keyboard=True, input_field_placeholder='Нажмите книпку ниже.')

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Меню')]
], resize_keyboard=True)

back_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад в меню', callback_data='Меню')]
])

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

category_choice = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💅 Маникюр', callback_data='category_1')],
    [InlineKeyboardButton(text='👣 Педикюр', callback_data='category_2')],
    [InlineKeyboardButton(text='⬅️ Назад в меню', callback_data='Меню')]
])

confirm_booking = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm_yes')],
    [InlineKeyboardButton(text='❌ Отменить', callback_data='confirm_no')]
])

another_service = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Да, записаться еще', callback_data='another_service_yes')],
    [InlineKeyboardButton(text='Нет, вернуться в меню', callback_data='another_service_no')]
])

yes_no_extension = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Да', callback_data='extension_yes')],
    [InlineKeyboardButton(text='❌ Нет', callback_data='extension_no')]
])

yes_no_design = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Да', callback_data='design_yes')],
    [InlineKeyboardButton(text='❌ Нет', callback_data='design_no')]
])

skip_comment = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⏩ Пропустить', callback_data='skip_comment')]
])

async def masters():
    all_masters = await get_masters()
    keyboard = InlineKeyboardBuilder()
    for master in all_masters:
        keyboard.add(InlineKeyboardButton(text=master.name, callback_data=f'master_{master.id}'))
    keyboard.add(back_menu.inline_keyboard[0][0])
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

async def masters_for_service(masters):
    keyboard = InlineKeyboardBuilder()
    for master in masters:
        keyboard.add(InlineKeyboardButton(text=master.name, callback_data=f'master_{master.id}'))
    keyboard.add(back.inline_keyboard[0][0])
    return keyboard.adjust(1).as_markup()

async def dates(dates_list):
    keyboard = InlineKeyboardBuilder()
    for date in dates_list:
        date_str = date.strftime('%Y-%m-%d')
        date_display = date.strftime('%d.%m.%Y')
        # Добавляем эмодзи для сегодня и завтра
        import datetime
        today = datetime.date.today()
        if date == today:
            date_display = f"📅 Сегодня ({date_display})"
        elif date == today + datetime.timedelta(days=1):
            date_display = f"📅 Завтра ({date_display})"
        else:
            date_display = f"📅 {date_display}"
        keyboard.add(InlineKeyboardButton(text=date_display, callback_data=f'date_{date_str}'))
    keyboard.add(back.inline_keyboard[0][0])
    return keyboard.adjust(1).as_markup()

async def hours(hours_list):
    keyboard = InlineKeyboardBuilder()
    for hour in hours_list:
        keyboard.add(InlineKeyboardButton(text=f"{hour:02d}:--", callback_data=f'hour_{hour}'))
    keyboard.add(back.inline_keyboard[0][0])
    return keyboard.adjust(3).as_markup()

async def minutes(hour, minutes_list):
    keyboard = InlineKeyboardBuilder()
    for minute in minutes_list:
        keyboard.add(InlineKeyboardButton(text=f"{hour:02d}:{minute:02d}", callback_data=f'minute_{minute}'))
    keyboard.add(back.inline_keyboard[0][0])
    return keyboard.adjust(3).as_markup()

async def times(times_list):
    keyboard = InlineKeyboardBuilder()
    for time in times_list:
        time_str = f"{time.hour:02d}:{time.minute:02d}"
        callback_data = f"time_{time.hour:02d}-{time.minute:02d}"
        keyboard.add(InlineKeyboardButton(text=time_str, callback_data=callback_data))
    keyboard.add(back.inline_keyboard[0][0])
    return keyboard.adjust(3).as_markup()

async def appointments(appointments_list):
    keyboard = InlineKeyboardBuilder()
    for appointment in appointments_list:
        id, master, service, date, time, is_cancelled = appointment
        if not is_cancelled:
            text = f"📅 {date.strftime('%d.%m')} {time.strftime('%H:%M')} - {service}"
            keyboard.add(InlineKeyboardButton(text=text, callback_data=f'appointment_{id}'))
    keyboard.add(back_menu.inline_keyboard[0][0])
    return keyboard.adjust(1).as_markup()

def appointment_actions(appointment_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✏️ Изменить запись', callback_data=f'edit_{appointment_id}')],
        [InlineKeyboardButton(text='❌ Отменить запись', callback_data=f'cancel_{appointment_id}')],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='view_or_reschedule')]
    ])

async def extension_types():
    keyboard = InlineKeyboardBuilder()
    # ID 13-17 - это услуги наращивания
    keyboard.add(InlineKeyboardButton(text='Длина мини', callback_data='extension_13'))
    keyboard.add(InlineKeyboardButton(text='Длина медиум', callback_data='extension_14'))
    keyboard.add(InlineKeyboardButton(text='Длина макс', callback_data='extension_15'))
    keyboard.add(InlineKeyboardButton(text='Простая коррекция', callback_data='extension_16'))
    keyboard.add(InlineKeyboardButton(text='Сложная коррекция', callback_data='extension_17'))
    keyboard.add(back.inline_keyboard[0][0])
    return keyboard.adjust(1).as_markup()

async def design_types():
    keyboard = InlineKeyboardBuilder()
    # ID 9-12 - это услуги дизайна
    keyboard.add(InlineKeyboardButton(text='Легкий дизайн', callback_data='design_9'))
    keyboard.add(InlineKeyboardButton(text='Сложный дизайн', callback_data='design_10'))
    keyboard.add(InlineKeyboardButton(text='Фрэнч', callback_data='design_11'))
    keyboard.add(InlineKeyboardButton(text='Аэрография', callback_data='design_12'))
    keyboard.add(back.inline_keyboard[0][0])
    return keyboard.adjust(1).as_markup()