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
| `masks` | `apply_land_mask(window, land_mask)`: keep land pixels only, from a land-polygon source the user chooses: `None`, a named source (default `natural-earth-10m`, public domain), or any polygon file or URL; `mask_attrs` records it |
| `bioclim` | BIOCLIM conventions: CHELSA (`"population"`) and WorldClim (`"dismo"`) compute `bio4` and `bio15` differently; exact conversions between them (see the module docstring) |

Dependencies: healpix-convert, rasterio, xarray, zarr, shapely. Never healpix-connector:
healpix-connector depends on recipes, not the other way.

## Coasts and land masks

Sources disagree at the coast: CHELSA v2.1 has values over the sea (outside its stated domain,
land surface areas), WorldClim marks the sea as nodata. A coastal HEALPix cell then averages land
and sea in one, land only in the other. Recipes apply the same land mask to every source; the user
chooses it:

| `land_mask` | Source | Licence | Note |
|---|---|---|---|
| `"natural-earth-10m"` (default) | Natural Earth 1:10m land polygons | public domain | small, read remotely in under a second; coastline generalised by up to a few km |
| a path or URL | any polygon file GDAL reads (e.g. OpenStreetMap land polygons, GSHHG, a national coastline) | its own | precise coastlines; record name and licence with `{"path", "name", "license"}` |
| `None` | no mask | | the source's own values, including any over the sea |

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
