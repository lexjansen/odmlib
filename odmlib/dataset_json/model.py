"""Dataset-JSON v1.1 model for odmlib.

Provides classes for creating, reading, and validating Dataset-JSON
documents per the CDISC Dataset-JSON v1.1 specification.

Key differences from Dataset-XML (odmlib.dataset_1_0_1):
- Column-oriented data (items metadata + rows of value arrays)
- camelCase property names at root level to match JSON spec
- Dataset name as key in itemGroupData dict instead of OID
- No XML serialization; pure JSON I/O

The Dataset-JSON v1.1 root structure:

.. code-block:: json

    {
        "datasetJSONVersion": "1.1.0",
        "fileOID": "...",
        "creationDateTime": "...",
        "clinicalData": {
            "studyOID": "...",
            "metaDataVersionOID": "...",
            "itemGroupData": {
                "AE": {
                    "records": 42,
                    "name": "AE",
                    "label": "Adverse Events",
                    "items": [ ... ],
                    "itemGroupDataSeq": [ [...], [...] ]
                }
            }
        }
    }
"""
from __future__ import annotations
from typing import Any, Optional
import json


class ItemMetadata:
    """Column definition for a dataset variable.

    Corresponds to one entry in a Dataset-JSON ``items`` array.  Each
    ``ItemMetadata`` defines one column (variable) of the dataset and links
    it back to the Define-XML ItemDef via its OID.

    Attributes:
        OID: The ItemDef OID from the Define-XML (e.g., "IT.STUDYID").
        name: Variable name (e.g., "STUDYID", "AETERM").
        label: Human-readable variable label.
        type: Data type; one of "string", "integer", "float", "double",
            "decimal", "boolean", "datetime", "date", "time", "URI".
        length: Optional maximum length for string variables.
        displayFormat: Optional SAS-style display format.
        keySequence: Optional sort key sequence number.
    """

    def __init__(
        self,
        OID: str,
        name: str,
        label: str,
        type: str,
        length: Optional[int] = None,
        displayFormat: Optional[str] = None,
        keySequence: Optional[int] = None,
    ) -> None:
        self.OID = OID
        self.name = name
        self.label = label
        self.type = type
        self.length = length
        self.displayFormat = displayFormat
        self.keySequence = keySequence

    def to_dict(self) -> dict[str, Any]:
        """Serialize this column definition to a dict for JSON output."""
        d: dict[str, Any] = {
            "OID": self.OID,
            "name": self.name,
            "label": self.label,
            "type": self.type,
        }
        if self.length is not None:
            d["length"] = self.length
        if self.displayFormat is not None:
            d["displayFormat"] = self.displayFormat
        if self.keySequence is not None:
            d["keySequence"] = self.keySequence
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ItemMetadata":
        """Deserialize an ItemMetadata from a dict (one entry in ``items``)."""
        return cls(
            OID=data["OID"],
            name=data["name"],
            label=data.get("label", ""),
            type=data["type"],
            length=data.get("length"),
            displayFormat=data.get("displayFormat"),
            keySequence=data.get("keySequence"),
        )

    def __repr__(self) -> str:
        return f"ItemMetadata(OID={self.OID!r}, name={self.name!r}, type={self.type!r})"


class DatasetRecord:
    """A single row of data in a dataset.

    Stores values as a list corresponding to the column order defined by
    the parent dataset's ``items`` list.  A value of ``None`` indicates
    a missing value for that column in this row.

    Attributes:
        values: List of values in column order.
    """

    def __init__(self, values: list[Any]) -> None:
        self.values = values

    def __repr__(self) -> str:
        return f"DatasetRecord({self.values!r})"


