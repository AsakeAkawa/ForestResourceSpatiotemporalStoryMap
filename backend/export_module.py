"""
Export module: GeoTIFF / PNG thematic map / PDF area report.
Recomputes raw data at higher resolution for export quality.
"""
import io
import math
from typing import Tuple, Optional, Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import rasterio
from rasterio.io import MemoryFile

from config import KUBUQI_BBOX, WCS_URL, BAND_MAP, WET_COEFFS, get_satellite_era, get_layer_name
from cache import get as cache_get, set as cache_set

# Higher resolution for export
EXPORT_W = 1400
EXPORT_H = 480

# Per-indicator classification bins matching frontend legends
# Each: list of (threshold, label, color_hex)
BINS = {
    "NDVI": [
        (-1.00, "< -0.2", "#6e4000"),    # (110,64,0)
        (-0.20, "-0.2 ~ 0.0", "#b58a2e"), # (181,138,46)
        ( 0.00, "0.0 ~ 0.15", "#e6c850"), # (230,200,80)
        ( 0.15, "0.15 ~ 0.3", "#b4d264"), # (180,210,100)
        ( 0.30, "0.3 ~ 0.5", "#78b43c"),  # (120,180,60)
        ( 0.50, "0.5 ~ 0.7", "#328c1e"),  # (50,140,30)
        ( 0.70, "0.7 ~ 1.0", "#0f4610"),  # (10,100,20)
        ( 1.00, "1.0",       "#003c0a"),  # (0,60,10)
    ],
    "FVC": [
        (0.00, "0.0 ~ 0.1  裸土",     "#b4965a"),
        (0.10, "0.1 ~ 0.25  稀疏植被", "#c3b964"),
        (0.25, "0.25 ~ 0.4  低覆盖",   "#91be46"),
        (0.40, "0.40 ~ 0.6  中覆盖",   "#50aa32"),
        (0.60, "0.60 ~ 0.8  高覆盖",   "#1e8c28"),
        (0.80, "0.80 ~ 1.0  全覆盖",   "#003c14"),
    ],
    "NDWI": [
        (-1.00, "< -0.4  旱地",        "#82501e"),
        (-0.40, "-0.4 ~ -0.1  较干",   "#c8aa78"),
        (-0.10, "-0.1 ~ 0.0  湿润过渡", "#e6e1c8"),
        ( 0.00, "0.00 ~ 0.15  浅水/湿地","#c8dceb"),
        ( 0.15, "0.15 ~ 0.40  水体",    "#64b4e6"),
        ( 0.40, "0.40 ~ 0.70  深水",    "#0a46d2"),
        ( 0.70, "0.70 ~ 1.0  极深水",   "#051e64"),
    ],
    "BSI": [
        (-1.00, "< -0.3  茂密植被",    "#006400"),
        (-0.30, "-0.3 ~ 0.0  植被区",  "#50a028"),
        ( 0.00, "0.00 ~ 0.15  过渡带",  "#dcd278"),
        ( 0.15, "0.15 ~ 0.30  轻度裸土","#c8aa5a"),
        ( 0.30, "0.30 ~ 0.50  中度裸土","#b98c3c"),
        ( 0.50, "0.50 ~ 0.70  重度裸土","#a0461e"),
        ( 0.70, "0.70 ~ 1.0  荒漠",     "#5a2805"),
    ],
    "RSEI": [
        (0.00, "0.00 ~ 0.15  严重退化","#b41e0f"),
        (0.15, "0.15 ~ 0.30  退化",    "#e6821e"),
        (0.30, "0.30 ~ 0.45  中等",    "#f5d23c"),
        (0.45, "0.45 ~ 0.60  一般",    "#d2dc50"),
        (0.60, "0.60 ~ 0.75  良好",    "#78c837"),
        (0.75, "0.75 ~ 0.90  优良",    "#28a028"),
        (0.90, "0.90 ~ 1.0  极优",     "#054614"),
    ],
    "CHANGE": [
        (-1.00, "< -0.20  显著退化",   "#b40a0a"),
        (-0.20, "-0.20 ~ -0.10  退化",  "#eb5050"),
        (-0.10, "-0.10 ~ -0.03  轻微退化","#faae8c"),
        (-0.03, "-0.03 ~ 0.00  微退化", "#fceee6"),
        ( 0.00, "0.00 ~ 0.03  稳定",    "#f5f5f5"),
        ( 0.03, "0.03 ~ 0.10  轻微改善","#e1f2dc"),
        ( 0.10, "0.10 ~ 0.20  改善",    "#a0e182"),
        ( 0.20, "0.20 ~ 1.0  显著改善", "#32b432"),
    ],
}

