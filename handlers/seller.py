import os

from utils import keyboards
from SimpleQIWI import *
from utils import sqliter
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hbold
from loguru import logger
from loader import bot
from aiogram.dispatcher.filters.state import State, StatesGroup

new_sql = sqliter.Sqlite(os.path.abspath(os.path.join('bot_garant.db')))


class WaiteSoldMessage(StatesGroup):
    """
    Режим FSM, создаем состояния
    для принятия ID,
    предметов для продажи и
    и стоимости
    """
    waite_id = State()
    waite_sold_item = State()
    waite_cost = State()


# @dp.callback_query_handler(text='button17')
async def started_seller(callback_query: types.CallbackQuery):
    """
    Режим продавца,
    запрос ID начало сделки
    :param callback_query: types.CallbackQuery
    :return: None
    """
    await callback_query.message.edit_text('Вы перешли в раздел продавца, следуйте дальнейшим указаниями бота:')
    await callback_query.message.edit_reply_markup(reply_markup=keyboards.back_main_menu)
    await callback_query.message.answer('Введите ID покупателя, если его у вас нет, то пускай'
                                        ' покупатель запросит его у бота в разделе "Я покупатель"'
                                        '\nДля отмены сделки нажмите кнопку "Назад"')
    await callback_query.answer()
    await WaiteSoldMessage.waite_id.set()


# @dp.message_handler(state=WaiteSoldMessage.waite_id, content_types=types.ContentTypes.TEXT)
async def waite_sold_items(message: types.Message, state: FSMContext):
    """
    Запрос предметов на продажу,
    проверка на корректность введенного ID
    :param message: types.Message
    :param state: FSMContext
    :return: None
    """
    await state.update_data(id=message.text)
    user_data = await state.get_data()

    if user_data['id'].isdigit() and len(user_data["id"]) <= 10:
        if int(message.text) != int(message.from_user.id):
            await message.answer('Введите предметы, которые собираетесь продавать (все в одном сообщении, для отмены сделки нажмите на кнопку ниже):', reply_markup=keyboards.cancel_button)
            await WaiteSoldMessage.waite_sold_item.set()
        else:
            await message.answer('ID введен некорректно, повторите попытку ввода(заметьте ID не должен содержать букв и превышать 10 символов)')
    else:
        await message.answer('Вы не можете проводить сделку сами с собой!')


# @dp.message_handler(state=WaiteSoldMessage.waite_sold_item, content_types=types.ContentTypes.TEXT)  # Запрос цены
async def waite_cost(message: types.Message, state: FSMContext):
    """
    Запрашиваем цену у покупателя,
    попутно все данные сохраняем в словарь
    :param message: types.Message
    :param state: FSMContext
    :return: None
    """
    await state.update_data(item=message.text)
    await message.answer('Введите сумму за которую вы продаете данные предметы'
                         '(для отмены сделки нажмите на кнопку ниже): ', reply_markup=keyboards.cancel_button)
    await WaiteSoldMessage.waite_cost.set()


# @dp.message_handler(state=WaiteSoldMessage.waite_cost, content_types=types.ContentTypes.TEXT)
async def send_all_info_about_offer(message: types.Message, state: FSMContext):
    """
    Отправка сведений покупателю,
    добавление ID суммы сделки,
    формирование и обновление данных
    у пользователей в личном кабинете
    :param message: types.Message
    :param state: FSMContext
    :return None
    """
    person_id = message.from_user.id
    try:

        if message.text.isdigit():
            user_data = await state.get_data()
            history = (f'{hbold("Сведения сделки:")}\n'
                       f'1️⃣ID покупателя:{user_data["id"]}\n'
                       f'2️⃣Предметы для продажи:{user_data["item"]}\n'
                       f'3️⃣Цена за все:{message.text}')
            await message.answer(history, reply_markup=keyboards.keyboard)
            await bot.send_message(user_data["id"], history + f'\n{hbold("Данные корректны?")}', reply_markup=keyboards.inline_kb3)
            logger.info(f'{message.from_user.username} предложил сделку: {user_data["id"]}, цена: {message.text}, Предметы для продажи: {user_data["item"]}')
            new_sql.add_second_id(person_id, user_data["id"])
            new_sql.add_money(person_id, user_data["id"], message.text)
            counter_1 = new_sql.get_all_information(person_id)
            counter_2 = new_sql.get_all_information(user_data["id"])
            first = int(counter_1[1]) + 1
            second = int(counter_2[1]) + 1
            first_pay = int(counter_1[2]) + int(message.text)
            second_sold = int(counter_2[0]) + int(message.text)
            logger.info(f"{first_pay}--{second_sold} сохранено в личный кабинет!")
            new_sql.add_pay(str(second_sold), user_data["id"])
            new_sql.add_sold(str(first_pay), person_id)
            new_sql.add_count(str(first), person_id)
            new_sql.add_count(str(second), user_data["id"])
            new_sql.add_history(history, person_id)
            new_sql.add_history(history, user_data["id"])
            await state.finish()
        else:
            await message.answer('Введите сумму цифрами!')

    except Exception as exc:
        logger.error(f'Ошибка: {exc}')
        await message.answer('Данные о ID указаны некорректно, проверьте правильность написания!'
                             ' Или попросите покупателя отправить ID повторно.')
        await state.finish()


