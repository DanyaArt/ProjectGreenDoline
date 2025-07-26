import sqlite3

def check_database():
    """Проверка содержимого базы данных"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Проверим структуру таблицы
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Структура таблицы users: {columns}")
        
        # Посчитаем пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        print(f"Всего пользователей: {total}")
        
        # Покажем всех пользователей
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        for i, user in enumerate(users):
            print(f"\nПользователь {i+1}:")
            for j, column in enumerate(columns):
                print(f"  {column}: {user[j]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Ошибка при проверке БД: {e}")

if __name__ == '__main__':
    check_database() 