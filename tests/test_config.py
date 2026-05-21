from pathlib import Path
from config import SCANS_DIR, SLIDE_IDS, MODEL_PATH, IMGSZ, HOST, PORT

def test_config_paths():
    assert isinstance(SCANS_DIR, Path)
    assert isinstance(MODEL_PATH, Path)
    assert "best_808_yolo8.mlpackage" in str(MODEL_PATH)

def test_slide_ids():
    assert isinstance(SLIDE_IDS, list)
    assert len(SLIDE_IDS) == 7
    assert all("Стекло" in s for s in SLIDE_IDS)

def test_imgsz():
    assert isinstance(IMGSZ, int) and IMGSZ > 0

def test_host_port():
    assert isinstance(HOST, str)
    assert isinstance(PORT, int)