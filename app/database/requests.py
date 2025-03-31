from app.database.models import async_session
from app.database.models import User, Master, Service, Appointment, Category
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload



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
async def set_appointment(session, tg_id, master, category, service):
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    session.add(Appointment(user=user.id, service=service, category=category, master=master))
    await session.commit()

@connection
async def get_appointment(session, tg_id):
    result = await session.execute(
        select(Master.name, Service.name, User.name)
        .join(Appointment, Appointment.master == Master.id)
        .join(Service, Appointment.service == Service.id)
        .join(User, User.id == Appointment.user)
        .where(User.tg_id == tg_id)
        .order_by(Appointment.id.desc())
    )
    return result.first()

