import os

from utils import keyboards
from utils import sqliter
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hbold
from loguru import logger
from loader import bot
from aiogram.dispatcher.filters.state import State, StatesGroup

new_sql = sqliter.Sqlite(os.path.abspath(os.path.join('bot_garant.db')))

root = None


# @dp.message_handler(commands=['admin'])
async def admin_menu(message: types.Message):
    """
    Разблокировка админ меню по ID
    :param message: types.Message
    :return: None
    """
    global root
    root = 688136452
    if root == message.from_user.id:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['Просмотр сообщений', 'Ответить на сообщение', 'Просмотреть ко-во пользователей',  'Сделать рекламный пост']

        keyboard.add(*buttons)
        await message.answer('Админ меню открыто. Приятного пользования.'
                             '\nЧтобы его закрыть пропишите или нажмите на команду /start.', reply_markup=keyboard)
    else:
        logger.info(f"Пользователь {message.from_user.id}|{message.from_user.username} попытался войти в 'админ меню' ")


# @dp.message_handler(lambda message: message.text == 'Просмотр сообщений')
async def view(message: types.Message):
    """
    Просмотр всех сообщений
    :param message: types.Message
    :return: None
    """
    if root == message.from_user.id:
        all_question = new_sql.get_question()
        for question in all_question:
            await message.answer(question)


# @dp.message_handler(lambda message: message.text == 'Просмотреть ко-во пользователей')
async def count_people(message: types.Message):
    """
    Просмотр кол-во пользователей
    :param message: types.Message
    :return: None
    """
    if root == message.from_user.id:
        count = 0
        users = new_sql.get_all_id()
        for _ in users:
            count += 1
        await message.answer(f'Всего пользователей:  {count}')


class Answer(StatesGroup):
    """
    Создаем состояния для
    ответа пользователем на их вопросы
    """
    id_person_waite = State()
    answer_waite = State()


# @dp.message_handler(lambda message: message.text == 'Ответить на сообщение')
async def answer(message: types.Message):
    """
    Вводим ID человека,
    которому хотим ответить на сообщение
    :param message: types.Message
    :return: None
    """
    if root == message.from_user.id:
        await message.answer('Введите ID человека, которому хотите ответить:')
        await Answer.id_person_waite.set()


# @dp.message_handler(state=Answer.id_person_waite, content_types=types.ContentTypes.TEXT)
async def id_person_waite(message: types.Message, state: FSMContext):
    """
    Вводим сообщение с ответом
    :param message: types.Message
    :param state: FSMContext
    :return: None
    """
    await state.update_data(id=message.text)
    await message.answer('Введите сообщение с ответом:')
    await Answer.answer_waite.set()


# @dp.message_handler(state=Answer.answer_waite, content_types=types.ContentTypes.TEXT)
async def answer_waite(message: types.Message, state: FSMContext):
    """
    Происходит отправка сообщения пользователю
    :param message: types.Message
    :param state: FSMContext
    :return: None
    """
    await state.update_data(answer=message.text)
    get_data = await state.get_data()
    try:
        await bot.send_message(get_data['id'], get_data['answer'])
        await state.finish()
        await message.answer('Сообщение отправлено!')
        logger.info(f'Отправлено сообщение с ответом пользователю: {message.from_user.id}')
    except Exception as exc:
        logger.error(f'Ошибка: {exc}. ID: {message.from_user.id}')
        await message.answer('Данные об ID указаны не верно, перепроверьте, или пользователь заблокировал бота.')
        await state.finish()


class WaitePost(StatesGroup):
    """
    Создаем состояния для приема
    частей рекламного поста
    """
    waite_title_headers = State()
    waite_text = State()
    waite_img = State()
    waite_href = State()


# @dp.message_handler(lambda message: message.text == "Сделать рекламный пост")
async def add_post(message: types.Message):
    """
    Активация рекламного поста
    прием заголовка
    :param message: types.Message
    :return: None
    """
    user_id = message.from_user.id
    if user_id == 688136452:
        await message.answer('Введите заголовок рекламного поста:')
        await WaitePost.waite_title_headers.set()


# @dp.message_handler(state=WaitePost.waite_title_headers)
async def waite_title(message: types.Message, state: FSMContext):
    """
    Прием основного текста
    :param message: types.Message
    :param state: FSMContext
    :return: None
    """
    await state.update_data(title=message.text)
    await message.answer('Введите основной текст: ')
    await WaitePost.waite_text.set()


# @dp.message_handler(state=WaitePost.waite_text)
async def waite_text(message: types.Message,  state: FSMContext):
    """
    Прием фотографии
    :param message: types.Message
    :param state: FSMContext
    :return: None
    """
    await state.update_data(text=message.text)
    await message.answer('Вставьте фотографию для привлечения внимания:')
    await WaitePost.waite_img.set()


# @dp.message_handler(state=WaitePost.waite_img, content_types=types.ContentTypes.PHOTO)
async def waite_img(message: types.Message, state: FSMContext):
    """
    Прием ссылки
    :param message: types.Message
    :param state: FSMContext
    :return: None
    """
    await state.update_data(img=message.photo[0].file_id)
    await message.answer('Введите ссылку рекламируемый объект: ')
    await WaitePost.waite_href.set()


# @dp.message_handler(state=WaitePost.waite_href)
async def waite_href_and_send(message: types.Message, state: FSMContext):
    """
     Отправка рекламного поста
     пользователям по их ID
    :param message: types.Message
    :param state: FSMContext
    :return: None
    """
    await state.update_data(href=message.text)
    user_data = await state.get_data()
    inline_post_kb = keyboards.InlineKeyboardButton('Перейти к источнику', url=user_data["href"])
    post_keyboard = keyboards.InlineKeyboardMarkup().add(inline_post_kb)
    users_id = new_sql.get_all_id()
    for i_id in users_id:
        try:
            await bot.send_photo(*i_id, user_data["img"],
                                 f'{hbold(user_data["title"])}\n\n{user_data["text"]}', reply_markup=post_keyboard)
        except Exception as exc:
            logger.error(f"Пользователь {i_id} заблокировал бота.|{exc}|")

    await state.finish()


def register_admin_menu(dispatcher: Dispatcher):
    """
    Регистрация хэхндлеров
    :param dispatcher: Dispatcher
    :return: None
    """
    dispatcher.register_message_handler(admin_menu, commands=['admin'])
    dispatcher.register_message_handler(view, lambda message: message.text == 'Просмотр сообщений')
    dispatcher.register_message_handler(count_people, lambda message: message.text == 'Просмотреть ко-во пользователей')
    dispatcher.register_message_handler(answer, lambda message: message.text == 'Ответить на сообщение')
    dispatcher.register_message_handler(id_person_waite, state=Answer.id_person_waite, content_types=types.ContentTypes.TEXT)
    dispatcher.register_message_handler(answer_waite, state=Answer.answer_waite, content_types=types.ContentTypes.TEXT)
    dispatcher.register_message_handler(add_post, lambda message: message.text == "Сделать рекламный пост")
    dispatcher.register_message_handler(waite_title, state=WaitePost.waite_title_headers)
    dispatcher.register_message_handler(waite_text, state=WaitePost.waite_text)
    dispatcher.register_message_handler(waite_img, state=WaitePost.waite_img, content_types=types.ContentTypes.PHOTO)
    dispatcher.register_message_handler(waite_href_and_send, state=WaitePost.waite_href)
