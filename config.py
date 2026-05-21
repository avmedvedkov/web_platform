"""Конфигурация приложения «МНПЦЛИ · Энтеробиоз»"""

from pathlib import Path

# Корень проекта
BASE_DIR = Path(__file__).resolve().parent

# Директория со сканами слайдов
SCANS_DIR = BASE_DIR / "scans"

# Идентификаторы стёкол, ожидаемые в scans/
SLIDE_IDS = [
    "Стекло 1", "Стекло 2", "Стекло 3",
    "Стекло 4", "Стекло 5", "Стекло 6", "Стекло 7"
]

# Путь к YOLO-модели (Core ML / PyTorch)
MODEL_PATH = BASE_DIR / "best.pt"

# Размер изображения, подаваемого в модель
IMGSZ = 320

# Порт и хост для Uvicorn
HOST = "0.0.0.0"
PORT = 8000

# Максимальное число миниатюр в кеше
THUMBNAIL_CACHE_SIZE = 500