"""
BSI (Bare Soil Index) calculation from Landsat imagery.
Fetches bands from GeoServer WCS with SCALESIZE (server-side resize),
computes BSI, applies colormap.

BSI = ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))
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


def fetch_bsi_bands(year: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """
    Fetch Blue, Red, NIR, and SWIR1 bands at web resolution from GeoServer WCS.
    Uses SCALESIZE for server-side downsampling — avoids downloading full-res data.
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
        blue = src.read(band_map["blue"]).astype(np.float32)
        red = src.read(band_map["red"]).astype(np.float32)
        nir = src.read(band_map["nir"]).astype(np.float32)
        swir1 = src.read(band_map["swir1"]).astype(np.float32)

        # Mask NoData artifacts (extreme values)
        mask = (
            (blue > -0.1) & (blue < 10) &
            (red > -0.1) & (red < 10) &
            (nir > -0.1) & (nir < 10) &
            (swir1 > -0.1) & (swir1 < 10)
        )
        blue = np.where(mask, blue, np.nan)
        red = np.where(mask, red, np.nan)
        nir = np.where(mask, nir, np.nan)
        swir1 = np.where(mask, swir1, np.nan)

        bounds = {
            "west": src.bounds.left,
            "south": src.bounds.bottom,
            "east": src.bounds.right,
            "north": src.bounds.top,
            "width": src.width,
            "height": src.height,
        }

    return blue, red, nir, swir1, bounds


def calc_bsi(blue: np.ndarray, red: np.ndarray, nir: np.ndarray, swir1: np.ndarray) -> np.ndarray:
    """
    BSI = ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))

    High BSI → bare soil (dry, sparse vegetation)
    Low BSI → dense vegetation or water
    """
    with np.errstate(all='ignore'):
        numerator = (swir1 + red) - (nir + blue)
        denominator = (swir1 + red) + (nir + blue)
        bsi = np.where(denominator > 0, numerator / denominator, np.nan)
        # Mask non-physical reflectance values
        bsi[(red > 1.5) | (nir > 1.5) | (swir1 > 1.5) | (blue > 1.5)] = np.nan
        bsi[(red < -0.1) | (nir < -0.1) | (swir1 < -0.1) | (blue < -0.1)] = np.nan
    return bsi.astype(np.float32)


def apply_colormap_bsi(bsi: np.ndarray) -> np.ndarray:
    """
    BSI → RGBA via soil-themed gradient. Returns (H, W, 4) uint8.

    Colormap design:
      -1.0  → deep green (dense vegetation)
      -0.3  → light green (sparse vegetation)
       0.0  → pale yellow (transition)
       0.2  → tan (mild bare soil)
       0.5  → brown (moderate bare soil)
       1.0  → dark brown (severe bare soil / desert)
    """
    h, w = bsi.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    valid = ~np.isnan(bsi)
    rgba[:, :, 3] = np.where(valid, 255, 0)

    clamped = np.clip(bsi, -1.0, 1.0)

    # Soil-themed color stops: [BSI_value, R, G, B]
    stops = np.array([
        [-1.00,   0, 100,   0],   # deep green — dense vegetation
        [-0.30,  80, 160,  40],   # medium green — vegetation
        [ 0.00, 220, 210, 120],   # pale yellow — transition zone
        [ 0.15, 200, 170,  90],   # light tan — mild bare soil
        [ 0.30, 185, 140,  60],   # tan — moderate bare soil
        [ 0.50, 160, 100,  30],   # brown — bare soil
        [ 0.70, 130,  70,  15],   # dark brown — severe bare soil
        [ 1.00,  90,  40,   5],   # very dark brown — desert
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


def compute_bsi_image_with_bounds(year: int) -> Tuple[bytes, dict]:
    """Fetch → BSI → colormap → PNG bytes + geo bounds."""
    blue, red, nir, swir1, bounds = fetch_bsi_bands(year)
    bsi = calc_bsi(blue, red, nir, swir1)
    cache_set(("BSI", year, None), bsi, bounds)
    rgba = apply_colormap_bsi(bsi)

    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue(), bounds
