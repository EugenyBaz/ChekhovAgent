FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# системные пакеты
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# копируем зависимости
COPY pyproject.toml poetry.lock* /app/

# устанавливаем poetry и зависимости
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --only main

# копируем код
COPY . /app/

# запуск бота
CMD ["python", "-m", "app.main"]