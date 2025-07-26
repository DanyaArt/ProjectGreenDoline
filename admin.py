from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, make_response
import sqlite3
from datetime import datetime
import hashlib
import telebot
import os
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '7709800436:AAG9zdInNqWmU-TW7IuzioHhy_McWnqLw0w')
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
import smtplib
from email.message import EmailMessage
import base64


def get_test_stats_sqlite(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), COALESCE((SELECT dominant_type FROM test_results WHERE user_id=? ORDER BY id DESC LIMIT 1), '') FROM test_results WHERE user_id=?", (user_id, user_id))
    count, dominant_type = cursor.fetchone()
    conn.close()
    return count, dominant_type

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-2024-klimov')

# Подключение к базе данных
def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # Для доступа к полям по имени
    return conn

# Главная страница админки
@app.route('/')
def index_page():
    return "Сайт работает! <a href='/admin'>Админ-панель</a>"

@app.route('/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    if user is None:
        conn.close()
        return "Пользователь не найден", 404
    error = None
    if request.method == 'POST' and 'last_name' in request.form:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        school = request.form['school']
        user_class = request.form['class']
        cursor.execute('''
            UPDATE users SET first_name=?, last_name=?, phone=?, school=?, class=? WHERE id=?
        ''', (first_name, last_name, phone, school, user_class, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_index'))
    # Получить историю сообщений
    if user['user_id']:
        messages = cursor.execute('SELECT sender, message, timestamp FROM messages WHERE user_id=? ORDER BY timestamp DESC', (user['user_id'],)).fetchall()
    else:
        messages = cursor.execute('''
            SELECT m.sender, m.message, m.timestamp FROM messages m
            JOIN users u ON m.user_id = u.user_id
            WHERE u.first_name=? AND u.last_name=?
            ORDER BY m.timestamp DESC
        ''', (user['first_name'], user['last_name'])).fetchall()
    # Получить историю попыток теста с процентами и профессиями
    test_history = cursor.execute('SELECT timestamp, dominant_type, nature_score, tech_score, people_score, signs_score, art_score FROM test_results WHERE user_id=? ORDER BY timestamp DESC', (user['id'],)).fetchall()
    test_attempts = len(test_history)
    conn.close()
    # Карта профессий по типу
    profession_map = {
        'Человек-природа': ['Агроном', 'Ветеринар', 'Эколог', 'Ландшафтный дизайнер', 'Зоотехник', 'Биолог'],
        'Человек-техника': ['Инженер', 'Механик', 'Программист', 'Электрик', 'Строитель', 'Автомеханик'],
        'Человек-человек': ['Учитель', 'Врач', 'Психолог', 'Менеджер', 'HR-специалист', 'Социальный работник'],
        'Человек-знаковая система': ['Бухгалтер', 'Финансовый аналитик', 'Переводчик', 'Архивариус', 'Экономист', 'Математик'],
        'Человек-художественный образ': ['Дизайнер', 'Художник', 'Музыкант', 'Актер', 'Писатель', 'Архитектор']
    }
    return render_template('edit_user.html', user=user, error=error, messages=messages, test_history=test_history, profession_map=profession_map, test_attempts=test_attempts)

@app.route('/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = get_db()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_index'))

@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.form['message']
    conn = get_db()
    cursor = conn.cursor()
    user_ids = [row[0] for row in cursor.execute('SELECT user_id FROM users').fetchall() if row[0]]
    conn.close()
    sent = 0
    for user_id in user_ids:
        try:
            bot.send_message(user_id, message)
            sent += 1
        except Exception as e:
            print(f'Ошибка отправки пользователю {user_id}: {e}')
    print(f'Рассылка завершена. Сообщение отправлено {sent} пользователям.')
    return redirect(url_for('admin_index'))

@app.route('/send_personal_message/<int:user_id>', methods=['POST'])
def send_personal_message(user_id):
    message = request.form['personal_message']
    conn = get_db()
    cursor = conn.cursor()
    tg_user_id = cursor.execute('SELECT user_id FROM users WHERE id=?', (user_id,)).fetchone()
    if not tg_user_id or not tg_user_id[0]:
        flash('У пользователя не найден Telegram ID. Он должен написать боту /start.', 'danger')
        conn.close()
        return redirect(url_for('edit_user', user_id=user_id))
        try:
            bot.send_message(tg_user_id[0], message)
            cursor.execute('INSERT INTO messages (user_id, sender, message) VALUES (?, ?, ?)', (tg_user_id[0], 'admin', message))
            conn.commit()
            flash('Сообщение отправлено пользователю в Telegram.', 'success')
        except Exception as e:
            flash(f'Ошибка отправки: {e}', 'danger')
    conn.close()
    return redirect(url_for('edit_user', user_id=user_id))

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    print(f"DEBUG: Попытка входа - телефон: {phone}")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверим, есть ли пользователь с таким телефоном
    user_by_phone = cursor.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
    if user_by_phone:
        print(f"DEBUG: Пользователь найден по телефону, password_hash: {user_by_phone['password_hash']}")
        print(f"DEBUG: Введенный password_hash: {password_hash}")
    
    user = cursor.execute(
        "SELECT * FROM users WHERE phone=? AND password_hash=?",
        (phone, password_hash)
    ).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        print(f"DEBUG: Вход успешен для пользователя ID: {user['id']}")
        return jsonify({'success': True, 'redirect': '/test.html'})
    else:
        print(f"DEBUG: Вход не удался - пользователь не найден или неправильный пароль")
        return jsonify({'success': False, 'error': 'Неправильный логин или пароль'})

@app.route('/test.html')
def test_page():
    user_id = session.get('user_id')
    return render_template('test.html', user_id=user_id)

@app.route('/admin')
def admin_index():
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверим структуру таблицы
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"DEBUG: Структура таблицы users: {columns}")
    
    if 'register_date' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        conn.commit()
    
    # Получим всех пользователей с отладочной информацией
    users = conn.execute('''
    SELECT id, user_id, 
           first_name, last_name, middle_name, 
           last_name || ' ' || first_name || ' ' || middle_name as full_name, 
           phone, school, class, tg,
           strftime('%Y-%m-%d %H:%M:%S', register_date) as register_date 
    FROM users 
    ORDER BY register_date DESC
    ''').fetchall()
    
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    print(f"DEBUG: Всего пользователей в БД: {total_users}")
    
    # Выведем всех пользователей для отладки
    for user in users:
        print(f"DEBUG: Пользователь - ID: {user['id']}, Telegram ID: {user['user_id']}, ФИО: {user['full_name']}, Телефон: {user['phone']}")
    
    conn.close()
    return render_template('admin.html', 
                         users=users, 
                         total_users=total_users,
                         current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

ADMIN_LOGIN = 'admin'
ADMIN_PASSWORD_HASH = hashlib.sha256('admin123'.encode('utf-8')).hexdigest()

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    # Сохраняем return_url при GET-запросе
    if request.method == 'GET':
        return_url = request.args.get('next') or request.referrer
        if return_url and '/admin' not in return_url and '/admin_login' not in return_url:
            session['admin_return_url'] = return_url
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        conn = get_db()
        cursor = conn.cursor()
        admin = cursor.execute('SELECT * FROM admins WHERE login=? AND password_hash=?', (login, password)).fetchone()
        conn.close()
        if admin:
            session['is_admin'] = True
            return redirect(url_for('admin_index'))
        else:
            error = 'Неверный логин или пароль'
    return render_template('admin_login.html', error=error)

@app.route('/admin_logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Вы вышли из админ-панели.')
    return_url = session.pop('admin_return_url', None)
    if return_url:
        return redirect(return_url)
    return redirect(url_for('test_page'))

@app.route('/sync_user_ids')
def sync_user_ids():
    conn = get_db()
    cursor = conn.cursor()
    # Найти user_id из messages, которых нет в users
    cursor.execute('SELECT DISTINCT user_id FROM messages WHERE user_id IS NOT NULL')
    message_user_ids = [row[0] for row in cursor.fetchall()]
    updated = 0
    for msg_user_id in message_user_ids:
        # Найти пользователя с пустым user_id, но с совпадающим именем/фамилией (или просто с пустым user_id)
        user = cursor.execute('SELECT id FROM users WHERE user_id IS NULL LIMIT 1').fetchone()
        if user:
            cursor.execute('UPDATE users SET user_id=? WHERE id=?', (msg_user_id, user['id']))
            updated += 1
    conn.commit()
    conn.close()
    return f'Синхронизировано {updated} пользователей. <a href=\"/admin\">Назад в админку</a>'

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    password = data.get('password')
    user_class = data.get('user_class')
    school = data.get('school')
    tg = data.get('tg')
    if tg:
        tg = tg.lstrip('@')
    else:
        tg = ''
    # Разделить ФИО на части (если нужно)
    fio = name.split()
    last_name = fio[0] if len(fio) > 0 else ''
    first_name = fio[1] if len(fio) > 1 else ''
    middle_name = fio[2] if len(fio) > 2 else ''

    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    conn = get_db()
    cursor = conn.cursor()
    # Проверка на существование пользователя с таким телефоном
    exists = cursor.execute('SELECT 1 FROM users WHERE phone=?', (phone,)).fetchone()
    if exists:
        conn.close()
        return jsonify({'success': False, 'error': 'Пользователь с таким телефоном уже существует'})
    # Проверяем, есть ли поле tg в таблице users
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'tg' not in columns:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN tg TEXT")
            conn.commit()
        except Exception:
            pass  # Если поле уже есть или другая ошибка, игнорируем
    cursor.execute(
        "INSERT INTO users (first_name, last_name, middle_name, phone, school, class, password_hash, tg) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (first_name, last_name, middle_name, phone, school, user_class, password_hash, tg)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/save-test-result', methods=['POST'])
def save_test_result():
    data = request.get_json()
    user_id = data.get('user_id')
    nature = data.get('nature')
    tech = data.get('tech')
    people = data.get('people')
    signs = data.get('signs')
    art = data.get('art')
    scores = {
        'Человек-природа': nature,
        'Человек-техника': tech,
        'Человек-человек': people,
        'Человек-знаковая система': signs,
        'Человек-художественный образ': art
    }
    dominant_type = max(scores, key=scores.get)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO test_results (user_id, nature_score, tech_score, people_score, signs_score, art_score, dominant_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, nature, tech, people, signs, art, dominant_type)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/send-test-result-email', methods=['POST'])
def send_test_result_email():
    data = request.get_json()
    email = data.get('email')
    text = data.get('text')
    chart_img = data.get('chart_img')  # base64 dataURL
    if not email or not text:
        return jsonify({'success': False, 'error': 'Нет email или текста'}), 400
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Результаты профориентационного теста'
        msg['From'] = 'Artdan1122@yandex.ru'
        msg['To'] = email
        msg.set_content(text)
        # Если есть картинка диаграммы — добавляем как вложение
        if chart_img and chart_img.startswith('data:image/png;base64,'):
            img_data = base64.b64decode(chart_img.split(',')[1])
            msg.add_attachment(img_data, maintype='image', subtype='png', filename='diagram.png')
        # Отправка через SMTP Яндекс
        with smtplib.SMTP_SSL('smtp.yandex.ru', 465) as smtp:
            smtp.login('Artdan1122@yandex.ru', os.environ.get('SMTP_PASSWORD', 'jtvknqismtxkamsr'))
            smtp.send_message(msg)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)