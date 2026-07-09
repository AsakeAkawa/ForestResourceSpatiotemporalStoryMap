"""
NDVI calculation from Landsat imagery.
Fetches bands from GeoServer WCS with SCALESIZE (server-side resize),
computes NDVI, applies colormap.
"""
import io
import urllib.request
from typing import Tuple

import numpy as np
from PIL import Image
import rasterio

from config import (
    WCS_URL,
    KUBUQI_BBOX,
    BAND_MAP,
    get_satellite_era,
    get_layer_name,
)
from cache import set as cache_set

WEB_W = 700   # target width for web display
WEB_H = 240   # target height (aspect ~3:1 for Kubuqi)


def fetch_bands(year: int) -> Tuple[np.ndarray, np.ndarray, dict]:
    """
    Fetch Red and NIR bands at web resolution from GeoServer WCS.
    Uses SCALESIZE for server-side downsampling — avoids downloading 1.6GB full-res.
    """
    era = get_satellite_era(year)
    band_map = BAND_MAP[era]
    layer = get_layer_name(year)

    bbox = KUBUQI_BBOX
    params = (
        f"SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage"
        f"&COVERAGEID={layer}"
        f"&FORMAT=image/tiff"
        f"&SUBSET=Lat({bbox['miny']},{bbox['maxy']})"
        f"&SUBSET=Long({bbox['minx']},{bbox['maxx']})"
        f"&SCALESIZE=i({WEB_W}),j({WEB_H})"
    )
    url = f"{WCS_URL}?{params}"

    with urllib.request.urlopen(url, timeout=120) as resp:
        data = resp.read()

    with rasterio.open(io.BytesIO(data)) as src:
        red = src.read(band_map["red"]).astype(np.float32)
        nir = src.read(band_map["nir"]).astype(np.float32)

        # Mask NoData artifacts (extreme values)
        mask = (red > -0.1) & (red < 10) & (nir > -0.1) & (nir < 10)
        red = np.where(mask, red, np.nan)
        nir = np.where(mask, nir, np.nan)

        bounds = {
            "west": src.bounds.left,
            "south": src.bounds.bottom,
            "east": src.bounds.right,
            "north": src.bounds.top,
            "width": src.width,
            "height": src.height,
        }

    return red, nir, bounds


def calc_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """NDVI = (NIR - Red) / (NIR + Red), masked for non-physical values."""
    with np.errstate(all='ignore'):
        denom = nir + red
        ndvi = np.where(denom > 0, (nir - red) / denom, np.nan)
        ndvi[(red > 1.5) | (nir > 1.5) | (red < -0.1) | (nir < -0.1)] = np.nan
    return ndvi.astype(np.float32)


def apply_colormap(ndvi: np.ndarray) -> np.ndarray:
    """NDVI → RGBA via brown→yellow→green gradient. Returns (H, W, 4) uint8."""
    h, w = ndvi.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    valid = ~np.isnan(ndvi)
    rgba[:, :, 3] = np.where(valid, 255, 0)

    clamped = np.clip(ndvi, -1.0, 1.0)

    stops = np.array([
        [-1.00, 110, 64,   0],
        [-0.20, 181, 138,  46],
        [ 0.00, 230, 200,  80],
        [ 0.15, 180, 210, 100],
        [ 0.30, 120, 180,  60],
        [ 0.50,  50, 140,  30],
        [ 0.70,  10, 100,  20],
        [ 1.00,   0,  60,  10],
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


def compute_ndvi_image_with_bounds(year: int) -> Tuple[bytes, dict]:
    """Fetch → NDVI → colormap → PNG bytes + geo bounds."""
    red, nir, bounds = fetch_bands(year)
    ndvi = calc_ndvi(red, nir)
    cache_set(("NDVI", year, None), ndvi, bounds)
    rgba = apply_colormap(ndvi)

    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue(), bounds
