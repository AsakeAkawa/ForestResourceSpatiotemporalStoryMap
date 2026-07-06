"""
FVC (Fractional Vegetation Cover) calculation from Landsat imagery.
Derived from NDVI using the pixel-purity model:

    FVC = (NDVI - NDVI_soil) / (NDVI_veg - NDVI_soil)

NDVI_soil and NDVI_veg are estimated from the 5th and 95th percentiles
of the NDVI distribution within the scene.
"""
import io
from typing import Tuple

import numpy as np
from PIL import Image

from ndvi import fetch_bands, calc_ndvi
from cache import set as cache_set

WEB_W = 700
WEB_H = 240


def calc_fvc(ndvi: np.ndarray) -> Tuple[np.ndarray, float, float]:
    """
    Compute FVC from NDVI using the percentile-based threshold method.

    FVC = (NDVI - NDVI_soil) / (NDVI_veg - NDVI_soil), clipped to [0, 1].

    Returns (fvc, ndvi_soil, ndvi_veg).
    """
    valid = ndvi[~np.isnan(ndvi)]
    if len(valid) == 0:
        ndvi_soil, ndvi_veg = 0.2, 0.5
    else:
        ndvi_soil = float(np.percentile(valid, 5))
        ndvi_veg = float(np.percentile(valid, 95))
        # Guard against degenerate range
        if ndvi_veg - ndvi_soil < 0.01:
            ndvi_soil = ndvi_veg - 0.01

    with np.errstate(all='ignore'):
        fvc = (ndvi - ndvi_soil) / (ndvi_veg - ndvi_soil)
        fvc = np.clip(fvc, 0.0, 1.0)
    return fvc.astype(np.float32), ndvi_soil, ndvi_veg


def apply_colormap_fvc(fvc: np.ndarray) -> np.ndarray:
    """
    FVC → RGBA via vegetation-density gradient. Returns (H, W, 4) uint8.

    Colormap design (fraction 0–1):
      0.00 → tan/brown (bare soil)
      0.15 → light yellow-green (sparse vegetation)
      0.35 → medium green (moderate cover)
      0.60 → rich green (good cover)
      0.85 → dark green (dense vegetation)
      1.00 → deep forest green (full cover)
    """
    h, w = fvc.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    valid = ~np.isnan(fvc)
    rgba[:, :, 3] = np.where(valid, 255, 0)

    clamped = np.clip(fvc, 0.0, 1.0)

    stops = np.array([
        [0.00, 180, 150,  90],   # tan — bare soil
        [0.10, 195, 185, 100],   # pale yellow-green
        [0.25, 145, 190,  70],   # light green — sparse veg
        [0.40,  80, 170,  50],   # medium green
        [0.60,  30, 140,  40],   # rich green
        [0.80,  10, 100,  30],   # dark green
        [1.00,   0,  60,  20],   # deep forest green — full cover
    ], dtype=np.float32)

    thresholds, colors = stops[:, 0], stops[:, 1:]
    idx = np.searchsorted(thresholds, clamped[valid]) - 1
    idx = np.clip(idx, 0, len(stops) - 2)

    v0, v1 = thresholds[idx], thresholds[idx + 1]
    c0, c1 = colors[idx], colors[idx + 1]
    denom = np.where(v1 - v0 == 0, 1, v1 - v0)
    t = ((clamped[valid] - v0) / denom)[:, np.newaxis]
    rgba[valid, :3] = (c0 + t * (c1 - c0)).astype(np.uint8)

    return rgba


def compute_fvc_image_with_bounds(year: int) -> Tuple[bytes, dict]:
    """Fetch → NDVI → FVC → colormap → PNG bytes + geo bounds."""
    red, nir, bounds = fetch_bands(year)
    ndvi = calc_ndvi(red, nir)
    fvc, ndvi_soil, ndvi_veg = calc_fvc(ndvi)
    cache_set(("FVC", year, None), fvc, bounds)
    rgba = apply_colormap_fvc(fvc)

    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue(), bounds
