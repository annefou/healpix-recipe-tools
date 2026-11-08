"""Reading a window of a (remote) EPSG:4326 GeoTIFF, as the staging step of a recipe needs it."""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Window:
    """Pixels of a lon/lat grid, rows from south to north."""

    values: np.ndarray  # (lat, lon), physical units (file scale and offset applied), NaN = nodata
    lon: np.ndarray  # pixel-centre longitudes, increasing
    lat: np.ndarray  # pixel-centre latitudes, increasing
    res_deg: float


def gdal_path(url: str, member: str | None = None) -> str:
    """GDAL path of a remote file, or of ``member`` inside a remote zip (read without downloading)."""
    if member is None:
        return "/vsicurl/" + url
    return f"/vsizip//vsicurl/{url}/{member}"


def read_window(path: str, bbox: tuple[float, float, float, float], pad_deg: float = 0.0) -> Window:
    """Read ``bbox`` = (west, south, east, north) plus ``pad_deg`` from a GeoTIFF in EPSG:4326.

    Only the byte ranges needed are fetched for a plain remote GeoTIFF; inside a zip the member is
    decompressed from its start, so a window can take tens of seconds. The file's scale and offset
    are applied and its declared nodata becomes NaN. A file that declares no nodata (CHELSA v2.1)
    is read as is: the recipe must say how that source marks missing data.
    """
    import rasterio
    from rasterio.windows import from_bounds

    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif,.zip")
    w, s, e, n = bbox[0] - pad_deg, bbox[1] - pad_deg, bbox[2] + pad_deg, bbox[3] + pad_deg
    with rasterio.open(path) as src:
        if src.crs is not None and src.crs.to_epsg() != 4326:
            raise ValueError(f"{path}: expected EPSG:4326, got {src.crs}")
        win = from_bounds(w, s, e, n, src.transform).round_offsets().round_lengths()
        raw = src.read(1, window=win)
        scale, offset, nodata = src.scales[0], src.offsets[0], src.nodata
        t = src.window_transform(win)
    values = raw.astype("float64")
    if nodata is not None:
        values[raw == nodata] = np.nan
    values = values * scale + offset
    lon = t.c + t.a * (np.arange(values.shape[1]) + 0.5)
    lat = t.f + t.e * (np.arange(values.shape[0]) + 0.5)
    if t.e < 0:  # north-up file: flip to ascending latitude
        values, lat = values[::-1], lat[::-1]
    return Window(values=values, lon=lon, lat=lat, res_deg=abs(t.a))
