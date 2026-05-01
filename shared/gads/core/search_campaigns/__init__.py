"""Search campaign salvage package.

The active Search staging contract currently lives in
``shared.rebuild.staging_validator``. This package is retained as salvage and
compatibility material until individual generators are rewritten and tested.
"""

from .search_csv_generator import SearchCSVGenerator

__all__ = ["SearchCSVGenerator"]
