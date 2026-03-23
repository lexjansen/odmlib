# odmlib

[![CI](https://github.com/swhume/odmlib/actions/workflows/ci.yml/badge.svg)](https://github.com/swhume/odmlib/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/odmlib.svg)](https://badge.fury.io/py/odmlib)
[![Python versions](https://img.shields.io/pypi/pyversions/odmlib)](https://pypi.org/project/odmlib/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

A Python library for creating, parsing, and validating CDISC ODM (Operational Data Model)
documents and extensions including Define-XML, Dataset-XML, and CT-XML.

## Supported Standards

| Standard | Package | Status |
|----------|---------|--------|
| ODM 1.3.2 | `odmlib.odm_1_3_2` | Stable |
| ODM 2.0 | `odmlib.odm_2_0` | Draft |
| Define-XML 2.0 | `odmlib.define_2_0` | Stable |
| Define-XML 2.1 | `odmlib.define_2_1` | Stable |
| Dataset-XML 1.0.1 | `odmlib.dataset_1_0_1` | Stable |
| CT-XML 1.1.1 | `odmlib.ct_1_1_1` | Stable |
| ARM 1.0 | `odmlib.arm_1_0` | Stable |
| Dataset-JSON v1.1 | `odmlib.dataset_json_1_1` | Stable |
| Dataset-JSON (legacy) | `odmlib.dataset_json` | Deprecated |

## Quick Start

### Load an existing ODM-XML file

```python
import odmlib.odm_loader as OL
import odmlib.loader as LD

loader = LD.ODMLoader(OL.XMLODMLoader())
loader.open_odm_document("study.xml")
odm = loader.root()

mdv = loader.MetaDataVersion()
for item_group in mdv.ItemGroupDef:
    print(f"{item_group.OID}: {item_group.Name}")

# Find a specific element
item = mdv.find("ItemDef", "OID", "IT.AGE")
```

### Load an ARM-extended Define-XML (ADaM)

```python
import odmlib.arm_loader as AL
import odmlib.loader as LD

loader = LD.ODMLoader(AL.XMLArmLoader())
loader.open_odm_document("define-adam.xml")
mdv = loader.MetaDataVersion()

# Access analysis result displays
for rd in mdv.AnalysisResultDisplays:
    print(f"{rd.OID}: {rd.Name}")
    for ar in rd.AnalysisResult:
        print(f"  Result: {ar.OID} ({ar.AnalysisPurpose})")
```

### Create an ODM document

```python
import odmlib.odm_1_3_2.model as ODM
import odmlib.ns_registry as NS

NS.NamespaceRegistry(prefix="odm",
    uri="http://www.cdisc.org/ns/odm/v1.3",
    is_default=True, is_reset=True)

gv = ODM.GlobalVariables(
    StudyName=ODM.StudyName(_content="My Study"),
    StudyDescription=ODM.StudyDescription(_content="Phase II trial"),
    ProtocolName=ODM.ProtocolName(_content="PROT-001"),
)
mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Version 1")
study = ODM.Study(OID="S.001", GlobalVariables=gv, MetaDataVersion=[mdv])
odm = ODM.ODM(
    FileOID="F.001", FileType="Snapshot",
    CreationDateTime="2024-01-01T00:00:00", Study=[study]
)
odm.write_xml("study.xml")
```

## Installation

```bash
pip install odmlib
```

For development:

```bash
git clone https://github.com/swhume/odmlib.git
cd odmlib
pip install -e ".[dev]"
```

## Features

- **Object-oriented interface** — work with ODM elements as Python objects
- **Type-validated attributes** — all assignments validated at assignment time
- **Bidirectional serialization** — convert between XML, JSON, and Python dicts
- **Validation** — OID uniqueness, ref/def integrity, Cerberus conformance, element ordering
- **Dynamic OID checking** — automatic ref/def mapping via model introspection
- **Extensible** — create custom extensions by subclassing model classes
- **Builder API** — fluent `ODMBuilder` for programmatic document construction
- **Context managers** — `open_odm()` and `open_define()` for safe file handling
- **Dataset-JSON v1.1** — create, read, write, and convert CDISC Dataset-JSON documents
- **Pandas integration** — export metadata/data to DataFrames; import DataFrame rows as ODM objects (optional, `pip install odmlib[dataframe]`)

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=odmlib --cov-report=term-missing

# Run a specific test file
python -m pytest tests/test_odm_loader.py -v
```

## Documentation

- [API Reference](https://swhume.github.io/odmlib)
- [Example Programs](https://github.com/swhume/odmlib_examples)
- [CDISC ODM Specification](https://www.cdisc.org/standards/data-exchange/odm)

## Dependencies

- [xmlschema](https://pypi.org/project/xmlschema/) — XML Schema validation
- [validators](https://pypi.org/project/validators/) — email/URL validation
- [Cerberus](https://docs.python-cerberus.org/) — conformance schema validation
- [pathvalidate](https://pypi.org/project/pathvalidate/) — filename validation

**Optional:**

- [pandas](https://pandas.pydata.org/) ≥ 1.5 — DataFrame integration (`pip install odmlib[dataframe]`)

## Known Limitations

- No `ItemData[Type]` support (typed item data elements, deprecated in ODM v2.0)
- No `ds:Signature` support (digital signatures)
- Single `MetaDataVersion` per load by default (use `idx` parameter for others)
- ODM v2.0 implementation is still draft

## License

[MIT](LICENSE.md)

## Contributing

Issues and pull requests are welcome at
[https://github.com/swhume/odmlib/issues](https://github.com/swhume/odmlib/issues).
