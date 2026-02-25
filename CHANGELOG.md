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

#### Phase 4
- Unified version to `0.2.0` across `pyproject.toml`, `odmlib/__init__.py`, and `docs/source/conf.py`
- `odmlib/__version__` now read dynamically from installed package metadata via `importlib.metadata`
- Installation: `pip install -e ".[dev]"` replaces `python setup.py develop`
- Installation: `pip install -e .` replaces `python setup.py install`
- `requirements.txt` aligned to match `pyproject.toml` dependency minimum versions

### Fixed

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

## [0.1.4] - Previous Release

- Last release using legacy `setup.py` packaging
- See git history for details

[Unreleased]: https://github.com/swhume/odmlib/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/swhume/odmlib/releases/tag/v0.1.4
