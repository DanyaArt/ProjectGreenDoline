# Профориентационный тест с Telegram ботом

Flask-приложение для проведения профориентационного тестирования с интеграцией Telegram бота.

## Деплой на Render

### 1. Подготовка репозитория

1. Создайте репозиторий на GitHub
2. Загрузите все файлы проекта
3. Убедитесь, что файлы `.gitignore`, `requirements.txt`, `Procfile`, `runtime.txt` присутствуют

### 2. Настройка на Render

#### Web Service (Flask приложение)
1. Зайдите на [render.com](https://render.com)
2. Создайте новый **Web Service**
3. Подключите ваш GitHub репозиторий
4. Настройки:
   - **Name**: `your-project-name-web`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn admin:app --bind 0.0.0.0:$PORT`

#### Background Worker (Telegram бот)
1. Создайте новый **Background Worker**
2. Подключите тот же репозиторий
3. Настройки:
   - **Name**: `your-project-name-worker`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`

### 3. Переменные окружения

Добавьте следующие переменные окружения в настройках каждого сервиса:

```
TELEGRAM_BOT_TOKEN=7709800436:AAG9zdInNqWmU-TW7IuzioHhy_McWnqLw0w
SECRET_KEY=your-super-secret-key-here
SMTP_PASSWORD=jtvknqismtxkamsr
```

### 4. База данных

SQLite файл `users.db` будет создан автоматически при первом запуске.

### 5. Проверка работы

1. Web Service будет доступен по URL вида: `https://your-project-name.onrender.com`
2. Telegram бот должен начать работать автоматически
3. Проверьте логи в Render Dashboard для диагностики

## Локальная разработка

```bash
pip install -r requirements.txt
python admin.py  # Запуск Flask приложения
python bot.py    # Запуск Telegram бота
```

## Структура проекта

- `admin.py` - Flask приложение с админ-панелью
- `bot.py` - Telegram бот
- `templates/` - HTML шаблоны
- `users.db` - SQLite база данных
- `requirements.txt` - Python зависимости
- `Procfile` - Конфигурация для Render 