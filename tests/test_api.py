from unittest.mock import patch
from pathlib import Path
import io
from PIL import Image
import pytest
from api import app, slides_data, processing_stats

def test_get_slides_empty(api_client):
    response = api_client.get("/api/slides")
    assert response.status_code == 200
    assert response.json() == {}

def test_get_slides_with_data(api_client, sample_slides_data):
    slides_data.update(sample_slides_data)
    response = api_client.get("/api/slides")
    assert response.status_code == 200
    data = response.json()
    assert "Стекло Test" in data
    assert len(data["Стекло Test"]["scans"]) == 2

def test_get_stats_empty(api_client):
    response = api_client.get("/api/stats")
    assert response.status_code == 200
    assert response.json() == {}

def test_get_stats_with_data(api_client, sample_processing_stats):
    processing_stats.update(sample_processing_stats)
    response = api_client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "test_model"

def test_review_update_success(api_client, sample_slides_data):
    slides_data.update(sample_slides_data)
    payload = {"slideId": "Стекло Test", "index": 0, "status": "confirmed"}
    response = api_client.post("/api/review", json=payload)
    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert slides_data["Стекло Test"]["scans"][0]["reviewStatus"] == "confirmed"
    stats = slides_data["Стекло Test"]["stats"]
    assert stats["pendingReview"] == 0

def test_review_update_invalid_status(api_client, sample_slides_data):
    slides_data.update(sample_slides_data)
    payload = {"slideId": "Стекло Test", "index": 0, "status": "invalid"}
    response = api_client.post("/api/review", json=payload)
    assert response.status_code == 422

def test_review_update_missing_slide(api_client):
    payload = {"slideId": "Nonexistent", "index": 0, "status": "confirmed"}
    response = api_client.post("/api/review", json=payload)
    assert response.status_code == 404

def test_thumbnail_generation(api_client, tmp_path):
    with patch('api.SCANS_DIR', tmp_path):
        slide = "TestSlide"
        (tmp_path / slide).mkdir()
        img = Image.new('RGB', (100, 100))
        img_path = tmp_path / slide / "test.bmp"
        img.save(img_path)
        response = api_client.get(f"/thumbnails/{slide}/test.bmp?size=64")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"