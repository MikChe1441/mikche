import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
import asyncio
from aiogram import F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters.command import Command
from aiogram import Bot, Dispatcher, types
import logging
import re

# # Путь к файлу JSON
# json_file_path = Path.home() / "profit-loss-table-eb4b5de8082f.json"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
logging.info("Код запущен")
bot = Bot(token='')
dp = Dispatcher(bot = bot)
cred_to_table = Credentials.from_service_account_file('profit-loss-table-eb4b5de8082f.json',scopes =scope)

def get_connection():
    google_table = gspread.authorize(credentials=cred_to_table)
    table_name = 'РАСХОДЫ-ДОХОДЫ'
    spreadsheet = google_table.open(table_name).worksheet('n')
    return spreadsheet

def get_options():
    data = get_connection().get_all_values()
    category_row = data[0][1:]
    return category_row
    # i need to pass this category_row to request_responce_telegram(category_row)

logging.info("Код 2")

def update_table(category:str = None, value:float = None):
    gc = gspread.authorize(credentials=cred_to_table)
    table_name = 'РАСХОДЫ-ДОХОДЫ'
    spreadsheet = gc.open(table_name).worksheet('n')
    data = spreadsheet.get_all_values()
    for dat in data[1:]:
        for i,d in enumerate(dat[:1]):
            if d != '':
                d = datetime.strptime(data[1:][:1][0][0],'%d.%m.%Y')
    for dat in data[1:]:
        for i, d in enumerate(dat[1:]):
            if d != '':
                # Заменяем запятые на точки
                d = d.replace(',', '.')
                # Преобразуем строку в число формата float
                try:
                    dat[i+1] = float(d)
                except ValueError:
                    print(f"Error: Unable to convert {d} to float")
    today = datetime.now().date().strftime('%d.%m.%Y')
    categories_row = data[0][1:]
    date_column = [row[0] for row in data]
    if today not in date_column:
        new_row = [today] + [''] * (len(categories_row) - 1)
        data.append(new_row)
    try:
        category_index = data[0][1:].index(category)+1
        for row in data:
            if row[0] == today:
                current_value = row[category_index]
                if current_value:
                    new_value = float(current_value)+ float(value)
                else:
                    new_value = value
                row[category_index] = float(new_value)
    except ValueError as e:
        print(f"Error: {e}")

    spreadsheet.update(data)
    


    

logging.info("Код 3")
category_options = get_options()

# Глобальные переменные для хранения категории и суммы
selected_category = None
entered_sum = None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logging.info("Код перед сообщением")

    # Создаем список кнопок клавиатуры
    keyboard_buttons = []
    for option in category_options:
        keyboard_buttons.append([types.KeyboardButton(text=option)])

    # Создаем клавиатуру с помощью списка кнопок
    keyboard = types.ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)
    
    await message.answer("Выберите категорию:", reply_markup=keyboard)

@dp.message(lambda message: re.match(r'^\d+(\.\d+)?$', message.text))
async def handle_entered_sum(message: types.Message):
    logging.info('вызвался обработчки суммы')
    global entered_sum
    money_spend_earned = message.text
    if money_spend_earned:
        entered_sum = money_spend_earned
        await message.answer(f"Вы потратили: {entered_sum}")
        if money_spend_earned:
            entered_sum = money_spend_earned
            await updating(selected_category, entered_sum) 
    else:
        logging.info('False')
        pass

@dp.message(F.text)
async def handle_selected_category(message: types.Message):
    global selected_category
    selected_category = message.text
    if selected_category in category_options:
        await message.answer(f"Выбрана категория: *{selected_category}*", parse_mode="Markdown")


async def updating(selected_category,entered_sum):
    update_table(selected_category,entered_sum)
    logging.info("Код асинк")
     # Обнуляем глобальные переменные после отправки в таблицу
    selected_category = None
    entered_sum = None


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
