"""Dataset-JSON support for odmlib (DEPRECATED).

.. deprecated:: 0.2.0
    This module uses plain Python classes instead of the ODMElement/descriptor
    pattern.  Use :mod:`odmlib.dataset_json_1_1` instead, which provides
    spec-conformant ODMElement-based classes for Dataset-JSON v1.1.
    This module will be removed in v0.3.0.

Example migration::

    # Before (deprecated):
    from odmlib.dataset_json import DatasetJSON, Dataset, ItemMetadata

    # After:
    from odmlib.dataset_json_1_1 import DatasetJSON, Column, SourceSystem
"""
import warnings
from odmlib.exceptions import OdmlibDeprecationWarning

warnings.warn(
    "odmlib.dataset_json is deprecated. Use odmlib.dataset_json_1_1 instead. "
    "Will be removed in v0.3.0.",
    OdmlibDeprecationWarning, stacklevel=2
)

from odmlib.dataset_json.model import DatasetJSON, Dataset, ItemMetadata, DatasetRecord

__all__ = ["DatasetJSON", "Dataset", "ItemMetadata", "DatasetRecord"]
