# Changelog

All notable changes to odmlib will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Error Reporting and Diagnostics (Phase 1)
- New `odmlib/exceptions.py` module with a structured exception hierarchy
- `OdmlibError` — base class for all odmlib exceptions
- `OdmlibValidationError` — replaces bare `ValueError` for validation failures; includes
  `element_path`, `hint`, `attribute`, `element_type`, and `actual_value` attributes
- `OdmlibRequiredAttributeError` — raised when a required attribute is missing at construction
- `OdmlibOIDError` — raised for OID uniqueness or ref/def integrity failures
- `OdmlibConformanceError` — raised when Cerberus conformance validation fails; exposes
  raw `cerberus_errors` dict for programmatic inspection
- `OdmlibElementOrderError` — raised when child elements violate ODM-spec ordering
- `OdmlibTypeError` — replaces bare `TypeError` for type/enum validation failures
- `OdmlibParsingError` — raised when an XML or JSON document cannot be parsed
- `OdmlibLoaderStateError` — raised when a loader method is called before the document is opened
- `OdmlibSerializationError` — raised when the model cannot be serialized to XML or JSON
- `OdmlibNamespaceError` — raised for namespace registration or lookup failures
- `OdmlibWarning`, `OdmlibDeprecationWarning`, `OdmlibInteroperabilityWarning` — warning hierarchy
- `ErrorCollector` — accumulates validation errors instead of raising on the first failure;
  `has_errors`, `add_error()`, `add_warning()`, `raise_if_errors()` API
- `ODMElement.validate()` method — unified validation entry point supporting both
  fail-fast (default) and collect-all-errors (`collect_errors=True`) modes
- All exceptions and `ErrorCollector` exported from `odmlib` package root
- `tests/test_exceptions.py` — 47 tests covering hierarchy, formatting, backward compat, and model integration
- `tests/test_collect_errors.py` — 10 tests covering fail-fast and collect-all-errors validation modes

#### Dataset-JSON v1.1 ODMElement Model
- New `odmlib/dataset_json_1_1/` package — spec-conformant Dataset-JSON v1.1 support using
  the ODMElement/descriptor pattern (one dataset per file, matching the v1.1 specification)
  - `DatasetJSON` — root element with `to_json()`, `from_json()`, `write_json()`, `read_json()`,
    `write_ndjson()`, `read_ndjson()`, `to_dict()`, `from_dict()`, `add_row()`, `add_column()`,
    `column_names` property
  - `Column` — column metadata with validated `dataType` and optional `targetDataType`,
    `length`, `displayFormat`, `keySequence`
  - `SourceSystem` — optional nested source system metadata object
  - `DatasetJSONElement` base class disables XML serialization (`to_xml()` raises
    `NotImplementedError`) and handles mixed list types in `to_dict()`
- New `odmlib/dataset_json_1_1/define_flattener.py` — converts Define-XML v2.1 metadata into
  11 tabular Dataset-JSON datasets (study, standards, datasets, variables, value_level,
  where_clauses, methods, comments, documents, codelists, codelist_terms)
  - `DefineFlattener.flatten_all()` returns dict of dataset name → DatasetJSON
  - `DefineFlattener.write_all(output_dir)` writes individual JSON files
  - O(1) ItemDef and WhereClauseDef lookups via index
  - `_safe_get()` utility for traversing deeply nested optional attributes
- New `odmlib/dataset_json_1_1/converter.py` — bidirectional Dataset-XML ↔ Dataset-JSON v1.1
  - `dataset_xml_to_dataset_json(odm_obj)` returns dict[str, DatasetJSON] (one per ItemGroupOID)
  - `dataset_json_to_dataset_xml(dataset_json, model)` converts back to Dataset-XML
- Updated `odmlib/dataframe.py` — Pandas integration for the new model
  - `dataset_json_to_dataframe()` now supports both legacy `Dataset` and new `DatasetJSON`
  - `define_metadata_to_dataframes(odm_root)` — Define-XML v2.1 → dict of DataFrames
  - `dataframe_to_dataset_json(df, name, label, oid)` — DataFrame → DatasetJSON v1.1
- `DatasetJSON`, `Column`, `SourceSystem`, `DefineFlattener`, `dataset_xml_to_dataset_json`,
  `dataset_json_to_dataset_xml` exported from `odmlib` package root
