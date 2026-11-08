"""Shared building blocks for HEALPix recipes.

A recipe turns one data source into HEALPix cells (WGS84, NESTED) with healpix-convert's public
API: a staging step (the source read into a lat/lon Zarr dataset with a STAC item) and a settings
dict. This library holds what recipes have in common, so each recipe keeps only what is specific
to its source (where the data are, units and definitions, licence, corrections). See CONTRACT.md.
"""

from healpix_recipe_tools import bioclim
from healpix_recipe_tools.geotiff import Window, gdal_path, read_window
from healpix_recipe_tools.masks import DEFAULT_LAND_MASK, KNOWN_MASKS, apply_land_mask, mask_attrs
from healpix_recipe_tools.settings import raster_settings, run
from healpix_recipe_tools.staging import stac_item, write_staged

__version__ = "0.1.0.dev0"
__all__ = ["DEFAULT_LAND_MASK", "KNOWN_MASKS", "Window", "apply_land_mask", "bioclim", "gdal_path", "mask_attrs", "raster_settings", "read_window", "run", "stac_item", "write_staged"]
