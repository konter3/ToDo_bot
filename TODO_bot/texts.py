from __future__ import annotations

# =====================
# Buttons
# =====================
BTN_MENU = "⬅️ В меню"
BTN_BACK = "⬅️ Назад"
BTN_NEXT = "➡️ Вперед"
BTN_CANCEL = "❌ Отмена"
BTN_YES = "✅ Да"

BTN_TASKS = "📋 Текущие дела"
BTN_ADD_TASK = "➕ Добавить дело"
BTN_DONE_TASKS = "✅ Выполненные дела"
BTN_DAILY_REMINDER = "⏰ Ежедневное напоминание"
BTN_CHECKLISTS = "🗂 Чек-листы"
BTN_USERS = "👑 Пользователи"

BTN_COMPLETE_ALL = "🗑 Выполнить все"
BTN_CLEAR_HISTORY = "🗑 Очистить историю"

BTN_ADD_CHECKLIST = "➕ Добавить чек-лист"
BTN_CHECKLIST_BACK_TO_LIST = "⬅️ Назад к списку чек-листов"
BTN_CHECKLIST_REMINDERS = "⏰ Напоминания"
BTN_CHECKLIST_EDIT = "✏️ Редактировать"
BTN_CHECKLIST_DELETE = "🗑️ Удалить чек-лист"
BTN_CHECKLIST_OPEN_REMINDERS = "⏰ Открыть настройки напоминаний"

BTN_SET_TIME = "🕘 Изменить время"
BTN_DAILY_DISABLE = "🔕 Выключить ежедневное напоминание"
BTN_DAILY_ENABLE = "🔔 Включить ежедневное напоминание"

BTN_CL_MODE_DAILY = "📅 Ежедневно в ..."
BTN_CL_MODE_ONCE = "⏱ Один раз в ..."
BTN_CL_DISABLE = "🔕 Выключить напоминания"
BTN_CL_DONT_SEND = "🚫 Не присылать"


# =====================
# Messages
# =====================
START_TITLE = "📝 Менеджер задач"

NO_ACCESS = "⛔ Нет доступа"

ADD_TASK_PROMPT = "✏️ Введите новое дело:"
ADD_TASK_SAVED = "✅ Дело добавлено"
ADD_TASK_NOT_TEXT = (
    "❌ Пожалуйста, отправьте текстовое сообщение.\n"
    "Фото, видео и файлы не принимаются."
)
ADD_TASK_CANCELED = "❌ Добавление дела отменено"

TASKS_EMPTY = "📭 Дел пока нет.\n\nНажмите «➕ Добавить дело», чтобы создать первую задачу."
TASKS_HEADER = "📋 Текущие дела:\n\n"

TASK_NOT_FOUND = "❌ Задача не найдена"
TASK_DONE = "✅ Задача выполнена"
TASKS_NONE_TO_COMPLETE = "✅ Дел нет для выполнения"
TASKS_ALL_DONE = "✅ Все задачи выполнены"

DONE_TASKS_EMPTY = "✅ Выполненных дел пока нет.\n\nОтмечайте задачи выполненными — и они появятся здесь."
DONE_TASKS_HEADER = "✅ Выполненные дела:\n\n"
DONE_TASKS_CLEARED = "✅ История выполненных дел очищена"
DONE_TASKS_CLEAR_FAILED = "❌ Не удалось очистить историю"
DONE_TASKS_CLEAR_CONFIRM = "⚠️ Вы уверены, что хотите очистить всю историю выполненных дел?"

USERS_HEADER = "👑 Пользователи:\n\n"

CHECKLIST_TITLE_PROMPT = "📝 Введите название чек-листа:\nНапример: Утренние дела"
CHECKLIST_TITLE_NOT_TEXT = "❌ Пожалуйста, введите название чек-листа текстом, без медиа."
CHECKLIST_TITLE_EMPTY = "❌ Название не может быть пустым. Введите текст."

CHECKLIST_ITEMS_PROMPT = (
    "📋 Введите пункты чек-листа\n"
    "Каждый пункт — с новой строки.\n\n"
    "Пример:\n"
    "Купить молоко\n"
    "Позвонить маме\n"
    "Записаться к врачу\n\n"
    "Когда закончите — отправьте сообщение."
)
CHECKLIST_ITEMS_NOT_TEXT = "❌ Пожалуйста, вводите пункты чек-листа только текстом, без медиа."
CHECKLIST_ITEMS_MIN_1 = "❌ Нужно минимум 1 пункт"

CHECKLISTS_EMPTY = "📋 У вас пока нет чек-листов"
CHECKLISTS_HEADER = "📋 Ваши чек-листы:"
CHECKLIST_CREATE_CANCELED = "❌ Создание чек-листа отменено"
CHECKLIST_NOT_FOUND = "Чек-лист не найден"
CHECKLIST_DELETED = "🗑️ Чек-лист удалён"

TIME_INPUT_PROMPT = "🕘 Введите время в формате HH:MM (например, 09:30)"
TIME_INPUT_BAD = "❌ Неверный формат. Пример: 09:30"

SETTINGS_SAVED = "✅ Готово. Настройки сохранены."

DAILY_TIME_UPDATED = "✅ Время обновлено. Ежедневное напоминание включено."
DAILY_DISABLED = "🔕 Ежедневное напоминание выключено"
DAILY_ENABLED = "🔔 Ежедневное напоминание включено"

CL_DISABLED_SHORT = "🔕 Выключено"
DAILY_ENABLED_SHORT = "🔔 Включено"

# Checklist reminders
CL_REMINDER_MENU = "⏰ Напоминания чек-листа\n\nТекущее: {info}\n\nВыберите режим:"
CL_INFO_OFF = "выключено 🔕"
CL_INFO_DAILY = "ежедневно в {time} ✅"
CL_INFO_WEEKLY = "каждый {weekday} в {time} ✅"
CL_INFO_ONCE_SENT = "один раз (уже отправлено) ✅"
CL_INFO_ONCE_AT = "один раз: {once_at} ✅"
CL_PROMPT_DAILY = "🕘 Введите время (HH:MM), в которое присылать чек-лист ежедневно."
CL_PROMPT_ONCE = "🕘 Введите время (HH:MM), в которое прислать чек-лист один раз (ближайшее такое время)."
CL_PROMPT_WEEKDAY = "📅 Выберите дни недели, когда присылать чек-лист. Можно выбрать несколько."

CL_DAYS_SELECTED = "Выбрано: {days}"
CL_DAYS_NONE = "Выбрано: —"
BTN_DONE = "✅ Готово"
BTN_EVERY_DAY = "Каждый день"

# Weekdays
WEEKDAYS = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]
WEEKDAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# Checklist edit
CHECKLIST_EDIT_PROMPT = (
    "✏️ Отправьте новый список пунктов\n"
    "Каждый пункт — с новой строки.\n\n"
    "Пример:\n"
    "Купить молоко\n"
    "Позвонить маме\n"
    "Записаться к врачу\n\n"
    "Старые пункты будут заменены."
)
CHECKLIST_EDIT_SAVED = "✅ Пункты чек-листа обновлены"
