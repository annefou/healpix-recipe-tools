"""Land masks: offline with a synthetic polygon file; network with Natural Earth on a real coast."""

import json

import numpy as np
import pytest

from healpix_recipe_tools import DEFAULT_LAND_MASK, KNOWN_MASKS, Window, apply_land_mask, mask_attrs
from healpix_recipe_tools.masks import land_pixels, resolve


def window():
    lon = np.arange(0.0, 2.0, 0.1) + 0.05  # 20 columns, 0.05 .. 1.95
    lat = np.arange(10.0, 11.0, 0.1) + 0.05  # 10 rows, south to north
    return Window(values=np.ones((lat.size, lon.size)), lon=lon, lat=lat, res_deg=0.1)


@pytest.fixture
def west_half_land(tmp_path):
    """Land = the western half (lon < 1) of the window, as a GeoJSON file."""
    poly = {"type": "Polygon", "coordinates": [[[-1, 9], [1, 9], [1, 12], [-1, 12], [-1, 9]]]}
    p = tmp_path / "land.geojson"
    p.write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": poly}]}))
    return str(p)


def test_pixels_whose_centre_is_on_land_are_kept(west_half_land):
    land = land_pixels(window(), west_half_land)
    assert land.shape == (10, 20)
    assert land[:, :10].all() and not land[:, 10:].any()


def test_sea_pixels_become_missing(west_half_land):
    out = apply_land_mask(window(), west_half_land)
    assert np.isnan(out.values[:, 10:]).all() and (out.values[:, :10] == 1).all()


def test_north_south_orientation_is_kept(tmp_path):
    """A polygon covering only the northern half must mask the southern rows (rows run south to north)."""
    poly = {"type": "Polygon", "coordinates": [[[-1, 10.5], [3, 10.5], [3, 12], [-1, 12], [-1, 10.5]]]}
    p = tmp_path / "north.geojson"
    p.write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": poly}]}))
    land = land_pixels(window(), str(p))
    assert land[5:].all() and not land[:5].any()  # rows 5.. are lat > 10.5


def test_no_mask_changes_nothing():
    w = window()
    assert apply_land_mask(w, None) is w
    assert "none" in mask_attrs(None)["land_mask"]


def test_a_path_is_recorded_with_an_unknown_licence(west_half_land):
    a = mask_attrs(west_half_land)
    assert west_half_land in a["land_mask"] and a["land_mask_license"] == "not stated"
    a = mask_attrs({"path": west_half_land, "name": "my coastline", "license": "CC-BY-4.0"})
    assert "my coastline" in a["land_mask"] and a["land_mask_license"] == "CC-BY-4.0"


def test_the_default_is_a_known_open_mask():
    m = resolve(DEFAULT_LAND_MASK)
    assert m == KNOWN_MASKS["natural-earth-10m"] and m["license"] == "public domain"


@pytest.mark.network
def test_natural_earth_separates_land_and_sea_in_the_gulf_of_cadiz():
    lon = np.arange(-7.0, -6.0, 1 / 120) + 1 / 240
    lat = np.arange(36.5, 37.5, 1 / 120) + 1 / 240
    w = Window(values=np.ones((lat.size, lon.size)), lon=lon, lat=lat, res_deg=1 / 120)
    land = land_pixels(w, DEFAULT_LAND_MASK)
    sea_r, sea_c = np.searchsorted(lat, 36.6), np.searchsorted(lon, -6.9)    # open sea
    land_r, land_c = np.searchsorted(lat, 37.4), np.searchsorted(lon, -6.1)  # Seville area
    assert not land[sea_r, sea_c] and land[land_r, land_c]
    assert 0.2 < land.mean() < 0.8
