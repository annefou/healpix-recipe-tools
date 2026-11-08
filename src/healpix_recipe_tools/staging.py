"""Writing the staged input healpix-convert reads: a lat/lon Zarr dataset with a STAC item."""

from __future__ import annotations

from pathlib import Path

from healpix_recipe_tools.geotiff import Window

#: healpix-convert requires ``stac_extensions`` on the staged item (it fails without it); the
#: projection extension is what its DEM GLO-30 example uses.
PROJECTION_EXTENSION = "https://stac-extensions.github.io/projection/v2.0.0/schema.json"


def stac_item(item_id: str, window: Window, period: tuple[str, str], *, license: str,
              links: list[dict] | None = None, properties: dict | None = None) -> dict:
    """The STAC item of a staged lon/lat window. ``period`` = (start, end) as ISO dates."""
    import shapely

    box = shapely.box(float(window.lon[0]), float(window.lat[0]), float(window.lon[-1]), float(window.lat[-1]))
    return {
        "type": "Feature",
        "stac_version": "1.1.0",
        "stac_extensions": [PROJECTION_EXTENSION],
        "id": item_id,
        "geometry": shapely.geometry.mapping(box),
        "bbox": list(box.bounds),
        "properties": {
            "datetime": None,
            "start_datetime": f"{period[0]}T00:00:00Z",
            "end_datetime": f"{period[1]}T23:59:59Z",
            "proj:code": "EPSG:4326",
            "license": license,
            **(properties or {}),
        },
        "links": list(links or []),
        "assets": {},
    }


def write_staged(path: str | Path, group: str, variable: str, window: Window, item: dict) -> Path:
    """Write ``window`` as variable ``variable`` of group ``group`` (e.g. "chelsa/v21") at ``path``."""
    import xarray as xr

    ds = xr.Dataset({variable: (("lat", "lon"), window.values.astype("float32"))},
                    coords={"lat": window.lat, "lon": window.lon})
    ds["lat"].attrs.update(standard_name="latitude", units="degrees_north")
    ds["lon"].attrs.update(standard_name="longitude", units="degrees_east")
    path = Path(path)
    xr.DataTree.from_dict({"/": xr.Dataset(attrs={"stac_discovery": item}), group: ds}).to_zarr(
        path, mode="w-", zarr_format=3)
    return path
