from utils import keyboards
from aiogram import types, Dispatcher
from loader import bot


# @dp.callback_query_handler(text='button18')
async def get_users_id(callback_query: types.CallbackQuery):
    """
    Получение ID покупателем
    :param callback_query: types.CallbackQuery
    :return: None
    """
    await callback_query.message.edit_text('Получите свой ID и отправьте его продавцу.'
                                           'Ждите следующих инструкций от бота, когда продавец выполнит все требования.🕔')
    await callback_query.message.edit_reply_markup(reply_markup=keyboards.inline_kb1)


# @dp.callback_query_handler(text='button1')
async def send_users_id(callback_query: types.CallbackQuery):
    """
    Отправка ботом ID покупателю
    :param callback_query: types.CallbackQuery
    :return: None
    """
    call = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f'{call}')


def register_buyer_handlers(dispatcher: Dispatcher):
    """
    Регистрация хэндлеров
    :param dispatcher: Dispatcher
    :return: None
    """
    dispatcher.register_callback_query_handler(get_users_id, text='button18')
    dispatcher.register_callback_query_handler(send_users_id, text='button1')
