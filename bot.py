import time
import random
import asyncio
import typing
import pickle
import datetime

from aiogram.types import base
import aiogram.utils.exceptions
import aiogram.utils.markdown as md
from aiogram import Bot as AioBot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from aiogram.types.message import ContentType
from aiohttp.helpers import BasicAuth
from aiogram.dispatcher.filters.state import State
from aiogram.utils.callback_data import CallbackData
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from utils.config import (TOKEN,
                          MAIN_ID,
                          MODER_ID,
                          ADMINS_ID,
                          ig_login,
                          ig_password
                          )
from utils.telegram_utils import (get_main_kb,
                                  get_menu_kb,
                                  get_acc_kb,
                                  )
from db.models.stat import Statistics
from db.models.user import User
from db.models.tasks import Tasks
from db.models.instagram_account import InstagramAccount
from states_groups.accounts_forms import AddAccountForm, AddTaskForm

ref_link = "https://t.me/{}?start={}"

storage = MemoryStorage()


class Bot(AioBot):

    async def send_message(self, chat_id: typing.Union[base.Integer, base.String], text: base.String,
                           parse_mode: typing.Union[base.String, None] = None,
                           disable_web_page_preview: typing.Union[base.Boolean, None] = None,
                           disable_notification: typing.Union[base.Boolean, None] = None,
                           reply_to_message_id: typing.Union[base.Integer, None] = None,
                           reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                      types.ReplyKeyboardMarkup,
                                                      types.ReplyKeyboardRemove,
                                                      types.ForceReply, None] = None) -> typing.Union[types.Message,
                                                                                                      typing.NoReturn]:
        try:
            return await super().send_message(chat_id,
                                              text,
                                              parse_mode,
                                              disable_web_page_preview,
                                              disable_notification,
                                              reply_to_message_id,
                                              reply_markup)
        except aiogram.exceptions.ChatNotFound:
            return
        except aiogram.utils.exceptions.BotBlocked:
            return
        except aiogram.exceptions.UserDeactivated:
            return


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=["start"], state="*")
async def start_cmd(message: types.Message, state: FSMContext):
    """
    Старт и регистрация с рефом или без
    """
    user = await User.get_user(uid=message.from_user.id)

    keyboard_markup = get_main_kb()

    if user is None:
        await Statistics.increase_param("new_users_today", None, 1)
        splited_text = message.text.split()
        uname = message.from_user.username if message.from_user.username else 'noLogin'
        if len(splited_text) > 1:
            ref_code = splited_text[-1]
            inviter = await User.get_user_by_ref_link(ref_code)

            if not inviter:
                await User.create_user(
                    uid=message.from_user.id, referrals=[], inviter=None,
                    username=uname)
            else:
                new_user = await User.create_user(
                    uid=message.from_user.id, inviter=inviter.uid, referrals=[],
                    username=uname)
                await User.add_referral(inviter, new_user)
        else:
            await User.create_user(
                uid=message.from_user.id, referrals=[], inviter=None,
                username=uname)

        await bot.send_message(message.from_user.id,
                               "Приветствеум в нашем боте",
                               reply_markup=keyboard_markup)
    else:
        await bot.send_message(message.from_user.id,
                               "Выберите дальнейшее действие",
                               reply_markup=keyboard_markup)

    current_state = await state.get_state()

    if current_state:
        await state.finish()


@dp.message_handler(commands=["send_all"])
async def give_currency(message: types.Message):
    user: User = await User.get_user(uid=message.from_user.id)

    if str(message.from_user.id) not in ADMINS_ID:
        await bot.send_message(message.from_user.id,
                               "Команда доступна только админам!")
        return

    await bot.send_message(message.from_user.id,
                           f"Начинаю рассылку...")
    all_users = await User.get_all_users()

    text = message.text[9:]

    async for user in all_users:
        try:
            await bot.send_message(user.uid, text)
        except aiogram.utils.exceptions.UserDeactivated:
            pass
        except aiogram.utils.exceptions.BotBlocked:
            pass
        except Exception as e:
            log.exception(e)

    await bot.send_message(message.from_user.id,
                           f"Рассылка завершена!")


@dp.message_handler(commands=["stat"])
async def give_currency(message: types.Message):
    user: User = await User.get_user(uid=message.from_user.id)

    if str(message.from_user.id) not in ADMINS_ID:
        await bot.send_message(message.from_user.id,
                               "Команда доступна только админам!")
        return

    users = await User.get_all_users()

    users_count = 0

    async for user in users:
        users_count += 1

    stat: Statistics = await Statistics.get_current_stat()
    text = f"""
Сегодня - {datetime.datetime.utcnow().strftime('%Y-%m-%d')}\n
Всего пользователей - {users_count}
Новых пользователей сегодня - {stat.new_users_today}
Открывали бота сегодня - {len(stat.open_bot_today)}
Добавлено денег сегодня - {stat.add_money_today}
Всего лайков - {stat.all_likes}
    """
    text2 = f"""
{datetime.datetime.utcnow().strftime('%Y-%m-%d')};\n
{users_count};{stat.new_users_today};\
{len(stat.open_bot_today)};{stat.add_money_today};\
{stat.all_likes}
    """
    await bot.send_message(message.from_user.id, text)
    await bot.send_message(message.from_user.id, text2)


