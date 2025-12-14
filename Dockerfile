# Используем официальный Python образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только файлы с зависимостями
COPY pyproject.toml poetry.lock* /app/

# Устанавливаем Poetry и зависимости
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root

# Копируем остальной код проекта
COPY . /app/

# Экспортируем переменные окружения
# ENV TELEGRAM_BOT_TOKEN=...
# ENV DEEPSEEK_API_KEY=...

# Команда запуска бота
CMD ["python", "-m", "app.main"]