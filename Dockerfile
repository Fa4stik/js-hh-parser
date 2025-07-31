FROM python:3.10-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY src/ ./src/
COPY start_api.py .

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 apiuser && chown -R apiuser:apiuser /app
USER apiuser

# Открываем порт
EXPOSE 8000

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV TRANSFORMERS_CACHE=/app/.cache

# Команда запуска
CMD ["python", "-m", "uvicorn", "src.ai.qwen:app", "--host", "0.0.0.0", "--port", "8000"] 