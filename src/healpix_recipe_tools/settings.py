"""healpix-convert settings for a lon/lat raster, as plain data, and running the conversion."""

from __future__ import annotations

from pathlib import Path

_WGS84 = {"name": "wgs84"}


def raster_settings(group: str, variable: str, attrs: dict, *, depth: int = 13, pyramid_to: int = 8,
                    chunk_depth: int = 7, license: str | None = None, license_links: list[dict] | None = None,
                    resampler: str = "bilinear", chunk_buffer_m: float = 3000.0) -> dict:
    """Settings for one variable of a ~1 km lon/lat raster staged as group ``group`` ("<root>/<name>").

    The raster is resampled at ``depth`` (13 is about 800 m), then the pyramid builds the coarser
    depths down to ``pyramid_to`` with ``mean``: on equal-area cells, block means are area-weighted
    cell means. ``attrs`` (units, long_name, ...) are set on the output variable with
    ``override_attrs``. Note: the pyramid's mean ignores missing children, so a cell only partly
    covered by data gets a value for part of its area, with nothing saying so.
    """
    root = group.split("/")[0]
    stac: dict = {}
    if license:
        stac["override_properties"] = {"license": license}
    if license_links:
        stac["override_links"] = list(license_links)
    return {
        **({"metadata": {"stac": stac}} if stac else {}),
        "multiscale_settings": {
            "groups": [root],
            "pyramid_groups": {root: {"derived_levels": list(range(depth - 1, pyramid_to - 1, -1)), "reduce": "mean"}},
        },
        "group_settings": {
            group: {
                "healpix": {"refinement_level": depth, "indexing_scheme": "nested", "ellipsoid": _WGS84},
                "chunk": {
                    "method": "healpix_cell_dense",
                    "healpix": {"refinement_level": chunk_depth, "indexing_scheme": "nested", "ellipsoid": _WGS84},
                    "chunk_buffer_width": float(chunk_buffer_m),
                },
                "resampler": {"name": resampler},
                "output_dtype": "float32",
                "metadata": {"override_attrs": {variable: dict(attrs)}},
            },
        },
    }


def run(staged: str | Path, settings: dict, output: str | Path, bbox: tuple[float, float, float, float]):
    """Convert ``staged`` with healpix-convert's public API, restricted to ``bbox``."""
    import healpix_convert as hc
    import shapely

    cfg = hc.ConvertSettings.model_validate(settings)
    return hc.create_healpix_dataset([str(staged)], cfg, str(output), output_extent=shapely.box(*bbox))
