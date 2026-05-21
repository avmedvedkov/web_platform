# МНПЦЛИ Энтеробиоз - Промышленное решение
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание директорий для данных
RUN mkdir -p scans logs

# Переменная окружения
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8001

# Порт приложения
EXPOSE 8001

# Команда запуска
CMD ["python", "main.py"]
