import sqlite3
import os

def sync_database():
    """Синхронизация базы данных"""
    try:
        # Подключение к локальной БД
        local_conn = sqlite3.connect('users.db')
        local_cursor = local_conn.cursor()
        
        # Получаем всех пользователей из локальной БД
        local_cursor.execute("SELECT * FROM users")
        local_users = local_cursor.fetchall()
        
        print(f"Найдено {len(local_users)} пользователей в локальной БД")
        
        # Подключение к серверной БД (если есть)
        if os.path.exists('users_server.db'):
            server_conn = sqlite3.connect('users_server.db')
            server_cursor = server_conn.cursor()
            
            # Создаем таблицу если её нет
            server_cursor.execute('''CREATE TABLE IF NOT EXISTS users
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
            
            # Копируем пользователей
            for user in local_users:
                try:
                    server_cursor.execute('''
                        INSERT OR IGNORE INTO users 
                        (user_id, first_name, last_name, middle_name, phone, school, class, password_hash, tg, register_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', user[1:])  # Пропускаем id
                except Exception as e:
                    print(f"Ошибка при копировании пользователя {user[1]}: {e}")
            
            server_conn.commit()
            server_conn.close()
            print("Пользователи скопированы в users_server.db")
        
        local_conn.close()
        
        # Показываем содержимое локальной БД
        print("\nСодержимое локальной БД:")
        local_conn = sqlite3.connect('users.db')
        local_cursor = local_conn.cursor()
        local_cursor.execute("SELECT user_id, first_name, last_name, phone FROM users")
        users = local_cursor.fetchall()
        for user in users:
            print(f"  Telegram ID: {user[0]}, ФИО: {user[2]} {user[1]}, Телефон: {user[3]}")
        local_conn.close()
        
    except Exception as e:
        print(f"Ошибка при синхронизации: {e}")

if __name__ == '__main__':
    sync_database() 