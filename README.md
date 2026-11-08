# healpix-recipe-tools

Shared building blocks for HEALPix recipes. A recipe turns one data source into HEALPix cells
(WGS84 ellipsoid, NESTED ids) with [healpix-convert](https://github.com/GRID4EARTH/healpix-convert)'s
public API, with nothing added to healpix-convert. This library holds what recipes have in common,
so each recipe keeps only what is specific to its source.

> **Status: trial**, extracted from
> [chelsa-healpix-recipe](https://github.com/annefou/chelsa-healpix-recipe) and
> [worldclim-healpix-recipe](https://github.com/annefou/worldclim-healpix-recipe). Start a new recipe
> from [healpix-recipe-template](https://github.com/annefou/healpix-recipe-template); what a recipe
> must provide is in its `CONTRACT.md`.

| Module | What it does |
|---|---|
| `geotiff` | `read_window(path, bbox, pad_deg)`: a window of an EPSG:4326 GeoTIFF, remote or inside a remote zip (`gdal_path`), scale/offset applied, declared nodata as NaN, rows south to north |
| `staging` | `stac_item(...)` and `write_staged(...)`: the lat/lon Zarr dataset with its STAC item that healpix-convert reads (including the `stac_extensions` it requires) |
| `settings` | `raster_settings(...)`: settings for a ~1 km raster (bilinear to depth 13, `mean` pyramid down to depth 8, attributes via `override_attrs`, licence in STAC); `run(...)` calls healpix-convert |
| `bioclim` | BIOCLIM conventions: CHELSA (`"population"`) and WorldClim (`"dismo"`) compute `bio4` and `bio15` differently; exact conversions between them (see the module docstring) |

Dependencies: healpix-convert, rasterio, xarray, zarr, shapely. Never healpix-connector:
healpix-connector depends on recipes, not the other way.

## Known limitation

The pyramid's `mean` ignores missing children, so a cell only partly covered by data (a coast, a
window edge) gets a value for part of its area, with nothing saying so. Coverage and the spread
within each cell need reductions healpix-convert does not offer yet.

## Tests

```bash
pixi run -e test test     # offline, including a synthetic field converted end to end by healpix-convert
```

## Licence

Apache License 2.0.
