# handlers/show_checklists.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
from config import DB_NAME

router = Router()


# --- Показываем список чек-листов ---
@router.callback_query(F.data == "checklists")
async def show_checklists(cb: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, title FROM checklists WHERE user_id=? ORDER BY id DESC",
            (cb.from_user.id,)
        )
        rows = await cursor.fetchall()

    if not rows:
        text = "📋 У вас пока нет чек-листов"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить чек-лист", callback_data="add_checklist")],
                [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")]
            ]
        )
    else:
        text = "📋 Ваши чек-листы:"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=title, callback_data=f"checklist:{checklist_id}")]
                for checklist_id, title in rows
            ] + [
                [InlineKeyboardButton(text="➕ Добавить чек-лист", callback_data="add_checklist")],
                [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")]
            ]
        )

    await cb.message.edit_text(text, reply_markup=keyboard)
    await cb.answer()


# --- Показываем конкретный чек-лист ---
@router.callback_query(F.data.startswith("checklist:"))
async def open_checklist(cb: CallbackQuery):
    checklist_id = int(cb.data.split(":")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, title, completed FROM checklist_items WHERE checklist_id=?",
            (checklist_id,)
        )
        items = await cursor.fetchall()

        cursor = await db.execute(
            "SELECT title FROM checklists WHERE id=?",
            (checklist_id,)
        )
        checklist_title = (await cursor.fetchone())[0]

    text = f"📋 {checklist_title}\n\n"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ {title}" if completed else title,
                    callback_data=f"checklist_item:{checklist_id}:{item_id}"
                )
            ] for item_id, title, completed in items
        ] + [
            [InlineKeyboardButton(text="🗑️ Удалить чек-лист", callback_data=f"delete_checklist:{checklist_id}")],
            [InlineKeyboardButton(text="⬅️ Назад к списку чек-листов", callback_data="checklists")]
        ]
    )

    await cb.message.edit_text(text, reply_markup=keyboard)
    await cb.answer()


# --- Отмечаем / снимаем отметку с пункта ---
@router.callback_query(F.data.startswith("checklist_item:"))
async def toggle_checklist_item(cb: CallbackQuery):
    _, checklist_id, item_id = cb.data.split(":")
    checklist_id, item_id = int(checklist_id), int(item_id)

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT completed FROM checklist_items WHERE id=?",
            (item_id,)
        )
        completed = (await cursor.fetchone())[0]

        # Переключаем
        new_completed = 0 if completed else 1
        await db.execute(
            "UPDATE checklist_items SET completed=? WHERE id=?",
            (new_completed, item_id)
        )
        await db.commit()

    # Обновляем меню чек-листа
    await open_checklist(cb)


# --- Удаляем чек-лист ---
@router.callback_query(F.data.startswith("delete_checklist:"))
async def delete_checklist(cb: CallbackQuery):
    checklist_id = int(cb.data.split(":")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM checklist_items WHERE checklist_id=?", (checklist_id,))
        await db.execute("DELETE FROM checklists WHERE id=?", (checklist_id,))
        await db.commit()

    await show_checklists(cb)
    await cb.answer("🗑️ Чек-лист удалён")

