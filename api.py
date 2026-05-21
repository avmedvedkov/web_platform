"""
Модуль FastAPI-приложения
Определяет маршруты и запускает сервер (без Pydantic)
"""

import io
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from PIL import Image

from config import SCANS_DIR

# Глобальное состояние приложения
slides_data: Dict[str, Any] = {}
processing_stats: Dict[str, Any] = {}
thumbnail_cache: Dict[str, bytes] = {}

app = FastAPI(title="МНПЦЛИ Энтеробиоз API")


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


@app.get("/api/slides")
async def get_slides():
    """Получить данные по всем слайдам"""
    return slides_data


@app.get("/api/stats")
async def get_stats():
    """Статистика обработки"""
    return processing_stats


@app.get("/thumbnails/{slide}/{filename}")
async def thumbnail(
    slide: str, filename: str, size: int = Query(120)
):
    """Сгенерировать и закешировать миниатюру"""
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


@app.post("/api/review")
async def update_review(request: Request):
    """
    Обновить статус проверки конкретного скана
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