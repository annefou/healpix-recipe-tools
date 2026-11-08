"""Offline end to end: a synthetic lon/lat field is staged and converted by healpix-convert."""

import numpy as np
import xarray as xr

from healpix_recipe_tools import Window, gdal_path, raster_settings, run, stac_item, write_staged
from healpix_recipe_tools.staging import PROJECTION_EXTENSION

BBOX = (-5.0, 40.0, -4.0, 41.0)


def window(fill):
    lon = np.arange(-5.5, -3.5, 1 / 120) + 1 / 240
    lat = np.arange(39.5, 41.5, 1 / 120) + 1 / 240
    return Window(values=fill(*np.meshgrid(lon, lat)), lon=lon, lat=lat, res_deg=1 / 120)


def convert(tmp_path, fill, pyramid_to=10):
    w = window(fill)
    item = stac_item("toy", w, ("2000-01-01", "2000-12-31"), license="CC0-1.0")
    staged = write_staged(tmp_path / "staged.zarr", "toy/v1", "t", w, item)
    run(staged, raster_settings("toy/v1", "t", {"units": "K"}, pyramid_to=pyramid_to), tmp_path / "out.zarr", BBOX)
    return xr.open_datatree(tmp_path / "out.zarr", engine="zarr")


def test_a_constant_field_stays_constant_at_every_depth(tmp_path):
    dt = convert(tmp_path, lambda lon, lat: np.full(lon.shape, 280.0))
    for d in (13, 12, 11, 10):
        v = dt[f"toy/{d}"].to_dataset()["t"].values
        assert np.nanmax(np.abs(v - 280.0)) < 1e-3, d


def test_a_linear_field_is_averaged_without_bias(tmp_path):
    from healpix_geo import nested

    dt = convert(tmp_path, lambda lon, lat: 10.0 * lat)  # cell mean of a linear field ~ its centre value
    ds = dt["toy/10"].to_dataset()
    lon, lat = nested.healpix_to_lonlat(ds["cell_ids"].values.astype("uint64"), 10, ellipsoid="WGS84")
    lon = (lon + 180.0) % 360.0 - 180.0
    # the output covers whole chunk cells, beyond the staged data: compare well inside it
    inside = (lat > 40.1) & (lat < 40.9) & (lon > -4.9) & (lon < -4.1)
    diff = ds["t"].values[inside] - 10.0 * lat[inside]
    assert inside.sum() > 50 and np.isfinite(diff).all()
    assert np.abs(diff).mean() < 0.01


def test_the_output_carries_the_units(tmp_path):
    dt = convert(tmp_path, lambda lon, lat: np.full(lon.shape, 1.0), pyramid_to=12)
    assert dt["toy/13"].to_dataset()["t"].attrs["units"] == "K"


def test_the_staged_item_has_what_healpix_convert_requires():
    item = stac_item("x", window(lambda lon, lat: lon), ("2000-01-01", "2000-12-31"), license="other")
    assert PROJECTION_EXTENSION in item["stac_extensions"]
    assert item["properties"]["proj:code"] == "EPSG:4326"


def test_gdal_paths():
    assert gdal_path("https://h/x.tif") == "/vsicurl/https://h/x.tif"
    assert gdal_path("https://h/a.zip", "m.tif") == "/vsizip//vsicurl/https://h/a.zip/m.tif"
