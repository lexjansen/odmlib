"""Converters between odmlib object models and Dataset-JSON format.

Provides utilities to:

- Convert Dataset-XML (``odmlib.dataset_1_0_1``) objects to Dataset-JSON
- Convert Dataset-JSON to Dataset-XML objects
- Extract column metadata from Define-XML ItemDefs when available

The primary entry point is :func:`dataset_xml_to_json`, which converts
an odmlib Dataset-XML ODM root object to a :class:`~odmlib.dataset_json.model.DatasetJSON`
ready for serialization.

Example::

    import odmlib.odm_loader as OL
    import odmlib.loader as LD
    import odmlib.ns_registry as NS
    from odmlib.dataset_json.converter import dataset_xml_to_json

    NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
                         is_default=True)
    NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")

    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="dataset_1_0_1",
                                          ns_uri="http://www.cdisc.org/ns/Dataset-XML/v1.0"))
    loader.open_odm_document("ae.xml")
    odm = loader.root()

    dsjson = dataset_xml_to_json(odm)
    dsjson.write_json("ae_dataset.json")
"""
from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING

from odmlib.dataset_json.model import DatasetJSON, Dataset, ItemMetadata, DatasetRecord

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Mapping from ODM DataType to Dataset-JSON type
# ---------------------------------------------------------------------------

_ODM_TO_DSJ_TYPE: dict[str, str] = {
    "text": "string",
    "string": "string",
    "integer": "integer",
    "float": "float",
    "double": "double",
    "decimal": "decimal",
    "date": "date",
    "time": "time",
    "datetime": "datetime",
    "boolean": "boolean",
    "URI": "URI",
    "partialDate": "string",
    "partialTime": "string",
    "partialDatetime": "string",
    "durationDatetime": "string",
    "intervalDatetime": "string",
    "incompleteDatetime": "string",
    "base64Binary": "string",
    "hexBinary": "string",
}


def dataset_xml_to_json(
    odm_obj: Any,
    define_mdv: Optional[Any] = None,
) -> DatasetJSON:
    """Convert an odmlib Dataset-XML ODM object to Dataset-JSON.

    Reads the ``ClinicalData`` section of a Dataset-XML 1.0.1 odmlib
    object and produces an equivalent :class:`~odmlib.dataset_json.model.DatasetJSON`
    in column-oriented format.

    Multiple ``ItemGroupData`` rows with the same ``ItemGroupOID`` are
    merged into one dataset.  The column set is the union of all ``ItemOID``
    values observed across all rows for that group.

    Args:
        odm_obj: An ODM root object from the ``dataset_1_0_1`` model
            (i.e., the object returned by a loader's ``root()`` or
            ``load_odm()`` method).
        define_mdv: Optional ``MetaDataVersion`` object from a loaded
            Define-XML document.  When provided, column labels, types,
            and lengths are read from the corresponding ``ItemDef``
            elements rather than defaulting to OID-based placeholders.

    Returns:
        A fully populated :class:`~odmlib.dataset_json.model.DatasetJSON`
        ready for :meth:`~odmlib.dataset_json.model.DatasetJSON.write_json`.

    Raises:
        AttributeError: If ``odm_obj`` does not have the expected
            Dataset-XML 1.0.1 structure.
    """
    dsjson = DatasetJSON(
        fileOID=getattr(odm_obj, "FileOID", ""),
        creationDateTime=getattr(odm_obj, "CreationDateTime", ""),
        asOfDateTime=getattr(odm_obj, "AsOfDateTime", None),
        originator=getattr(odm_obj, "Originator", None),
        sourceSystem=getattr(odm_obj, "SourceSystem", None),
        sourceSystemVersion=getattr(odm_obj, "SourceSystemVersion", None),
    )

    clinical = getattr(odm_obj, "ClinicalData", None)
    if clinical is None:
        return dsjson

    dsjson.studyOID = getattr(clinical, "StudyOID", "")
    dsjson.metaDataVersionOID = getattr(clinical, "MetaDataVersionOID", "")

    # Group ItemGroupData records by ItemGroupOID.  Each unique OID becomes
    # one dataset in the output.
    datasets_by_oid: dict[str, list[Any]] = {}
    for igd in (getattr(clinical, "ItemGroupData", None) or []):
        oid = igd.ItemGroupOID
        if oid not in datasets_by_oid:
            datasets_by_oid[oid] = []
        datasets_by_oid[oid].append(igd)

    for oid, igd_list in datasets_by_oid.items():
        # Collect the union of all ItemOIDs appearing across rows, preserving
        # insertion order so column order is stable.
        item_oids: list[str] = []
        seen: set[str] = set()
        for igd in igd_list:
            for item_data in (getattr(igd, "ItemData", None) or []):
                if item_data.ItemOID not in seen:
                    item_oids.append(item_data.ItemOID)
                    seen.add(item_data.ItemOID)

        # Build column metadata, enriching from Define-XML when available.
        items = [_get_item_metadata(ioid, define_mdv) for ioid in item_oids]

        # Derive a human-readable dataset name from the OID.  For OIDs like
        # "IG.AE" use the trailing segment; otherwise fall through to the OID.
        ds_name = oid.split(".")[-1] if "." in oid else oid
        ds_label = _get_itemgroup_label(oid, define_mdv)

        dataset = Dataset(name=ds_name, label=ds_label, items=items)
        for igd in igd_list:
            values = _extract_row_values(igd, item_oids)
            dataset.records.append(DatasetRecord(values))

        dsjson.add_dataset(dataset)

    return dsjson