# @dp.callback_query_handler(text='btn7')
async def callback_no(callback_query: types.CallbackQuery):
    """
    Дополнительная проверка,
    покупатель подтверждает,
    что все данные по настояще корректны
    :param callback_query: types.CallbackQuery
    :return: None
    """
    await callback_query.message.edit_reply_markup()
    first_id = callback_query.from_user.id
    await bot.send_message(new_sql.take_second_id(first_id), 'Покупатель отклонил сделку. Причина: Данные сделки некорректны!'
                                                             '\nОбсудите со второй стороной подробнее сведения сделки.')


# @dp.callback_query_handler(text='btn6')  # Происходит оплата
async def user_pay(callback_query: types.CallbackQuery):
    """
    Пользователь выбирает способ оплаты,
    :param callback_query: types.CallbackQuery
    :return: None
    """
    await callback_query.message.edit_reply_markup()
    await callback_query.message.answer('Финальная часть сделки. Оплатите товар по указанной цене выше.\n'
                                        'Способы оплаты:', reply_markup=keyboards.inline_kb4)
    await callback_query.answer()


# @dp.callback_query_handler(text='btn8')  # Человек оплачивает покупку
async def user_send_money(callback_query: types.CallbackQuery):
    """
    Происходит оплата,
    работа с QIWI API
    :param callback_query: types.CallbackQuery
    :return: None
    """
    await callback_query.message.edit_reply_markup()
    person_id = callback_query.from_user.id
    token = os.getenv("QIWI_TOKEN")
    phone = os.getenv("PHONE_NUMBER")
    api = QApi(token=token, phone=phone)
    price = new_sql.get_money_for_pay(person_id)
    comment = api.bill(int(price))
    await callback_query.message.answer(f"💵Переведите сумму указанную выше.💵"
                                        f"\n{hbold('По номеру телефона:')} {phone} "
                                        f" \n{hbold('В комментарии к переводу вставьте этот текст:')}\n{comment}"
                                        f"\n\n{hbold('У вас 5 минут, чтобы совершить оплату, после чего сделка будет автоматически отменена.')}")

    api.start()
    # Проверка о поступлении платежа на кошелек QIWI
    start_time = 0
    while True:
        if api.check(comment):
            await callback_query.message.answer('Перевод прошел успешно!✅', reply_markup=keyboards.keyboard)
            await bot.send_message(new_sql.take_second_id(person_id), 'Покупатель оплатил сделку, выполните свою часть сделки!'
                                                                      ' После выполнения подтвердите ниже:', reply_markup=keyboards.inline_kb5)
            logger.info('Покупатель оплатил сделку!')
            break
        elif start_time == 300:
            await callback_query.message.answer('Сделка отменена...')
            await bot.send_message(new_sql.take_second_id(person_id), 'Сделка была отменена, покупатель не перевел оплату в течении 5 минут.')
            logger.info('Сделка отменена!')
            break
        start_time += 1
        time.sleep(1)
    api.stop()


# @dp.callback_query_handler(text='btn9')  # Проверка офера покупателем, после чего подтверждение сделки
async def check_offer(callback_query: types.CallbackQuery):
    """
    Проверка офера покупателем,
    переход к следующему шагу
    :param callback_query: types.CallbackQuery
    :return: None
    """
    await callback_query.message.edit_reply_markup()
    person_id = callback_query.from_user.id
    await bot.send_message(new_sql.take_second_id(person_id), 'Продавец выполнил свою часть сделки,'
                                                              ' как можно тщательнее все проверьте и подтвердите сделку',
                           reply_markup=keyboards.inline_kb6)


