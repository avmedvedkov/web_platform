import time
from pathlib import Path
from typing import Dict, List, Any
import torch
from PIL import Image
from ultralytics import YOLO
from config import SCANS_DIR, IMGSZ

# Размер батча – можно подстроить под вашу память (M3 24GB легко тянет 32-64)
BATCH_SIZE = 32

def process_scans(
    model: YOLO,
    slide_ids: List[str],
    scans_dir: Path = SCANS_DIR
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Обработать все слайды партии с использованием batch‑инференса.
    """
    # Определяем устройство (MPS, если доступно, иначе CPU)
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    model.to(device)

    # Словарь с названиями классов (0: 'helminth-egg', 1: 'trematode-helminth-egg')
    class_names = model.names

    slides_data: Dict[str, Any] = {}
    total_files = 0
    total_inference_time = 0.0
    overall_start = time.time()
    slides_summary = []

    for slide_id in slide_ids:
        slide_path = scans_dir / slide_id
        if not slide_path.exists():
            continue

        image_files = sorted([
            f for f in slide_path.iterdir()
            if f.suffix.lower() in ('.bmp', '.jpg', '.png')
        ])
        slide_total = len(image_files)
        print(f"\n📁 Стекло {slide_id}: {slide_total} файлов")

        # Подготавливаем список путей
        img_paths = [str(slide_path / f) for f in image_files]
        scans: List[Dict[str, Any]] = []
        slide_start = time.time()
        inference_time_slide = 0.0

        # Batch-обработка
        for i in range(0, slide_total, BATCH_SIZE):
            batch_paths = img_paths[i:i + BATCH_SIZE]
            batch_files = image_files[i:i + BATCH_SIZE]

            # Получаем оригинальные размеры изображений (до инференса)
            orig_sizes = []
            for f in batch_files:
                try:
                    with Image.open(slide_path / f) as pil_img:
                        orig_sizes.append(pil_img.size)  # (w, h)
                except Exception:
                    orig_sizes.append((0, 0))  # заглушка для ошибочных

            # Инференс на батче
            t0 = time.perf_counter()
            results = model(batch_paths, imgsz=IMGSZ, device=device, verbose=False)
            t1 = time.perf_counter()
            dt = t1 - t0
            inference_time_slide += dt

            # Разбор результатов для каждого изображения в батче
            for j, (res, orig_size, fname) in enumerate(zip(results, orig_sizes, batch_files)):
                orig_w, orig_h = orig_size
                try:
                    boxes = res.boxes
                    detections = []
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            conf = box.conf[0].item()
                            cls_id = int(box.cls[0].item())
                            detections.append({
                                "x1": x1,
                                "y1": y1,
                                "x2": x2,
                                "y2": y2,
                                "confidence": conf,
                                "class_id": cls_id,
                                "class_name": class_names[cls_id]
                            })

                    # Подсчёт по классам
                    class_counts = {
                        'helminth-egg': sum(1 for d in detections if d['class_name'] == 'helminth-egg'),
                        'trematode-helminth-egg': sum(1 for d in detections if d['class_name'] == 'trematode-helminth-egg')
                    }
                    num_eggs = len(detections)
                    scan_type = "positive" if num_eggs > 0 else "negative"
                    confidence = (
                        round(sum(d["confidence"] for d in detections) / num_eggs * 100)
                        if num_eggs else None
                    )

                    scans.append({
                        "index": i + j,
                        "filename": fname.name,
                        "scanType": scan_type,
                        "numEggs": num_eggs,
                        "numHelminthEgg": class_counts['helminth-egg'],
                        "numTrematodeEgg": class_counts['trematode-helminth-egg'],
                        "confidence": confidence,
                        "detections": detections,
                        "imgUrl": f"/scans/{slide_id}/{fname.name}",
                        "thumbUrl": f"/thumbnails/{slide_id}/{fname.name}?size=120",
                        "reviewStatus": (
                            "auto_approved" if scan_type == "negative" else "pending"
                        ),
                        "errorType": None,
                        "imgWidth": orig_w,
                        "imgHeight": orig_h
                    })
                except Exception as exc:
                    scans.append({
                        "index": i + j,
                        "filename": fname.name,
                        "scanType": "error",
                        "numEggs": 0,
                        "numHelminthEgg": 0,
                        "numTrematodeEgg": 0,
                        "confidence": None,
                        "detections": [],
                        "imgUrl": f"/scans/{slide_id}/{fname.name}",
                        "thumbUrl": f"/thumbnails/{slide_id}/{fname.name}?size=120",
                        "reviewStatus": "pending",
                        "errorType": str(exc),
                        "imgWidth": 0,
                        "imgHeight": 0
                    })

            # Прогресс каждые BATCH_SIZE*2 изображений (или реже)
            processed_so_far = i + len(batch_files)
            if processed_so_far % (BATCH_SIZE * 2) == 0 or processed_so_far == slide_total:
                elapsed = time.time() - slide_start
                speed = processed_so_far / elapsed if elapsed > 0 else 0
                print(
                    f"  {processed_so_far}/{slide_total} | скорость: {speed:.1f} ф/с "
                    f"| инференс батча: {dt:.4f}с"
                )

        # Статистика слайда
        pos = sum(1 for s in scans if s["scanType"] == "positive")
        neg = sum(1 for s in scans if s["scanType"] == "negative")
        err = sum(1 for s in scans if s["scanType"] == "error")
        pend = sum(1 for s in scans if s["reviewStatus"] == "pending")
        total_helminth = sum(s.get("numHelminthEgg", 0) for s in scans)
        total_trematode = sum(s.get("numTrematodeEgg", 0) for s in scans)
        slide_elapsed = time.time() - slide_start

        print(
            f"  Готово: +{pos} -{neg} !{err} ?{pend} "
            f"| яиц: {total_helminth + total_trematode} "
            f"(helminth: {total_helminth}, trematode: {total_trematode}) "
            f"| время: {slide_elapsed:.2f}с, инференс: {inference_time_slide:.2f}с"
        )

        stats = {
            "total": len(scans),
            "positive": pos,
            "negative": neg,
            "errors": err,
            "pendingReview": pend,
            "totalEggs": total_helminth + total_trematode,
            "helminthEggs": total_helminth,
            "trematodeEggs": total_trematode
        }
        slides_data[slide_id] = {"scans": scans, "stats": stats}

        total_files += len(scans)
        total_inference_time += inference_time_slide
        slides_summary.append({
            "slide": slide_id,
            "count": len(scans),
            "positive": pos,
            "errors": err,
            "helminthEggs": total_helminth,
            "trematodeEggs": total_trematode
        })

    total_time = time.time() - overall_start

    processing_stats = {
        "model_name": str(Path("runs/detect/train-10/weights/best.pt")),  # путь к обученной модели
        "total_files": total_files,
        "total_time": round(total_time, 2),
        "inference_time": round(total_inference_time, 2),
        "average_inference_ms": (
            round((total_inference_time / total_files * 1000), 2)
            if total_files else 0
        ),
        "speed": round(total_files / total_time, 2) if total_time else 0,
        "slides_summary": slides_summary
    }

    print("\n" + "=" * 60)
    print("ОБРАБОТКА ЗАВЕРШЕНА")
    print(f"Файлов: {total_files}, общее время: {total_time:.2f}с")
    print(
        f"Инференс: {total_inference_time:.2f}с, "
        f"среднее на файл: {processing_stats['average_inference_ms']} мс"
    )
    print("=" * 60)

    return slides_data, processing_stats