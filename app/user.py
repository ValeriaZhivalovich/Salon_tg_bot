import os
import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
# from app.g4f.chat import get_chat
# import app.g4f.promts as promt

from app.utils import update_history, delete_last_step, history

from app.database.requests import (
    set_user, add_user, set_appointment, get_appointment,
    get_masters_for_service, get_service_by_id, get_master_by_id,
    get_busy_slots, get_user_appointments, cancel_appointment,
    get_masters_for_multiple_services
) 
import app.keyboards as kb
from app.calendar import booking_calendar
from aiogram_calendar import SimpleCalendarCallback

router = Router()


class Reg(StatesGroup):
    name = State()
    last_name = State()
    contact = State()


class Appointment(StatesGroup):
    category = State()
    service = State()
    master = State()
    date = State()
    hour = State()
    minute = State()
    need_extension = State()
    extension_type = State()
    need_design = State()
    design_type = State()
    comment = State()
    confirm = State()





@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await set_user(message.from_user.id)
    if user:
        await message.answer(f'Приветствую, {user.name}!', reply_markup=kb.main)
        await state.clear()
    else:
        await message.answer(
            f"Рад с Вами познакомиться, {message.from_user.username}!\n\n"
            "Давайте пройдем короткую регистрацию, чтобы я запомнил Вас как нашего клиента❤️\n\n"
            "Напишите своё <b>ИМЯ</b>",
            parse_mode="HTML"
        )
        await state.set_state(Reg.name)


@router.message(Reg.name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Reg.last_name)
    await message.answer('Теперь напишите <b>ФАМИЛИЮ</b>', parse_mode="HTML")

@router.message(Reg.last_name)
async def reg_lastname(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await state.set_state(Reg.contact)
    await message.answer('Отправьте номер телефона', reply_markup=kb.contact)


@router.message(Reg.contact, F.contact)
async def reg_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    print(message.from_user.id, data['name'], data['last_name'], message.contact.phone_number)
    await add_user(message.from_user.id, data['name'], data['last_name'], message.contact.phone_number)
    await state.clear()
    await message.answer(f'Супер! Теперь Вам открыто меню задач.', reply_markup=kb.main)
    await message.answer("Выберите действие:", reply_markup=kb.menu)




@router.message(F.text == 'Меню')
async def router_menu(message: Message, state: FSMContext):
    await menu(message, state)

@router.callback_query(F.data == 'Меню')
async def router_menu_(callback: CallbackQuery, state: FSMContext):
    # Если сообщение содержит фото (например, прайс-лист), удаляем его
    if callback.message.photo:
        await callback.message.delete()
        # Отправляем новое сообщение с меню
        sent_message = await callback.bot.send_message(
            chat_id=callback.message.chat.id, 
            text="Меню:", 
            reply_markup=kb.menu
        )
        update_history(
            user_id = callback.from_user.id, 
            message_id = sent_message.message_id, 
            func = menu, 
            callback_data='Меню', 
            section = None,
            position = None
        )
    else:
        # Обычное редактирование текстового сообщения
        await menu(callback, state)

async def menu(event, state):
    
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    
    # Если это CallbackQuery, редактируем сообщение
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            text="Меню:", 
            reply_markup=kb.menu
        )
        sent_message = event.message
    else:
        # Если это обычное сообщение, отправляем новое
        sent_message = await event.bot.send_message(
            chat_id=chat_id, 
            text="Меню:", 
            reply_markup=kb.menu
        )
    
    update_history(
        user_id = event.from_user.id, 
        message_id = sent_message.message_id, 
        func = menu, 
        callback_data='Меню', 
        section = None,
        position = None
    )
    






# ----------кнопка ПОСМОТРЕТЬ ЦЕНЫ -----------
@router.callback_query(F.data == 'view_prices')
async def router_view_prices(callback: CallbackQuery, state: FSMContext):
    await view_prices(callback, state)

