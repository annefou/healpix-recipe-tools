"""Land masks: keep land pixels only, from a land-polygon source the user chooses.

Sources differ at the coast: CHELSA v2.1 has values over the sea (outside its stated domain, "the
earth's land surface areas"), while WorldClim marks the sea as nodata. Without a mask, a coastal
HEALPix cell averages land and sea in one source and land only in the other. Applying the same land
mask to every source makes coastal cells describe the same thing.

``land_mask`` is one of:

- ``None``: no mask, the source's own values;
- a name in ``KNOWN_MASKS`` (the default, ``DEFAULT_LAND_MASK``, is Natural Earth 10 m land);
- a path or URL to any polygon file GDAL reads (GeoPackage, GeoJSON, shapefile, also inside a zip,
  e.g. ``gdal_path(url, member)``), in EPSG:4326, whose polygons are land;
- a dict ``{"path": ..., "name": ..., "license": ...}`` to record the name and licence too.

A pixel is land when its centre is inside a polygon. The mask applied, and its licence, go into the
output's attributes.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from healpix_recipe_tools.geotiff import Window

#: Named land-polygon sources. Others (OpenStreetMap land polygons, GSHHG, a national coastline)
#: are passed as a path or URL.
KNOWN_MASKS = {
    "natural-earth-10m": {
        "name": "Natural Earth 1:10m land polygons (ne_10m_land)",
        "path": "/vsizip//vsicurl/https://naciscdn.org/naturalearth/10m/physical/ne_10m_land.zip/ne_10m_land.shp",
        "license": "public domain",
        "url": "https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-land/",
        "note": "1:10 million scale: the coastline is generalised by up to a few km, so single ~1 km "
                "pixels on an intricate coast may be misclassified; fine for cells of ~10 km and more",
    },
}

DEFAULT_LAND_MASK = "natural-earth-10m"


def resolve(land_mask) -> dict | None:
    """The mask as a dict with at least ``path`` and ``name``, or None for no mask."""
    if land_mask is None:
        return None
    if isinstance(land_mask, dict):
        if "path" not in land_mask:
            raise ValueError("a land_mask dict needs a 'path'")
        return {"name": land_mask["path"], "license": "not stated", **land_mask}
    if land_mask in KNOWN_MASKS:
        return dict(KNOWN_MASKS[land_mask])
    path = str(land_mask)
    if path.startswith(("http://", "https://")):
        path = "/vsicurl/" + path
    return {"name": str(land_mask), "path": path, "license": "not stated"}


def land_pixels(window: Window, land_mask) -> np.ndarray | None:
    """Boolean (lat, lon) array: True where the pixel centre is on land. None when no mask."""
    import os

    import pyogrio
    import shapely
    from rasterio.features import geometry_mask
    from rasterio.transform import from_origin

    mask = resolve(land_mask)
    if mask is None:
        return None
    os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".zip,.shp,.shx,.dbf,.prj,.cpg,.gpkg,.geojson,.json")
    res = window.res_deg
    west, east = float(window.lon[0]) - res / 2, float(window.lon[-1]) + res / 2
    south, north = float(window.lat[0]) - res / 2, float(window.lat[-1]) + res / 2
    info = pyogrio.read_info(mask["path"])
    crs = (info.get("crs") or "").upper()
    if crs and crs not in ("EPSG:4326", "OGC:CRS84"):
        raise ValueError(f"land mask {mask['name']}: expected EPSG:4326, got {crs}")
    _, _, wkb, _ = pyogrio.raw.read(mask["path"], bbox=(west, south, east, north))
    shape = (window.lat.size, window.lon.size)
    if len(wkb) == 0:
        return np.zeros(shape, dtype=bool)  # no land polygon in the window: all sea
    geoms = [g for g in shapely.from_wkb(wkb) if g is not None and not g.is_empty]
    # rasterio works north-up; the window's rows run from south to north
    north_up = geometry_mask(geoms, out_shape=shape, transform=from_origin(west, north, res, res),
                             invert=True, all_touched=False)
    return north_up[::-1]


def apply_land_mask(window: Window, land_mask) -> Window:
    """The window with non-land pixels set to NaN (unchanged when ``land_mask`` is None)."""
    land = land_pixels(window, land_mask)
    if land is None:
        return window
    values = np.where(land, window.values, np.nan)
    return dataclasses.replace(window, values=values)


def mask_attrs(land_mask) -> dict:
    """Attributes recording the land mask applied (empty when none)."""
    mask = resolve(land_mask)
    if mask is None:
        return {"land_mask": "none: the source's own values, including any over the sea"}
    return {"land_mask": f"land pixels only, by pixel centre: {mask['name']}",
            "land_mask_license": mask["license"]}
