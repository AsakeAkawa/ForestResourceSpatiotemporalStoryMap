"""
Satellite band configuration for Landsat 5 / 8 / 9.
All images have 6 bands stored as COGs.

Landsat 5 (1986-1995):  Band 1=Blue 2=Green 3=Red 4=NIR 5=SWIR1 6=SWIR2
Landsat 8 (2015-2021):  Band 1=Blue 2=Green 3=Red 4=NIR 5=SWIR1 6=SWIR2
                         (corresponds to original LS8 bands 2-7)
Landsat 9 (2022-2024):  Same as Landsat 8
"""

GEOSERVER_URL = "http://8.152.203.155:8080/geoserver"
WORKSPACE = "kubuqi"
WCS_URL = f"{GEOSERVER_URL}/{WORKSPACE}/wcs"

# Kubuqi bounding box (WGS84)
KUBUQI_BBOX = {
    "minx": 107.0462,
    "miny": 40.0757,
    "maxx": 109.9845,
    "maxy": 40.8556,
}

# Band index mapping: which band number to use for each satellite era
# Keyed by era, values: {"red": band_index, "nir": band_index}
# Band indices are 1-based (matches rasterio convention)
BAND_MAP = {
    "L5": {"blue": 1, "green": 2, "red": 3, "nir": 4, "swir1": 5, "swir2": 6},   # Landsat 5: 1986-1995
    "L8": {"blue": 1, "green": 2, "red": 4, "nir": 5, "swir1": 6, "swir2": 3},   # Landsat 8: 2015-2021
    "L9": {"blue": 1, "green": 2, "red": 4, "nir": 5, "swir1": 6, "swir2": 3},   # Landsat 9: 2022-2024 (same as L8)
}

# Tasseled Cap Wetness coefficients (Crist & Cicone 1984 / Baig et al. 2014)
# Applied to Top-of-Atmosphere reflectance
WET_COEFFS = {
    "L5": {"blue": 0.0315, "green": 0.2021, "red": 0.3102, "nir": 0.1594, "swir1": -0.6806, "swir2": -0.6109},
    "L8": {"blue": 0.1511, "green": 0.1973, "red": 0.3283, "nir": 0.3407, "swir1": -0.7117, "swir2": -0.4559},
    "L9": {"blue": 0.1511, "green": 0.1973, "red": 0.3283, "nir": 0.3407, "swir1": -0.7117, "swir2": -0.4559},
}


def get_satellite_era(year: int) -> str:
    """Determine which satellite era a given year belongs to."""
    if 1986 <= year <= 1995:
        return "L5"
    elif 2015 <= year <= 2021:
        return "L8"
    elif 2022 <= year <= 2024:
        return "L9"
    else:
        raise ValueError(f"No satellite data for year {year}. Available: 1986-1995, 2015-2024")


def get_layer_name(year: int) -> str:
    """Get the GeoServer WCS coverage name for a given year."""
    return f"Kubuqi_{year}_cog"