def dataset_json_to_xml(
    dsjson: DatasetJSON,
    dataset_xml_model: Any,
) -> Any:
    """Convert a :class:`~odmlib.dataset_json.model.DatasetJSON` to a Dataset-XML odmlib object.

    Args:
        dsjson: A :class:`~odmlib.dataset_json.model.DatasetJSON` instance.
        dataset_xml_model: The ``odmlib.dataset_1_0_1.model`` module (or
            equivalent) containing ``ODM``, ``ClinicalData``,
            ``ItemGroupData``, and ``ItemData`` classes.

    Returns:
        An odmlib ODM root object populated with ClinicalData, suitable
        for serialization with :meth:`write_xml`.
    """
    import datetime

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    odm = dataset_xml_model.ODM(
        FileOID=dsjson.fileOID,
        FileType="Snapshot",
        CreationDateTime=dsjson.creationDateTime or now,
        DatasetXMLVersion="1.0.1",
    )
    if dsjson.asOfDateTime:
        odm.AsOfDateTime = dsjson.asOfDateTime
    if dsjson.originator:
        odm.Originator = dsjson.originator
    if dsjson.sourceSystem:
        odm.SourceSystem = dsjson.sourceSystem
    if dsjson.sourceSystemVersion:
        odm.SourceSystemVersion = dsjson.sourceSystemVersion

    clinical = dataset_xml_model.ClinicalData(
        StudyOID=dsjson.studyOID,
        MetaDataVersionOID=dsjson.metaDataVersionOID,
    )
    odm.ClinicalData = clinical

    seq = 1
    for dataset in dsjson.datasets:
        item_names = dataset.item_names
        for record in dataset.records:
            igd = dataset_xml_model.ItemGroupData(
                ItemGroupOID=dataset.name,
                ItemGroupDataSeq=str(seq),
            )
            for col_name, value in zip(item_names, record.values):
                if value is not None:
                    # Find ItemOID from items list
                    item_oid = _name_to_oid(col_name, dataset)
                    igd.ItemData.append(
                        dataset_xml_model.ItemData(
                            ItemOID=item_oid,
                            Value=str(value),
                        )
                    )
            clinical.ItemGroupData.append(igd)
            seq += 1

    return odm


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_item_metadata(item_oid: str, define_mdv: Optional[Any]) -> ItemMetadata:
    """Return ItemMetadata for *item_oid*, enriched from Define-XML if available."""
    if define_mdv is not None:
        item_defs = getattr(define_mdv, "ItemDef", None) or []
        for item_def in item_defs:
            if getattr(item_def, "OID", None) == item_oid:
                return ItemMetadata(
                    OID=item_oid,
                    name=getattr(item_def, "Name", item_oid),
                    label=_get_description_text(item_def),
                    type=_map_data_type(getattr(item_def, "DataType", "string")),
                    length=getattr(item_def, "Length", None),
                )
    # Fallback: minimal metadata derived from the OID
    name = item_oid.split(".")[-1] if "." in item_oid else item_oid
    return ItemMetadata(OID=item_oid, name=name, label="", type="string")


def _get_itemgroup_label(item_group_oid: str, define_mdv: Optional[Any]) -> str:
    """Return the label for an ItemGroupDef from Define-XML, or empty string."""
    if define_mdv is None:
        return ""
    ig_defs = getattr(define_mdv, "ItemGroupDef", None) or []
    for ig_def in ig_defs:
        if getattr(ig_def, "OID", None) == item_group_oid:
            return _get_description_text(ig_def)
    return ""


def _get_description_text(element: Any) -> str:
    """Extract description text from an odmlib element's Description child."""
    desc = getattr(element, "Description", None)
    if desc is not None and hasattr(desc, "TranslatedText"):
        tt_list = desc.TranslatedText
        if tt_list:
            return getattr(tt_list[0], "_content", "") or ""
    return ""


def _map_data_type(odm_type: str) -> str:
    """Map an ODM DataType string to a Dataset-JSON type string."""
    return _ODM_TO_DSJ_TYPE.get(odm_type, "string")


def _extract_row_values(igd: Any, item_oids: list[str]) -> list[Any]:
    """Extract an ordered list of values from an ItemGroupData row.

    Values are placed in the column order defined by *item_oids*.
    Missing items (not present in this row) are represented as ``None``.
    """
    oid_to_value: dict[str, Any] = {}
    for item_data in (getattr(igd, "ItemData", None) or []):
        oid_to_value[item_data.ItemOID] = getattr(item_data, "Value", None)
    return [oid_to_value.get(oid) for oid in item_oids]


def _name_to_oid(col_name: str, dataset: Dataset) -> str:
    """Look up the OID for a column name in a Dataset's items list."""
    for item in dataset.items:
        if item.name == col_name:
            return item.OID
    return col_name
