"""
NDVI change detection: compute NDVI for two years, align, subtract,
apply divergence colormap, return PNG + bounds.

Integrated with GeoServer WCS (not local files).
"""
import io
from typing import Tuple

import numpy as np
from PIL import Image

from ndvi import fetch_bands, calc_ndvi
from cache import set as cache_set


def calc_change(ndvi1: np.ndarray, ndvi2: np.ndarray) -> np.ndarray:
    """
    Pixel-wise change: ΔNDVI = NDVI_{year2} - NDVI_{year1}.
    Returns NaN where either input is NaN.
    """
    valid = (~np.isnan(ndvi1)) & (~np.isnan(ndvi2))
    change = np.full_like(ndvi1, np.nan, dtype=np.float32)
    change[valid] = ndvi2[valid] - ndvi1[valid]
    return change


def apply_colormap_change(change: np.ndarray) -> np.ndarray:
    """
    Divergence colormap: red (degradation) → white (stable) → green (improvement).
    Returns RGBA uint8 (H, W, 4).
    """
    h, w = change.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    valid = ~np.isnan(change)
    rgba[:, :, 3] = np.where(valid, 255, 0)

    clamped = np.clip(change, -1.0, 1.0)

    # Matches frontend legend: red(degradation) → white(stable) → green(improvement)
    # Scale: -0.2 → 0 → +0.2 (greening threshold lowered for visual impact)
    # Frontend hex: b40a0a → eb5050 → faae8c → fceee6 → f5f5f5 → e1f2dc → a0e182 → 32b432 → 006400
    stops = np.array([
        [-1.00, 0xb4, 0x0a, 0x0a],   # strong degradation
        [-0.20, 0xeb, 0x50, 0x50],   # moderate degradation
        [-0.10, 0xfa, 0xae, 0x8c],   # slight degradation
        [-0.03, 0xfc, 0xee, 0xe6],   # very slight degradation
        [ 0.00, 0xf5, 0xf5, 0xf5],   # stable
        [ 0.03, 0xe1, 0xf2, 0xdc],   # very slight improvement
        [ 0.10, 0xa0, 0xe1, 0x82],   # slight improvement
        [ 0.20, 0x32, 0xb4, 0x32],   # moderate improvement
        [ 1.00, 0x00, 0x64, 0x00],   # strong improvement
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


def compute_change_image_with_bounds(year1: int, year2: int) -> Tuple[bytes, dict]:
    """
    Full pipeline:
      1. Fetch bands for year1 → compute NDVI1
      2. Fetch bands for year2 → compute NDVI2
      3. Both come from the same GeoServer layer (same CRS/size), so no alignment needed
      4. Δ = NDVI2 - NDVI1
      5. Divergence colormap → PNG
    """
    # Year 1
    red1, nir1, bounds1 = fetch_bands(year1)
    ndvi1 = calc_ndvi(red1, nir1)

    # Year 2
    red2, nir2, bounds2 = fetch_bands(year2)
    ndvi2 = calc_ndvi(red2, nir2)

    # Both use same SCALESIZE → same dimensions, no alignment needed
    if ndvi1.shape != ndvi2.shape:
        h = min(ndvi1.shape[0], ndvi2.shape[0])
        w = min(ndvi1.shape[1], ndvi2.shape[1])
        ndvi1, ndvi2 = ndvi1[:h, :w], ndvi2[:h, :w]

    change = calc_change(ndvi1, ndvi2)
    cache_set(("CHANGE", year1, year2), change, bounds1)
    rgba = apply_colormap_change(change)

    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue(), bounds1
