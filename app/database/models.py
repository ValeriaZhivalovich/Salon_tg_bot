from sqlalchemy import ForeignKey, String, BigInteger, Integer, DateTime, Time, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
import datetime


import os
from dotenv import load_dotenv
load_dotenv()

URL = os.getenv('SQLALCHEMY_URL', 'sqlite+aiosqlite:///db.sqlite3')

engine = create_async_engine(url=URL)

async_session = async_sessionmaker(engine, class_=AsyncSession)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id = mapped_column(BigInteger, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=True)
    last_name: Mapped[str] = mapped_column(String(20), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)


class Master(Base):
    __tablename__ = 'masters'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20))
    work_start: Mapped[datetime.time] = mapped_column(Time, default=datetime.time(9, 0))  # 9:00
    work_end: Mapped[datetime.time] = mapped_column(Time, default=datetime.time(18, 0))  # 18:00


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20))


class Service(Base):
    __tablename__ = 'services'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20))
    prise: Mapped[str] = mapped_column(String(10))
    category: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)  # Длительность услуги в минутах


class MasterService(Base):
    __tablename__ = 'master_services'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(ForeignKey('masters.id'))
    service_id: Mapped[int] = mapped_column(ForeignKey('services.id'))


class Appointment(Base):
    __tablename__ = 'appointments'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user: Mapped[int] = mapped_column(ForeignKey('users.id'))
    master: Mapped[int] = mapped_column(ForeignKey('masters.id'))
    category: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    service: Mapped[int] = mapped_column(ForeignKey('services.id'))
    date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=True)
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Дополнительные услуги
    extension_id: Mapped[int] = mapped_column(Integer, nullable=True)
    design_id: Mapped[int] = mapped_column(Integer, nullable=True)
    comment: Mapped[str] = mapped_column(String(500), nullable=True)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)