# @dp.callback_query_handler(text='btn10')  # Получение денег после успешной сделки
async def get_money(callback_query: types.CallbackQuery):
    """
    Последний шаг,
    получение денег продавцом
    :param callback_query: types.CallbackQuery
    :return: None
    """
    person_is = callback_query.from_user.id
    await callback_query.message.edit_reply_markup()
    await bot.send_message(new_sql.take_second_id(person_is), 'Сделка прошла успешно, вы можете получить деньги!', reply_markup=keyboards.inline_kb7)
    logger.info('Предмет  покупателем получены')


class TakeMoney(StatesGroup):
    """
    Формируем состояние
    для принятия номера телефона
    """
    waite_number = State()


# @dp.callback_query_handler(text='btn11')  # Прием номера телефона
async def get_phone_number(callback_query: types.CallbackQuery):
    """
    Прием номера телефона
    :param callback_query: types.CallbackQuery
    :return: None
    """
    await callback_query.message.edit_reply_markup()
    await callback_query.message.answer('Напишите боту номер вашего телефона:')

    await TakeMoney.waite_number.set()


# @dp.message_handler(state=TakeMoney.waite_number, content_types=types.ContentTypes.TEXT)
async def send_users_money(message: types.Message, state: FSMContext):
    """
    Отправка денег продавцу,
    работа с QIWI API
    :param message: types.Message
    :param state: FSMContext
    :return: None
    """
    first_id = message.from_user.id
    token = os.getenv("QIWI_TOKEN")
    phone = os.getenv("PHONE_NUMBER")
    money = new_sql.get_money_for_pay(first_id)  # Достаем сумму из бд, для дальнейшей отправки пользователю
    await state.update_data(number=message.text)
    try:
        if message.text.isdigit():                # Проверка номера телефона на его корректность
            user_data = await state.get_data()
            api = QApi(token=token, phone=phone)
            print(*api.balance)

            api.pay(account=user_data['number'], amount=money)  # Перевод средств
            await message.answer('Оплата переведена!', reply_markup=keyboards.inline_kb8)
            await bot.send_message(new_sql.take_second_id(first_id), 'Сделка прошла успешно!', reply_markup=keyboards.inline_kb8)
            await state.finish()
            logger.info(f'Оплата переведена!--{message.from_user.id}, {message.from_user.username}')
        else:
            await message.answer('Введите номер цифрами!')
    except Exception as exc:
        logger.error(f'Ошибка: {exc}')
        await message.answer('Ошибка, некорректный номер, проверьте правильность набранного номера!')


async def cancel_button(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Отмена сделки, через
    инлайн клавиатуру
    :param  callback_query: types.CallbackQuery
    :param state: FSMContext
    :return: None
    """
    await state.finish()
    await callback_query.message.answer('Сделка отменена...')
    await callback_query.message.edit_reply_markup()


def register_seller_handlers(dispatcher: Dispatcher):
    """
    Регистрация хэндлеров
    :param dispatcher: Dispatcher
    :return: None
    """
    dispatcher.register_callback_query_handler(started_seller, text='button17')
    dispatcher.register_message_handler(waite_sold_items, state=WaiteSoldMessage.waite_id, content_types=types.ContentTypes.TEXT)
    dispatcher.register_message_handler(waite_cost, state=WaiteSoldMessage.waite_sold_item, content_types=types.ContentTypes.TEXT)
    dispatcher.register_message_handler(send_all_info_about_offer, state=WaiteSoldMessage.waite_cost, content_types=types.ContentTypes.TEXT)
    dispatcher.register_callback_query_handler(user_pay, text='btn6')
    dispatcher.register_callback_query_handler(user_send_money, text='btn8')
    dispatcher.register_callback_query_handler(callback_no, text='btn7')
    dispatcher.register_callback_query_handler(check_offer, text='btn9')
    dispatcher.register_callback_query_handler(get_money, text='btn10')
    dispatcher.register_callback_query_handler(get_phone_number, text='btn11')
    dispatcher.register_message_handler(send_users_money, state=TakeMoney.waite_number, content_types=types.ContentTypes.TEXT)
    dispatcher.register_callback_query_handler(cancel_button, text='cancel', state='*')