@dp.message_handler(commands=["send"])
async def give_currency(message: types.Message):
    user: User = await User.get_user(uid=message.from_user.id)

    if str(message.from_user.id) not in ADMINS_ID:
        await bot.send_message(message.from_user.id,
                               "Команда доступна только админам!")
        return

    splited = message.text.split()

    if len(splited) < 3:
        await bot.send_message(message.from_user.id,
                               f"Недостаточно параметров")
        return

    user_id = int(splited[1])
    text = " ".join(splited[2:])
    try:
        await bot.send_message(user_id, text)
    except aiogram.utils.exceptions.ChatNotFound:
        await bot.send_message(message.from_user.id, f"Чат с таким айди не найден")
    else:
        await bot.send_message(message.from_user.id, f"Отправлено!")


@dp.message_handler(text='🔙 Назад', state="*")
async def order_nakrutka(message: types.Message, state: FSMContext):
    await state.reset_state()
    markup = get_main_kb()
    await message.answer('Вы отменили действие',
                         reply_markup=markup, )


@dp.message_handler(text="Добавить аккаунт")
@dp.callback_query_handler(text="add_accounts")
async def add_acc(message: types.Message, state: FSMContext):
    """
    Кнопка добавить аккаунт
    """
    markup = get_menu_kb()

    await message.answer('Чтобы управлять вашим аккаунтом'
                         ', нам понадобится логин и пароль к нему.'
                         f',\nВведите логин аккаунта, например durov',
                         reply_markup=markup)

    await AddAccountForm.login.set()


@dp.message_handler(state=AddAccountForm.login)
async def add_pass(message: types.Message, state: FSMContext):
    login = message.text.lower()

    await state.update_data(login=login)

    markup = get_menu_kb()

    await message.answer('Введите пароль от аккаунта',
                         reply_markup=markup,
                         )

    await AddAccountForm.password.set()


@dp.message_handler(state=AddAccountForm.password)
async def add_proxy(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)

    markup = get_menu_kb()

    await message.answer('Добавьте прокси в формате ip:port:login:password',
                         reply_markup=markup,
                         )

    await AddAccountForm.proxy.set()


@dp.message_handler(state=AddAccountForm.proxy)
async def add_confirm(message: types.Message, state: FSMContext):
    await state.update_data(proxy=message.text)

    async with state.proxy() as data:
        login = data.get('login')
        password = data.get('password')
        proxy = data.get('proxy')

    markup = types.ReplyKeyboardMarkup(
        keyboard=
        [
            [types.KeyboardButton(text='Подтвердить✅')],
            [types.KeyboardButton(text='Отменить❌')],
        ],
        resize_keyboard=True,
    )

    await message.answer(f'Мы сохраним:'
                         f'\nЛогин - {login}'
                         f'\nПароль - {password}'
                         f'\nПрокси - {proxy}',
                         reply_markup=markup,
                         )
    await AddAccountForm.confirm.set()


@dp.message_handler(text='Отменить❌', state=AddAccountForm.confirm)
async def order_nakrutka(message: types.Message, state: FSMContext):
    await state.reset_state()
    markup = get_main_kb()
    await message.answer('Вы отменили добавление акканта',
                         reply_markup=markup, )


@dp.message_handler(text='Отменить❌', state="*")
async def order_nakrutka(message: types.Message, state: FSMContext):
    await state.reset_state()
    markup = get_main_kb()
    await message.answer('Вы отменили добавление акканта',
                         reply_markup=markup, )


@dp.message_handler(text='Подтвердить✅', state=AddAccountForm.confirm)
async def comlited_add_acc(message: types.Message, state: FSMContext):
    user: User = await User.get_user(message.from_user.id)

    async with state.proxy() as data:
        login = data.get('login')
        password = data.get('password')
        proxy = data.get('proxy')

    await InstagramAccount.create_account(user=user, ig_login=login, ig_password=password, proxy=proxy)

    markup = get_main_kb()

    await message.answer('Аккаунт успешно добавлен!', reply_markup=markup)
    await state.reset_state()


@dp.message_handler(text="Добавить задание")
@dp.callback_query_handler(text="add_task")
async def add_task(message: types.Message, state: FSMContext):
    """
    Кнопка добавить Задание
    """
    user: User = await User.get_user(message.from_user.id)

    all_task = await InstagramAccount.get_user_accs(user)

    markup = types.ReplyKeyboardMarkup(row_width=2,
                                       resize_keyboard=True,
                                       )
    all_user_accs = list()
    async for task in all_task:
        print(all_user_accs)
        all_user_accs.append(
            task.dump().get('ig_login'))
    for acc in set(all_user_accs):
        markup.insert(types.KeyboardButton(text=acc))

    markup.row(types.KeyboardButton(text='Назад'))

    await message.answer('Здесь вы можете поставить задание на свои аккаунты'
                         f',\nВыберите. на какой из аккаунтов создать задание',
                         reply_markup=markup)

    await AddTaskForm.account.set()

