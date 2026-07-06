"""
Точка входа: запуск нужной фичи пайплайна обработки DXF-чертежей.

Доступные функции (раскомментируйте нужную в блоке if __name__):

  clean_dxf(path)
      Очищает DXF от текста, размеров, штриховок и осей.
      Модуль: lib.cleaning
      Результат: *_cleaned.dxf

  convert_dxf_to_png(path)
      Рендерит modelspace DXF в PNG (dpi=300, max 4096 px по длинной стороне).
      Модуль: lib.converter
      Результат: .png рядом с DXF

  train_floor_plan_model()
      Обучает YOLO segmentation-модель на датасете models/floor-plan.v1i.yolov8.
      Модуль: lib.recognition
      Результат: models/floor_plan_best.pt

  detect_objects_in_png(png_path)
      Тест обученной модели на PNG: инференс + превью с bbox.
      Модуль: lib.recognition
      Требует: models/floor_plan_best.pt
      Результат: *_detected.png

  detect_objects_in_dxf(path)
      Распознавание на PNG + заливка зон в DXF (отдельный шаг).
      Модуль: lib.recognition
      Результат: *_detected.dxf

  recognize_from_image(png_path)
      Распознавание через Roboflow API (окна, двери, стены).
      Модуль: lib.roboflow
      Требует: ROBOFLOW_API_KEY и ROBOFLOW_MODEL_ID
      Результат: *_ai_zones.dxf
"""
from __future__ import annotations

import sys
from pathlib import Path

from lib.recognition import detect_objects_in_png

# from lib import clean_dxf, convert_dxf_to_png
# from lib.recognition import detect_objects_in_dxf, train_floor_plan_model
# from lib.roboflow import recognize_from_image

# ---------------------------------------------------------------------------
# Входные файлы (можно передать аргументом командной строки)
# ---------------------------------------------------------------------------

IMAGE_FILE = "01_example_1_flor.png"
MODEL_FILE = "models/floor_plan_best.pt"


if __name__ == "__main__":
    # --- 1. Очистка DXF ---
    # result_dxf_path = clean_dxf("01_example_1_flor.dxf")
    # print(result_dxf_path)

    # --- 2. Конвертация DXF → PNG ---
    # result_path = convert_dxf_to_png("01_example_1_flor.dxf")
    # print(result_path)

    # --- 3. Обучение YOLO-модели на датасете floor-plan ---
    # model_path = train_floor_plan_model()
    # print(model_path)

    # --- 4. Тест обученной модели на PNG (без DXF) ---
    image_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(IMAGE_FILE)
    preview_png, detections = detect_objects_in_png(image_path, model_path=MODEL_FILE)

    print(f"Превью: {preview_png}")
    print(f"Всего объектов: {len(detections)}")
    for class_name in ("door", "wall", "window"):
        count = sum(1 for item in detections if item.class_name == class_name)
        print(f"  {class_name}: {count}")

    # --- 5. Заливка распознанных зон в DXF (отдельный запрос) ---
    # output_dxf, detections = detect_objects_in_dxf("01_example_1_flor.dxf", png_path=image_path)
    # print(output_dxf, len(detections))

    # --- 6. Распознавание через Roboflow API ---
    # result_dxf = recognize_from_image(image_path)
    # print(result_dxf)
