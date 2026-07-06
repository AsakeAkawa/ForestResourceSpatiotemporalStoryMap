"""
Forest Resource Spatiotemporal StoryMap — Backend API
Provides real-time remote sensing analysis: NDVI, FVC, NDWI, BSI, RSEI, and change detection.
"""
import io
import traceback

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse

from ndvi import compute_ndvi_image_with_bounds
from bsi import compute_bsi_image_with_bounds
from fvc import compute_fvc_image_with_bounds
from ndwi import compute_ndwi_image_with_bounds
from rsei import compute_rsei_image_with_bounds
from change_detection import compute_change_image_with_bounds
from export_module import export_geotiff, export_png, export_pdf
from config import KUBUQI_BBOX, get_layer_name

app = FastAPI(
    title="Forest RS Analysis API",
    description="Real-time remote sensing ecological index computation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/bounds")
async def bounds():
    """Return the Kubuqi area bounding box for frontend overlay positioning."""
    return {
        "bbox": KUBUQI_BBOX,
        "years_available": list(range(1986, 1996)) + list(range(2015, 2025)),
    }


@app.get("/api/ndvi/{year}")
async def ndvi_get(year: int):
    """
    Compute NDVI for a given year and return the rendered PNG image.
    Geo bounds are returned in the X-Bounds-West/South/East/North response headers.
    """
    try:
        png_bytes, bounds = compute_ndvi_image_with_bounds(year)
        headers = {
            "X-Bounds-West": str(bounds["west"]),
            "X-Bounds-South": str(bounds["south"]),
            "X-Bounds-East": str(bounds["east"]),
            "X-Bounds-North": str(bounds["north"]),
            "X-Image-Width": str(bounds["width"]),
            "X-Image-Height": str(bounds["height"]),
        }
        return Response(content=png_bytes, media_type="image/png", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ndvi")
async def ndvi_post(year: int = Query(..., description="Target year")):
    """
    POST endpoint for NDVI computation.
    Returns PNG image with bounds in headers.
    """
    try:
        png_bytes, bounds = compute_ndvi_image_with_bounds(year)
        headers = {
            "X-Bounds-West": str(bounds["west"]),
            "X-Bounds-South": str(bounds["south"]),
            "X-Bounds-East": str(bounds["east"]),
            "X-Bounds-North": str(bounds["north"]),
            "X-Image-Width": str(bounds["width"]),
            "X-Image-Height": str(bounds["height"]),
        }
        return Response(content=png_bytes, media_type="image/png", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bsi/{year}")
async def bsi_get(year: int):
    """
    Compute BSI (Bare Soil Index) for a given year and return the rendered PNG image.
    Geo bounds are returned in the X-Bounds-West/South/East/North response headers.
    """
    try:
        png_bytes, bounds = compute_bsi_image_with_bounds(year)
        headers = {
            "X-Bounds-West": str(bounds["west"]),
            "X-Bounds-South": str(bounds["south"]),
            "X-Bounds-East": str(bounds["east"]),
            "X-Bounds-North": str(bounds["north"]),
            "X-Image-Width": str(bounds["width"]),
            "X-Image-Height": str(bounds["height"]),
        }
        return Response(content=png_bytes, media_type="image/png", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bsi")
async def bsi_post(year: int = Query(..., description="Target year")):
    """
    POST endpoint for BSI computation.
    Returns PNG image with bounds in headers.
    """
    try:
        png_bytes, bounds = compute_bsi_image_with_bounds(year)
        headers = {
            "X-Bounds-West": str(bounds["west"]),
            "X-Bounds-South": str(bounds["south"]),
            "X-Bounds-East": str(bounds["east"]),
            "X-Bounds-North": str(bounds["north"]),
            "X-Image-Width": str(bounds["width"]),
            "X-Image-Height": str(bounds["height"]),
        }
        return Response(content=png_bytes, media_type="image/png", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fvc/{year}")
async def fvc_get(year: int):
    """
    Compute FVC (Fractional Vegetation Cover) for a given year and return the rendered PNG image.
    Geo bounds are returned in the X-Bounds-West/South/East/North response headers.
    """
    try:
        png_bytes, bounds = compute_fvc_image_with_bounds(year)
        headers = {
            "X-Bounds-West": str(bounds["west"]),
            "X-Bounds-South": str(bounds["south"]),
            "X-Bounds-East": str(bounds["east"]),
            "X-Bounds-North": str(bounds["north"]),
            "X-Image-Width": str(bounds["width"]),
            "X-Image-Height": str(bounds["height"]),
        }
        return Response(content=png_bytes, media_type="image/png", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fvc")
async def fvc_post(year: int = Query(..., description="Target year")):
    """
    POST endpoint for FVC computation.
    Returns PNG image with bounds in headers.
    """
    try:
        png_bytes, bounds = compute_fvc_image_with_bounds(year)
        headers = {
            "X-Bounds-West": str(bounds["west"]),
            "X-Bounds-South": str(bounds["south"]),
            "X-Bounds-East": str(bounds["east"]),
            "X-Bounds-North": str(bounds["north"]),
            "X-Image-Width": str(bounds["width"]),
            "X-Image-Height": str(bounds["height"]),
        }
        return Response(content=png_bytes, media_type="image/png", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ndwi/{year}")
async def ndwi_get(year: int):
    """
    Compute NDWI (Normalized Difference Water Index) for a given year and return the rendered PNG image.
    Geo bounds are returned in the X-Bounds-West/South/East/North response headers.
    """
    try:
        png_bytes, bounds = compute_ndwi_image_with_bounds(year)
        headers = {
            "X-Bounds-West": str(bounds["west"]),
            "X-Bounds-South": str(bounds["south"]),
            "X-Bounds-East": str(bounds["east"]),
            "X-Bounds-North": str(bounds["north"]),
            "X-Image-Width": str(bounds["width"]),
            "X-Image-Height": str(bounds["height"]),
        }
        return Response(content=png_bytes, media_type="image/png", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ndwi")
async def ndwi_post(year: int = Query(..., description="Target year")):
    """
    POST endpoint for NDWI computation.
    Returns PNG image with bounds in headers.
    """
    try:
        png_bytes, bounds = compute_ndwi_image_with_bounds(year)
        headers = {
            "X-Bounds-West": str(bounds["west"]),
            "X-Bounds-South": str(bounds["south"]),
            "X-Bounds-East": str(bounds["east"]),
            "X-Bounds-North": str(bounds["north"]),
            "X-Image-Width": str(bounds["width"]),
            "X-Image-Height": str(bounds["height"]),
        }
        return Response(content=png_bytes, media_type="image/png", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rsei/{year}")
async def rsei_get(year: int):
    """
    Compute RSEI (Remote Sensing Ecological Index) for a given year
    and return the rendered PNG image.
    Geo bounds are returned in the X-Bounds-West/South/East/North response headers.
    """
    try:
        png_bytes, bounds = compute_rsei_image_with_bounds(year)
        headers = {
            "X-Bounds-West": str(bounds["west"]),
            "X-Bounds-South": str(bounds["south"]),
            "X-Bounds-East": str(bounds["east"]),
            "X-Bounds-North": str(bounds["north"]),
            "X-Image-Width": str(bounds["width"]),
            "X-Image-Height": str(bounds["height"]),
        }
        return Response(content=png_bytes, media_type="image/png", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rsei")
async def rsei_post(year: int = Query(..., description="Target year")):
    """
    POST endpoint for RSEI computation.
    Returns PNG image with bounds in headers.
    """
    try:
        png_bytes, bounds = compute_rsei_image_with_bounds(year)
        headers = {
            "X-Bounds-West": str(bounds["west"]),
            "X-Bounds-South": str(bounds["south"]),
            "X-Bounds-East": str(bounds["east"]),
            "X-Bounds-North": str(bounds["north"]),
            "X-Image-Width": str(bounds["width"]),
            "X-Image-Height": str(bounds["height"]),
        }
        return Response(content=png_bytes, media_type="image/png", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/change/{year1}/{year2}")
async def change_get(year1: int, year2: int):
    """
    Compute NDVI change between two years.
    Returns a divergence-colormap PNG (red=degradation, green=improvement).
    Geo bounds are returned in the X-Bounds-* response headers.
    """
    try:
        png_bytes, bounds = compute_change_image_with_bounds(year1, year2)
        headers = {
            "X-Bounds-West": str(bounds["west"]),
            "X-Bounds-South": str(bounds["south"]),
            "X-Bounds-East": str(bounds["east"]),
            "X-Bounds-North": str(bounds["north"]),
            "X-Image-Width": str(bounds["width"]),
            "X-Image-Height": str(bounds["height"]),
        }
        return Response(content=png_bytes, media_type="image/png", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export")
async def export_data(
    format: str = Query(..., description="TIFF | PNG | PDF"),
    indicator: str = Query(..., description="NDVI | FVC | NDWI | BSI | RSEI | CHANGE"),
    year: int = Query(..., description="Target year (or start year for CHANGE)"),
    year2: int = Query(None, description="End year (required for CHANGE indicator)"),
):
    """
    Export analysis result in the requested format.

    - TIFF: GeoTIFF (single-band float32, LZW compressed)
    - PNG:  PNG thematic map with colorbar legend
    - PDF:  Area statistics report with classification table
    """
    fmt = format.upper()
    ind = indicator.upper()
    try:
        if fmt == "TIFF":
            if ind == "CHANGE" and year2 is None:
                raise HTTPException(400, "CHANGE requires both year and year2")
            data = export_geotiff(ind, year, year2)
            filename = f"{ind}_{year}.tif" if ind != "CHANGE" else f"CHANGE_{year}_{year2}.tif"
            return Response(content=data, media_type="image/tiff",
                            headers={"Content-Disposition": f'attachment; filename="{filename}"'})

        elif fmt == "PNG":
            if ind == "CHANGE" and year2 is None:
                raise HTTPException(400, "CHANGE requires both year and year2")
            data = export_png(ind, year, year2)
            filename = f"{ind}_{year}.png" if ind != "CHANGE" else f"CHANGE_{year}_{year2}.png"
            return Response(content=data, media_type="image/png",
                            headers={"Content-Disposition": f'attachment; filename="{filename}"'})

        elif fmt == "PDF":
            if ind == "CHANGE" and year2 is None:
                raise HTTPException(400, "CHANGE requires both year and year2")
            data = export_pdf(ind, year, year2)
            filename = f"{ind}_{year}.pdf" if ind != "CHANGE" else f"CHANGE_{year}_{year2}.pdf"
            return Response(content=data, media_type="application/pdf",
                            headers={"Content-Disposition": f'attachment; filename="{filename}"'})

        else:
            raise HTTPException(400, f"Unknown format: {fmt}. Use TIFF, PNG, or PDF.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/info/{year}")
async def info(year: int):
    """Return metadata about a specific year's data source."""
    from config import get_satellite_era, BAND_MAP
    try:
        era = get_satellite_era(year)
        return {
            "year": year,
            "satellite_era": era,
            "bands": BAND_MAP[era],
            "layer": get_layer_name(year),
            "bbox": KUBUQI_BBOX,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
