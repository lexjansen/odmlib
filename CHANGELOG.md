# Changelog

All notable changes to odmlib will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `pyproject.toml` for modern Python packaging (replaces `setup.py` as primary config)
- GitHub Actions CI: automated testing on Python 3.9–3.13
- GitHub Actions: automated PyPI publishing on tagged releases
- `CHANGELOG.md` for tracking changes going forward
- Semantic versioning policy starting at 0.2.0

### Changed
- Unified version to `0.2.0` across `pyproject.toml`, `odmlib/__init__.py`, and `docs/source/conf.py`
- `odmlib/__version__` now read dynamically from installed package metadata via `importlib.metadata`
- Installation: `pip install -e ".[dev]"` replaces `python setup.py develop`
- Installation: `pip install -e .` replaces `python setup.py install`
- `requirements.txt` aligned to match `pyproject.toml` dependency minimum versions

### Fixed
- `MANIFEST.in` typo: `test/data` corrected to `tests/data`
- Version inconsistency: was 0.1.4 (`setup.py`), 0.1.2 (`__init__.py`), 0.1.0 (`docs/`)
- Missing `odmlib.odm_2_0` package in build configuration (now auto-discovered via `packages.find`)

## [0.1.4] - Previous Release

- Last release using legacy `setup.py` packaging
- See git history for details

[Unreleased]: https://github.com/swhume/odmlib/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/swhume/odmlib/releases/tag/v0.1.4
