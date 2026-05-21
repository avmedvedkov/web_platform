import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from api import app, slides_data, processing_stats


# ----- вспомогательные классы для эмуляции боксов -----
class FakeTensor:
    """Подменяет torch.Tensor для tolist() и item()."""
    def __init__(self, data):
        self.data = data

    def tolist(self):
        # data может быть списком или числом
        if isinstance(self.data, (list, tuple)):
            return list(self.data)
        return [self.data]

    def item(self):
        # возвращает первый элемент, если data – список, иначе само число
        if isinstance(self.data, (list, tuple)):
            return self.data[0]
        return self.data


class FakeBox:
    """Эмулирует один детектированный объект Ultralytics."""
    def __init__(self, x1, y1, x2, y2, conf, cls_id=0):
        self.xyxy = [FakeTensor([x1, y1, x2, y2])]
        self.conf = [FakeTensor(conf)]
        self.cls = [FakeTensor(cls_id)]


# ----- фикстуры -----
@pytest.fixture
def mock_yolo_model():
    """Мок YOLO-модели, возвращающий 2 детекции для любого файла, не содержащего 'empty'."""
    def predict_side_effect(source, **kwargs):
        # source – либо путь к файлу, либо список
        if isinstance(source, list):
            source = source[0]
        result = MagicMock()
        if "empty" in str(source).lower():
            result.boxes = None
        else:
            result.boxes = [
                FakeBox(10.0, 20.0, 50.0, 60.0, 0.95),
                FakeBox(70.0, 80.0, 120.0, 130.0, 0.88),
            ]
        return [result]

    # Главная хитрость: создаём MagicMock сразу с side_effect
    model = MagicMock(side_effect=predict_side_effect)
    # если в коде используется model.predict, дублируем
    model.predict = MagicMock(side_effect=predict_side_effect)
    return model


@pytest.fixture
def api_client():
    """Тестовый клиент FastAPI с чистыми глобальными данными."""
    slides_data.clear()
    processing_stats.clear()
    return TestClient(app)


@pytest.fixture
def sample_slides_data():
    """Пример данных слайда для API-тестов."""
    return {
        "Стекло Test": {
            "scans": [
                {
                    "index": 0,
                    "filename": "img01.bmp",
                    "scanType": "positive",
                    "numEggs": 2,
                    "confidence": 92,
                    "detections": [{"x1":10,"y1":20,"x2":50,"y2":60,"confidence":0.95,"class_id":0}],
                    "imgUrl": "/scans/Стекло Test/img01.bmp",
                    "thumbUrl": "/thumbnails/Стекло Test/img01.bmp?size=120",
                    "reviewStatus": "pending",
                    "errorType": None,
                    "imgWidth": 640,
                    "imgHeight": 480,
                },
                {
                    "index": 1,
                    "filename": "img02.bmp",
                    "scanType": "negative",
                    "numEggs": 0,
                    "confidence": None,
                    "detections": [],
                    "imgUrl": "/scans/Стекло Test/img02.bmp",
                    "thumbUrl": "/thumbnails/Стекло Test/img02.bmp?size=120",
                    "reviewStatus": "auto_approved",
                    "errorType": None,
                    "imgWidth": 640,
                    "imgHeight": 480,
                },
            ],
            "stats": {"total": 2, "positive": 1, "negative": 1, "errors": 0, "pendingReview": 1},
        }
    }


@pytest.fixture
def sample_processing_stats():
    """Пример общей статистики."""
    return {
        "model_name": "test_model",
        "total_files": 2,
        "total_time": 0.5,
        "inference_time": 0.4,
        "average_inference_ms": 200.0,
        "speed": 4.0,
        "slides_summary": [{"slide": "Стекло Test", "count": 2, "positive": 1, "errors": 0}],
    }