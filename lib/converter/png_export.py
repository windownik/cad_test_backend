"""Экспорт DXF-чертежа в PNG через matplotlib."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import ezdxf
import matplotlib.pyplot as plt
from ezdxf import bbox as ezdxf_bbox
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import ColorPolicy, Configuration
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

from lib.common.io import resolve_dxf_path
from lib.common.logging_config import logger


class PngExportMeta(TypedDict):
    """Метаданные границ чертежа для обратного пересчёта координат."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float
    cad_width: float
    cad_height: float
    image_width_px: int
    image_height_px: int


def calc_image_pixels(cad_width: float, cad_height: float, *, max_side_px: int) -> tuple[int, int]:
    """Вычисляет размер PNG в пикселях с сохранением пропорций чертежа."""
    if cad_width <= 0 or cad_height <= 0:
        return max_side_px, max_side_px

    if cad_width >= cad_height:
        width_px = max_side_px
        height_px = max(1, round(max_side_px * cad_height / cad_width))
    else:
        height_px = max_side_px
        width_px = max(1, round(max_side_px * cad_width / cad_height))

    return width_px, height_px


def dxf_to_png(
    dxf_path: str | Path,
    png_path: str | Path,
    *,
    dpi: int = 300,
    max_side_px: int = 4096,
) -> PngExportMeta:
    """
    Рендерит modelspace DXF-файла в PNG и возвращает границы чертежа.

    Размер изображения вычисляется из bbox чертежа: длинная сторона
    масштабируется до max_side_px пикселей с сохранением пропорций.
    """
    resolved_dxf = resolve_dxf_path(dxf_path)
    destination = Path(png_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    doc = ezdxf.readfile(str(resolved_dxf))
    msp = doc.modelspace()

    bbox = ezdxf_bbox.extents(msp)
    x_min, y_min = bbox.extmin[0], bbox.extmin[1]
    x_max, y_max = bbox.extmax[0], bbox.extmax[1]
    cad_width = x_max - x_min
    cad_height = y_max - y_min

    width_px, height_px = calc_image_pixels(cad_width, cad_height, max_side_px=max_side_px)

    fig = plt.figure(
        figsize=(width_px / dpi, height_px / dpi),
        dpi=dpi,
        facecolor="white",
    )
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_facecolor("white")

    config = Configuration(
        color_policy=ColorPolicy.COLOR_SWAP_BW,
        min_lineweight=72.0 / dpi,
    )
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax, adjust_figure=False)
    Frontend(ctx, backend, config=config).draw_layout(msp)

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    fig.savefig(destination, facecolor="white", pad_inches=0)
    plt.close(fig)

    meta: PngExportMeta = {
        "x_min": x_min,
        "y_min": y_min,
        "x_max": x_max,
        "y_max": y_max,
        "cad_width": cad_width,
        "cad_height": cad_height,
        "image_width_px": width_px,
        "image_height_px": height_px,
    }
    logger.info("PNG сохранён: %s (%dx%d px)", destination.name, width_px, height_px)
    return meta
