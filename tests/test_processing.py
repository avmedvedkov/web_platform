import tempfile
import shutil
from pathlib import Path
from PIL import Image
import pytest
from unittest.mock import patch, MagicMock
from processing import process_scans, SCANS_DIR, IMGSZ

@pytest.fixture
def temp_scan_dirs():
    base = Path(tempfile.mkdtemp())
    for slide in ["Стекло A", "Стекло B"]:
        slide_dir = base / slide
        slide_dir.mkdir()
        for i in range(3):
            img = Image.new('RGB', (100, 100))
            img.save(slide_dir / f"scan_{i:03d}.bmp")
    yield base
    shutil.rmtree(base)

def test_process_scans_positive_detections(mock_yolo_model, temp_scan_dirs):
    slides, stats = process_scans(mock_yolo_model, ["Стекло A"], scans_dir=temp_scan_dirs)
    scans = slides["Стекло A"]["scans"]
    assert len(scans) == 3
    for scan in scans:
        assert scan["scanType"] == "positive"
        assert scan["numEggs"] == 2
        assert scan["confidence"] == 92
        assert scan["reviewStatus"] == "pending"
    assert stats["slides_summary"][0]["positive"] == 3
    assert stats["total_files"] == 3

def test_process_scans_empty_detections(mock_yolo_model, temp_scan_dirs):
    def empty_side_effect(source, **kwargs):
        if isinstance(source, list):
            source = source[0]
        result = MagicMock()
        result.boxes = None
        return [result]

    # Переопределяем side_effect самого мока, а не __call__
    mock_yolo_model.side_effect = empty_side_effect

    slides, stats = process_scans(mock_yolo_model, ["Стекло A"], scans_dir=temp_scan_dirs)
    for scan in slides["Стекло A"]["scans"]:
        assert scan["scanType"] == "negative"
        assert scan["numEggs"] == 0
        assert scan["confidence"] is None
        assert scan["reviewStatus"] == "auto_approved"

    slides, stats = process_scans(mock_yolo_model, ["Стекло A"], scans_dir=temp_scan_dirs)
    for scan in slides["Стекло A"]["scans"]:
        assert scan["scanType"] == "negative"
        assert scan["numEggs"] == 0
        assert scan["confidence"] is None
        assert scan["reviewStatus"] == "auto_approved"

def test_process_scans_error_handling(mock_yolo_model, temp_scan_dirs):
    mock_yolo_model.side_effect = Exception("Test error")
    slides, stats = process_scans(mock_yolo_model, ["Стекло A"], scans_dir=temp_scan_dirs)
    for scan in slides["Стекло A"]["scans"]:
        assert scan["scanType"] == "error"
        assert "Test error" in scan["errorType"]
        assert scan["reviewStatus"] == "pending"

def test_process_scans_respects_slide_ids(mock_yolo_model, temp_scan_dirs):
    slides, _ = process_scans(mock_yolo_model, ["Стекло B"], scans_dir=temp_scan_dirs)
    assert "Стекло A" not in slides
    assert "Стекло B" in slides
    assert len(slides["Стекло B"]["scans"]) == 3

def test_process_scans_timing_and_speed(mock_yolo_model, temp_scan_dirs):
    slides, stats = process_scans(mock_yolo_model, ["Стекло A"], scans_dir=temp_scan_dirs)
    assert stats["total_time"] >= 0
    assert stats["inference_time"] >= 0
    assert stats["speed"] >= 0
    assert stats["average_inference_ms"] >= 0