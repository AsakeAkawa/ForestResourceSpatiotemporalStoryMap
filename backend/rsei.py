"""
RSEI (Remote Sensing Ecological Index) from Landsat imagery.

Combines three ecological indicators via Principal Component Analysis (PCA):

    NDVI  — greenness  (Normalized Difference Vegetation Index)
    WET   — wetness    (Tasseled Cap Wetness component)
    NDBSI — dryness    (mean of BSI + IBI, soil & built-up index)

RSEI = 1 - PC1[f(NDVI, WET, NDBSI)]

Reference: Xu Hanqiu (2013) — "A remote sensing urban ecological index"

Note: LST (heat) is omitted because thermal band data is not available
      in the current 6-band COG setup.
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
    WET_COEFFS,
    get_satellite_era,
    get_layer_name,
)
from cache import set as cache_set

WEB_W = 700
WEB_H = 240


# ---------------------------------------------------------------------------
# 1. Data fetching
# ---------------------------------------------------------------------------

def fetch_all_bands(year: int) -> Tuple[dict, dict]:
    """
    Fetch all 6 bands (Blue, Green, Red, NIR, SWIR1, SWIR2)
    at web resolution from GeoServer WCS.

    Returns (bands_dict, bounds_dict).
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

    with urllib.request.urlopen(url, timeout=30) as resp:
        data = resp.read()

    with rasterio.open(io.BytesIO(data)) as src:
        bands = {}
        for name in ["blue", "green", "red", "nir", "swir1", "swir2"]:
            arr = src.read(band_map[name]).astype(np.float32)
            bands[name] = arr

        # Shared validity mask (exclude NoData / extreme values)
        mask = None
        for arr in bands.values():
            m = (arr > -0.1) & (arr < 10)
            mask = m if mask is None else mask & m

        for name in bands:
            bands[name] = np.where(mask, bands[name], np.nan)

        bounds = {
            "west": src.bounds.left,
            "south": src.bounds.bottom,
            "east": src.bounds.right,
            "north": src.bounds.top,
            "width": src.width,
            "height": src.height,
        }

    return bands, bounds


# ---------------------------------------------------------------------------
# 2. Ecological indicators
# ---------------------------------------------------------------------------

def calc_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """NDVI = (NIR - Red) / (NIR + Red)"""
    with np.errstate(all='ignore'):
        denom = nir + red
        ndvi = np.where(denom > 0, (nir - red) / denom, np.nan)
        ndvi[(red > 1.5) | (nir > 1.5) | (red < -0.1) | (nir < -0.1)] = np.nan
    return ndvi.astype(np.float32)


def calc_wet(bands: dict, era: str) -> np.ndarray:
    """
    Tasseled Cap Wetness component.

    L5:  WET =  0.0315*B + 0.2021*G + 0.3102*R
               + 0.1594*NIR - 0.6806*SWIR1 - 0.6109*SWIR2
    L8+: WET =  0.1511*B + 0.1973*G + 0.3283*R
               + 0.3407*NIR - 0.7117*SWIR1 - 0.4559*SWIR2
    """
    coeffs = WET_COEFFS[era]
    wet = np.zeros_like(bands["blue"], dtype=np.float32)
    for name in ["blue", "green", "red", "nir", "swir1", "swir2"]:
        wet += coeffs[name] * bands[name]
    return wet


def calc_ndbsi(bands: dict) -> np.ndarray:
    """
    NDBSI = (BSI + IBI) / 2

    BSI = ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))

    IBI = (2*SWIR1/(SWIR1+NIR) - NIR/(NIR+Red) - Green/(Green+SWIR1))
        / (2*SWIR1/(SWIR1+NIR) + NIR/(NIR+Red) + Green/(Green+SWIR1))
    """
    blue = bands["blue"]
    green = bands["green"]
    red = bands["red"]
    nir = bands["nir"]
    swir1 = bands["swir1"]

    with np.errstate(all='ignore'):
        # --- BSI ---
        bsi_num = (swir1 + red) - (nir + blue)
        bsi_den = (swir1 + red) + (nir + blue)
        bsi = np.where(bsi_den > 0, bsi_num / bsi_den, np.nan)

        # --- IBI ---
        term_a = 2.0 * swir1 / (swir1 + nir + 1e-6)
        term_b = nir / (nir + red + 1e-6)
        term_c = green / (green + swir1 + 1e-6)
        ibi = (term_a - term_b - term_c) / (term_a + term_b + term_c + 1e-6)

        # --- NDBSI ---
        ndbsi = (bsi + ibi) / 2.0

    return ndbsi.astype(np.float32)


# ---------------------------------------------------------------------------
# 3. Normalization & PCA
# ---------------------------------------------------------------------------

