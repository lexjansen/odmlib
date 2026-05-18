"""Flatten Define-XML v2.1 metadata into tabular Dataset-JSON v1.1 datasets.

This module converts a loaded Define-XML v2.1 ODM object hierarchy into
a set of Dataset-JSON v1.1 datasets, one per metadata table. Each table
captures a different aspect of the Define-XML metadata in a flat,
tabular format suitable for analysis and round-tripping.

Classes:
    :class:`DefineFlattener` -- converts Define-XML v2.1 to Dataset-JSON tables

Target datasets (11 core):
    study, standards, datasets, variables, value_level, where_clauses,
    methods, comments, documents, codelists, codelist_terms

Additional datasets (lossless-roundtrip extensions, optional on read):
    aliases, origins
"""
from __future__ import annotations

import datetime
import os
from typing import Any, Optional

from odmlib.dataset_json_1_1.model import DatasetJSON, Column


def _safe_get(element: Any, *attrs, default=None) -> Any:
    """Safely traverse nested optional attributes and indices.

    Navigates through a chain of attribute accesses and list indexing,
    returning ``default`` if any level is missing, None, or raises
    AttributeError/IndexError/TypeError.

    Args:
        element: Starting object.
        *attrs: Sequence of attribute names (str) or list indices (int).
        default: Value to return if traversal fails (default: None).

    Returns:
        The value at the end of the chain, or ``default``.

    Examples:
        >>> _safe_get(item_def, "Description", "TranslatedText", 0, "_content")
        'Age'
        >>> _safe_get(item_def, "CodeListRef", "CodeListOID")
        'CL.AGEU'
        >>> _safe_get(None, "anything")  # returns None
    """
    current = element
    for attr in attrs:
        if current is None:
            return default
        try:
            if isinstance(attr, int):
                current = current[attr]
            else:
                current = getattr(current, attr)
        except (AttributeError, IndexError, TypeError, KeyError):
            return default
    return current if current is not None else default


def _make_column(item_oid: str, name: str, label: str,
                 data_type: str = "string", key_seq: int = None) -> Column:
    """Create a Column with common defaults."""
    kwargs = {
        "itemOID": item_oid,
        "name": name,
        "label": label,
        "dataType": data_type,
    }
    if key_seq is not None:
        kwargs["keySequence"] = key_seq
    return Column(**kwargs)


def _str_or_none(value: Any) -> Optional[str]:
    """Convert a value to string, or return None if it is None."""
    if value is None:
        return None
    return str(value)


