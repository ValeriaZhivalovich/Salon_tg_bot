import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
# from app.g4f.chat import get_chat
# import app.g4f.promts as promt

from app.utils import update_history, delete_last_step, history

from app.database.requests import set_user, add_user, set_appointment, get_appointment 
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
    await menu(callback, state)

async def menu(event, state):
    
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id

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
    await delete_last_step(event, event.from_user.id, chat_id)
    






# ----------кнопка ПОСМОТРЕТЬ ЦЕНЫ -----------
@router.callback_query(F.data == 'view_prices')
async def router_view_prices(callback: CallbackQuery, state: FSMContext):
    await view_prices(callback, state)

async def view_prices(event, state):
    chat_id = event.message.chat.id
    photo_path = os.path.join('app', 'media', 'img', 'price.jpg')

    sent_message = await event.bot.send_photo(
        chat_id=chat_id, photo=FSInputFile(photo_path), 
        caption="Прайс-лист", 
        reply_markup=kb.back_menu
    )

    update_history(
        user_id = event.from_user.id, 
        message_id = sent_message.message_id, 
        func = view_prices, 
        callback_data='view_prices', 
        section = 'prices',
        position = 0
    )
    await delete_last_step(event, event.from_user.id, chat_id)
    

    


# --------кнопка ЗАПИСАТЬСЯ НА УСЛУГУ ---------
@router.callback_query(F.data == 'book_service')
async def router_get_master(callback: CallbackQuery, state: FSMContext):
    await get_master(callback, state)

async def get_master(event, state):
    await state.set_state(Appointment.master)
    chat_id = event.message.chat.id

    sent_message = await event.bot.send_message(
        chat_id = chat_id, 
        text='Выберите мастера', 
        reply_markup=await kb.masters()
    )
    
    update_history(
        user_id = event.from_user.id, 
        message_id = sent_message.message_id, 
        func = get_master, 
        callback_data='book_service', 
        section = 'service',
        position = 0
    )
    await delete_last_step(event, event.from_user.id, chat_id)
    
 


# --------кнопка ВЫбора МАСТЕРА ---------
@router.callback_query(F.data.startswith('master_'), Appointment.master)
async def router_get_category(callback: CallbackQuery, state: FSMContext):
    await get_category(callback, state)

async def get_category(event, state):
    await state.set_state(Appointment.category)
    chat_id = event.message.chat.id

    await event.answer('Мастер выбран.')
    
    if event.data.startswith('master_'):
        data = event.data
    else:
        data = history[event.from_user.id][-2]['callback_data']
        

    await state.update_data(master=data.split('_')[1])
    
    sent_message = await event.bot.send_message(
        chat_id = chat_id, 
        text='Выберите категорию', 
        reply_markup=await kb.categories()
    )

    update_history(
        user_id = event.from_user.id, 
        message_id = sent_message.message_id, 
        func = get_category, 
        callback_data=data, 
        section = 'service',
        position = 1
    )
    await delete_last_step(event, event.from_user.id, chat_id)
    
    


# --------кнопка ВЫбОРА КАТЕГОРИИ ---------
@router.callback_query(F.data.startswith('category_'), Appointment.category)
async def router_get_service(callback: CallbackQuery, state: FSMContext):
    await get_service(callback, state)

async def get_service(event, state):
    await state.set_state(Appointment.service)
    chat_id = event.message.chat.id

    await event.answer('Категория выбрана.')

    if event.data.startswith('category_'):
        data = event.data
    else:
        data = history[event.from_user.id][-2]['callback_data']

    await state.update_data(category=data.split('_')[1])

    sent_message = await event.bot.send_message(
        chat_id = chat_id, 
        text='Выберите услугу', 
        reply_markup=await kb.services(data.split('_')[1])
    )

    update_history(
        user_id = event.from_user.id, 
        message_id = sent_message.message_id, 
        func = get_service, 
        callback_data=data, 
        section = 'service',
        position = 2
    )
    await delete_last_step(event, event.from_user.id, chat_id)

   

# --------кнопка выбора УСЛУГИ  ---------
@router.callback_query(F.data.startswith('service_'), Appointment.service)
async def router_finish(callback: CallbackQuery, state: FSMContext):
    await finish(callback, state)

async def finish(event, state):
    chat_id = event.message.chat.id
    await event.answer('Услуга выбрана.')
    data = await state.get_data()
    await set_appointment(event.from_user.id, data['master'], data['category'], event.data.split('_')[1])
    appointment = await get_appointment(event.from_user.id)
    
    sent_message = await event.bot.send_message(
        chat_id = chat_id, 
        text=f'Вы успешно записаны! \n\nИнформация о записи: \n\n<b>Мастер:</b> {appointment[0]}\n<b>Услуга:</b> {appointment[1]}', 
        parse_mode="HTML",
        reply_markup=kb.back_menu
    )

    update_history(
        user_id = event.from_user.id, 
        message_id = sent_message.message_id, 
        func = finish, 
        callback_data= event.data, 
        section = 'service',
        position = 3
    )
    await delete_last_step(event, event.from_user.id, chat_id)
 



def get_entry_by_position(user_id, section, position):
    return next(
        (entry for entry in history.get(user_id, []) if entry["section"] == section and entry["position"] == position),
        None
    )



@router.callback_query(F.data.startswith('back'))
async def router_back(callback: CallbackQuery, state: FSMContext):
    await back(callback, state)

async def back(event, state):
    
    user_id = event.from_user.id
    section = history[user_id][-1]['section']
    position = history[user_id][-1]['position']-1
    
    print(section)
    data = get_entry_by_position(user_id, section, position)
    print(data)
    func_to_call = data['function']
        
    # Устанавливаем состояние в зависимости от вызываемой функции
    if func_to_call == get_master:
        await state.set_state(Appointment.master)
    elif func_to_call == get_category:
        await state.set_state(Appointment.category)
    elif func_to_call == get_service:
        await state.set_state(Appointment.service)

    await func_to_call(event, state)
    