# ─── raw data pipelines ───────────────────────────────────────────────

def _fetch(year: int, band_names: list[str]):
    """Generic fetch: WCS → {name: 2D float32 array}, bounds. Subset of bands."""
    era = get_satellite_era(year)
    bm = BAND_MAP[era]
    layer = get_layer_name(year)
    import urllib.request
    params = (
        f"SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage"
        f"&COVERAGEID={layer}&FORMAT=image/tiff"
        f"&SUBSET=Lat({KUBUQI_BBOX['miny']},{KUBUQI_BBOX['maxy']})"
        f"&SUBSET=Long({KUBUQI_BBOX['minx']},{KUBUQI_BBOX['maxx']})"
        f"&SCALESIZE=i({EXPORT_W}),j({EXPORT_H})"
    )
    url = f"{WCS_URL}?{params}"
    with urllib.request.urlopen(url, timeout=120) as resp:
        data = resp.read()
    with rasterio.open(io.BytesIO(data)) as src:
        arrays = {}
        for name in band_names:
            arr = src.read(bm[name]).astype(np.float32)
            mask = (arr > -0.1) & (arr < 10)
            arrays[name] = np.where(mask, arr, np.nan)
        return arrays, {
            "west": src.bounds.left, "south": src.bounds.bottom,
            "east": src.bounds.right, "north": src.bounds.top,
            "width": src.width, "height": src.height,
        }


def _ndvi_raw(year: int):
    """Return (ndvi, bounds)."""
    bands, bounds = _fetch(year, ["red", "nir"])
    with np.errstate(all='ignore'):
        r, n = bands["red"], bands["nir"]
        denom = r + n
        ndvi = np.where(denom > 0, (n - r) / denom, np.nan).astype(np.float32)
    return ndvi, bounds


def _fvc_raw(year: int):
    ndvi, bounds = _ndvi_raw(year)
    valid = ndvi[~np.isnan(ndvi)]
    lo, hi = np.percentile(valid, 5), np.percentile(valid, 95)
    if hi - lo < 0.01: hi = lo + 0.01
    fvc = np.clip((ndvi - lo) / (hi - lo), 0, 1).astype(np.float32)
    return fvc, bounds


def _bsi_raw(year: int):
    bands, bounds = _fetch(year, ["blue", "red", "nir", "swir1"])
    with np.errstate(all='ignore'):
        b, r, n, s = bands["blue"], bands["red"], bands["nir"], bands["swir1"]
        num = (s + r) - (n + b)
        denom = (s + r) + (n + b)
        bsi = np.where(denom > 0, num / denom, np.nan).astype(np.float32)
    return bsi, bounds


def _ndwi_raw(year: int):
    bands, bounds = _fetch(year, ["green", "nir"])
    with np.errstate(all='ignore'):
        g, n = bands["green"], bands["nir"]
        denom = g + n
        ndwi = np.where(denom > 0, (g - n) / denom, np.nan).astype(np.float32)
    return ndwi, bounds


