from app.database.models import async_session
from app.database.models import User, Master, Service, Appointment, Service_section
from sqlalchemy import select, update


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
    return await session.scalars(select(Service_section))

@connection
async def get_services(session, category):
    return await session.scalars(select(Service).where(Service.section == category))


@connection
async def set_appointment(session, tg_id, master, service):
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    session.add(Appointment(user=user.id, service=service, master=master))
    await session.commit()