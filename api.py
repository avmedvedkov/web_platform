"""
Модуль FastAPI-приложения
Определяет маршруты и запускает сервер (без Pydantic)
"""

import io
import secrets
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query, Request, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from PIL import Image

from config import SCANS_DIR

# Глобальное состояние приложения
slides_data: Dict[str, Any] = {}
processing_stats: Dict[str, Any] = {}
thumbnail_cache: Dict[str, bytes] = {}

app = FastAPI(title="МНПЦЛИ Энтеробиоз API")

# Простая система аутентификации
security = HTTPBasic()

# Заглушка пользователей (в продакшене использовать БД)
USERS_DB = {
    "admin": "admin",
    "doctor": "doctor123",
    "lab": "lab2024"
}

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Проверка логина и пароля"""
    correct_password = USERS_DB.get(credentials.username)
    if not correct_password or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def optional_auth(request: Request):
    """Опциональная авторизация для публичных эндпоинтов"""
    # Для статики и favicon авторизация не требуется
    return True


# ----- Вспомогательная валидация вместо Pydantic -----
def validate_review_update(body: dict) -> dict:
    """
    Проверяет наличие и типы полей для обновления статуса проверки

    Ожидаемые ключи:
      - slideId  : str
      - index    : int
      - status   : str, одно из ('confirmed', 'rejected')

    Возвращает словарь с этими значениями
    Выбрасывает HTTPException при ошибке валидации
    """
    slide_id = body.get("slideId")
    index = body.get("index")
    status = body.get("status")

    if not isinstance(slide_id, str):
        raise HTTPException(status_code=422, detail="slideId должен быть строкой")
    if not isinstance(index, int):
        raise HTTPException(status_code=422, detail="index должен быть целым числом")
    if status not in ("confirmed", "rejected"):
        raise HTTPException(
            status_code=422,
            detail="status должен быть 'confirmed' или 'rejected'"
        )
    return {"slideId": slide_id, "index": index, "status": status}


# ---------- Маршруты ----------
@app.get("/")
async def index():
    """Главная страница – SPA интерфейс"""
    return FileResponse("static/index.html")


@app.get("/favicon.svg")
async def favicon():
    """Возвращает favicon в формате SVG"""
    icon_path = Path("static/favicon.svg")
    if icon_path.exists():
        return FileResponse(icon_path)
    raise HTTPException(status_code=404)


@app.post("/api/login")
async def login(request: Request):
    """
    Эндпоинт для входа пользователя
    Принимает JSON: {"username": "...", "password": "..."}
    Возвращает: {"success": true, "username": "..."} или ошибку 401
    """
    body = await request.json()
    username = body.get("username")
    password = body.get("password")
    
    if not username or not password:
        raise HTTPException(status_code=422, detail="Логин и пароль обязательны")
    
    correct_password = USERS_DB.get(username)
    if not correct_password or password != correct_password:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    return {"success": True, "username": username}


@app.get("/api/slides", dependencies=[Depends(get_current_user)])
async def get_slides():
    """Получить данные по всем слайдам (требуется авторизация)"""
    return slides_data


@app.get("/api/stats", dependencies=[Depends(get_current_user)])
async def get_stats():
    """Статистика обработки (требуется авторизация)"""
    return processing_stats


@app.get("/thumbnails/{slide}/{filename}")
async def thumbnail(
    slide: str, filename: str, size: int = Query(120)
):
    """Сгенерировать и закешировать миниатюру (без авторизации для загрузки изображений)"""
    cache_key = f"{slide}/{filename}/{size}"
    if cache_key in thumbnail_cache:
        return StreamingResponse(
            io.BytesIO(thumbnail_cache[cache_key]),
            media_type="image/jpeg"
        )

    original_path = SCANS_DIR / slide / filename
    if not original_path.exists():
        raise HTTPException(status_code=404)

    try:
        img = Image.open(original_path).convert("RGB")
        img.thumbnail((size, size), Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)

        if len(thumbnail_cache) >= 500:
            thumbnail_cache.pop(next(iter(thumbnail_cache)))
        thumbnail_cache[cache_key] = buffer.read()
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="image/jpeg")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/review", dependencies=[Depends(get_current_user)])
async def update_review(request: Request):
    """
    Обновить статус проверки конкретного скана (требуется авторизация)
    Принимает JSON: {"slideId": "...", "index": 0, "status": "confirmed"}
    """
    body = await request.json()
    data = validate_review_update(body)

    slide = slides_data.get(data["slideId"])
    if not slide:
        raise HTTPException(status_code=404, detail="Слайд не найден")

    scans = slide["scans"]
    if data["index"] >= len(scans):
        raise HTTPException(status_code=404, detail="Скан не найден")

    scan = scans[data["index"]]
    scan["reviewStatus"] = data["status"]

    # Пересчёт статистики слайда
    pos = sum(1 for s in scans if s["scanType"] == "positive")
    neg = sum(1 for s in scans if s["scanType"] == "negative")
    err = sum(1 for s in scans if s["scanType"] == "error")
    pend = sum(1 for s in scans if s["reviewStatus"] == "pending")
    slide["stats"] = {
        "total": len(scans),
        "positive": pos,
        "negative": neg,
        "errors": err,
        "pendingReview": pend
    }
    return {"success": True}


# Монтирование статических файлов
app.mount("/scans", StaticFiles(directory="scans"), name="scans")