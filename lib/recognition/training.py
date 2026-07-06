"""Обучение YOLO segmentation-модели на датасете планов этажей."""

from __future__ import annotations

from pathlib import Path

from lib.common.logging_config import logger

# ---------------------------------------------------------------------------
# Настройки обучения (оптимизировано для MacBook Pro, 24 GB RAM)
# ---------------------------------------------------------------------------

DATASET_DIR: Path = Path("models/floor-plan.v1i.yolov8")
DATASET_YAML: Path = DATASET_DIR / "data.yaml"
BASE_MODEL: str = "yolov8n-seg.pt"
EPOCHS: int = 100
IMAGE_SIZE: int = 800
BATCH_SIZE: int = 2
PATIENCE: int = 20
WORKERS: int = 0  # на macOS fork DataLoader часто вызывает зависания
PROJECT_DIR: Path = Path("models/runs")
RUN_NAME: str = "floor-plan-seg"
BEST_MODEL_OUTPUT: Path = Path("models/floor_plan_best.pt")


def _resolve_device() -> str:
    """Выбирает MPS (Apple Silicon GPU) или CPU как запасной вариант."""
    try:
        import torch
    except ImportError:
        logger.warning("torch не найден, используется CPU")
        return "cpu"

    if torch.backends.mps.is_available():
        return "mps"

    logger.warning("MPS недоступен — обучение пойдёт на CPU (будет значительно медленнее)")
    return "cpu"


def _write_resolved_dataset_yaml(yaml_path: Path) -> Path:
    """
    Создаёт data.yaml с абсолютным path к датасету.

    Ultralytics при path: '.' ищет valid/images в cwd проекта, а не в папке датасета.
    """
    lines = yaml_path.read_text(encoding="utf-8").splitlines()
    dataset_root = yaml_path.parent.resolve()
    resolved_lines: list[str] = []
    path_written = False

    for line in lines:
        if line.startswith("path:"):
            resolved_lines.append(f"path: {dataset_root}")
            path_written = True
        else:
            resolved_lines.append(line)

    if not path_written:
        resolved_lines.insert(0, f"path: {dataset_root}")

    resolved_yaml = yaml_path.parent / "data.resolved.yaml"
    resolved_yaml.write_text("\n".join(resolved_lines) + "\n", encoding="utf-8")
    return resolved_yaml


def train_floor_plan_model(
    *,
    dataset_yaml: str | Path | None = None,
    base_model: str | None = None,
    epochs: int | None = None,
    imgsz: int | None = None,
    batch: int | None = None,
    patience: int | None = None,
    workers: int | None = None,
    project: str | Path | None = None,
    name: str | None = None,
    copy_best_to: str | Path | None = None,
) -> Path:
    """
    Обучает YOLO segmentation-модель на датасете YOLOv8 TXT из папки models/.

    Датасет floor-plan.v1i.yolov8 содержит полигональную разметку (door, wall, window),
    поэтому используется базовая модель yolov8n-seg.pt, а не detect-вариант.

    При нехватке памяти уменьшите BATCH_SIZE (8 → 6 → 4) или IMAGE_SIZE (1024 → 640).

    Returns:
        Путь к файлу best.pt (скопированному в models/floor_plan_best.pt по умолчанию).
    """
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise ImportError(
            "Пакет ultralytics не установлен. Выполните: pip install ultralytics"
        ) from exc

    yaml_path = Path(dataset_yaml or DATASET_YAML).expanduser().resolve()
    if not yaml_path.exists():
        raise FileNotFoundError(f"Файл датасета не найден: {yaml_path}")

    dataset_data_yaml = _write_resolved_dataset_yaml(yaml_path)

    run_project = Path(project or PROJECT_DIR).expanduser().resolve()
    run_name = name or RUN_NAME
    destination = Path(copy_best_to or BEST_MODEL_OUTPUT).expanduser().resolve()
    device = _resolve_device()

    logger.info("Старт обучения: %s", dataset_data_yaml)
    logger.info("Базовая модель: %s", base_model or BASE_MODEL)
    logger.info("Устройство: %s | batch=%s | imgsz=%s", device, batch or BATCH_SIZE, imgsz or IMAGE_SIZE)

    model = YOLO(base_model or BASE_MODEL)
    model.train(
        data=str(dataset_data_yaml),
        epochs=epochs if epochs is not None else EPOCHS,
        imgsz=imgsz if imgsz is not None else IMAGE_SIZE,
        batch=batch if batch is not None else BATCH_SIZE,
        patience=patience if patience is not None else PATIENCE,
        project=str(run_project),
        name=run_name,
        device=device,
        workers=workers if workers is not None else WORKERS,
        cache=False,
        amp=True,
        exist_ok=True,
    )

    best_weights = run_project / run_name / "weights" / "best.pt"
    if not best_weights.exists():
        raise FileNotFoundError(f"Веса best.pt не найдены после обучения: {best_weights}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(best_weights.read_bytes())
    logger.info("Лучшие веса сохранены: %s", destination)
    return destination