def min_max_normalize(arr: np.ndarray) -> np.ndarray:
    """Normalize to [0, 1] using 2nd–98th percentile range for robustness."""
    valid = arr[~np.isnan(arr)]
    if len(valid) == 0:
        return arr
    lo = float(np.percentile(valid, 2))
    hi = float(np.percentile(valid, 98))
    if hi - lo < 1e-8:
        return np.zeros_like(arr)
    return np.clip((arr - lo) / (hi - lo), 0.0, 1.0)


def pca_first_component(stack: np.ndarray) -> np.ndarray:
    """
    Perform PCA on (K, N) data array, return the FIRST principal component
    as a 1D array of length N.

    stack: (K, N) — K indicators, N valid pixels, each row normalized to [0, 1]
    """
    k, n = stack.shape
    # Center the data
    mean = stack.mean(axis=1, keepdims=True)
    centered = stack - mean

    # Covariance matrix (K, K)
    cov = (centered @ centered.T) / (n - 1)

    # Eigendecomposition
    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    # Sort by eigenvalue descending
    idx = np.argsort(eigenvalues)[::-1]
    eigenvectors = eigenvectors[:, idx]

    # First principal component: project data onto PC1
    pc1 = eigenvectors[:, 0] @ centered  # (N,)

    return pc1


# ---------------------------------------------------------------------------
# 4. Colormap
# ---------------------------------------------------------------------------

def apply_colormap_rsei(rsei: np.ndarray) -> np.ndarray:
    """
    RSEI → RGBA via ecological-quality gradient. Returns (H, W, 4) uint8.

    Colormap (0 = poor ecology → 1 = excellent ecology):
      0.00 → dark red    (severely degraded)
      0.15 → orange      (degraded)
      0.35 → yellow      (moderate)
      0.55 → light green (good)
      0.75 → green       (very good)
      1.00 → dark green  (excellent)
    """
    h, w = rsei.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    valid = ~np.isnan(rsei)
    rgba[:, :, 3] = np.where(valid, 255, 0)

    clamped = np.clip(rsei, 0.0, 1.0)

    stops = np.array([
        [0.00, 180,  30,  15],   # dark red — severely degraded
        [0.15, 230, 130,  30],   # orange — degraded
        [0.30, 245, 210,  60],   # yellow — below average
        [0.45, 210, 220,  80],   # yellow-green — moderate
        [0.60, 120, 200,  55],   # light green — good
        [0.75,  40, 160,  40],   # green — very good
        [0.90,  10, 110,  30],   # dark green — excellent
        [1.00,   5,  70,  20],   # deep forest green — pristine
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


# ---------------------------------------------------------------------------
# 5. Main entry point
# ---------------------------------------------------------------------------

def compute_rsei_image_with_bounds(year: int) -> Tuple[bytes, dict]:
    """
    Full RSEI pipeline:

    1. Fetch all 6 bands from GeoServer WCS
    2. Compute NDVI (greenness), WET (wetness), NDBSI (dryness)
    3. Normalize each indicator to [0, 1]
    4. PCA → extract first principal component
    5. RSEI = 1 - PC1_norm  (higher = better ecology)
    6. Apply colormap → PNG
    """
    era = get_satellite_era(year)
    bands, bounds = fetch_all_bands(year)

    # Compute three ecological indicators
    ndvi = calc_ndvi(bands["red"], bands["nir"])
    wet = calc_wet(bands, era)
    ndbsi = calc_ndbsi(bands)

    # Normalize to [0, 1]
    ndvi_n = min_max_normalize(ndvi)
    wet_n = min_max_normalize(wet)
    ndbsi_n = min_max_normalize(ndbsi)

    # For NDBSI, higher = more degraded, so invert: 1 - ndbsi_n
    # (so all three indicators point in the same direction: higher = better)
    ndbsi_n = 1.0 - ndbsi_n

    # Stack valid pixels for PCA
    valid = (~np.isnan(ndvi_n)) & (~np.isnan(wet_n)) & (~np.isnan(ndbsi_n))
    if valid.sum() < 3:
        raise ValueError(f"Too few valid pixels ({valid.sum()}) for PCA on year {year}")

    n_valid = valid.sum()
    stack = np.empty((3, n_valid), dtype=np.float32)
    stack[0] = ndvi_n[valid]
    stack[1] = wet_n[valid]
    stack[2] = ndbsi_n[valid]

    # PCA → PC1
    pc1_1d = pca_first_component(stack)

    # Normalize PC1 to [0, 1]
    pc1_1d_n = min_max_normalize(pc1_1d)

    # RSEI = 1 - PC1  (so higher RSEI = better ecology)
    rsei_1d = 1.0 - pc1_1d_n

    # Reshape back to image
    rsei = np.full(ndvi.shape, np.nan, dtype=np.float32)
    rsei[valid] = rsei_1d

    cache_set(("RSEI", year, None), rsei, bounds)
    # Colormap → PNG
    rgba = apply_colormap_rsei(rsei)
    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)

    return buf.getvalue(), bounds
