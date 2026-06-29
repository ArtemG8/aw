# Использовать официальный образ Python
FROM python:3.11-slim

# Настройка окружения, чтобы Python не создавал файлы кэша .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Принудительно задаем корень проекта для импортов
ENV PYTHONPATH=/app

# Устанавливаем рабочую папку в контейнере
WORKDIR /app

# Сначала копируем ТОЛЬКО файл зависимостей (для ускорения сборки кэша Docker)
COPY requirements.txt .

# Обновляем pip и устанавливаем все библиотеки из requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта в контейнер
COPY . .

# Команда запуска бота напрямую
CMD ["python", "main.py"]