async def view_prices(event, state):
    chat_id = event.message.chat.id if hasattr(event, 'message') else event.chat.id
    photo_path = os.path.join('app', 'media', 'img', 'price.jpg')
    
    # Всегда удаляем старое сообщение и отправляем новое с фото
    if isinstance(event, CallbackQuery):
        await event.message.delete()
    
    sent_message = await event.bot.send_photo(
        chat_id=chat_id, photo=FSInputFile(photo_path), 
        caption="Прайс-лист", 
        reply_markup=kb.back_menu
    )

    update_history(
        user_id = event.from_user.id, 
        message_id = sent_message.message_id, 
        func = menu,  # Изменено на menu, чтобы кнопка "Назад в меню" работала правильно
        callback_data='Меню', 
        section = None,
        position = None
    )
    

    


# --------кнопка ЗАПИСАТЬСЯ НА УСЛУГУ ---------
@router.callback_query(F.data == 'book_service')
async def router_get_category(callback: CallbackQuery, state: FSMContext):
    await get_category(callback, state)

async def get_category(event, state):
    await state.set_state(Appointment.category)
    chat_id = event.message.chat.id if hasattr(event, 'message') else event.chat.id
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            text='Выберите тип услуги:', 
            reply_markup=kb.category_choice
        )
        sent_message = event.message
    else:
        sent_message = await event.bot.send_message(
            chat_id = chat_id, 
            text='Выберите тип услуги:', 
            reply_markup=kb.category_choice
        )
    
    update_history(
        user_id = event.from_user.id, 
        message_id = sent_message.message_id, 
        func = get_category, 
        callback_data='book_service', 
        section = 'service',
        position = 0
    )
    
 


# --------кнопка ВЫбОРА КАТЕГОРИИ ---------
@router.callback_query(F.data.startswith('category_'), Appointment.category)
async def router_get_service(callback: CallbackQuery, state: FSMContext):
    await get_service(callback, state)
    
    

async def get_service(event, state):
    await state.set_state(Appointment.service)
    chat_id = event.message.chat.id

    await event.answer('Категория выбрана.')

    # Сохраняем ID категории только если это новый выбор
    if event.data.startswith('category_'):
        category_id = int(event.data.split('_')[1])
        await state.update_data(category=category_id)
    
    # Получаем ID категории из состояния для отображения услуг
    data = await state.get_data()
    category_id = data.get('category')

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            text='Выберите услугу', 
            reply_markup=await kb.services(category_id)
        )
        sent_message = event.message
    else:
        sent_message = await event.bot.send_message(
            chat_id = chat_id, 
            text='Выберите услугу', 
            reply_markup=await kb.services(category_id)
        )

    update_history(
        user_id = event.from_user.id, 
        message_id = sent_message.message_id, 
        func = get_service, 
        callback_data=event.data, 
        section = 'service',
        position = 1
    )

   

# --------кнопка выбора УСЛУГИ  ---------
@router.callback_query(F.data.startswith('service_'), Appointment.service)
async def router_check_design(callback: CallbackQuery, state: FSMContext):
    # Сохраняем ID услуги
    service_id = int(callback.data.split('_')[1])
    await state.update_data(service=service_id)
    await callback.answer('Услуга выбрана.')
    await check_design(callback, state)

async def get_master(event, state):
    await state.set_state(Appointment.master)
    chat_id = event.message.chat.id

    # Отправляем уведомление только для CallbackQuery
    if isinstance(event, CallbackQuery):
        await event.answer('Выбираем мастера...')
    
    # Получаем все выбранные услуги из состояния
    data = await state.get_data()
    
    # Собираем список всех выбранных услуг
    service_ids = []
    
    # Основная услуга
    if data.get('service'):
        service_ids.append(int(data['service']))
    
    # Дизайн
    if data.get('design_type'):
        service_ids.append(int(data['design_type']))
    
    # Наращивание
    if data.get('extension_type'):
        service_ids.append(int(data['extension_type']))
    
    # Получаем мастеров, которые выполняют ВСЕ выбранные услуги
    masters = await get_masters_for_multiple_services(service_ids)
    
    if not masters:
        await event.message.edit_text(
            text='К сожалению, никто из мастеров не выполняет все выбранные услуги.\n'
                 'Попробуйте выбрать другие услуги.', 
            reply_markup=kb.back
        )
    else:
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(
                text='Выберите мастера (показаны только те, кто может выполнить все выбранные услуги):', 
                reply_markup=await kb.masters_for_service(masters)
            )
            sent_message = event.message
        else:
            sent_message = await event.bot.send_message(
                chat_id = chat_id, 
                text='Выберите мастера (показаны только те, кто может выполнить все выбранные услуги):', 
                reply_markup=await kb.masters_for_service(masters)
            )

        update_history(
            user_id = event.from_user.id, 
            message_id = sent_message.message_id, 
            func = get_master, 
            callback_data='', 
            section = 'service',
            position = 2
        )

