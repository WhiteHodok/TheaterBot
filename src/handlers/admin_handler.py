import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, FSInputFile

from config import secrets, supabase, bot, dp
from src.keyboards.user_keyboard import buy_now_maker, buy_error_maker
from src.phrases import BUY_TICKET_THANKS, TICKET, ERROR_PAYMENT
from src.states.user_states import User

admin_router = Router()


def extract_variables(text):
    """Извлекает переменные из текста."""

    # Извлекаем номер места
    seat = re.search(r"Место: (\d+)", text).group(1)

    # Извлекаем chat_id
    chat_id = re.search(r"ID чата: (\d+)", text).group(1)

    return {
        "seat": seat,
        "chat_id": chat_id,
    }


async def reload_main_message(chat_id):
    chat_id = int(chat_id)
    state_with: FSMContext = FSMContext(
        storage=dp.storage,
        key=StorageKey(
            chat_id=chat_id,
            user_id=chat_id,
            bot_id=bot.id))
    state_data = await state_with.get_data()
    main_message_id = state_data.get('main_message_id')
    try:
        await bot.delete_message(chat_id=chat_id, message_id=main_message_id)
    finally:
        await state_with.set_state(User.payment)
        return state_with


@admin_router.callback_query(F.data == 'yes', lambda c: c.message.chat.id == secrets.admin_id)
async def admin_accept_payment(callback: CallbackQuery, state: FSMContext):
    client_data = extract_variables(callback.message.caption)
    client_chat_id = client_data.get('chat_id')
    chat_id = callback.message.chat.id
    response = supabase.table('Seats').update({'accepted': True}).match({'seat_id': client_data.get('seat'), 'chat_id': client_chat_id, 'status': True, 'accepted': False}).execute()
    if response.data:
        await bot.edit_message_caption(
            chat_id=chat_id,
            message_id=callback.message.message_id,
            caption='✅ '+callback.message.caption,
            reply_markup=None,
            parse_mode='HTML'
        )
        await bot.send_photo(
            chat_id=client_chat_id,
            photo=FSInputFile(f'./src/photo/{client_data.get('seat')}_билет.jpg'),
            caption=TICKET,
            parse_mode='HTML'
        )
        state_with = await reload_main_message(client_chat_id)
        main_message = await bot.send_photo(
            chat_id=client_chat_id,
            photo=FSInputFile(f'./src/photo/thanks.jpg'),
            caption=BUY_TICKET_THANKS,
            parse_mode='HTML',
            reply_markup=buy_now_maker(),
            message_effect_id="5159385139981059251"
        )
        await state_with.set_data({'main_message_id': main_message.message_id})
    else:
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption='❌Критическая ошибка, необходима проверка❌\n\n'+callback.message.caption,
            reply_markup=None,
            parse_mode='HTML'
        )


@admin_router.callback_query(F.data == 'no', lambda c: c.message.chat.id == secrets.admin_id)
async def admin_cancel_payment(callback: CallbackQuery, state: FSMContext):
    client_data = extract_variables(callback.message.caption)
    client_chat_id = client_data.get('chat_id')
    chat_id = callback.message.chat.id
    response = supabase.table('Seats').delete().match({'seat_id': client_data.get('seat'), 'chat_id': client_chat_id, 'status': True, 'accepted': False}).execute()
    await bot.edit_message_caption(
        chat_id=chat_id,
        message_id=callback.message.message_id,
        caption='❌ ' + callback.message.caption,
        reply_markup=None,
        parse_mode='HTML'
    )
    await bot.send_message(
        chat_id=client_chat_id,
        text=f'<b>Оплата билета {client_data.get("seat")} отменена</b>',
        parse_mode='HTML',
        message_effect_id="5104841245755180586"
    )
    state_with = await reload_main_message(client_chat_id)
    main_message = await bot.send_photo(
        chat_id=client_chat_id,
        photo=FSInputFile(f'./src/photo/error.jpg'),
        caption=ERROR_PAYMENT,
        parse_mode='HTML',
        reply_markup=buy_error_maker()
    )
    await state_with.set_data({'main_message_id': main_message.message_id})
