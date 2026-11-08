# The recipe contract

A recipe turns **one data source** into HEALPix cells (WGS84 ellipsoid, NESTED ids) with
[healpix-convert](https://github.com/GRID4EARTH/healpix-convert)'s public API. It is code, not data:
it holds what someone who knows the source has checked, so that others can use the source safely.
Written from the first two recipes
([CHELSA](https://github.com/annefou/chelsa-healpix-recipe),
[WorldClim](https://github.com/annefou/worldclim-healpix-recipe)); it will grow with the first
polygon and time-series sources.

## What a recipe provides

| Name | What |
|---|---|
| `SOURCE` | name, version, reference period, DOI, licence (SPDX, or `"other"` with the licence text and terms URL), where the data are |
| `GROUP` | the staged group, `"<source>/<version>"`; the output pyramid is `"<source>/<depth>"` |
| `VARIABLES` | per variable: `units`, `long_name` (and `standard_name` where CF has one), **checked** (below) |
| `settings(variable, ...)` | the healpix-convert settings, as plain data |
| `stage(variable, bbox, path, ...)` | the source read into a lat/lon Zarr dataset with a STAC item |
| `convert(variable, bbox, output, ...)` | `stage` then healpix-convert; returns the output DataTree |

Shared pieces come from [healpix-recipe-tools](https://github.com/annefou/healpix-recipe-tools)
(`read_window`, `stac_item`, `write_staged`, `raster_settings`, `run`, `bioclim`). If a recipe needs
something generic that is missing, add it there, not in the recipe.

## Rules

1. **Dependencies:** healpix-convert and healpix-recipe-tools (and what reading the source needs).
   Never healpix-connector: it depends on recipes, not the other way.
2. **Corrections are checked against the source's own data**, not only its documentation, with a
   script in `examples/` that anyone can rerun and whose result is in the README. CHELSA's
   specification gives wrong units for `bio4` and `bio15`; WorldClim and CHELSA compute `bio4` and
   `bio15` differently under the same names. Expect such surprises.
3. **Missing data**: say how the source marks it. A file that declares no nodata value (CHELSA) is
   read as is, so a numeric fill would be averaged in as data.
4. **Licence**: the recipe's code is Apache-2.0; the data keep their own licence, which goes into
   `SOURCE`, the README and the STAC metadata of every output. A non-open licence (WorldClim) is
   stated plainly: converted layers may then not be shared without the provider's permission.
5. **Reference test**: one network test converts a small region and compares the cell means with
   values produced once by an **independent** method, stored in `tests/reference/` with how they
   were made. No live dependency on that method.
6. **Pins**: healpix-convert at the commit the recipe was tested with; `pixi.lock` committed.
7. **Releases**: one repository per source, named `<source>-healpix-recipe`; each release gets its own
   Zenodo DOI, so a paper can cite the exact recipe version it used.

## Review checklist

- [ ] `SOURCE` complete, each field taken from the provider's pages
- [ ] every unit and definition checked against the data (script in `examples/`, result in README)
- [ ] missing-data encoding known and handled
- [ ] licence stated in `SOURCE`, README and STAC output; non-open licences flagged
- [ ] depth chosen from the source's resolution, and why, in the README
- [ ] offline tests pass; the reference test passes with its tolerances stated
- [ ] README: what, variables, checks, agreement table, open points, citation