def _rsei_raw(year: int):
    era = get_satellite_era(year)
    bands, bounds = _fetch(year, ["blue", "green", "red", "nir", "swir1", "swir2"])
    with np.errstate(all='ignore'):
        r, n = bands["red"], bands["nir"]
        ndvi = np.where((r+n)>0, (n-r)/(r+n), np.nan)

        coeffs = WET_COEFFS[era]
        wet = np.zeros_like(bands["blue"])
        for k, v in coeffs.items(): wet += v * bands[k]

        b, g, s1 = bands["blue"], bands["green"], bands["swir1"]
        bsi_num = (s1+r)-(n+b); bsi_den = (s1+r)+(n+b)
        bsi = np.where(bsi_den>0, bsi_num/bsi_den, np.nan)
        ta = 2*s1/(s1+n+1e-6); tb = n/(n+r+1e-6); tc = g/(g+s1+1e-6)
        ibi = (ta-tb-tc)/(ta+tb+tc+1e-6)
        ndbsi = (bsi+ibi)/2.0

    def norm(arr):
        v=arr[~np.isnan(arr)]; lo,hi=np.percentile(v,2),np.percentile(v,98)
        if hi-lo<1e-8: return np.zeros_like(arr)
        return np.clip((arr-lo)/(hi-lo),0,1)

    ndvi_n, wet_n, ndbsi_n = norm(ndvi), norm(wet), norm(ndbsi)
    ndbsi_n = 1.0-ndbsi_n
    valid = (~np.isnan(ndvi_n))&(~np.isnan(wet_n))&(~np.isnan(ndbsi_n))
    nv = valid.sum()
    if nv<3: raise ValueError("too few valid pixels for RSEI PCA")
    stack = np.empty((3,nv),np.float32)
    stack[0]=ndvi_n[valid];stack[1]=wet_n[valid];stack[2]=ndbsi_n[valid]
    mean=stack.mean(1,keepdims=True);cen=stack-mean
    cov=(cen@cen.T)/(nv-1)
    ev,evec=np.linalg.eigh(cov);pc1=evec[:,-1]@cen
    pc1_n=norm(pc1);rsei_1d=1.0-pc1_n
    rsei=np.full(ndvi.shape,np.nan,np.float32)
    rsei[valid]=rsei_1d
    return rsei,bounds


def _change_raw(year1: int, year2: int):
    ndvi1, bounds = _ndvi_raw(year1)
    ndvi2, _ = _ndvi_raw(year2)
    # shape may differ by 1px — trim
    h, w = min(ndvi1.shape[0], ndvi2.shape[0]), min(ndvi1.shape[1], ndvi2.shape[1])
    ndvi1, ndvi2 = ndvi1[:h,:w], ndvi2[:h,:w]
    valid = (~np.isnan(ndvi1)) & (~np.isnan(ndvi2))
    chg = np.full_like(ndvi1, np.nan, np.float32)
    chg[valid] = ndvi2[valid] - ndvi1[valid]
    bounds["width"], bounds["height"] = w, h
    return chg, bounds


DATA_SOURCES: dict[str, Callable] = {
    "NDVI": lambda y,_y2: _ndvi_raw(y),
    "FVC":  lambda y,_y2: _fvc_raw(y),
    "NDWI": lambda y,_y2: _ndwi_raw(y),
    "BSI":  lambda y,_y2: _bsi_raw(y),
    "RSEI": lambda y,_y2: _rsei_raw(y),
    "CHANGE": lambda y1,y2: _change_raw(y1, y2),
}

def _cached_source(indicator, year, year2=None):
    """Check memory cache first; if hit, return (data, bounds). Otherwise recompute and cache."""
    key = (indicator, year, year2)
    cached = cache_get(key)
    if cached is not None:
        return cached
    data, bounds = DATA_SOURCES[indicator](year, year2)
    cache_set(key, data, bounds)
    return data, bounds

# ─── colormap rendering (export quality PNG) ──────────────────────────

def _hex_to_rgb(h: str) -> tuple:
    return int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)

