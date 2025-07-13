from aiogram_calendar import SimpleCalendar
from aiogram.types import InlineKeyboardMarkup
import datetime

class BookingCalendar:
    def __init__(self):
        self.calendar = SimpleCalendar(locale='ru_RU.UTF-8')
    
    async def start_calendar(
        self,
        year: int = datetime.datetime.now().year,
        month: int = datetime.datetime.now().month
    ) -> InlineKeyboardMarkup:
        """
        Создает календарь для текущего и следующего месяца
        """
        return await self.calendar.start_calendar(year=year, month=month)
    
    async def process_selection(self, callback_query, callback_data: dict) -> tuple:
        """
        Обрабатывает выбор даты в календаре
        Возвращает (selected, date) где selected - True если дата выбрана
        """
        return await self.calendar.process_selection(callback_query, callback_data)
    
    @staticmethod
    def is_date_available(date: datetime.date) -> bool:
        """
        Проверяет, доступна ли дата для записи
        (текущий или следующий месяц)
        """
        # Преобразуем datetime в date если необходимо
        if isinstance(date, datetime.datetime):
            date = date.date()
            
        today = datetime.date.today()
        # Дата должна быть не раньше сегодня
        if date < today:
            return False
        
        # Проверяем, что дата в пределах текущего или следующего месяца
        last_day_next_month = None
        if today.month == 12:
            # Если текущий месяц декабрь, следующий - январь следующего года
            last_day_next_month = datetime.date(today.year + 1, 1, 1) + datetime.timedelta(days=31)
            last_day_next_month = last_day_next_month.replace(day=1) - datetime.timedelta(days=1)
        else:
            # Для остальных месяцев
            if today.month == 11:
                last_day_next_month = datetime.date(today.year, 12, 31)
            else:
                last_day_next_month = datetime.date(today.year, today.month + 2, 1) - datetime.timedelta(days=1)
        
        return date <= last_day_next_month

booking_calendar = BookingCalendar()