# МНПЦЛИ Энтеробиоз - Система автоматического распознавания

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

## Описание

Промышленная система автоматического распознавания энтеробиоза по микроскопическим изображениям.

## Быстрый старт

### Запуск через Docker (рекомендуется)

```bash
# Сборка и запуск одной командой
docker-compose up --build
```

Приложение будет доступно по адресу: http://localhost:8001

### Локальный запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск приложения
python main.py
```

## Учётные данные

| Логин   | Пароль      | Роль           |
|---------|-------------|----------------|
| admin   | admin       | Администратор  |
| doctor  | doctor123   | Врач           |
| lab     | lab2024     | Лаборант       |

## Структура проекта

```
/workspace/
├── api.py              # FastAPI приложение
├── main.py             # Точка входа
├── model.py            # ML модель
├── processing.py       # Обработка изображений
├── config.py           # Конфигурация
├── requirements.txt    # Зависимости Python
├── Dockerfile          # Docker образ
├── docker-compose.yml  # Docker Compose
├── static/
│   └── index.html      # Веб-интерфейс
└── scans/              # Директория сканов
```

## API Endpoints

| Метод | Endpoint        | Описание                    | Авторизация |
|-------|-----------------|-----------------------------|-------------|
| POST  | /api/login      | Вход в систему              | Нет         |
| GET   | /api/slides     | Получить список слайдов     | Да          |
| GET   | /api/stats      | Статистика обработки        | Да          |
| POST  | /api/review     | Обновить статус проверки    | Да          |
| GET   | /thumbnails/... | Миниатюры изображений       | Да          |

## Переменные окружения

| Переменная      | Значение по умолчанию | Описание              |
|-----------------|----------------------|-----------------------|
| HOST            | 0.0.0.0              | Хост для сервера      |
| PORT            | 8001                 | Порт для сервера      |
| SCANS_DIR       | scans                | Директория сканов     |

## Производство

Для развёртывания в промышленной среде:

1. Настройте переменные окружения
2. Используйте reverse proxy (nginx)
3. Настройте HTTPS
4. Подключите базу данных для хранения пользователей
5. Настройте логирование и мониторинг

## Лицензия

© 2026 МНПЦЛИ. Все права защищены.