def _render_with_legend(data: np.ndarray, bins: list, title: str) -> bytes:
    """Render float data as RGBA with a legend bar at bottom."""
    h, w = data.shape
    bar_h = 60
    out_h = h + bar_h
    rgba = np.full((out_h, w, 4), 255, dtype=np.uint8)

    # Colormap using bins thresholds + hex colors
    valid = ~np.isnan(data)
    colors = [_hex_to_rgb(b[2]) for b in bins]

    for i in range(len(bins) - 1):
        v0, v1 = bins[i][0], bins[i+1][0]
        if i == len(bins) - 2:
            mask = valid & (data >= v0)  # last segment: include upper bound
        else:
            mask = valid & (data >= v0) & (data < v1)
        yy, xx = np.where(mask)
        t = (data[mask] - v0) / (v1 - v0 + 1e-10)
        for ch in range(3):
            c0, c1 = float(colors[i][ch]), float(colors[i+1][ch])
            rgba[yy, xx, ch] = np.clip(c0 + t * (c1 - c0), 0, 255).astype(np.uint8)

    # Alpha: transparent where no data was assigned (still white + no valid pixel)
    assigned = np.any(rgba[:h,:,:3] > 0, axis=2)
    rgba[:h, :, 3] = np.where(assigned, 255, 0)

    # Legend bar
    y0, y1 = h, out_h
    seg_w = w // (len(bins)-1)
    for i in range(len(bins)-1):
        x0, x1 = i*seg_w, (i+1)*seg_w
        rgba[y0:y1, x0:x1, :3] = np.array(colors[i], dtype=np.uint8)

    img = Image.fromarray(rgba, mode="RGBA")
    draw = ImageDraw.Draw(img)
    # 尝试加载中文字体（Windows / Linux / macOS）
    font = font_sm = None
    for fp in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
               "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
               "/System/Library/Fonts/PingFang.ttc"]:
        try:
            font = ImageFont.truetype(fp, 16)
            font_sm = ImageFont.truetype(fp, 12)
            break
        except:
            continue
    if font is None:
        font = font_sm = ImageFont.load_default()

    draw.text((10, h+6), title, fill=(0,0,0), font=font)
    # 图例数值标注：在每个色段边界下方标注阈值
    for i, b in enumerate(bins):
        x = int(i * w / (len(bins) - 1))
        x = max(5, min(x, w - 50))  # 防止文字溢出
        label = f"{b[0]:.2f}" if abs(b[0]) < 10 else str(int(b[0]))
        draw.text((x, h + 34), label, fill=(0,0,0), font=font_sm)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ─── GeoTIFF export ───────────────────────────────────────────────────

def export_geotiff(indicator: str, year: int, year2: int = None) -> bytes:
    data, bounds = _cached_source(indicator, year, year2)
    profile = {
        "driver": "GTiff", "height": data.shape[0], "width": data.shape[1],
        "count": 1, "dtype": np.float32, "crs": "EPSG:4326",
        "transform": rasterio.transform.from_bounds(
            bounds["west"], bounds["south"], bounds["east"], bounds["north"],
            bounds["width"], bounds["height"],
        ),
        "nodata": -9999.0, "compress": "lzw",
    }
    buf = io.BytesIO()
    with MemoryFile() as mem:
        with mem.open(**profile) as dst:
            dst.write(np.where(np.isnan(data), -9999.0, data).astype(np.float32), 1)
        buf.write(mem.read())
    return buf.getvalue()


# ─── PNG themed map export ────────────────────────────────────────────

def export_png(indicator: str, year: int, year2: int = None) -> bytes:
    data, bounds = _cached_source(indicator, year, year2)
    bins = BINS[indicator]
    title = f"{indicator} {year}" if year2 is None else f"{indicator} Change {year}-{year2}"
    return _render_with_legend(data, bins, title)


# ─── PDF area report ──────────────────────────────────────────────────