class DefineFlattener:
    """Convert Define-XML v2.1 metadata into tabular Dataset-JSON datasets.

    Initializes with a loaded Define-XML v2.1 ODM root object and provides
    methods to flatten each metadata element type into a separate
    Dataset-JSON v1.1 dataset.

    Args:
        odm_root: A loaded Define-XML v2.1 ODM root object (from odmlib loader).
        study_idx: Index of the Study element to use (default: 0). For
            Define-XML, there is always exactly one Study.

    Example::

        import odmlib.define_loader as DL
        import odmlib.loader as LD
        from odmlib.dataset_json_1_1.define_flattener import DefineFlattener

        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package='define_2_1'))
        loader.open_odm_document('define.xml')
        odm = loader.root()

        flattener = DefineFlattener(odm)
        datasets = flattener.flatten_all()
        flattener.write_all('/output/dir')
    """

    # Dataset-JSON version for all generated files
    DATASET_JSON_VERSION = "1.1.0"

    # Names of all metadata tables produced by flatten_all
    TABLE_NAMES = [
        "study", "standards", "datasets", "variables", "value_level",
        "where_clauses", "methods", "comments", "documents",
        "codelists", "codelist_terms",
    ]

    # Lossless-roundtrip extension datasets (optional when reading back)
    EXTRA_TABLE_NAMES = ["aliases", "origins"]

    def __init__(self, odm_root: Any, study_idx: int = 0):
        self._odm = odm_root
        self._study = odm_root.Study
        self._gv = self._study.GlobalVariables
        self._mdv = self._study.MetaDataVersion
        self._creation_dt = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
        # Build lookup indexes for O(1) access
        self._item_def_index = self._build_item_def_index()
        self._where_clause_index = self._build_where_clause_index()

    def _build_item_def_index(self) -> dict:
        """Build OID -> ItemDef lookup from MetaDataVersion.ItemDef."""
        item_defs = getattr(self._mdv, "ItemDef", None) or []
        return {item_def.OID: item_def for item_def in item_defs}

    def _build_where_clause_index(self) -> dict:
        """Build OID -> WhereClauseDef lookup."""
        wc_defs = getattr(self._mdv, "WhereClauseDef", None) or []
        return {wc.OID: wc for wc in wc_defs}

    def _make_dataset(self, name: str, label: str, columns: list,
                      rows: list) -> DatasetJSON:
        """Create a DatasetJSON instance with standard metadata fields."""
        ds = DatasetJSON(
            datasetJSONCreationDateTime=self._creation_dt,
            datasetJSONVersion=self.DATASET_JSON_VERSION,
            fileOID=_safe_get(self._odm, "FileOID"),
            studyOID=_safe_get(self._study, "OID"),
            metaDataVersionOID=_safe_get(self._mdv, "OID"),
            itemGroupOID=f"IG.DEFINE.{name.upper()}",
            records=len(rows),
            name=name,
            label=label,
            columns=columns,
        )
        if rows:
            ds.rows = rows
        return ds

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def flatten_all(self) -> dict:
        """Flatten all Define-XML metadata into Dataset-JSON datasets.

        Returns:
            dict[str, DatasetJSON]: Mapping of dataset name to DatasetJSON
                for all 11 metadata tables.
        """
        return {
            "study": self.flatten_study(),
            "standards": self.flatten_standards(),
            "datasets": self.flatten_datasets(),
            "variables": self.flatten_variables(),
            "value_level": self.flatten_value_level(),
            "where_clauses": self.flatten_where_clauses(),
            "methods": self.flatten_methods(),
            "comments": self.flatten_comments(),
            "documents": self.flatten_documents(),
            "codelists": self.flatten_codelists(),
            "codelist_terms": self.flatten_codelist_terms(),
            "aliases": self.flatten_aliases(),
            "origins": self.flatten_origins(),
        }

    def write_all(self, output_dir: str, indent: int = 2) -> list:
        """Write all metadata datasets to individual JSON files.

        Args:
            output_dir: Directory to write files to. Created if it does
                not exist.
            indent: JSON indentation level (default: 2).

        Returns:
            list[str]: List of written file paths.
        """
        os.makedirs(output_dir, exist_ok=True)
        datasets = self.flatten_all()
        paths = []
        for name, ds in datasets.items():
            path = os.path.join(output_dir, f"{name}.json")
            ds.write_json(path, indent=indent)
            paths.append(path)
        return paths

    # ------------------------------------------------------------------ #
    # Individual flatteners
    # ------------------------------------------------------------------ #

    def flatten_study(self) -> DatasetJSON:
        """Flatten ODM root + Study + GlobalVariables + MetaDataVersion.

        Returns:
            DatasetJSON: Single-row dataset with study-level metadata.
        """
        columns = [
            _make_column("DEFINE.STUDY.FILEOID", "FileOID", "File OID"),
            _make_column("DEFINE.STUDY.CREATIONDATETIME", "CreationDateTime",
                         "Creation Date/Time"),
            _make_column("DEFINE.STUDY.ASOFDATETIME", "AsOfDateTime",
                         "As-Of Date/Time"),
            _make_column("DEFINE.STUDY.ORIGINATOR", "Originator", "Originator"),
            _make_column("DEFINE.STUDY.SOURCESYSTEM", "SourceSystem",
                         "Source System"),
            _make_column("DEFINE.STUDY.SOURCESYSTEMVERSION",
                         "SourceSystemVersion", "Source System Version"),
            _make_column("DEFINE.STUDY.STUDYOID", "StudyOID", "Study OID"),
            _make_column("DEFINE.STUDY.STUDYNAME", "StudyName", "Study Name"),
            _make_column("DEFINE.STUDY.STUDYDESCRIPTION", "StudyDescription",
                         "Study Description"),
            _make_column("DEFINE.STUDY.PROTOCOLNAME", "ProtocolName",
                         "Protocol Name"),
            _make_column("DEFINE.STUDY.MDVOID", "MetaDataVersionOID",
                         "MetaDataVersion OID"),
            _make_column("DEFINE.STUDY.MDVNAME", "MetaDataVersionName",
                         "MetaDataVersion Name"),
            _make_column("DEFINE.STUDY.DEFINEVERSION", "DefineVersion",
                         "Define-XML Version"),
            _make_column("DEFINE.STUDY.COMMENTOID", "CommentOID",
                         "Comment OID"),
            _make_column("DEFINE.STUDY.CONTEXT", "Context", "Context"),
        ]

        row = [
            _safe_get(self._odm, "FileOID"),
            _safe_get(self._odm, "CreationDateTime"),
            _safe_get(self._odm, "AsOfDateTime"),
            _safe_get(self._odm, "Originator"),
            _safe_get(self._odm, "SourceSystem"),
            _safe_get(self._odm, "SourceSystemVersion"),
            _safe_get(self._study, "OID"),
            _safe_get(self._gv, "StudyName", "_content"),
            _safe_get(self._gv, "StudyDescription", "_content"),
            _safe_get(self._gv, "ProtocolName", "_content"),
            _safe_get(self._mdv, "OID"),
            _safe_get(self._mdv, "Name"),
            _safe_get(self._mdv, "DefineVersion"),
            _safe_get(self._mdv, "CommentOID"),
            _safe_get(self._odm, "Context"),
        ]

        return self._make_dataset("study", "Study Metadata", columns, [row])

    def flatten_standards(self) -> DatasetJSON:
        """Flatten MetaDataVersion.Standards.Standard elements.

        Returns:
            DatasetJSON: One row per Standard element. Empty if Standards
                are not loaded (known limitation).
        """
        columns = [
            _make_column("DEFINE.STD.OID", "OID", "Standard OID", key_seq=1),
            _make_column("DEFINE.STD.NAME", "Name", "Standard Name"),
            _make_column("DEFINE.STD.TYPE", "Type", "Standard Type"),
            _make_column("DEFINE.STD.PUBLISHINGSET", "PublishingSet",
                         "Publishing Set"),
            _make_column("DEFINE.STD.VERSION", "Version", "Standard Version"),
            _make_column("DEFINE.STD.STATUS", "Status", "Standard Status"),
            _make_column("DEFINE.STD.COMMENTOID", "CommentOID", "Comment OID"),
        ]

        rows = []
        standards_obj = _safe_get(self._mdv, "Standards")
        if standards_obj is not None:
            standard_list = _safe_get(standards_obj, "Standard") or []
            for std in standard_list:
                rows.append([
                    _safe_get(std, "OID"),
                    _safe_get(std, "Name"),
                    _safe_get(std, "Type"),
                    _safe_get(std, "PublishingSet"),
                    _safe_get(std, "Version"),
                    _safe_get(std, "Status"),
                    _safe_get(std, "CommentOID"),
                ])

        return self._make_dataset("standards", "Standards", columns, rows)

    def flatten_datasets(self) -> DatasetJSON:
        """Flatten MetaDataVersion.ItemGroupDef elements.

        Returns:
            DatasetJSON: One row per ItemGroupDef (dataset definition).
        """
        columns = [
            _make_column("DEFINE.DS.OID", "OID", "Dataset OID", key_seq=1),
            _make_column("DEFINE.DS.NAME", "Name", "Dataset Name"),
            _make_column("DEFINE.DS.REPEATING", "Repeating", "Repeating"),
            _make_column("DEFINE.DS.ISREFERENCEDATA", "IsReferenceData",
                         "Is Reference Data"),
            _make_column("DEFINE.DS.SASDATASETNAME", "SASDatasetName",
                         "SAS Dataset Name"),
            _make_column("DEFINE.DS.DOMAIN", "Domain", "Domain"),
            _make_column("DEFINE.DS.PURPOSE", "Purpose", "Purpose"),
            _make_column("DEFINE.DS.STRUCTURE", "Structure", "Structure"),
            _make_column("DEFINE.DS.ARCHIVELOCATIONID", "ArchiveLocationID",
                         "Archive Location ID"),
            _make_column("DEFINE.DS.COMMENTOID", "CommentOID", "Comment OID"),
            _make_column("DEFINE.DS.ISNONSTANDARD", "IsNonStandard",
                         "Is Non-Standard"),
            _make_column("DEFINE.DS.STANDARDOID", "StandardOID",
                         "Standard OID"),
            _make_column("DEFINE.DS.HASNODATA", "HasNoData", "Has No Data"),
            _make_column("DEFINE.DS.DESCRIPTIONTEXT", "DescriptionText",
                         "Description"),
            _make_column("DEFINE.DS.CLASSNAME", "ClassName", "Class Name"),
            _make_column("DEFINE.DS.SUBCLASSNAME", "SubClassName",
                         "Sub-Class Name"),
            _make_column("DEFINE.DS.LEAFID", "leafID", "Leaf ID"),
            _make_column("DEFINE.DS.LEAFHREF", "leafHref", "Leaf Href"),
            _make_column("DEFINE.DS.LEAFTITLE", "leafTitle", "Leaf Title"),
        ]

        rows = []
        item_group_defs = getattr(self._mdv, "ItemGroupDef", None) or []
        for igd in item_group_defs:
            rows.append([
                _safe_get(igd, "OID"),
                _safe_get(igd, "Name"),
                _safe_get(igd, "Repeating"),
                _safe_get(igd, "IsReferenceData"),
                _safe_get(igd, "SASDatasetName"),
                _safe_get(igd, "Domain"),
                _safe_get(igd, "Purpose"),
                _safe_get(igd, "Structure"),
                _safe_get(igd, "ArchiveLocationID"),
                _safe_get(igd, "CommentOID"),
                _safe_get(igd, "IsNonStandard"),
                _safe_get(igd, "StandardOID"),
                _safe_get(igd, "HasNoData"),
                _safe_get(igd, "Description", "TranslatedText", 0, "_content"),
                _safe_get(igd, "Class", "Name"),
                _safe_get(igd, "Class", "SubClass", 0, "Name"),
                _safe_get(igd, "leaf", "ID"),
                _safe_get(igd, "leaf", "href"),
                _safe_get(igd, "leaf", "title", "_content"),
            ])

        return self._make_dataset("datasets", "Dataset Definitions",
                                  columns, rows)

    def flatten_variables(self) -> DatasetJSON:
        """Flatten ItemRef + ItemDef pairs within each ItemGroupDef.

        Returns:
            DatasetJSON: One row per variable (ItemRef+ItemDef) per dataset.
        """
        columns = [
            _make_column("DEFINE.VAR.DATASETOID", "DatasetOID", "Dataset OID",
                         key_seq=1),
            _make_column("DEFINE.VAR.ITEMOID", "ItemOID", "Item OID",
                         key_seq=2),
            _make_column("DEFINE.VAR.ORDERNUMBER", "OrderNumber",
                         "Order Number", "integer"),
            _make_column("DEFINE.VAR.MANDATORY", "Mandatory", "Mandatory"),
            _make_column("DEFINE.VAR.KEYSEQUENCE", "KeySequence",
                         "Key Sequence", "integer"),
            _make_column("DEFINE.VAR.METHODOID", "MethodOID", "Method OID"),
            _make_column("DEFINE.VAR.ROLE", "Role", "Role"),
            _make_column("DEFINE.VAR.ROLECODELISTOID", "RoleCodeListOID",
                         "Role CodeList OID"),
            _make_column("DEFINE.VAR.ISNONSTANDARD", "IsNonStandard",
                         "Is Non-Standard"),
            _make_column("DEFINE.VAR.HASNODATA", "HasNoData", "Has No Data"),
            _make_column("DEFINE.VAR.NAME", "Name", "Variable Name"),
            _make_column("DEFINE.VAR.DATATYPE", "DataType", "Data Type"),
            _make_column("DEFINE.VAR.LENGTH", "Length", "Length", "integer"),
            _make_column("DEFINE.VAR.SIGNIFICANTDIGITS", "SignificantDigits",
                         "Significant Digits", "integer"),
            _make_column("DEFINE.VAR.SASFIELDNAME", "SASFieldName",
                         "SAS Field Name"),
            _make_column("DEFINE.VAR.DISPLAYFORMAT", "DisplayFormat",
                         "Display Format"),
            _make_column("DEFINE.VAR.COMMENTOID", "CommentOID", "Comment OID"),
            _make_column("DEFINE.VAR.DESCRIPTIONTEXT", "DescriptionText",
                         "Description"),
            _make_column("DEFINE.VAR.CODELISTOID", "CodeListOID",
                         "CodeList OID"),
            _make_column("DEFINE.VAR.VALUELISTOID", "ValueListOID",
                         "ValueList OID"),
            _make_column("DEFINE.VAR.ORIGINTYPE", "OriginType", "Origin Type"),
            _make_column("DEFINE.VAR.ORIGINSOURCE", "OriginSource",
                         "Origin Source"),
        ]

        rows = []
        item_group_defs = getattr(self._mdv, "ItemGroupDef", None) or []
        for igd in item_group_defs:
            dataset_oid = igd.OID
            item_refs = getattr(igd, "ItemRef", None) or []
            for item_ref in item_refs:
                item_oid = item_ref.ItemOID
                item_def = self._item_def_index.get(item_oid)

                rows.append([
                    dataset_oid,
                    item_oid,
                    _safe_get(item_ref, "OrderNumber"),
                    _safe_get(item_ref, "Mandatory"),
                    _safe_get(item_ref, "KeySequence"),
                    _safe_get(item_ref, "MethodOID"),
                    _safe_get(item_ref, "Role"),
                    _safe_get(item_ref, "RoleCodeListOID"),
                    _safe_get(item_ref, "IsNonStandard"),
                    _safe_get(item_ref, "HasNoData"),
                    _safe_get(item_def, "Name"),
                    _safe_get(item_def, "DataType"),
                    _safe_get(item_def, "Length"),
                    _safe_get(item_def, "SignificantDigits"),
                    _safe_get(item_def, "SASFieldName"),
                    _safe_get(item_def, "DisplayFormat"),
                    _safe_get(item_def, "CommentOID"),
                    _safe_get(item_def, "Description", "TranslatedText",
                              0, "_content"),
                    _safe_get(item_def, "CodeListRef", "CodeListOID"),
                    _safe_get(item_def, "ValueListRef", "ValueListOID"),
                    _safe_get(item_def, "Origin", 0, "Type"),
                    _safe_get(item_def, "Origin", 0, "Source"),
                ])

        return self._make_dataset("variables", "Variable Definitions",
                                  columns, rows)

    def flatten_value_level(self) -> DatasetJSON:
        """Flatten ValueListDef ItemRef entries with joined ItemDef metadata.

        Returns:
            DatasetJSON: One row per ItemRef within each ValueListDef.
        """
        columns = [
            _make_column("DEFINE.VL.VALUELISTOID", "ValueListOID",
                         "ValueList OID", key_seq=1),
            _make_column("DEFINE.VL.ITEMOID", "ItemOID", "Item OID",
                         key_seq=2),
            _make_column("DEFINE.VL.ORDERNUMBER", "OrderNumber",
                         "Order Number", "integer"),
            _make_column("DEFINE.VL.MANDATORY", "Mandatory", "Mandatory"),
            _make_column("DEFINE.VL.METHODOID", "MethodOID", "Method OID"),
            _make_column("DEFINE.VL.WHERECLAUSEOID", "WhereClauseOID",
                         "WhereClause OID"),
            _make_column("DEFINE.VL.NAME", "Name", "Variable Name"),
            _make_column("DEFINE.VL.DATATYPE", "DataType", "Data Type"),
            _make_column("DEFINE.VL.LENGTH", "Length", "Length", "integer"),
            _make_column("DEFINE.VL.SIGNIFICANTDIGITS", "SignificantDigits",
                         "Significant Digits", "integer"),
            _make_column("DEFINE.VL.SASFIELDNAME", "SASFieldName",
                         "SAS Field Name"),
            _make_column("DEFINE.VL.DISPLAYFORMAT", "DisplayFormat",
                         "Display Format"),
            _make_column("DEFINE.VL.COMMENTOID", "CommentOID", "Comment OID"),
            _make_column("DEFINE.VL.DESCRIPTIONTEXT", "DescriptionText",
                         "Description"),
            _make_column("DEFINE.VL.CODELISTOID", "CodeListOID",
                         "CodeList OID"),
            _make_column("DEFINE.VL.ORIGINTYPE", "OriginType", "Origin Type"),
            _make_column("DEFINE.VL.ORIGINSOURCE", "OriginSource",
                         "Origin Source"),
        ]

        rows = []
        value_list_defs = getattr(self._mdv, "ValueListDef", None) or []
        for vld in value_list_defs:
            vl_oid = vld.OID
            item_refs = getattr(vld, "ItemRef", None) or []
            for item_ref in item_refs:
                item_oid = item_ref.ItemOID
                item_def = self._item_def_index.get(item_oid)

                # Get first WhereClauseRef OID
                wc_oid = _safe_get(item_ref, "WhereClauseRef", 0,
                                   "WhereClauseOID")

                rows.append([
                    vl_oid,
                    item_oid,
                    _safe_get(item_ref, "OrderNumber"),
                    _safe_get(item_ref, "Mandatory"),
                    _safe_get(item_ref, "MethodOID"),
                    wc_oid,
                    _safe_get(item_def, "Name"),
                    _safe_get(item_def, "DataType"),
                    _safe_get(item_def, "Length"),
                    _safe_get(item_def, "SignificantDigits"),
                    _safe_get(item_def, "SASFieldName"),
                    _safe_get(item_def, "DisplayFormat"),
                    _safe_get(item_def, "CommentOID"),
                    _safe_get(item_def, "Description", "TranslatedText",
                              0, "_content"),
                    _safe_get(item_def, "CodeListRef", "CodeListOID"),
                    _safe_get(item_def, "Origin", 0, "Type"),
                    _safe_get(item_def, "Origin", 0, "Source"),
                ])

        return self._make_dataset("value_level",
                                  "Value-Level Metadata", columns, rows)

    def flatten_where_clauses(self) -> DatasetJSON:
        """Flatten WhereClauseDef RangeCheck elements.

        Returns:
            DatasetJSON: One row per RangeCheck within each WhereClauseDef.
        """
        columns = [
            _make_column("DEFINE.WC.WHERECLAUSEOID", "WhereClauseOID",
                         "WhereClause OID", key_seq=1),
            _make_column("DEFINE.WC.COMMENTOID", "WhereClauseCommentOID",
                         "WhereClause Comment OID"),
            _make_column("DEFINE.WC.COMPARATOR", "Comparator", "Comparator"),
            _make_column("DEFINE.WC.SOFTHARD", "SoftHard", "Soft/Hard"),
            _make_column("DEFINE.WC.ITEMOID", "ItemOID", "Item OID"),
            _make_column("DEFINE.WC.CHECKVALUES", "CheckValues",
                         "Check Values"),
        ]

        rows = []
        wc_defs = getattr(self._mdv, "WhereClauseDef", None) or []
        for wcd in wc_defs:
            wc_oid = wcd.OID
            wc_comment_oid = _safe_get(wcd, "CommentOID")
            range_checks = getattr(wcd, "RangeCheck", None) or []
            for rc in range_checks:
                # Join CheckValue._content values with ", "
                check_values = getattr(rc, "CheckValue", None) or []
                cv_str = ", ".join(
                    cv._content for cv in check_values
                    if _safe_get(cv, "_content") is not None
                )

                rows.append([
                    wc_oid,
                    wc_comment_oid,
                    _safe_get(rc, "Comparator"),
                    _safe_get(rc, "SoftHard"),
                    _safe_get(rc, "ItemOID"),
                    cv_str if cv_str else None,
                ])

        return self._make_dataset("where_clauses",
                                  "Where Clause Definitions", columns, rows)

    def flatten_methods(self) -> DatasetJSON:
        """Flatten MethodDef elements with FormalExpression denormalization.

        For methods with multiple FormalExpressions, produces one row per
        FormalExpression (repeating the parent fields) to ensure no data
        loss for round-tripping.

        Returns:
            DatasetJSON: One row per MethodDef (or per FormalExpression
                if multiple exist).
        """
        columns = [
            _make_column("DEFINE.MT.OID", "OID", "Method OID", key_seq=1),
            _make_column("DEFINE.MT.NAME", "Name", "Method Name"),
            _make_column("DEFINE.MT.TYPE", "Type", "Method Type"),
            _make_column("DEFINE.MT.DESCRIPTIONTEXT", "DescriptionText",
                         "Description"),
            _make_column("DEFINE.MT.FORMALEXPRESSIONCONTEXT",
                         "FormalExpressionContext",
                         "Formal Expression Context"),
            _make_column("DEFINE.MT.FORMALEXPRESSIONTEXT",
                         "FormalExpressionText", "Formal Expression Text"),
            _make_column("DEFINE.MT.DOCUMENTREFLEAFIDS",
                         "DocumentRefLeafIDs", "Document Ref Leaf IDs"),
        ]

        rows = []
        method_defs = getattr(self._mdv, "MethodDef", None) or []
        for md in method_defs:
            oid = _safe_get(md, "OID")
            name = _safe_get(md, "Name")
            mtype = _safe_get(md, "Type")
            desc = _safe_get(md, "Description", "TranslatedText",
                             0, "_content")

            # Collect DocumentRef leafIDs
            doc_refs = getattr(md, "DocumentRef", None) or []
            doc_leaf_ids = ", ".join(
                dr.leafID for dr in doc_refs
                if _safe_get(dr, "leafID") is not None
            )
            doc_leaf_ids = doc_leaf_ids if doc_leaf_ids else None

            # FormalExpressions: one row per expression, or one row with
            # None if no expressions
            formal_exprs = getattr(md, "FormalExpression", None) or []
            if formal_exprs:
                for fe in formal_exprs:
                    rows.append([
                        oid, name, mtype, desc,
                        _safe_get(fe, "Context"),
                        _safe_get(fe, "_content"),
                        doc_leaf_ids,
                    ])
            else:
                rows.append([
                    oid, name, mtype, desc,
                    None, None, doc_leaf_ids,
                ])

        return self._make_dataset("methods", "Method Definitions",
                                  columns, rows)

    def flatten_comments(self) -> DatasetJSON:
        """Flatten CommentDef elements.

        Returns:
            DatasetJSON: One row per CommentDef.
        """
        columns = [
            _make_column("DEFINE.COM.OID", "OID", "Comment OID", key_seq=1),
            _make_column("DEFINE.COM.DESCRIPTIONTEXT", "DescriptionText",
                         "Description"),
            _make_column("DEFINE.COM.DOCUMENTREFLEAFIDS",
                         "DocumentRefLeafIDs", "Document Ref Leaf IDs"),
        ]

        rows = []
        comment_defs = getattr(self._mdv, "CommentDef", None) or []
        for cd in comment_defs:
            doc_refs = getattr(cd, "DocumentRef", None) or []
            doc_leaf_ids = ", ".join(
                dr.leafID for dr in doc_refs
                if _safe_get(dr, "leafID") is not None
            )
            rows.append([
                _safe_get(cd, "OID"),
                _safe_get(cd, "Description", "TranslatedText", 0, "_content"),
                doc_leaf_ids if doc_leaf_ids else None,
            ])

        return self._make_dataset("comments", "Comment Definitions",
                                  columns, rows)

    def flatten_documents(self) -> DatasetJSON:
        """Flatten leaf (external document reference) elements.

        Returns:
            DatasetJSON: One row per leaf element.
        """
        columns = [
            _make_column("DEFINE.DOC.ID", "ID", "Document ID", key_seq=1),
            _make_column("DEFINE.DOC.HREF", "href", "Document Href"),
            _make_column("DEFINE.DOC.TITLE", "title", "Document Title"),
        ]

        rows = []
        leaves = getattr(self._mdv, "leaf", None) or []
        for lf in leaves:
            rows.append([
                _safe_get(lf, "ID"),
                _safe_get(lf, "href"),
                _safe_get(lf, "title", "_content"),
            ])

        return self._make_dataset("documents", "Document References",
                                  columns, rows)

    def flatten_codelists(self) -> DatasetJSON:
        """Flatten CodeList elements.

        Returns:
            DatasetJSON: One row per CodeList.
        """
        columns = [
            _make_column("DEFINE.CL.OID", "OID", "CodeList OID", key_seq=1),
            _make_column("DEFINE.CL.NAME", "Name", "CodeList Name"),
            _make_column("DEFINE.CL.DATATYPE", "DataType", "Data Type"),
            _make_column("DEFINE.CL.ISNONSTANDARD", "IsNonStandard",
                         "Is Non-Standard"),
            _make_column("DEFINE.CL.STANDARDOID", "StandardOID",
                         "Standard OID"),
            _make_column("DEFINE.CL.SASFORMATNAME", "SASFormatName",
                         "SAS Format Name"),
            _make_column("DEFINE.CL.COMMENTOID", "CommentOID", "Comment OID"),
            _make_column("DEFINE.CL.DESCRIPTIONTEXT", "DescriptionText",
                         "Description"),
            _make_column("DEFINE.CL.EXTERNALDICTIONARY", "ExternalDictionary",
                         "External Dictionary"),
            _make_column("DEFINE.CL.EXTERNALVERSION", "ExternalVersion",
                         "External Version"),
            _make_column("DEFINE.CL.EXTERNALREF", "ExternalRef",
                         "External Ref"),
            _make_column("DEFINE.CL.EXTERNALHREF", "ExternalHref",
                         "External Href"),
        ]

        rows = []
        code_lists = getattr(self._mdv, "CodeList", None) or []
        for cl in code_lists:
            rows.append([
                _safe_get(cl, "OID"),
                _safe_get(cl, "Name"),
                _safe_get(cl, "DataType"),
                _safe_get(cl, "IsNonStandard"),
                _safe_get(cl, "StandardOID"),
                _safe_get(cl, "SASFormatName"),
                _safe_get(cl, "CommentOID"),
                _safe_get(cl, "Description", "TranslatedText", 0, "_content"),
                _safe_get(cl, "ExternalCodeList", "Dictionary"),
                _safe_get(cl, "ExternalCodeList", "Version"),
                _safe_get(cl, "ExternalCodeList", "ref"),
                _safe_get(cl, "ExternalCodeList", "href"),
            ])

        return self._make_dataset("codelists", "CodeList Definitions",
                                  columns, rows)

    def flatten_codelist_terms(self) -> DatasetJSON:
        """Flatten CodeListItem and EnumeratedItem elements within CodeLists.

        Returns:
            DatasetJSON: One row per CodeListItem or EnumeratedItem.
        """
        columns = [
            _make_column("DEFINE.CLT.CODELISTOID", "CodeListOID",
                         "CodeList OID", key_seq=1),
            _make_column("DEFINE.CLT.CODEDVALUE", "CodedValue",
                         "Coded Value", key_seq=2),
            _make_column("DEFINE.CLT.RANK", "Rank", "Rank"),
            _make_column("DEFINE.CLT.ORDERNUMBER", "OrderNumber",
                         "Order Number", "integer"),
            _make_column("DEFINE.CLT.EXTENDEDVALUE", "ExtendedValue",
                         "Extended Value"),
            _make_column("DEFINE.CLT.DECODEDTEXT", "DecodedText",
                         "Decoded Text"),
        ]

        rows = []
        code_lists = getattr(self._mdv, "CodeList", None) or []
        for cl in code_lists:
            cl_oid = cl.OID

            # CodeListItems (have Decode)
            cli_items = getattr(cl, "CodeListItem", None) or []
            for cli in cli_items:
                rows.append([
                    cl_oid,
                    _safe_get(cli, "CodedValue"),
                    _safe_get(cli, "Rank"),
                    _safe_get(cli, "OrderNumber"),
                    _safe_get(cli, "ExtendedValue"),
                    _safe_get(cli, "Decode", "TranslatedText", 0, "_content"),
                ])

            # EnumeratedItems (no Decode)
            ei_items = getattr(cl, "EnumeratedItem", None) or []
            for ei in ei_items:
                rows.append([
                    cl_oid,
                    _safe_get(ei, "CodedValue"),
                    _safe_get(ei, "Rank"),
                    _safe_get(ei, "OrderNumber"),
                    _safe_get(ei, "ExtendedValue"),
                    None,  # EnumeratedItems have no Decode
                ])

        return self._make_dataset("codelist_terms",
                                  "CodeList Terms", columns, rows)

    def flatten_aliases(self) -> DatasetJSON:
        """Flatten Alias elements from every element type that carries them.

        Normalized one-row-per-Alias table keyed by the owning element.
        Covers ItemGroupDef, ItemDef, CodeList, and the CodeListItem /
        EnumeratedItem terms (which the codelist_terms table cannot hold
        an Alias for).  ``Member`` disambiguates a codelist term by its
        CodedValue; it is empty for the OID-addressable element types.

        Returns:
            DatasetJSON: One row per Alias.
        """
        columns = [
            _make_column("DEFINE.AL.PARENTTYPE", "ParentType",
                         "Parent Element Type", key_seq=1),
            _make_column("DEFINE.AL.PARENTOID", "ParentOID",
                         "Parent OID", key_seq=2),
            _make_column("DEFINE.AL.MEMBER", "Member",
                         "CodeList Term Coded Value", key_seq=3),
            _make_column("DEFINE.AL.CONTEXT", "Context", "Context"),
            _make_column("DEFINE.AL.NAME", "Name", "Name"),
        ]

        rows = []

        def _emit(parent_type, parent_oid, member, element):
            for alias in getattr(element, "Alias", None) or []:
                rows.append([
                    parent_type, parent_oid, member,
                    _safe_get(alias, "Context"),
                    _safe_get(alias, "Name"),
                ])

        for igd in getattr(self._mdv, "ItemGroupDef", None) or []:
            _emit("ItemGroupDef", igd.OID, None, igd)
        for idf in getattr(self._mdv, "ItemDef", None) or []:
            _emit("ItemDef", idf.OID, None, idf)
        for cl in getattr(self._mdv, "CodeList", None) or []:
            _emit("CodeList", cl.OID, None, cl)
            for cli in getattr(cl, "CodeListItem", None) or []:
                _emit("CodeListItem", cl.OID,
                      _safe_get(cli, "CodedValue"), cli)
            for ei in getattr(cl, "EnumeratedItem", None) or []:
                _emit("EnumeratedItem", cl.OID,
                      _safe_get(ei, "CodedValue"), ei)

        return self._make_dataset("aliases", "Alias Definitions",
                                  columns, rows)

    def flatten_origins(self) -> DatasetJSON:
        """Flatten the full ItemDef Origin trees (one row per Origin).

        The inline OriginType / OriginSource columns on the variables and
        value_level tables only capture the first Origin's Type and Source.
        This table captures every Origin with its Description (text and
        language) and DocumentRef leafIDs, enabling lossless rebuild.

        Returns:
            DatasetJSON: One row per Origin within each ItemDef.
        """
        columns = [
            _make_column("DEFINE.OR.ITEMOID", "ItemOID", "Item OID",
                         key_seq=1),
            _make_column("DEFINE.OR.ORDERNUMBER", "OrderNumber",
                         "Origin Order", "integer", key_seq=2),
            _make_column("DEFINE.OR.TYPE", "Type", "Origin Type"),
            _make_column("DEFINE.OR.SOURCE", "Source", "Origin Source"),
            _make_column("DEFINE.OR.DESCRIPTIONTEXT", "DescriptionText",
                         "Description"),
            _make_column("DEFINE.OR.DESCRIPTIONLANG", "DescriptionLang",
                         "Description Language"),
            _make_column("DEFINE.OR.DOCUMENTREFLEAFIDS", "DocumentRefLeafIDs",
                         "Document Ref Leaf IDs"),
        ]

        rows = []
        for idf in getattr(self._mdv, "ItemDef", None) or []:
            for i, origin in enumerate(getattr(idf, "Origin", None) or []):
                leaf_ids = [
                    _safe_get(dr, "leafID")
                    for dr in getattr(origin, "DocumentRef", None) or []
                    if _safe_get(dr, "leafID") is not None
                ]
                rows.append([
                    idf.OID,
                    i + 1,
                    _safe_get(origin, "Type"),
                    _safe_get(origin, "Source"),
                    _safe_get(origin, "Description", "TranslatedText", 0,
                              "_content"),
                    _safe_get(origin, "Description", "TranslatedText", 0,
                              "lang"),
                    ", ".join(leaf_ids) if leaf_ids else None,
                ])

        return self._make_dataset("origins", "Origin Definitions",
                                  columns, rows)
