"""Dataset-JSON v1.1 model package for odmlib.

Provides ODMElement-based classes conforming to the CDISC Dataset-JSON
v1.1 specification, with JSON and NDJSON serialization support.
Also provides a Define-XML v2.1 metadata flattener for converting
Define-XML metadata into tabular Dataset-JSON datasets, and converters
between Dataset-XML 1.0.1 and Dataset-JSON v1.1.
"""
from odmlib.dataset_json_1_1.model import DatasetJSON, Column, SourceSystem
from odmlib.dataset_json_1_1.define_flattener import DefineFlattener
from odmlib.dataset_json_1_1.converter import (
    dataset_xml_to_dataset_json,
    dataset_json_to_dataset_xml,
)

__all__ = [
    "DatasetJSON", "Column", "SourceSystem",
    "DefineFlattener",
    "dataset_xml_to_dataset_json", "dataset_json_to_dataset_xml",
]
