from aiogram.utils import executor
from loader import dp
from loguru import logger
from handlers import admin_menu
from handlers import main_menu
from handlers import buyer
from handlers import seller

logger.add('logger.log', format='{time} {level} {message}',
           level='ERROR')

admin_menu.register_admin_menu(dp)
main_menu.register_main_menu(dp)
buyer.register_buyer_handlers(dp)
seller.register_seller_handlers(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)