- New how-to guide: `docs/source/guides/dataset_json.rst`
- New API reference page: `docs/source/odmlib.dataset_json_1_1.rst`
- New tests: `tests/test_dataset_json_1_1_model.py` (68 tests),
  `tests/test_define_flattener.py` (45 tests),
  `tests/test_dataset_json_1_1_converter.py` (21 tests),
  `tests/test_dataframe_phase3.py` (39 tests)

#### Interoperability and Format Support (Phase 6)
- New `odmlib/dataset_json/` package — CDISC Dataset-JSON v1.1 support with no additional
  dependencies required
  - `DatasetJSON` — root document object with `to_json()`, `write_json()`, `from_json()`,
    `read_json()`, `to_dict()`, `from_dict()`, `get_dataset()` API
  - `Dataset` — one dataset/domain with column definitions and data rows;
    `add_record()` validates row length against the column count at assignment time
  - `ItemMetadata` — column definition (OID, name, label, type, length, displayFormat,
    keySequence) matching the Dataset-JSON v1.1 `items` array schema
  - `DatasetRecord` — a single row of values in column order
- New `odmlib/dataset_json/converter.py` — bidirectional conversion utilities
  - `dataset_xml_to_json(odm_obj, define_mdv=None)` — converts a Dataset-XML 1.0.1 odmlib
    object to Dataset-JSON; multiple rows with the same ItemGroupOID are merged into one
    dataset; missing items in a row produce `None` values (column union)
  - `dataset_json_to_xml(dsjson, dataset_xml_model)` — converts Dataset-JSON back to a
    Dataset-XML odmlib object suitable for `write_xml()`
  - Accepts an optional Define-XML MetaDataVersion to enrich column metadata (labels,
    types, lengths) from `ItemDef` elements
- New `odmlib/dataframe.py` — optional Pandas DataFrame integration
  - `metadata_to_dataframe(mdv, element_type, attributes=None)` — exports odmlib metadata
    elements (ItemDef, ItemGroupDef, CodeList, etc.) as a DataFrame
  - `clinical_data_to_dataframe(clinical_data, item_group_oid)` — flattens ODM 1.3.2
    hierarchical clinical data (SubjectData → StudyEventData → FormData → ItemGroupData)
    into a tabular DataFrame
  - `dataset_to_dataframe(clinical_data)` — flattens Dataset-XML 1.0.1 ClinicalData
    (flat structure, no SubjectData) into a DataFrame
  - `dataset_json_to_dataframe(dataset)` — converts a Dataset-JSON `Dataset` object to a
    DataFrame with columns named by variable name
  - `dataframe_to_items(df, model_module, element_type, column_mapping=None)` — creates
    odmlib element instances from a DataFrame (one row per element); skips invalid rows
  - Graceful degradation: importing the module always succeeds; calling any function
    raises `ImportError` with install hint when pandas is absent
- Optional dependency group `dataframe` added to `pyproject.toml`:
  `pip install odmlib[dataframe]` installs pandas ≥ 1.5
- pandas ≥ 1.5 added to the `dev` dependency group so the full test suite
  runs against pandas in CI development environments
- New `tests/test_dataset_json.py` — 36 tests for the Dataset-JSON model
- New `tests/test_dataset_json_converter.py` — 15 tests for converter functions
- New `tests/test_dataframe.py` — 23 tests for DataFrame integration
  (skipped automatically when pandas is not installed)
- New how-to guide: `docs/source/guides/interoperability.rst`
- New API reference pages: `odmlib.dataset_json` and `odmlib.dataframe`
- Both new pages added to Sphinx `index.rst`

#### Packaging Modernization (Phase 4)
- `pyproject.toml` for modern Python packaging (replaces `setup.py` as primary config)
- GitHub Actions CI: automated testing on Python 3.9–3.13
- GitHub Actions: automated PyPI publishing on tagged releases
- `CHANGELOG.md` for tracking changes going forward
- Semantic versioning policy starting at 0.2.0

### Changed

#### Phase 1
- All ~70 `ValueError`/`TypeError` raises across 16 files replaced with structured odmlib exceptions
- `odmlib/odm_element.py`: `verify_order()` now raises `OdmlibElementOrderError` with a hint to use
  `reorder_object()`; `reorder_object()` issues an `OdmlibWarning` before silently reordering
