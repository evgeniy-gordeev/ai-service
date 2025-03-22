FROM python:3.9-slim as builder

WORKDIR /app

# Установка только необходимых системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование только файла requirements
COPY requirements.txt .

# Установка зависимостей с оптимизацией
RUN pip install --no-cache-dir -U pip setuptools wheel && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.9-slim as runtime

WORKDIR /app

# Копирование виртуального окружения из предыдущего этапа
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем только необходимые файлы приложения
COPY src/ /app/src/

# Открываем порт
EXPOSE 8001

# Запуск приложения через uvicorn с настройками производительности
CMD ["uvicorn", "src.tenders_api:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]