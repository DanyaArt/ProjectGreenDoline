import telebot
from datetime import datetime
import time
from telebot import types
import sqlite3
import hashlib
import os

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Настройка подключения к базе данных
def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INTEGER UNIQUE,
             first_name TEXT,
             last_name TEXT,
             middle_name TEXT,
             phone TEXT,
             school TEXT,
             class TEXT,
             password_hash TEXT,
             tg TEXT,
             register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    return conn, cursor

# Инициализация базы данных
conn, cursor = init_db()

# Теперь можно инициализировать бота
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '7709800436:AAG9zdInNqWmU-TW7IuzioHhy_McWnqLw0w')
bot = telebot.TeleBot(TOKEN)


# Подключение к базе данных уже создано в init_db()

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Войти"), types.KeyboardButton("Зарегистрироваться"))
    return markup

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    updated = False
    with sqlite3.connect('users.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        if message.from_user.username:
            username = message.from_user.username.lstrip('@')
            cursor.execute(
                "UPDATE users SET user_id=? WHERE tg=? AND (user_id IS NULL OR user_id='')",
                (message.from_user.id, username)
            )
            if cursor.rowcount > 0:
                updated = True
        if not updated and message.contact:
            cursor.execute(
                "UPDATE users SET user_id=? WHERE phone=? AND (user_id IS NULL OR user_id='')",
                (message.from_user.id, message.contact.phone_number)
            )
            if cursor.rowcount > 0:
                updated = True
        conn.commit()
    print(f"[DEBUG] user_id update on /start: username={message.from_user.username}, id={message.from_user.id}, updated={updated}")
    msg = bot.send_message(
        message.chat.id,
        "Выберите действие:",
        reply_markup=get_main_menu()
    )
    bot.register_next_step_handler(msg, process_start_choice)

def process_start_choice(message):
    choice = message.text.strip().lower()
    if "войти" in choice:
        msg = bot.send_message(message.chat.id, "Введите ваш номер телефона для входа:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_login_phone)
    elif "зарегистр" in choice:
        start_registration(message)
    else:
        msg = bot.send_message(message.chat.id, "Пожалуйста, выберите 'Войти' или 'Зарегистрироваться'.")
        bot.register_next_step_handler(msg, process_start_choice)

def process_login_phone(message):
    if message.text == 'Отмена':
        return start(message)
    with sqlite3.connect('users.db', check_same_thread=False) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE phone = ?", (message.text.strip(),))
    user = cursor.fetchone()
    if user:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Отмена'))
        msg = bot.send_message(message.chat.id, "Введите ваш пароль:", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m: process_login_password_by_phone(m, user))
    else:
        bot.send_message(message.chat.id, "Пользователь с таким номером не найден. Зарегистрируйтесь через сайт или бота.")
        start(message)

def process_login_password_by_phone(message, user):
    if message.text == 'Отмена':
        return start(message)
    password = message.text
    password_hash = hash_password(password)
    if password_hash == user['password_hash']:
        # Обновляем user_id для этого пользователя
        with sqlite3.connect('users.db', check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET user_id=? WHERE phone=?", (message.from_user.id, user['phone']))
            conn.commit()
        bot.send_message(message.chat.id, "✅ Вход выполнен успешно!", reply_markup=types.ReplyKeyboardRemove())
        show_menu(message)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Отмена'))
        msg = bot.send_message(message.chat.id, "❌ Неверный пароль. Попробуйте ещё раз:", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m: process_login_password_by_phone(m, user))

# Процесс регистрации
def start_registration(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Отмена'))
    msg = bot.send_message(message.chat.id, "Давайте зарегистрируемся. Введите вашу фамилию:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_last_name)

def process_last_name(message):
    if message.text == 'Отмена':
        return start(message)
    last_name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Отмена'))
    msg = bot.send_message(message.chat.id, "Теперь введите ваше имя:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_first_name(m, last_name))

def process_first_name(message, last_name):
    if message.text == 'Отмена':
        return start(message)
    first_name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Отмена'))
    msg = bot.send_message(message.chat.id, "Введите ваше отчество:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_middle_name(m, last_name, first_name))

def process_middle_name(message, last_name, first_name):
    if message.text == 'Отмена':
        return start(message)
    middle_name = message.text
    
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    reg_button = types.KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)
    keyboard.add(reg_button)
    keyboard.add(types.KeyboardButton('Отмена'))
    
    msg = bot.send_message(message.chat.id, "Отправьте ваш номер телефона:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, lambda m: process_phone(m, last_name, first_name, middle_name))

def process_phone(message, last_name, first_name, middle_name):
    if message.text == 'Отмена':
        return start(message)
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text
    # Проверка уникальности телефона
    with sqlite3.connect('users.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE phone = ?", (phone,))
        exists = cursor.fetchone()
    if exists:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Отмена'))
        msg = bot.send_message(message.chat.id, "Пользователь с таким номером уже существует. Пожалуйста, используйте другой номер или войдите в свой аккаунт.", reply_markup=markup)
        return bot.register_next_step_handler(msg, lambda m: process_phone(m, last_name, first_name, middle_name))
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Отмена'))
    msg = bot.send_message(message.chat.id, "Введите номер вашей школы:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_school(m, last_name, first_name, middle_name, phone))

def process_school(message, last_name, first_name, middle_name, phone):
    if message.text == 'Отмена':
        return start(message)
    school = message.text.strip()
    # Проверка: школа должна быть числом от 1 до 9999
    if not school.isdigit() or not (1 <= int(school) <= 9999):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Отмена'))
        msg = bot.send_message(message.chat.id, "Пожалуйста, введите номер школы цифрами (от 1 до 9999):", reply_markup=markup)
        return bot.register_next_step_handler(msg, lambda m: process_school(m, last_name, first_name, middle_name, phone))
    # Proceed to class selection
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [types.KeyboardButton(str(i)) for i in range(1, 12)]
    markup.add(*buttons)
    markup.add(types.KeyboardButton('Отмена'))
    msg = bot.send_message(message.chat.id, "Выберите ваш класс:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_class(m, last_name, first_name, middle_name, phone, school))


def process_class(message, last_name, first_name, middle_name, phone, school):
    if message.text == 'Отмена':
        return start(message)
    class_num = message.text.strip()
    # Проверка: класс только от 1 до 11
    if not class_num.isdigit() or not (1 <= int(class_num) <= 11):
        markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        buttons = [types.KeyboardButton(str(i)) for i in range(1, 12)]
        markup.add(*buttons)
        markup.add(types.KeyboardButton('Отмена'))
        msg = bot.send_message(message.chat.id, "Пожалуйста, выберите класс от 1 до 11:", reply_markup=markup)
        return bot.register_next_step_handler(msg, lambda m: process_class(m, last_name, first_name, middle_name, phone, school))
    # После класса — запросить пароль
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Отмена'))
    msg = bot.send_message(message.chat.id, "Придумайте пароль для входа:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_password1(m, last_name, first_name, middle_name, phone, school, class_num))

def process_password1(message, last_name, first_name, middle_name, phone, school, class_num):
    if message.text == 'Отмена':
        return start(message)
    password1 = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Отмена'))
    msg = bot.send_message(message.chat.id, "Повторите пароль:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_password2(m, last_name, first_name, middle_name, phone, school, class_num, password1))

def process_password2(message, last_name, first_name, middle_name, phone, school, class_num, password1):
    if message.text == 'Отмена':
        return start(message)
    password2 = message.text
    if password1 != password2:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Отмена'))
        msg = bot.send_message(message.chat.id, "Пароли не совпадают! Попробуйте снова. Придумайте пароль:", reply_markup=markup)
        return bot.register_next_step_handler(msg, lambda m: process_password1(m, last_name, first_name, middle_name, phone, school, class_num))
    password_hash = hash_password(password1)
    try:
        print('Попытка вставки пользователя в БД...')
        with sqlite3.connect('users.db', check_same_thread=False) as conn:
            cursor = conn.cursor()
            
            # Проверим, существует ли таблица
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                print("ОШИБКА: Таблица users не существует!")
                # Создадим таблицу
                cursor.execute('''CREATE TABLE users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER UNIQUE,
                      first_name TEXT,
                      last_name TEXT,
                      middle_name TEXT,
                      phone TEXT,
                      school TEXT,
                      class TEXT,
                      password_hash TEXT,
                      tg TEXT,
                      register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                conn.commit()
                print("Таблица users создана!")
            
            print(f"DEBUG: Регистрация пользователя - телефон: {phone}, password_hash: {password_hash}")
            print(f"DEBUG: Данные для вставки: user_id={message.from_user.id}, first_name={first_name}, last_name={last_name}, middle_name={middle_name}, phone={phone}, school={school}, class={class_num}")
            
            cursor.execute(
                "INSERT INTO users (user_id, first_name, last_name, middle_name, phone, school, class, register_date, password_hash) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)",
                (message.from_user.id, first_name, last_name, middle_name, phone, school, class_num, password_hash)
            )
            conn.commit()
            print('Пользователь успешно добавлен!')
            
            # Проверим, что пользователь действительно добавлен
            cursor.execute("SELECT * FROM users WHERE user_id=?", (message.from_user.id,))
            added_user = cursor.fetchone()
            if added_user:
                print(f"Проверка: пользователь найден в БД с ID: {added_user[0]}")
            else:
                print("ОШИБКА: пользователь не найден в БД после вставки!")
            
            bot.send_message(message.chat.id, "✅ Регистрация завершена!", reply_markup=types.ReplyKeyboardRemove())
            show_menu(message)
    except Exception as e:
        import traceback
        print('Ошибка при регистрации:', traceback.format_exc())
        bot.send_message(message.chat.id, f"Ошибка при регистрации: {e}")

# Главное меню
def show_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_profile = types.KeyboardButton("👤 Мой профиль")
    btn_edit = types.KeyboardButton("✏️ Изменить данные")
    btn_delete = types.KeyboardButton("🗑️ Удалить профиль")
    markup.add(btn_profile, btn_edit, btn_delete)
    
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=markup)

# Просмотр профиля
@bot.message_handler(func=lambda message: message.text == "👤 Мой профиль")
def show_profile(message):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if user:
        # Форматирование даты регистрации
        register_date = user[7]
        if register_date and str(register_date).lower() != 'none':
            try:
                if isinstance(register_date, str):
                    dt = datetime.strptime(register_date, "%Y-%m-%d %H:%M:%S")
                else:
                    dt = datetime.fromtimestamp(time.mktime(register_date))
                register_date = dt.strftime("%d.%m.%Y %H:%M")
            except:
                register_date = "неизвестно"
        else:
            register_date = "не указана"
        # Обработка школы
        school = user[5]
        if not school or str(school).lower() == 'none':
            school = "не указана"
        # ФИО: фамилия, имя, отчество
        profile_text = f"""
📌 <b>Ваш профиль</b>:

👤 <b>ФИО:</b> {user[3]} {user[2]} {user[8]}
📞 <b>Телефон:</b> {user[4]}
🏫 <b>Школа:</b> {school}
🎒 <b>Класс:</b> {user[6]}
📅 <b>Дата регистрации:</b> {register_date}
        """
        bot.send_message(message.chat.id, profile_text, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "Профиль не найден. Нажмите /start для регистрации")

# Редактирование профиля
@bot.message_handler(func=lambda message: message.text == "✏️ Изменить данные")
def edit_profile(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    btn1 = types.KeyboardButton("Изменить имя")
    btn2 = types.KeyboardButton("Изменить телефон")
    btn3 = types.KeyboardButton("Изменить школу")
    btn4 = types.KeyboardButton("Изменить класс")
    btn_back = types.KeyboardButton("↩️ Назад")
    markup.add(btn1, btn2, btn3, btn4, btn_back)
    
    bot.send_message(message.chat.id, "Что вы хотите изменить?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text.startswith("Изменить"))
def select_field_to_edit(message):
    field = message.text.replace("Изменить ", "").lower()
    
    if field == "телефон":
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        reg_button = types.KeyboardButton(text="📱 Отправить номер", request_contact=True)
        keyboard.add(reg_button)
        msg = bot.send_message(message.chat.id, "Отправьте новый номер телефона:", reply_markup=keyboard)
    else:
        msg = bot.send_message(message.chat.id, f"Введите новое значение для {field}:",
                             reply_markup=types.ReplyKeyboardRemove())
    
    bot.register_next_step_handler(msg, lambda m: update_profile(m, field))

def update_profile(message, field):
    try:
        new_value = message.contact.phone_number if field == "телефон" and message.contact else message.text
        user_id = message.from_user.id
        db_field = {
            "имя": "first_name",
            "отчество": "middle_name",
            "телефон": "phone",
            "школу": "school",
            "класс": "class"
        }.get(field)
        # Проверки для школы и класса
        if db_field == "school":
            if not new_value.isdigit() or not (1 <= int(new_value) <= 9999):
                msg = bot.send_message(message.chat.id, "Пожалуйста, введите номер школы цифрами (от 1 до 9999):")
                return bot.register_next_step_handler(msg, lambda m: update_profile(m, field))
        if db_field == "class":
            if not new_value.isdigit() or not (1 <= int(new_value) <= 11):
                msg = bot.send_message(message.chat.id, "Пожалуйста, выберите класс от 1 до 11:")
                return bot.register_next_step_handler(msg, lambda m: update_profile(m, field))
        if db_field:
            cursor.execute(f"UPDATE users SET {db_field} = ? WHERE user_id = ?", (new_value, user_id))
            conn.commit()
            bot.send_message(message.chat.id, f"✅ {field.capitalize()} успешно изменен!")
            show_menu(message)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при обновлении: {str(e)}")

# Удаление профиля
@bot.message_handler(func=lambda message: message.text == "🗑️ Удалить профиль")
def confirm_delete(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    btn_yes = types.KeyboardButton("✅ Да, удалить")
    btn_no = types.KeyboardButton("❌ Нет, отменить")
    markup.add(btn_yes, btn_no)
    
    bot.send_message(message.chat.id, "Вы уверены, что хотите удалить свой профиль? Все данные будут безвозвратно удалены.", 
                    reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "✅ Да, удалить")
def delete_profile(message):
    try:
        cursor.execute("DELETE FROM users WHERE user_id = ?", (message.from_user.id,))
        conn.commit()
        bot.send_message(message.chat.id, "Ваш профиль удален. Для новой регистрации нажмите /start", 
                        reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при удалении: {str(e)}")

# Навигация назад
@bot.message_handler(func=lambda message: message.text in ["↩️ Назад", "❌ Нет, отменить"])
def back_to_menu(message):
    show_menu(message)

@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and m.text not in ["Войти", "Зарегистрироваться", "👤 Мой профиль", "✏️ Изменить данные", "🗑️ Удалить профиль", "↩️ Назад", "❌ Нет, отменить", "✅ Да, удалить"])
def save_user_message(message):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (user_id, sender, message) VALUES (?, ?, ?)', (message.from_user.id, 'user', message.text))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f'Ошибка при сохранении сообщения пользователя: {e}')

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()