# --------кнопка выбора МАСТЕРА ---------
@router.callback_query(F.data.startswith('master_'), Appointment.master)
async def router_get_date(callback: CallbackQuery, state: FSMContext):
    # Сохраняем ID мастера
    master_id = int(callback.data.split('_')[1])
    await state.update_data(master=master_id)
    await callback.answer('Мастер выбран.')
    await get_date(callback, state)
 



async def get_date(event, state):
    await state.set_state(Appointment.date)
    chat_id = event.message.chat.id
    
    await event.answer('Услуга выбрана.')
    
    # Сохраняем ID услуги только если это новый выбор
    if event.data.startswith('service_'):
        service_id = int(event.data.split('_')[1])
        await state.update_data(service=service_id)
    
    # Используем календарь для выбора даты
    calendar_markup = await booking_calendar.start_calendar()
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            text='Выберите дату для записи (доступны текущий и следующий месяц):', 
            reply_markup=calendar_markup
        )
        sent_message = event.message
    else:
        sent_message = await event.bot.send_message(
            chat_id = chat_id, 
            text='Выберите дату для записи (доступны текущий и следующий месяц):', 
            reply_markup=calendar_markup
        )
    
    update_history(
        user_id = event.from_user.id, 
        message_id = sent_message.message_id, 
        func = get_date, 
        callback_data=event.data, 
        section = 'service',
        position = 3
    )


