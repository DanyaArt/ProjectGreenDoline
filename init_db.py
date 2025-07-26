import sqlite3
import os

def init_database():
    """Инициализация базы данных с правильной структурой"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Создание таблицы пользователей
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER UNIQUE,
                  first_name TEXT,
                  last_name TEXT,
                  middle_name TEXT,
                  phone TEXT UNIQUE,
                  school TEXT,
                  class TEXT,
                  password_hash TEXT,
                  tg TEXT,
                  register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Создание таблицы сообщений
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  sender TEXT,
                  message TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Создание таблицы результатов тестов
    cursor.execute('''CREATE TABLE IF NOT EXISTS test_results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  nature_score INTEGER,
                  tech_score INTEGER,
                  people_score INTEGER,
                  signs_score INTEGER,
                  art_score INTEGER,
                  dominant_type TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Создание таблицы админов
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  login TEXT UNIQUE,
                  password_hash TEXT)''')
    
    # Добавление админа по умолчанию
    import hashlib
    admin_password_hash = hashlib.sha256('admin123'.encode('utf-8')).hexdigest()
    cursor.execute('''INSERT OR IGNORE INTO admins (login, password_hash) VALUES (?, ?)''', 
                   ('admin', admin_password_hash))
    
    conn.commit()
    conn.close()
    print("База данных успешно инициализирована!")

if __name__ == '__main__':
    init_database() 