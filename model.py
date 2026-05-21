"""Модуль инициализации YOLO-модели"""

from pathlib import Path
import torch
from ultralytics import YOLO


def load_detection_model(model_path: Path) -> YOLO:
    """
    Загрузить YOLO-модель по указанному пути

    :param model_path: абсолютный или относительный путь к файлу модели
    :return: объект модели YOLO
    :raises FileNotFoundError: если файл не найден
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Модель не найдена: {model_path}")
    model = YOLO(str(model_path), task='detect')
    # «Прогреваем» модель, чтобы CoreML скомпилировалась и закешировалась один раз
    dummy_input = torch.zeros(1, 3, 320, 320)
    model(dummy_input, verbose=False)
    return model