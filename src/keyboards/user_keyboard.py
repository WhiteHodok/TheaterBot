from aiogram.types import KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import supabase


def menu_maker():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.row(
        InlineKeyboardButton(text='Купить билет', callback_data='buy_ticket')
    )
    return keyboard_builder.as_markup(resize_keyboard=True)


def scene_maker():
    response = supabase.table('Seats').select('*').execute()
    data = response.data
    keyboard_builder = InlineKeyboardBuilder()
    for seat_number in range(1, 36):
        if any(seat["seat_id"] == seat_number for seat in data):
            keyboard_builder.button(text='❌', callback_data='❌')
        else:
            keyboard_builder.button(text=str(seat_number), callback_data=str(seat_number))
    size = 5
    keyboard_builder.adjust(size)
    keyboard_builder.row(
        InlineKeyboardButton(text='Назад', callback_data='back_menu')
    )
    return keyboard_builder.as_markup(resize_keyboard=True)


def buying_seat_request_maker():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.row(InlineKeyboardButton(text='Оплатить', callback_data='payment'))
    keyboard_builder.row(InlineKeyboardButton(text='Назад', callback_data='back_seat'))
    return keyboard_builder.as_markup(resize_keyboard=True)


def back_seat_payment_maker():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.row(InlineKeyboardButton(text='Назад', callback_data='back_seat_in_wait_photo'))
    return keyboard_builder.as_markup(resize_keyboard=True)


def buy_now_maker():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.row(InlineKeyboardButton(text='Купить ещё билет', callback_data='back_seat'))
    return keyboard_builder.as_markup(resize_keyboard=True)


def buy_error_maker():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.row(InlineKeyboardButton(text='Выбрать другое место', callback_data='back_seat'))
    return keyboard_builder.as_markup(resize_keyboard=True)


def accept_payment_maker():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.add(InlineKeyboardButton(text='✅ Подтвердить', callback_data='yes'))
    keyboard_builder.add(InlineKeyboardButton(text='❌ Отменить', callback_data='no'))
    return keyboard_builder.as_markup(resize_keyboard=True)
