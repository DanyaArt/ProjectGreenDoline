web: python init_db.py && gunicorn admin:app --bind 0.0.0.0:$PORT
worker: python init_db.py && python bot.py 