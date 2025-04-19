FROM python:3.11-slim

WORKDIR /app

# Установим зависимости
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Копируем весь код
COPY ./app /app

# Запускаем бота
CMD ["python", "bot.py"]
