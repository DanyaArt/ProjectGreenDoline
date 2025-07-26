import telebot
from telebot import types
import sqlite3
from datetime import datetime

TOKEN = '7709800436:AAG9zdInNqWmU-TW7IuzioHhy_McWnqLw0w'
bot = telebot.TeleBot(TOKEN)

def get_db():
    conn = sqlite3.connect('users_fresh.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        first_name TEXT,
        last_name TEXT,
        middle_name TEXT,
        phone TEXT,
        school INTEGER,
        class INTEGER,
        register_date TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton('Мой профиль'),
        types.KeyboardButton('Изменить'),
        types.KeyboardButton('Удалить')
    )
    bot.send_message(chat_id, reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id=?', (message.from_user.id,)).fetchone()
    conn.close()
    if user:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы.')
        show_main_menu(message.chat.id)
    else:
        msg = bot.send_message(message.chat.id, 'Введите вашу фамилию:')
        bot.register_next_step_handler(msg, process_last_name)

def process_last_name(message):
    last_name = message.text.strip()
    msg = bot.send_message(message.chat.id, 'Введите ваше имя:')
    bot.register_next_step_handler(msg, lambda m: process_first_name(m, last_name))

def process_first_name(message, last_name):
    first_name = message.text.strip()
    msg = bot.send_message(message.chat.id, 'Введите ваше отчество:')
    bot.register_next_step_handler(msg, lambda m: process_middle_name(m, last_name, first_name))

def process_middle_name(message, last_name, first_name):
    middle_name = message.text.strip()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Отправить номер телефона', request_contact=True))
    msg = bot.send_message(message.chat.id, 'Пожалуйста, отправьте свой номер телефона кнопкой ниже:', reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_phone(m, last_name, first_name, middle_name))

def process_phone(message, last_name, first_name, middle_name):
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()
    msg = bot.send_message(message.chat.id, 'Введите номер вашей школы (только цифры, например 50):', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, lambda m: process_school(m, last_name, first_name, middle_name, phone))

def process_school(message, last_name, first_name, middle_name, phone):
    school = message.text.strip()
    if not school.isdigit() or not (1 <= int(school) <= 999):
        msg = bot.send_message(message.chat.id, 'Пожалуйста, введите номер школы цифрами (от 1 до 999):')
        return bot.register_next_step_handler(msg, lambda m: process_school(m, last_name, first_name, middle_name, phone))
    msg = bot.send_message(message.chat.id, 'Введите ваш класс (от 1 до 11):')
    bot.register_next_step_handler(msg, lambda m: process_class(m, last_name, first_name, middle_name, phone, int(school)))

def process_class(message, last_name, first_name, middle_name, phone, school):
    class_num = message.text.strip()
    if not class_num.isdigit() or not (1 <= int(class_num) <= 11):
        msg = bot.send_message(message.chat.id, 'Пожалуйста, введите класс от 1 до 11:')
        return bot.register_next_step_handler(msg, lambda m: process_class(m, last_name, first_name, middle_name, phone, school))
    conn = get_db()
    conn.execute('INSERT INTO users (user_id, first_name, last_name, middle_name, phone, school, class, register_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                 (message.from_user.id, first_name, last_name, middle_name, phone, school, int(class_num), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, '✅ Регистрация завершена!')
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'мой профиль')
def show_profile(message):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id=?', (message.from_user.id,)).fetchone()
    conn.close()
    if user:
        profile = f"""
📌 Ваш профиль:

👤 ФИО: {user['last_name']} {user['first_name']} {user['middle_name']}
📞 Телефон: {user['phone']}
🏫 Школа: {user['school']}
🎒 Класс: {user['class']}
📅 Дата регистрации: {user['register_date']}
        """
        bot.send_message(message.chat.id, profile)
    else:
        bot.send_message(message.chat.id, 'Вы не зарегистрированы. Нажмите /start.')

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'изменить')
def edit_profile(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('Имя', 'Фамилия', 'Отчество', 'Телефон', 'Школа', 'Класс', 'Назад')
    msg = bot.send_message(message.chat.id, 'Что вы хотите изменить?', reply_markup=markup)
    bot.register_next_step_handler(msg, process_edit_choice)

def process_edit_choice(message):
    field = message.text.lower()
    if field == 'имя':
        msg = bot.send_message(message.chat.id, 'Введите новое имя:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, lambda m: save_edit(m, 'first_name'))
    elif field == 'фамилия':
        msg = bot.send_message(message.chat.id, 'Введите новую фамилию:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, lambda m: save_edit(m, 'last_name'))
    elif field == 'отчество':
        msg = bot.send_message(message.chat.id, 'Введите новое отчество:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, lambda m: save_edit(m, 'middle_name'))
    elif field == 'телефон':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton('Отправить номер телефона', request_contact=True))
        msg = bot.send_message(message.chat.id, 'Отправьте новый номер телефона кнопкой ниже:', reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m: save_edit(m, 'phone'))
    elif field == 'школа':
        msg = bot.send_message(message.chat.id, 'Введите новый номер школы (от 1 до 999):', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, lambda m: save_edit(m, 'school'))
    elif field == 'класс':
        msg = bot.send_message(message.chat.id, 'Введите новый класс (от 1 до 11):', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, lambda m: save_edit(m, 'class'))
    elif field == 'назад':
        show_main_menu(message.chat.id)
    else:
        bot.send_message(message.chat.id, 'Некорректный выбор. Попробуйте снова.')
        edit_profile(message)

def save_edit(message, field):
    user_id = message.from_user.id
    value = None
    if field == 'phone':
        if message.contact and message.contact.phone_number:
            value = message.contact.phone_number
        else:
            value = message.text.strip()
    else:
        value = message.text.strip()
    # Валидация
    if field == 'school':
        if not value.isdigit() or not (1 <= int(value) <= 999):
            msg = bot.send_message(message.chat.id, 'Пожалуйста, введите номер школы цифрами (от 1 до 999):')
            return bot.register_next_step_handler(msg, lambda m: save_edit(m, 'school'))
        value = int(value)
    if field == 'class':
        if not value.isdigit() or not (1 <= int(value) <= 11):
            msg = bot.send_message(message.chat.id, 'Пожалуйста, введите класс от 1 до 11:')
            return bot.register_next_step_handler(msg, lambda m: save_edit(m, 'class'))
        value = int(value)
    conn = get_db()
    conn.execute(f'UPDATE users SET {field}=? WHERE user_id=?', (value, user_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, '✅ Данные успешно обновлены!')
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'удалить')
def delete_profile(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('Да, удалить', 'Нет, отмена')
    msg = bot.send_message(message.chat.id, 'Вы уверены, что хотите удалить профиль? Это действие необратимо.', reply_markup=markup)
    bot.register_next_step_handler(msg, confirm_delete)

def confirm_delete(message):
    if message.text.lower().startswith('да'):
        user_id = message.from_user.id
        conn = get_db()
        conn.execute('DELETE FROM users WHERE user_id=?', (user_id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, 'Ваш профиль удалён. Для новой регистрации нажмите /start.', reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, 'Удаление отменено.')
        show_main_menu(message.chat.id)

if __name__ == '__main__':
    print('Бот запущен...')
    bot.infinity_polling() 