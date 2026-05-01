"""PMAX campaign salvage package.

PMAX tooling is preserved as reference material. It is not part of the active
Search-first Google Ads Editor staging workflow unless a later PMAX phase
explicitly activates it.
"""

from .pmax_csv_generator import PMAXAssetGroupReference, PMAXCSVGenerator, PMAXWorkflowInactive

__all__ = ["PMAXCSVGenerator", "PMAXAssetGroupReference", "PMAXWorkflowInactive"]
