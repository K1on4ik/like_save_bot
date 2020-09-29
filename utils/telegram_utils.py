import datetime

import aiogram.utils.markdown as md
from aiogram import Bot
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.callback_data import CallbackData

from db.models.instagram_account import InstagramAccount
from db.models.stat import Statistics
from db.models.tasks import Tasks
from db.models.user import User
from utils.config import MAIN_ID, MODER_ID, ADMINS_ID


def get_main_kb(*args, **kwargs) -> ReplyKeyboardMarkup:
    """Get main keyboard.
    :return markup:"""
    markup = ReplyKeyboardMarkup(
        keyboard=
        [
            [KeyboardButton("Добавить аккаунт"), KeyboardButton('Добавить задание')],
            [KeyboardButton("Кабинет"), KeyboardButton("❗ Правила")],
        ],
        row_width=4,
        resize_keyboard=True,
    )

    return markup


def get_menu_kb():
    """
    Клавиатура с кнопкой меню (для стейтов)
    """
    markup = ReplyKeyboardMarkup(row_width=1,
                                          resize_keyboard=True, )

    markup.add(
        KeyboardButton("🔙 Назад"))

    return markup


def get_acc_kb(account):
    """
    Клавиатура для аккаунта
    """
    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(
        InlineKeyboardButton(f'❌ Удалить',
                                   callback_data=f"del-{account.pk}"),
    )

    markup.add(
        InlineKeyboardButton(f'🔙 Назад',
                                   callback_data=f"my_accounts"),
    )
    return markup