def export_pdf(indicator: str, year: int, year2: int = None) -> bytes:
    data, bounds = _cached_source(indicator, year, year2)
    bins = BINS[indicator]
    # Build ASCII-safe short labels for PDF (no CJK)
    short_bins = []
    for lo, label, color_hex in bins:
        parts = label.split()
        short_name = parts[0] if parts else label  # first token = numeric range
        short_bins.append((lo, short_name, color_hex))
    bins = short_bins
    valid = data[~np.isnan(data)]

    # Pixel area in m2
    lat_center = (bounds["north"] + bounds["south"]) / 2
    m_per_deg_lon = 111320 * math.cos(math.radians(lat_center))
    m_per_deg_lat = 111320
    lon_span = bounds["east"] - bounds["west"]
    lat_span = bounds["north"] - bounds["south"]
    px_area_m2 = (lon_span * m_per_deg_lon / bounds["width"]) * (lat_span * m_per_deg_lat / bounds["height"])
    px_area_km2 = px_area_m2 / 1e6

    # Classify & count
    rows = []
    for i in range(len(bins)-1):
        lo, hi = bins[i][0], bins[i+1][0]
        if i == len(bins)-2:
            mask = (valid >= lo) & (valid <= hi + 0.1)
        else:
            mask = (valid >= lo) & (valid < hi)
        count = mask.sum()
        area_km2 = count * px_area_km2
        pct = count / len(valid) * 100 if len(valid) > 0 else 0
        label = bins[i][1]
        color = bins[i][2]
        rows.append({"label": label, "count": count, "area_km2": area_km2, "pct": pct, "color": color})

    total_area = sum(r["area_km2"] for r in rows)

    # Build PDF with matplotlib (single page report)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(11, 8.5), dpi=200)
    fig.patch.set_facecolor("white")

    # Title
    yr_str = f"{year}" if year2 is None else f"{year} → {year2}"
    fig.suptitle(f"Forest RS Analysis — {indicator} Area Report\nYear: {yr_str}  |  Region: Kubuqi Desert",
                 fontsize=14, fontweight="bold", y=0.96)

    # Table
    col_labels = ["Class", "Pixels", "Area (km²)", "Percent", "Color"]
    cell_text = []
    cell_colors_c = []
    for r in rows:
        cell_text.append([r["label"], f'{r["count"]:,}', f'{r["area_km2"]:.1f}', f'{r["pct"]:.1f}%', ""])
        hex_c = r["color"]
        cell_colors_c.append(["#ffffff","#ffffff","#ffffff","#ffffff", hex_c])

    ax_table = fig.add_axes([0.05, 0.45, 0.9, 0.45])
    ax_table.axis("off")
    table = ax_table.table(cellText=cell_text, colLabels=col_labels, cellColours=cell_colors_c,
                           loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.8)
    # Header styling
    for j in range(len(col_labels)):
        table[0,j].set_facecolor("#333333")
        table[0,j].set_text_props(color="white", fontweight="bold")

    # Summary stats
    ax_stats = fig.add_axes([0.05, 0.30, 0.9, 0.12])
    ax_stats.axis("off")
    stats_text = (
        f"Total Valid Pixels: {len(valid):,}    |    "
        f"Pixel Resolution: {int(bounds['width'])} × {int(bounds['height'])}    |    "
        f"Pixel Area: {px_area_km2:.4f} km²    |    "
        f"Total Area: {total_area:.1f} km²"
    )
    ax_stats.text(0.5, 0.5, stats_text, transform=ax_stats.transAxes,
                  ha="center", va="center", fontsize=9, fontfamily="monospace")

    # Colormap bar
    ax_bar = fig.add_axes([0.15, 0.18, 0.70, 0.04])
    bar_colors = [_hex_to_rgb(b[2]) for b in bins]
    bar_colors = [(c[0]/255, c[1]/255, c[2]/255) for c in bar_colors]
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    ax_bar.imshow(gradient, aspect="auto", cmap=matplotlib.colors.ListedColormap(bar_colors))
    ax_bar.set_xticks([0, 128, 255])
    ax_bar.set_xticklabels([bins[0][1].split()[0], "0", bins[-1][1].split()[-1]], fontsize=8)
    ax_bar.set_yticks([])

    # Footer
    ax_footer = fig.add_axes([0.05, 0.08, 0.9, 0.06])
    ax_footer.axis("off")
    ax_footer.text(0.5, 0.5, "Generated by Forest RS Analysis System  |  Data: Landsat via GeoServer WCS",
                   transform=ax_footer.transAxes, ha="center", va="center", fontsize=8, color="gray")

    buf = io.BytesIO()
    fig.savefig(buf, format="pdf", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
