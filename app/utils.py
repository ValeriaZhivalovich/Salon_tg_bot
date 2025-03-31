from collections import defaultdict

history = defaultdict(list)


def update_history(user_id, message_id, func, callback_data, section, position):
    removed_entry = None  # Для хранения удаленного элемента
    
    # Фильтруем список, убирая старый элемент с той же функцией
    new_history = []
    for entry in history.get(user_id, []):
        if entry["function"] == func:
            removed_entry = entry  # Запоминаем удаленный элемент
        else:
            new_history.append(entry)

    # Обновляем список
    new_history.append(
        {
            "message_id": message_id, 
            "callback_data": callback_data, 
            "function": func, 
            "section": section,
            "position": position
        }
    )
    history[user_id] = new_history
    
    return removed_entry


async def delete_last_step(event, user_id, chat_id):
    """Удаляет последний шаг пользователя, если он есть."""
    data = history[user_id]
    if data and len(data) > 1:  # Проверяем, есть ли данные для пользователя
        message_id = data[-2]['message_id']
        await event.bot.delete_message(chat_id=chat_id, message_id=message_id)
        
    return None 