# --------обработчик выбора даты из календаря ---------
@router.callback_query(SimpleCalendarCallback.filter(), Appointment.date)
async def process_calendar(callback: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await booking_calendar.process_selection(callback, callback_data)
    
    if selected:
        # Проверяем, что дата доступна для записи
        if booking_calendar.is_date_available(date):
            # Преобразуем datetime в date если необходимо
            if isinstance(date, datetime.datetime):
                date = date.date()
            await state.update_data(date=date)
            await get_time(callback, state)
        else:
            await callback.answer(
                "Выбранная дата недоступна для записи. Пожалуйста, выберите дату в пределах текущего или следующего месяца.",
                show_alert=True
            )

async def get_time(event, state):
    await state.set_state(Appointment.hour)
    chat_id = event.message.chat.id
    
    # Отправляем уведомление только для CallbackQuery
    if isinstance(event, CallbackQuery):
        await event.answer('Дата выбрана.')
    
    # Получаем данные из состояния
    data = await state.get_data()
    
    # Проверяем наличие необходимых данных
    if 'master' not in data:
        await event.answer("Произошла ошибка. Пожалуйста, начните запись заново.", show_alert=True)
        await menu(event, state)
        return
        
    master_id = data['master']
    service_id = data['service']
    date = data['date']
    
    # Получаем информацию о мастере и услуге
    master = await get_master_by_id(int(master_id))
    service = await get_service_by_id(int(service_id))
    
    # Получаем занятые слоты
    busy_slots = await get_busy_slots(int(master_id), date)
    
    # Генерируем доступные временные слоты
    available_times = []
    work_start_hour = master.work_start.hour
    work_end_hour = master.work_end.hour
    service_duration_minutes = service.duration_minutes
    
    # Проверяем каждые 30 минут
    for hour in range(work_start_hour, work_end_hour):
        for minute in [0, 30]:
            start_time = datetime.time(hour, minute)
            # Вычисляем время окончания
            end_minutes = hour * 60 + minute + service_duration_minutes
            if end_minutes > work_end_hour * 60:
                continue
            end_time = datetime.time(end_minutes // 60, end_minutes % 60)
            
            # Проверяем пересечения с занятыми слотами с учетом 15-минутного буфера
            time_is_available = True
            for busy_start, busy_end in busy_slots:
                # Добавляем 15-минутный буфер после окончания предыдущей записи
                buffer_minutes = 15
                total_minutes = busy_end.hour * 60 + busy_end.minute + buffer_minutes
                
                # Проверяем, не выходит ли время за пределы дня
                if total_minutes >= 24 * 60:
                    # Если выходит за полночь, то слот недоступен до конца дня
                    time_is_available = False
                    break
                    
                busy_end_with_buffer = datetime.time(
                    total_minutes // 60,
                    total_minutes % 60
                )
                
                # Проверка пересечения времени с учетом буфера
                if not (end_time <= busy_start or start_time >= busy_end_with_buffer):
                    time_is_available = False
                    break
            
            if time_is_available:
                available_times.append(start_time)
    
    if not available_times:
        await event.message.edit_text(
            text='К сожалению, на выбранную дату нет свободного времени.\nВыберите другую дату:', 
            reply_markup=kb.back
        )
        sent_message = event.message
    else:
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(
                text=f'Выберите время начала процедуры\n(длительность: {service.duration_minutes} мин):', 
                reply_markup=await kb.times(available_times)
            )
            sent_message = event.message
        else:
            sent_message = await event.bot.send_message(
                chat_id = chat_id, 
                text=f'Выберите время начала процедуры\n(длительность: {service.duration_minutes} мин):', 
                reply_markup=await kb.times(available_times)
            )
    
    update_history(
        user_id = event.from_user.id, 
        message_id = sent_message.message_id, 
        func = get_time, 
        callback_data=event.data, 
        section = 'service',
        position = 4
    )


# --------кнопка выбора ВРЕМЕНИ ---------
@router.callback_query(F.data.startswith('time_'), Appointment.hour)
async def router_handle_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Время выбрано.')
    
    # Получаем время из callback (формат: time_HH-MM)
    time_str = callback.data.split('_')[1]
    hour, minute = map(int, time_str.split('-'))
    
    # Сохраняем время в состоянии
    start_time = datetime.time(hour, minute)
    data = await state.get_data()
    service = await get_service_by_id(int(data['service']))
    end_minutes = hour * 60 + minute + service.duration_minutes
    end_time = datetime.time(end_minutes // 60, end_minutes % 60)
    
    await state.update_data(start_time=start_time, end_time=end_time)
    
    # Переходим к комментарию (дизайн и наращивание уже были выбраны)
    await ask_comment(callback, state)


# --------кнопка НАРАЩИВАНИЕ ДА/НЕТ ---------
@router.callback_query(F.data.in_(['extension_yes', 'extension_no']), Appointment.need_extension)
async def handle_extension_choice(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'extension_yes':
        await state.set_state(Appointment.extension_type)
        await callback.message.edit_text(
            text='Выберите тип наращивания:',
            reply_markup=await kb.extension_types()
        )
    else:
        await state.update_data(need_extension=False, extension_type=None)
        await get_master(callback, state)

# --------кнопка выбора ТИПА НАРАЩИВАНИЯ ---------
@router.callback_query(F.data.startswith('extension_'), Appointment.extension_type)
async def handle_extension_type(callback: CallbackQuery, state: FSMContext):
    if not callback.data.startswith('extension_yes') and not callback.data.startswith('extension_no'):
        extension_id = int(callback.data.split('_')[1])
        await state.update_data(need_extension=True, extension_type=extension_id)
        await get_master(callback, state)

async def check_design(event, state):
    await state.set_state(Appointment.need_design)
    
    # Проверяем тип события для правильной обработки
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            text='Будет ли дизайн?',
            reply_markup=kb.yes_no_design
        )
    else:
        # Если это Message, нужно отправить новое сообщение
        await event.answer(
            text='Будет ли дизайн?',
            reply_markup=kb.yes_no_design
        )

# --------кнопка ДИЗАЙН ДА/НЕТ ---------
@router.callback_query(F.data.in_(['design_yes', 'design_no']), Appointment.need_design)
async def handle_design_choice(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'design_yes':
        await state.set_state(Appointment.design_type)
        await callback.message.edit_text(
            text='Выберите тип дизайна:',
            reply_markup=await kb.design_types()
        )
    else:
        await state.update_data(need_design=False, design_type=None)
        await check_extension(callback, state)

# --------кнопка выбора ТИПА ДИЗАЙНА ---------
@router.callback_query(F.data.startswith('design_'), Appointment.design_type)
async def handle_design_type(callback: CallbackQuery, state: FSMContext):
    if not callback.data.startswith('design_yes') and not callback.data.startswith('design_no'):
        design_id = int(callback.data.split('_')[1])
        await state.update_data(need_design=True, design_type=design_id)
        await check_extension(callback, state)

async def check_extension(event, state):
    data = await state.get_data()
    category_id = data.get('category')
    
    # Наращивание только для маникюра с покрытием или укреплением (категория 1, услуги 2 и 3)
    if int(category_id) == 1 and int(data['service']) in [2, 3]:
        # Спрашиваем про наращивание
        await state.set_state(Appointment.need_extension)
        await event.message.edit_text(
            text='Будет ли наращивание?',
            reply_markup=kb.yes_no_extension
        )
    else:
        # Для остальных услуг пропускаем наращивание
        await state.update_data(need_extension=False, extension_type=None)
        await get_master(event, state)

async def ask_comment(event, state):
    await state.set_state(Appointment.comment)
    await event.message.edit_text(
        text='Хотите добавить комментарий к записи?\n\n'
             'Например:\n'
             '• Приду не одна\n'
             '• Хочу нежно коралловый цвет\n'
             '• Маникюр к свадьбе\n\n'
             'Отправьте текст комментария или нажмите "Пропустить"',
        reply_markup=kb.skip_comment
    )

# --------обработка КОММЕНТАРИЯ ---------
@router.message(Appointment.comment)
async def handle_comment(message: Message, state: FSMContext):
    comment_text = ""
    
    # Проверяем, есть ли текст
    if message.text:
        comment_text = message.text
    
    # Проверяем, есть ли фото
    if message.photo:
        comment_text += " [Прикреплено фото]"
    
    # Проверяем, есть ли документ (изображение отправленное как файл)
    if message.document and message.document.mime_type and message.document.mime_type.startswith('image/'):
        comment_text += " [Прикреплено изображение]"
    
    await state.update_data(comment=comment_text if comment_text else None)
    # Удаляем сообщение пользователя
    await message.delete()
    # Переходим к подтверждению
    await confirm_booking(message, state)

# --------кнопка ПРОПУСТИТЬ комментарий ---------
@router.callback_query(F.data == 'skip_comment', Appointment.comment)
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    await confirm_booking(callback, state)

async def confirm_booking(event, state):
    await state.set_state(Appointment.confirm)
    
    # Получаем все данные
    data = await state.get_data()
    
    # Получаем информацию для отображения
    master = await get_master_by_id(int(data['master']))
    service = await get_service_by_id(int(data['service']))
    
    # Формируем текст подтверждения
    confirmation_text = (
        f'📋 <b>Пожалуйста, подтвердите запись:</b>\n\n'
        f'👤 <b>Мастер:</b> {master.name}\n'
        f'💇 <b>Основная услуга:</b> {service.name}\n'
    )
    
    # Добавляем информацию о наращивании
    if data.get('need_extension'):
        extension = await get_service_by_id(int(data['extension_type']))
        confirmation_text += f'➕ <b>Наращивание:</b> {extension.name}\n'
    
    # Добавляем информацию о дизайне
    if data.get('need_design'):
        design = await get_service_by_id(int(data['design_type']))
        confirmation_text += f'🎨 <b>Дизайн:</b> {design.name}\n'
    
    confirmation_text += (
        f'\n📅 <b>Дата:</b> {data["date"].strftime("%d.%m.%Y")}\n'
        f'🕐 <b>Время:</b> {data["start_time"].strftime("%H:%M")} - {data["end_time"].strftime("%H:%M")}\n'
    )
    
    # Добавляем комментарий
    if data.get('comment'):
        confirmation_text += f'\n📝 <b>Комментарий:</b> {data["comment"]}\n'
    
    confirmation_text += '\nПодтвердить запись?'
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            text=confirmation_text,
            parse_mode="HTML",
            reply_markup=kb.confirm_booking
        )
        sent_message = event.message
    else:
        chat_id = event.chat.id
        sent_message = await event.bot.send_message(
            chat_id = chat_id, 
            text=confirmation_text,
            parse_mode="HTML",
            reply_markup=kb.confirm_booking
        )
    
    update_history(
        user_id = event.from_user.id, 
        message_id = sent_message.message_id, 
        func = confirm_booking, 
        callback_data=event.data, 
        section = 'service',
        position = 5
    )

# --------кнопка ПОДТВЕРЖДЕНИЯ записи ---------
@router.callback_query(F.data == 'confirm_yes', Appointment.confirm)
async def confirm_yes(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Записываем...')
    
    # Получаем все данные
    data = await state.get_data()
    
    # Сохраняем запись
    await set_appointment(
        callback.from_user.id, 
        int(data['master']), 
        int(data['category']), 
        int(data['service']),
        data['date'],
        data['start_time'],
        data['end_time'],
        extension_id=int(data['extension_type']) if data.get('extension_type') else None,
        design_id=int(data['design_type']) if data.get('design_type') else None,
        comment=data.get('comment')
    )
    
    # Получаем информацию для отображения
    appointment = await get_appointment(callback.from_user.id)
    master_name, service_name, user_name, date, time = appointment
    
    await callback.message.edit_text(
        text=f'✅ <b>Вы успешно записаны!</b>\n\n'
             f'👤 <b>Мастер:</b> {master_name}\n'
             f'💇 <b>Услуга:</b> {service_name}\n'
             f'📅 <b>Дата:</b> {date.strftime("%d.%m.%Y")}\n'
             f'🕐 <b>Время:</b> {time.strftime("%H:%M")}\n\n'
             f'Хотите записаться на еще одну услугу?', 
        parse_mode="HTML",
        reply_markup=kb.another_service
    )
    
    await state.clear()

# --------кнопка ОТМЕНЫ подтверждения ---------
@router.callback_query(F.data == 'confirm_no', Appointment.confirm)
async def confirm_no(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Запись отменена')
    await state.clear()
    await menu(callback, state)

# --------кнопка ЕЩЕ ОДНА УСЛУГА ---------
@router.callback_query(F.data == 'another_service_yes')
async def another_service_yes(callback: CallbackQuery, state: FSMContext):
    await get_category(callback, state)

@router.callback_query(F.data == 'another_service_no')
async def another_service_no(callback: CallbackQuery, state: FSMContext):
    await menu(callback, state)


def get_entry_by_position(user_id, section, position):
    return next(
        (entry for entry in history.get(user_id, []) if entry["section"] == section and entry["position"] == position),
        None
    )



# --------кнопка ПРОСМОТРЕТЬ / ОТМЕНИТЬ ЗАПИСЬ ---------
@router.callback_query(F.data == 'view_or_reschedule')
async def view_or_reschedule(callback: CallbackQuery, state: FSMContext):
    appointments = await get_user_appointments(callback.from_user.id)
    
    if not appointments:
        await callback.message.edit_text(
            text="У вас пока нет активных записей.", 
            reply_markup=kb.back_menu
        )
    else:
        text = "📄 <b>Ваши записи:</b>\n\n"
        text += "<i>Нажмите на запись для выбора действия</i>\n\n"
        
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=await kb.appointments(appointments)
        )
    
    update_history(
        user_id = callback.from_user.id, 
        message_id = callback.message.message_id, 
        func = view_or_reschedule, 
        callback_data='view_or_reschedule', 
        section = None,
        position = None
    )


# --------кнопка ВЫБОРА ЗАПИСИ ---------
@router.callback_query(F.data.startswith('appointment_'))
async def select_appointment_action(callback: CallbackQuery, state: FSMContext):
    appointment_id = int(callback.data.split('_')[1])
    
    # Получаем информацию о записи
    appointments = await get_user_appointments(callback.from_user.id)
    appointment = next((a for a in appointments if a[0] == appointment_id), None)
    
    if appointment:
        id, master, service, date, time, is_cancelled = appointment
        
        text = (
            f"📅 <b>Детали записи:</b>\n\n"
            f"👤 <b>Мастер:</b> {master}\n"
            f"💇 <b>Услуга:</b> {service}\n"
            f"📆 <b>Дата:</b> {date.strftime('%d.%m.%Y')}\n"
            f"🕐 <b>Время:</b> {time.strftime('%H:%M')}\n\n"
            f"Что вы хотите сделать?"
        )
        
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=kb.appointment_actions(appointment_id)
        )

# --------кнопка ОТМЕНЫ ЗАПИСИ ---------
@router.callback_query(F.data.startswith('cancel_'))
async def cancel_appointment_handler(callback: CallbackQuery, state: FSMContext):
    appointment_id = int(callback.data.split('_')[1])
    
    result = await cancel_appointment(appointment_id, callback.from_user.id)
    
    if result:
        await callback.answer("Запись успешно отменена!", show_alert=True)
        # Обновляем список записей
        await view_or_reschedule(callback, state)
    else:
        await callback.answer("Ошибка при отмене записи", show_alert=True)

# --------кнопка ИЗМЕНЕНИЯ ЗАПИСИ ---------
@router.callback_query(F.data.startswith('edit_'))
async def edit_appointment_handler(callback: CallbackQuery, state: FSMContext):
    appointment_id = int(callback.data.split('_')[1])
    
    # Отменяем старую запись
    result = await cancel_appointment(appointment_id, callback.from_user.id)
    
    if result:
        await callback.answer("Старая запись отменена. Создайте новую.", show_alert=True)
        # Начинаем процесс новой записи
        await get_master(callback, state)
    else:
        await callback.answer("Ошибка при изменении записи", show_alert=True)

# --------кнопка ПОСМОТРЕТЬ РАБОТЫ ---------
@router.callback_query(F.data == 'view_works')
async def view_works(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Функция просмотра работ пока не реализована.", 
        reply_markup=kb.back_menu
    )

# --------кнопка ЗАДАТЬ ВОПРОС БОТУ ---------
@router.callback_query(F.data == 'ask_bot')
async def ask_bot(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Функция вопросов боту пока не реализована.", 
        reply_markup=kb.back_menu
    )

# --------кнопка СВЯЗАТЬСЯ С МАСТЕРОМ ---------
@router.callback_query(F.data == 'contact_master')
async def contact_master(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Функция связи с мастером пока не реализована.", 
        reply_markup=kb.back_menu
    )


@router.callback_query(F.data.startswith('back'))
async def router_back(callback: CallbackQuery, state: FSMContext):
    await back(callback, state)

async def back(event, state):
    
    user_id = event.from_user.id
    
    # Проверяем, есть ли история для пользователя
    if user_id not in history or len(history[user_id]) < 2:
        # Если истории нет или недостаточно записей, возвращаемся в меню
        await menu(event, state)
        return
    
    section = history[user_id][-1]['section']
    position = history[user_id][-1]['position']-1
    
    print(f"Back: section={section}, position={position}")
    data = get_entry_by_position(user_id, section, position)
    print(f"Back: data={data}")
    
    if not data:
        # Если не нашли данные, возвращаемся в меню
        await menu(event, state)
        return
    
    func_to_call = data['function']
        
    # Устанавливаем состояние в зависимости от вызываемой функции
    if func_to_call == get_category:
        await state.set_state(Appointment.category)
    elif func_to_call == get_service:
        await state.set_state(Appointment.service)
    elif func_to_call == get_master:
        await state.set_state(Appointment.master)
    elif func_to_call == get_date:
        await state.set_state(Appointment.date)
    elif func_to_call == get_time:
        await state.set_state(Appointment.hour)

    await func_to_call(event, state)
    