#Доделать создание графика запуска


@dp.message_handler(text="❗ Правила")
@dp.callback_query_handler(text="rules")
async def rules_callback_handler(message: types.Message):
    """
    Кнопка правила
    """

    await bot.send_message(message.from_user.id, f"Здесь ссылка на Правила")


# временный первый вход
@dp.message_handler(commands=["go"])
async def reg(message: types.Message):
    await bot.send_message(message.from_user.id, 'Заходим в аккаунт')
    await instagram_login()
    await bot.send_message(message.from_user.id, 'Вход совершен успешно')


@dp.message_handler(state='*')
async def text(message: types.Message):
    await bot.send_message(message.from_user.id, f'Собираем посты по хэштегу #{message.text}')
    posts_urls = await collect_link_by_hashtag(message.text)
    len_all = len(posts_urls)
    await bot.send_message(message.from_user.id, f'Собрали {len_all} постов')
    await bot.send_message(message.from_user.id, f'Начинаем лайкать')
    await like_photo_by_hashtag(posts_urls)
    await bot.send_message(message.from_user.id, f'Прошли все посты')


async def close_browser():
    browser.close()
    browser.quit()


# метод логина
async def instagram_login():
    browser = webdriver.Firefox()
    browser.get('https://www.instagram.com')
    time.sleep(random.randrange(3, 5))

    username_input = browser.find_element_by_name('username')
    username_input.clear()
    username_input.send_keys(ig_login)

    time.sleep(2)

    password_input = browser.find_element_by_name('password')
    password_input.clear()
    password_input.send_keys(ig_password)

    password_input.send_keys(Keys.ENTER)
    time.sleep(40)
    pickle.dump(browser.get_cookies(), open(f"{ig_login}.pkl", "wb"))
    browser.close()
    browser.quit()


async def collect_link_by_hashtag(hashtag):
    browser = webdriver.Firefox()
    browser.get('https://www.instagram.com')
    cookies = pickle.load(open(f"{ig_login}.pkl", "rb"))
    for cookie in cookies:
        browser.add_cookie(cookie)
    browser.get(f'https://www.instagram.com/explore/tags/{hashtag}/')
    await asyncio.sleep(5)

    posts_urls = []
    #Надо брать количество постов из Instagram
    for i in range(1, int(400 / 13)):
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(random.randrange(3, 5))
        print(f'Проход {i}')
        hrefs = browser.find_elements_by_tag_name('a')
        for item in hrefs:
            hrefs = browser.find_elements_by_tag_name('a')
            try:
                href = item.get_attribute('href')
                if '/p/' in href:
                    if href not in posts_urls:
                        posts_urls.append(href)
                        # time.sleep(1)
                        print(f'{len(posts_urls)}')
                else:
                    continue
            except StaleElementReferenceException:
                print('Словлено исключение')
                print(f"{i}")
    browser.close()
    browser.quit()
    return posts_urls


async def like_photo_by_hashtag(posts_urls):
    print(posts_urls)
    browser = webdriver.Firefox()
    browser.get('https://www.instagram.com')
    cookies = pickle.load(open(f"{ig_login}.pkl", "rb"))
    for cookie in cookies:
        browser.add_cookie(cookie)
    num_post = 1
    for url in posts_urls:
        print(f'Post №{num_post}')
        num_post += 1
        try:
            browser.get(url)
            try:
                time.sleep(1)
                if browser.find_element_by_css_selector(
                        "[aria-label='Не нравится']") not in browser.find_elements_by_css_selector('.aria-label'):
                    print('уже стоит лайк')
            except Exception as ex:
                like_button = browser.find_element_by_xpath(
                    '/html/body/div[1]/section/main/div/div[1]/article/div[3]/section[1]/span[1]/button').click()
                print('поставили лайк')
            try:
                if browser.find_element_by_css_selector(
                        "[aria-label=Удалить]") not in browser.find_elements_by_css_selector('.aria-label'):
                    print('уже сохранено')
            except Exception as ex:
                save_button = browser.find_element_by_xpath(
                    '/html/body/div[1]/section/main/div/div[1]/article/div[3]/section[1]/span[3]/div/div/button').click()
                print('Сохранили')
            time.sleep(random.randrange(1, 2))

        except Exception as ex:
            print(ex)
            browser.close()
    browser.close()
    browser.quit()


if __name__ == '__main__':
    import os

    os.environ['TZ'] = 'Europe/Moscow'
    if not os.name == 'nt':
        time.tzset()
    loop = asyncio.get_event_loop()

    # loop.create_task(start_like())
    loop.create_task(executor.start_polling(dp, skip_updates=True))
    loop.run_forever()
