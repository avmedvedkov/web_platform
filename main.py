"""
Точка входа приложения
Загружает модель, запускает первичную обработку и стартует Uvicorn
"""

import uvicorn

from model import load_detection_model
from processing import process_scans
import api
from config import SLIDE_IDS, MODEL_PATH, HOST, PORT


def main() -> None:
    """
    Инициализация и запуск веб-сервера

    1. Загрузка YOLO-модели
    2. Обработка всех слайдов партии
    3. Запуск FastAPI-сервера
    """
    print("=" * 60)
    print("Загрузка модели...")
    model = load_detection_model(MODEL_PATH)

    print("Старт обработки сканов...")
    # Обновляем глобальные переменные в модуле api
    api.slides_data, api.processing_stats = process_scans(model, SLIDE_IDS)

    print("Запуск веб-сервера...")
    uvicorn.run(api.app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()