class Dataset:
    """A single dataset (domain) in Dataset-JSON format.

    Corresponds to one entry under ``clinicalData.itemGroupData`` in the
    Dataset-JSON file.  A dataset has column definitions (``items``) and
    an array of data rows (``records``).

    Attributes:
        name: Dataset name (e.g., "AE", "DM").  Used as the key in the
            ``itemGroupData`` dict.
        label: Human-readable dataset label.
        items: List of :class:`ItemMetadata` defining the columns.
        records: List of :class:`DatasetRecord` containing the row data.
    """

    def __init__(
        self,
        name: str,
        label: str,
        items: Optional[list[ItemMetadata]] = None,
        records: Optional[list[DatasetRecord]] = None,
    ) -> None:
        self.name = name
        self.label = label
        self.items = items or []
        self.records = records or []

    @property
    def item_names(self) -> list[str]:
        """Variable names in column order."""
        return [item.name for item in self.items]

    def add_record(self, values: list[Any]) -> None:
        """Add a row of data.

        Args:
            values: List of values matching the column order of ``self.items``.

        Raises:
            ValueError: If ``len(values) != len(self.items)``.
        """
        if len(values) != len(self.items):
            raise ValueError(
                f"Expected {len(self.items)} values for dataset '{self.name}', "
                f"got {len(values)}"
            )
        self.records.append(DatasetRecord(values))

    def to_dict(self) -> dict[str, Any]:
        """Serialize this dataset to a dict for JSON output."""
        return {
            "records": len(self.records),
            "name": self.name,
            "label": self.label,
            "items": [item.to_dict() for item in self.items],
            "itemGroupDataSeq": [rec.values for rec in self.records],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Dataset":
        """Deserialize a Dataset from a dict (one entry in ``itemGroupData``)."""
        items = [ItemMetadata.from_dict(item) for item in data.get("items", [])]
        records = [DatasetRecord(row) for row in data.get("itemGroupDataSeq", [])]
        return cls(
            name=data["name"],
            label=data.get("label", ""),
            items=items,
            records=records,
        )

    def __len__(self) -> int:
        return len(self.records)

    def __repr__(self) -> str:
        return (
            f"Dataset(name={self.name!r}, label={self.label!r}, "
            f"records={len(self.records)}, columns={len(self.items)})"
        )


class DatasetJSON:
    """Root object for a Dataset-JSON v1.1 document.

    Represents a complete Dataset-JSON file per the CDISC Dataset-JSON v1.1
    specification.  Supports creating documents programmatically,
    serializing to JSON, and deserializing from JSON.

    Attributes:
        datasetJSONVersion: Specification version string (default "1.1.0").
        fileOID: Globally unique identifier for this file.
        creationDateTime: ISO 8601 creation timestamp.
        studyOID: Study OID from the Define-XML.
        metaDataVersionOID: MetaDataVersion OID from the Define-XML.
        asOfDateTime: Optional ISO 8601 point-in-time for the data.
        originator: Optional name of the originating organization.
        sourceSystem: Optional name of the source system.
        sourceSystemVersion: Optional version of the source system.
        metaDataRef: Optional URI to the associated Define-XML file.
        datasets: List of :class:`Dataset` objects in this file.

    Example::

        dsjson = DatasetJSON(
            fileOID="ODM.DATASET.001",
            creationDateTime="2024-01-15T12:00:00",
            studyOID="CDISC01",
            metaDataVersionOID="MDV.001",
        )
        items = [ItemMetadata(OID="IT.A", name="A", label="Var A", type="string")]
        ds = Dataset(name="AE", label="Adverse Events", items=items)
        ds.add_record(["value"])
        dsjson.add_dataset(ds)
        dsjson.write_json("ae.json")
    """

    def __init__(
        self,
        datasetJSONVersion: str = "1.1.0",
        fileOID: str = "",
        creationDateTime: str = "",
        studyOID: str = "",
        metaDataVersionOID: str = "",
        asOfDateTime: Optional[str] = None,
        originator: Optional[str] = None,
        sourceSystem: Optional[str] = None,
        sourceSystemVersion: Optional[str] = None,
        metaDataRef: Optional[str] = None,
        datasets: Optional[list[Dataset]] = None,
    ) -> None:
        self.datasetJSONVersion = datasetJSONVersion
        self.fileOID = fileOID
        self.creationDateTime = creationDateTime
        self.studyOID = studyOID
        self.metaDataVersionOID = metaDataVersionOID
        self.asOfDateTime = asOfDateTime
        self.originator = originator
        self.sourceSystem = sourceSystem
        self.sourceSystemVersion = sourceSystemVersion
        self.metaDataRef = metaDataRef
        self.datasets = datasets or []

    def add_dataset(self, dataset: Dataset) -> None:
        """Append a :class:`Dataset` to this document."""
        self.datasets.append(dataset)

    def get_dataset(self, name: str) -> Optional[Dataset]:
        """Return the dataset with the given name, or None if not found."""
        for ds in self.datasets:
            if ds.name == name:
                return ds
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize this document to a nested dict for JSON output."""
        clinical: dict[str, Any] = {
            "studyOID": self.studyOID,
            "metaDataVersionOID": self.metaDataVersionOID,
            "itemGroupData": {ds.name: ds.to_dict() for ds in self.datasets},
        }
        if self.metaDataRef:
            clinical["metaDataRef"] = self.metaDataRef

        d: dict[str, Any] = {
            "datasetJSONVersion": self.datasetJSONVersion,
            "fileOID": self.fileOID,
            "creationDateTime": self.creationDateTime,
            "clinicalData": clinical,
        }
        if self.asOfDateTime:
            d["asOfDateTime"] = self.asOfDateTime
        if self.originator:
            d["originator"] = self.originator
        if self.sourceSystem:
            d["sourceSystem"] = self.sourceSystem
        if self.sourceSystemVersion:
            d["sourceSystemVersion"] = self.sourceSystemVersion
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize to a JSON string.

        Args:
            indent: Number of spaces for JSON indentation (default 2).

        Returns:
            A formatted JSON string.
        """
        return json.dumps(self.to_dict(), indent=indent)

    def write_json(self, filename: str, indent: int = 2) -> None:
        """Write this document to a JSON file.

        Args:
            filename: Path to the output file.
            indent: Number of spaces for JSON indentation (default 2).
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DatasetJSON":
        """Deserialize a DatasetJSON from a nested dict.

        Args:
            data: Dict as produced by :meth:`to_dict` or parsed from JSON.

        Returns:
            A populated :class:`DatasetJSON` instance.
        """
        clinical = data.get("clinicalData", {})
        igdata = clinical.get("itemGroupData", {})
        datasets = [Dataset.from_dict(ds_data) for ds_data in igdata.values()]
        return cls(
            datasetJSONVersion=data.get("datasetJSONVersion", "1.1.0"),
            fileOID=data.get("fileOID", ""),
            creationDateTime=data.get("creationDateTime", ""),
            studyOID=clinical.get("studyOID", ""),
            metaDataVersionOID=clinical.get("metaDataVersionOID", ""),
            asOfDateTime=data.get("asOfDateTime"),
            originator=data.get("originator"),
            sourceSystem=data.get("sourceSystem"),
            sourceSystemVersion=data.get("sourceSystemVersion"),
            metaDataRef=clinical.get("metaDataRef"),
            datasets=datasets,
        )

    @classmethod
    def from_json(cls, json_string: str) -> "DatasetJSON":
        """Deserialize a DatasetJSON from a JSON string.

        Args:
            json_string: A JSON string as returned by :meth:`to_json`.

        Returns:
            A populated :class:`DatasetJSON` instance.
        """
        return cls.from_dict(json.loads(json_string))

    @classmethod
    def read_json(cls, filename: str) -> "DatasetJSON":
        """Read a Dataset-JSON file from disk.

        Args:
            filename: Path to the JSON file.

        Returns:
            A populated :class:`DatasetJSON` instance.
        """
        with open(filename, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def __repr__(self) -> str:
        return (
            f"DatasetJSON(fileOID={self.fileOID!r}, "
            f"studyOID={self.studyOID!r}, "
            f"datasets={len(self.datasets)})"
        )
