import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
# from app.g4f.chat import get_chat
# import app.g4f.promts as promt

from app.database.requests import set_user, add_user, set_appointment
import app.keyboards as kb

router = Router()


class Reg(StatesGroup):
    name = State()
    last_name = State()
    contact = State()


class Appointment(StatesGroup):
    master = State()
    category = State()
    service = State()


history_messages = []
history_callbacks = []
history_callbacks_data = []



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

async def menu(event, state):

    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id

    history_callbacks_data.clear()
    history_callbacks.clear()


    
    sent_message = await event.bot.send_message(
        chat_id=chat_id, 
        text="Выберите действие:", 
        reply_markup=kb.menu
    )
    
    if history_messages:
        await event.bot.delete_message(chat_id=chat_id, message_id=history_messages.pop())
    
    history_messages.append(sent_message.message_id)
    history_callbacks.append(menu)
    history_callbacks_data.append('Меню')




# ----------кнопка ПОСМОТРЕТЬ ЦЕНЫ -----------
@router.callback_query(F.data == 'view_prices')
async def router_view_prices(callback: CallbackQuery, state: FSMContext):
    await view_prices(callback, state)

async def view_prices(callback, state):
    chat_id = callback.message.chat.id
    photo_path = os.path.join('app', 'media', 'img', 'price.jpg')
    history_callbacks.append(view_prices)

    sent_message = await callback.bot.send_photo(
        chat_id=chat_id, photo=FSInputFile(photo_path), 
        caption="Прайс-лист", 
        reply_markup=kb.back
    )

    if history_messages:
        await callback.bot.delete_message(chat_id=chat_id, message_id=history_messages.pop())

    history_messages.append(sent_message.message_id)
    history_callbacks_data.pop()
    history_callbacks_data.append(callback.data)


# --------кнопка ЗАПИСАТЬСЯ НА УСЛУГУ ---------
@router.callback_query(F.data == 'book_service')
async def router_get_master(callback: CallbackQuery, state: FSMContext):
    await get_master(callback, state)

async def get_master(callback, state):
    await state.set_state(Appointment.master)
    chat_id = callback.message.chat.id
    history_callbacks.append(get_master)

    sent_message = await callback.bot.send_message(
        chat_id = chat_id, 
        text='Выберите мастера', 
        reply_markup=await kb.masters()
    )
    
    if history_messages:
        await callback.bot.delete_message(chat_id=chat_id, message_id=history_messages.pop())


    history_messages.append(sent_message.message_id)
    a = history_callbacks_data.pop()
    history_callbacks_data.append(callback.data)
 


# --------кнопка ВЫбора КАТЕГОРИИ ---------
@router.callback_query(F.data.startswith('master_'), Appointment.master)
async def router_get_category(callback: CallbackQuery, state: FSMContext):
    await get_category(callback, state)

async def get_category(callback, state):
    await state.set_state(Appointment.category)
    chat_id = callback.message.chat.id
    history_callbacks.append(get_category)

    await callback.answer('Мастер выбран.')
    
    if callback.data.startswith('master_'):
        data = callback.data.split('_')[1] 
    else:
        print(history_callbacks_data)
        data = history_callbacks_data[-1].split('_')[1]
        

    await state.update_data(master=data)
    
    send_message = await callback.bot.send_message(
        chat_id = chat_id, 
        text='Выберите категорию', 
        reply_markup=await kb.categories()
    )
    if history_messages:
        await callback.bot.delete_message(chat_id=chat_id, message_id=history_messages.pop())
    
    history_messages.append(send_message.message_id)
    history_callbacks_data.pop()
    history_callbacks_data.append(callback.data)
    


# --------кнопка ВЫбОРА КАТЕГОРИИ ---------
@router.callback_query(F.data.startswith('category_'), Appointment.category)
async def router_get_service(callback: CallbackQuery, state: FSMContext):
    await get_service(callback, state)

async def get_service(callback, state):
    await state.set_state(Appointment.service)
    chat_id = callback.message.chat.id
    history_callbacks.append(get_service)

    await callback.answer('Категория выбрана.')

    if callback.data.startswith('category_'):
        data = callback.data.split('_')[1] 
    else:
        print(history_callbacks_data)
        data = history_callbacks_data[-1].split('_')[1]

    await state.update_data(category=data)

    send_message = await callback.bot.send_message(
        chat_id = chat_id, 
        text='Выберите услугу', 
        reply_markup=await kb.services(data)
    )

    if history_messages:
        await callback.bot.delete_message(chat_id=chat_id, message_id=history_messages.pop())

    history_messages.append(send_message.message_id)
    history_callbacks_data.pop()
    history_callbacks_data.append(callback.data)
   

# --------функция ФИНИШ---------
@router.callback_query(F.data.startswith('service_'), Appointment.service)
async def get_service_finish(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Услуга выбрана.')
    data = await state.get_data()
    await set_appointment(callback.from_user.id, data['master'], data['category'], callback.data.split('_')[1])
    await callback.message.answer('Вы успешно записаны!.', reply_markup=kb.main)
 







@router.callback_query(F.data.startswith('back'))
async def back(callback: CallbackQuery, state: FSMContext):
    global history_callbacks
    if len(history_callbacks) > 1:
        del history_callbacks[-1]
        func_to_call = history_callbacks[-1]
        
        # Устанавливаем состояние в зависимости от вызываемой функции
        if func_to_call == get_master:
            await state.set_state(Appointment.master)
        elif func_to_call == get_category:
            await state.set_state(Appointment.category)
        elif func_to_call == get_service:
            await state.set_state(Appointment.service)

        await func_to_call(callback, state)
    else:
        await menu(callback, state)