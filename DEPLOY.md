# Инструкция по деплою на Render

## Шаг 1: Подготовка GitHub репозитория

1. Создайте новый репозиторий на GitHub
2. Загрузите все файлы проекта в репозиторий
3. Убедитесь, что файл `users.db` НЕ загружен (он в .gitignore)

## Шаг 2: Регистрация на Render

1. Зайдите на https://render.com
2. Зарегистрируйтесь через GitHub
3. Подключите ваш репозиторий

## Шаг 3: Создание Web Service

1. Нажмите "New +" → "Web Service"
2. Выберите ваш репозиторий
3. Настройки:
   - **Name**: `your-project-web`
   - **Environment**: `Python 3`
   - **Region**: выберите ближайший
   - **Branch**: `main` (или `master`)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python init_db.py && gunicorn admin:app --bind 0.0.0.0:$PORT`

## Шаг 4: Создание Background Worker

1. Нажмите "New +" → "Background Worker"
2. Выберите тот же репозиторий
3. Настройки:
   - **Name**: `your-project-worker`
   - **Environment**: `Python 3`
   - **Region**: тот же, что и для Web Service
   - **Branch**: `main` (или `master`)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python init_db.py && python bot.py`

## Шаг 5: Настройка переменных окружения

Для ОБОИХ сервисов добавьте переменные окружения:

### Web Service переменные:
```
TELEGRAM_BOT_TOKEN=7709800436:AAG9zdInNqWmU-TW7IuzioHhy_McWnqLw0w
SECRET_KEY=your-super-secret-key-2024-klimov
SMTP_PASSWORD=jtvknqismtxkamsr
```

### Background Worker переменные:
```
TELEGRAM_BOT_TOKEN=7709800436:AAG9zdInNqWmU-TW7IuzioHhy_McWnqLw0w
```

## Шаг 6: Запуск деплоя

1. Нажмите "Create Web Service" и "Create Background Worker"
2. Дождитесь завершения деплоя (может занять 5-10 минут)
3. Проверьте логи на наличие ошибок

## Шаг 7: Проверка работы

1. **Web Service**: откройте URL вида `https://your-project-web.onrender.com`
2. **Telegram бот**: отправьте `/start` вашему боту
3. **Админ-панель**: `https://your-project-web.onrender.com/admin`
   - Логин: `admin`
   - Пароль: `admin123`

## Возможные проблемы

### Ошибка "No module named 'sqlite3'"
- SQLite встроен в Python, но если ошибка - добавьте в requirements.txt:
  ```
  pysqlite3-binary
  ```

### Бот не отвечает
- Проверьте логи Background Worker
- Убедитесь, что TELEGRAM_BOT_TOKEN правильный
- Проверьте, что бот не заблокирован

### Ошибки с базой данных
- База данных создается автоматически при первом запуске
- Если проблемы - проверьте логи инициализации

## Полезные команды

### Просмотр логов:
- В Render Dashboard → ваш сервис → Logs

### Перезапуск сервиса:
- В Render Dashboard → ваш сервис → Manual Deploy

### Обновление кода:
- Просто загрузите изменения в GitHub
- Render автоматически пересоберет проект 