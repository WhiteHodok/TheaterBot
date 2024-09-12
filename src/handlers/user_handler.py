import asyncio

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message, CallbackQuery, LabeledPrice, FSInputFile, InputMediaPhoto, PreCheckoutQuery

from config import bot, secrets, supabase, dp
from src.handlers.events import error_bot
from src.keyboards.user_keyboard import scene_maker, menu_maker, buying_seat_request_maker, back_seat_payment_maker, \
    buy_now_maker, buy_error_maker, accept_payment_maker
from src.phrases import INFO_ABOUT, SEAT_ABOUT, TICKET, BUY_ERROR, BUY_TICKET_THANKS, SEND_SCREENSHOT, TRANSACTION_SENT, \
    ERROR_BUY_SEAT
from src.states.user_states import User

user_router = Router()


async def reservation(seat_id, callback, state):
    chat_id = callback.from_user.id
    supabase.table('Seats').insert({'seat_id': seat_id, 'chat_id': chat_id, 'name': callback.from_user.username, 'status': False, 'accepted': False}).execute()
    await asyncio.sleep(6000)
    response = supabase.table('Seats').select('*').match({'seat_id': seat_id, 'chat_id': chat_id, 'status': False, 'accepted': False}).execute()
    if response.data:
        supabase.table('Seats').delete().match({'seat_id': seat_id, 'chat_id': chat_id, 'status': False, 'accepted': False}).execute()
        await buy_ticket(callback, state)


@user_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext):
    """
    Функция выводит информацию о спектакле с кнопкой "Купить"
    Функция пытается удалить
    -предыдущее сообщение с информацией о спектакле
    -сообщение с оплатой
    -команду /start
    """
    try:
        chat_id = message.chat.id
        try:
            response = supabase.table('UserData').select('*').eq('chat_id', chat_id).execute()
            if not response.data:
                supabase.table('UserData').insert(
                    {'chat_id': chat_id, 'username': message.from_user.username}).execute()
        except:
            pass
        state_data = await state.get_data()
        await state.set_state(User.menu)
        try:
            main_message_id = state_data.get('main_message_id')
            await bot.delete_message(chat_id=chat_id, message_id=main_message_id)
        except:
            pass
        try:
            invoice_message_id = state_data.get('invoice_message_id')
            if invoice_message_id:
                await bot.delete_message(chat_id=chat_id, message_id=invoice_message_id)
        except:
            pass
        file_path = './src/photo/cover.png'
        main_message = await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(file_path),
            caption=INFO_ABOUT,
            reply_markup=menu_maker(),
            parse_mode='HTML'
        )
        await state.update_data(main_message_id=main_message.message_id)
        await message.delete()
    except Exception as e:
        await error_bot('command start', message, str(e))


@user_router.callback_query(F.data == 'back_menu', User.seat)
async def back_menu(callback: CallbackQuery, state: FSMContext):
    """
    Функция обрабатывает нажатие на кнопку "Назад"
    """
    try:
        chat_id = callback.message.chat.id
        await state.set_state(User.menu)
        media = InputMediaPhoto(
            media=FSInputFile('./src/photo/cover.png'),
            caption=INFO_ABOUT,
            parse_mode='HTML'
        )
        await bot.edit_message_media(
            chat_id=chat_id,
            message_id=callback.message.message_id,
            media=media,
            reply_markup=menu_maker()
        )
    except Exception as e:
        await error_bot('back menu', callback.message, str(e))


@user_router.callback_query(F.data == 'back_seat', User.payment)
@user_router.callback_query(F.data == 'buy_ticket', User.menu)
async def buy_ticket(callback: CallbackQuery, state: FSMContext):
    """
    Функция обрабатывает нажатие на кнопку "Купить билет"
    """
    try:
        chat_id = callback.message.chat.id
        await state.set_state(User.seat)
        file_path = './src/photo/seat.png'
        media = InputMediaPhoto(media=FSInputFile(file_path),
                                caption=SEAT_ABOUT,
                                parse_mode='HTML'
                                )
        try:
            await bot.edit_message_media(
                chat_id=chat_id,
                message_id=callback.message.message_id,
                media=media,
                reply_markup=scene_maker()
            )
        except:
            main_message = await bot.send_photo(
                chat_id=chat_id,
                photo=FSInputFile(file_path),
                caption=SEAT_ABOUT,
                reply_markup=scene_maker(),
                parse_mode='HTML'
            )
            await state.update_data(main_message_id=main_message.message_id)
    except Exception as e:
        await error_bot('buy ticket', callback.message, str(e))