- `odmlib/odm_1_3_2`, `odmlib/define_2_0`, `odmlib/define_2_1` conformance checkers now raise
  `OdmlibConformanceError` with structured `cerberus_errors` attribute instead of `ValueError(dict)`

#### Dynamic OID Ref/Def Generation (Phase 7)
- New `odmlib/oid_generator.py` module with fully dynamic OID ref/def checking derived
  from model class introspection — eliminates manual maintenance of `oid_ref.py` files
- `DynamicOIDRef` class — drop-in replacement for the manual `OIDRef` classes with the
  same `add_oid()`, `add_oid_ref()`, `check_oid_refs()`, and `check_unreferenced_oids()` API
- `create_oid_checker(model_package, extra_skip_attrs=None, extra_skip_elems=None)` factory
  function — primary public API for creating OID checkers; exported from `odmlib` package root
- `odmlib/oid_generator_config.py` — per-model skip-attribute and skip-element configuration
- **ODM 2.0 OID checking** now supported for the first time via `create_oid_checker("odm_2_0")`
- Manual `OIDRef` classes in `rules/oid_ref.py` for all three model packages
  (`odm_1_3_2`, `define_2_0`, `define_2_1`) now emit `OdmlibDeprecationWarning` on
  instantiation; they remain functional and will be removed in v0.3.0
- `tests/test_oid_generator.py` — 57 new tests covering model introspection, mapping
  correctness, DynamicOIDRef behavior, end-to-end validation, and deprecation warnings

#### Phase 4
- Unified version to `0.2.0` across `pyproject.toml`, `odmlib/__init__.py`, and `docs/source/conf.py`
- `odmlib/__version__` now read dynamically from installed package metadata via `importlib.metadata`
- Installation: `pip install -e ".[dev]"` replaces `python setup.py develop`
- Installation: `pip install -e .` replaces `python setup.py install`
- `requirements.txt` aligned to match `pyproject.toml` dependency minimum versions

### Fixed

#### Phase 7
- Trailing space bugs in `odmlib/odm_1_3_2/rules/oid_ref.py` `_init_def_ref()`:
  `"SignatureOID "` corrected to `"SignatureOID"` and `"ItemOID "` corrected to `"ItemOID"`;
  these would have caused silent failures in `check_unreferenced_oids()`

#### Phase 4
- `MANIFEST.in` typo: `test/data` corrected to `tests/data`
- Version inconsistency: was 0.1.4 (`setup.py`), 0.1.2 (`__init__.py`), 0.1.0 (`docs/`)
- Missing `odmlib.odm_2_0` package in build configuration (now auto-discovered via `packages.find`)

### Deprecation Notice

In v0.2.x, odmlib validation and type exceptions dual-inherit from `ValueError`/`TypeError` so that
all existing `except ValueError` and `except TypeError` clauses continue to work unchanged.

**v0.3.0 breaking change:** The `ValueError`/`TypeError` base classes will be removed. Update any
`except ValueError` → `except OdmlibValidationError` and `except TypeError` → `except OdmlibTypeError`
before upgrading to v0.3.0.

The `odmlib.dataset_json` module (plain Python classes) is deprecated in v0.2.0
and will be removed in v0.3.0. Migrate to `odmlib.dataset_json_1_1`:

```python
# Before (deprecated):
from odmlib.dataset_json import DatasetJSON, Dataset, ItemMetadata

# After:
from odmlib.dataset_json_1_1 import DatasetJSON, Column, SourceSystem
```

The manual `OIDRef` classes in `odmlib/odm_1_3_2/rules/oid_ref.py`,
`odmlib/define_2_0/rules/oid_ref.py`, and `odmlib/define_2_1/rules/oid_ref.py` are deprecated
in v0.2.0 and will be removed in v0.3.0.  Migrate to `create_oid_checker()`:

```python
# Before (deprecated):
from odmlib.odm_1_3_2.rules.oid_ref import OIDRef
checker = OIDRef()

# After:
from odmlib.oid_generator import create_oid_checker
checker = create_oid_checker("odm_1_3_2")
```

## [0.1.4] - Previous Release

- Last release using legacy `setup.py` packaging
- See git history for details

[Unreleased]: https://github.com/swhume/odmlib/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/swhume/odmlib/releases/tag/v0.1.4
