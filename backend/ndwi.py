"""
NDWI (Normalized Difference Water Index) calculation from Landsat imagery.
Fetches bands from GeoServer WCS with SCALESIZE (server-side resize),
computes NDWI, applies colormap.

NDWI = (Green - NIR) / (Green + NIR)   [McFeeters, 1996]

High positive NDWI → open water
Negative NDWI → terrestrial vegetation / soil
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


def fetch_ndwi_bands(year: int) -> Tuple[np.ndarray, np.ndarray, dict]:
    """
    Fetch Green and NIR bands at web resolution from GeoServer WCS.
    Uses SCALESIZE for server-side downsampling.
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
        green = src.read(band_map["green"]).astype(np.float32)
        nir = src.read(band_map["nir"]).astype(np.float32)

        # Mask NoData artifacts (extreme values)
        mask = (green > -0.1) & (green < 10) & (nir > -0.1) & (nir < 10)
        green = np.where(mask, green, np.nan)
        nir = np.where(mask, nir, np.nan)

        bounds = {
            "west": src.bounds.left,
            "south": src.bounds.bottom,
            "east": src.bounds.right,
            "north": src.bounds.top,
            "width": src.width,
            "height": src.height,
        }

    return green, nir, bounds


def calc_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    NDWI = (Green - NIR) / (Green + NIR)

    Positive → water (Green > NIR)
    Negative → terrestrial vegetation / soil (NIR > Green)
    """
    with np.errstate(all='ignore'):
        denom = green + nir
        ndwi = np.where(denom > 0, (green - nir) / denom, np.nan)
        # Mask non-physical reflectance values
        ndwi[(green > 1.5) | (nir > 1.5)] = np.nan
        ndwi[(green < -0.1) | (nir < -0.1)] = np.nan
    return ndwi.astype(np.float32)


def apply_colormap_ndwi(ndwi: np.ndarray) -> np.ndarray:
    """
    NDWI → RGBA via water-themed gradient. Returns (H, W, 4) uint8.

    Colormap design:
      -1.0  → dark brown (dry land)
      -0.3  → light tan (moist soil)
       0.0  → off-white (transition zone)
       0.1  → light blue (shallow water / wet area)
       0.4  → medium blue (water)
       0.7  → deep blue (deep water)
       1.0  → dark navy (very deep / clear water)
    """
    h, w = ndwi.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    valid = ~np.isnan(ndwi)
    rgba[:, :, 3] = np.where(valid, 255, 0)

    clamped = np.clip(ndwi, -1.0, 1.0)

    stops = np.array([
        [-1.00, 130,  80,  30],   # dark brown — dry land
        [-0.40, 200, 170, 120],   # light tan — soil
        [-0.10, 230, 225, 200],   # pale — moist / transition
        [ 0.00, 200, 220, 235],   # very light blue — wet edge
        [ 0.15, 100, 180, 230],   # light blue — shallow water
        [ 0.40,  30, 130, 210],   # medium blue — water
        [ 0.70,  10,  70, 170],   # deep blue — deep water
        [ 1.00,   5,  30, 100],   # dark navy — very deep / clear water
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


def compute_ndwi_image_with_bounds(year: int) -> Tuple[bytes, dict]:
    """Fetch → NDWI → colormap → PNG bytes + geo bounds."""
    green, nir, bounds = fetch_ndwi_bands(year)
    ndwi = calc_ndwi(green, nir)
    cache_set(("NDWI", year, None), ndwi, bounds)
    rgba = apply_colormap_ndwi(ndwi)

    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue(), bounds
