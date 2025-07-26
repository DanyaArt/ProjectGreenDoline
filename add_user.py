import sqlite3
from datetime import datetime
import hashlib

# Введите данные пользователя ниже
user_id = 123456789  # Telegram user_id
first_name = 'Иван'
last_name = 'Иванов'
middle_name = 'Иванович'
phone = '+79990001122'
school = '50'
user_class = '9'
register_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("Порядок столбцов в таблице users:")
for col in columns:
    print(f"{col[0]}: {col[1]}")
conn.close()
print('Пользователь успешно добавлен!') 