from app.database.models import async_session
from app.database.models import User, Master, Service, Appointment, Category, MasterService
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload
import datetime



def connection(func):
    async def wrapper(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return wrapper


@connection 
async def set_user(session, tg_id): 
    user = await session.scalar(select(User).where(User.tg_id == tg_id))

    if not user:
        return False
    else:
        return user


@connection
async def add_user(session, tg_id, name, last_name, contact):
    session.add(User(tg_id=tg_id, name=name, last_name=last_name, phone_number=contact))
    await session.commit()


@connection
async def get_masters(session):
    return await session.scalars(select(Master))


@connection
async def get_categories(session):
    return await session.scalars(select(Category))

@connection
async def get_services(session, category):
    return await session.scalars(select(Service).where(Service.category == category))


@connection
async def set_appointment(session, tg_id, master, category, service, date, start_time, end_time, 
                         extension_id=None, design_id=None, comment=None):
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    session.add(Appointment(
        user=user.id, 
        service=service, 
        category=category, 
        master=master,
        date=date,
        start_time=start_time,
        end_time=end_time,
        extension_id=extension_id,
        design_id=design_id,
        comment=comment
    ))
    await session.commit()

@connection
async def get_appointment(session, tg_id):
    result = await session.execute(
        select(Master.name, Service.name, User.name, Appointment.date, Appointment.start_time)
        .join(Appointment, Appointment.master == Master.id)
        .join(Service, Appointment.service == Service.id)
        .join(User, User.id == Appointment.user)
        .where(User.tg_id == tg_id)
        .order_by(Appointment.id.desc())
    )
    return result.first()


@connection
async def get_masters_for_service(session, service_id):
    """Получить мастеров, которые выполняют данную услугу"""
    result = await session.execute(
        select(Master)
        .join(MasterService, Master.id == MasterService.master_id)
        .where(MasterService.service_id == service_id)
    )
    return result.scalars().all()


@connection
async def get_masters_for_multiple_services(session, service_ids):
    """Получить мастеров, которые выполняют ВСЕ указанные услуги"""
    if not service_ids:
        return []
    
    # Фильтруем None значения
    service_ids = [sid for sid in service_ids if sid is not None]
    
    if not service_ids:
        return []
    
    # Подзапрос для подсчета количества услуг, которые выполняет каждый мастер из списка
    subquery = (
        select(MasterService.master_id)
        .where(MasterService.service_id.in_(service_ids))
        .group_by(MasterService.master_id)
        .having(func.count(MasterService.service_id) == len(service_ids))
    ).subquery()
    
    # Получаем мастеров, которые выполняют ВСЕ указанные услуги
    result = await session.execute(
        select(Master)
        .where(Master.id.in_(select(subquery.c.master_id)))
    )
    return result.scalars().all()


@connection
async def get_service_by_id(session, service_id):
    """Получить услугу по ID"""
    return await session.scalar(select(Service).where(Service.id == service_id))


@connection
async def get_master_by_id(session, master_id):
    """Получить мастера по ID"""
    return await session.scalar(select(Master).where(Master.id == master_id))


@connection
async def get_busy_slots(session, master_id, date):
    """Получить занятые слоты мастера на определенную дату"""
    result = await session.execute(
        select(Appointment.start_time, Appointment.end_time)
        .where(
            and_(
                Appointment.master == master_id,
                Appointment.date == date,
                Appointment.is_cancelled == False
            )
        )
    )
    return result.all()


@connection
async def get_user_appointments(session, tg_id):
    """Получить все записи пользователя"""
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    if not user:
        return []
    
    result = await session.execute(
        select(
            Appointment.id,
            Master.name,
            Service.name,
            Appointment.date,
            Appointment.start_time,
            Appointment.is_cancelled
        )
        .join(Master, Appointment.master == Master.id)
        .join(Service, Appointment.service == Service.id)
        .where(
            and_(
                Appointment.user == user.id,
                Appointment.date >= datetime.date.today()
            )
        )
        .order_by(Appointment.date, Appointment.start_time)
    )
    return result.all()


@connection
async def cancel_appointment(session, appointment_id, user_tg_id):
    """Отменить запись"""
    user = await session.scalar(select(User).where(User.tg_id == user_tg_id))
    if not user:
        return False
    
    appointment = await session.scalar(
        select(Appointment).where(
            and_(
                Appointment.id == appointment_id,
                Appointment.user == user.id
            )
        )
    )
    
    if appointment:
        appointment.is_cancelled = True
        await session.commit()
        return True
    return False