@user_router.callback_query(User.seat, lambda c: c.data.isdigit())
async def payment(callback: CallbackQuery, state: FSMContext):
    """
    Функция обрабатывает нажатие на место
    """
    try:
        await state.set_state(User.payment)
        chat_id = callback.message.chat.id
        seat = int(callback.data)
        state_data = await state.get_data()
        response = supabase.table('Seats').select('*').eq('seat_id', seat).execute()
        if not response.data:
            try:
                main_message_id = state_data.get('main_message_id')
                await bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=main_message_id,
                    caption=f'Перейти к оплате места <b>{seat}</b>',
                    reply_markup=buying_seat_request_maker(),
                    parse_mode='HTML'
                )
                await state.update_data(seat=seat)
            except:
                pass
    except Exception as e:
        await error_bot('payment', callback.message, str(e))


@user_router.callback_query(F.data == 'payment', User.payment)
async def payment_ticket(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    seat = await state.get_data()
    seat = seat.get('seat')
    response = supabase.table('Seats').select('*').eq('seat_id', seat).execute()
    data = response.data
    if not data:
        await state.set_state(User.wait_photo)
        asyncio.create_task(reservation(seat, callback, state))
        await bot.edit_message_caption(
            chat_id=chat_id,
            message_id=callback.message.message_id,
            caption=SEND_SCREENSHOT + f'\nМесто: {seat}',
            reply_markup=back_seat_payment_maker(),
            parse_mode='HTML'
        )
    else:
        await state.set_state(User.payment)
        await bot.edit_message_caption(
            chat_id=chat_id,
            message_id=callback.message.message_id,
            caption=BUY_ERROR+f'\nМесто: {seat}',
            reply_markup=buy_error_maker(),
            parse_mode='HTML'
        )


@user_router.callback_query(F.data == 'back_seat_in_wait_photo', User.wait_photo)
async def back_seat_in_wait_photo(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    seat_id = await state.get_data()
    seat_id = seat_id.get('seat')
    supabase.table('Seats').delete().match({'seat_id': seat_id, 'chat_id': chat_id, 'status': False, 'accepted': False}).execute()
    await buy_ticket(callback, state)


@user_router.message(F.photo, User.wait_photo)
async def wait_photo(message: Message, state: FSMContext):
    await state.set_state(User.payment)
    chat_id = message.chat.id
    data = await state.get_data()
    seat = data.get('seat')
    main_message_id = data.get('main_message_id')
    response = supabase.table('Seats').update({'status': True}).match({'seat_id': seat, 'chat_id': chat_id, 'status': False, 'accepted': False}).execute()
    if response.data:
        await bot.send_photo(
            chat_id=secrets.admin_id,
            photo=message.photo[-1].file_id,
            caption=f'ID чата: {chat_id}\nПокупатель: @{message.from_user.username}\nМесто: {seat}\nКомментарий: {message.caption}',
            reply_markup=accept_payment_maker(),
            parse_mode='HTML'
        )
        try:
            await bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=main_message_id,
                reply_markup=None,
            )
        except:
            pass
        main_message = await bot.send_photo(
            chat_id=message.chat.id,
            photo=FSInputFile('./src/photo/wait_ticket.jpg'),
            caption=TRANSACTION_SENT,
            parse_mode='HTML',
            reply_markup=buy_now_maker()
        )
    else:
        main_message = await bot.send_photo(
            chat_id=message.chat.id,
            photo=FSInputFile('./src/photo/error.jpg'),
            caption=ERROR_BUY_SEAT,
            parse_mode='HTML',
            reply_markup=buy_error_maker()
        )
    await state.update_data(main_message_id=main_message.message_id)
