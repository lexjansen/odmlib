"""Tests for DefineBuilder — reconstructing Define-XML 2.1 from Dataset-JSON."""
import os
import tempfile
from unittest import TestCase

import odmlib.define_2_1.model as DEF
import odmlib.define_loader as DL
import odmlib.loader as LD
from odmlib.dataset_json_1_1 import DefineFlattener, DefineBuilder
from odmlib.dataset_json_1_1.model import DatasetJSON, Column


def _make_test_dataset(name, columns, rows):
    """Helper to create a minimal DatasetJSON for testing."""
    cols = [
        Column(itemOID=f"TEST.{c}", name=c, label=c, dataType="string")
        for c in columns
    ]
    ds = DatasetJSON(
        datasetJSONCreationDateTime="2026-01-01T00:00:00",
        datasetJSONVersion="1.1.0",
        itemGroupOID=f"IG.TEST.{name.upper()}",
        records=len(rows),
        name=name,
        label=f"Test {name}",
        columns=cols,
    )
    if rows:
        ds.rows = rows
    return ds


def _make_empty_datasets(**overrides):
    """Create a full set of 11 datasets with defaults for minimal build."""
    study_cols = [
        "FileOID", "CreationDateTime", "AsOfDateTime", "Originator",
        "SourceSystem", "SourceSystemVersion", "StudyOID", "StudyName",
        "StudyDescription", "ProtocolName", "MetaDataVersionOID",
        "MetaDataVersionName", "DefineVersion", "CommentOID", "Context",
    ]
    study_row = [
        "F.TEST", "2026-01-01T00:00:00", None, None,
        None, None, "S.TEST", "Test Study",
        "Test Description", "Test Protocol", "MDV.TEST",
        "Test MDV", "2.1.0", None, "Submission",
    ]
    defaults = {
        "study": _make_test_dataset("study", study_cols, [study_row]),
        "standards": _make_test_dataset("standards", ["OID"], []),
        "datasets": _make_test_dataset("datasets", ["OID"], []),
        "variables": _make_test_dataset("variables", ["DatasetOID"], []),
        "value_level": _make_test_dataset("value_level", ["ValueListOID"], []),
        "where_clauses": _make_test_dataset("where_clauses", ["WhereClauseOID"], []),
        "methods": _make_test_dataset("methods", ["OID"], []),
        "comments": _make_test_dataset("comments", ["OID"], []),
        "documents": _make_test_dataset("documents", ["ID"], []),
        "codelists": _make_test_dataset("codelists", ["OID"], []),
        "codelist_terms": _make_test_dataset("codelist_terms", ["CodeListOID"], []),
    }
    defaults.update(overrides)
    return defaults


class TestDefineBuilderDocuments(TestCase):
    """Test _build_documents()."""

    def test_build_documents(self):
        ds = _make_test_dataset("documents", ["ID", "href", "title"], [
            ["LF.blankcrf", "blankcrf.pdf", "Blank CRF"],
            ["LF.acrf", "acrf.pdf", "Annotated CRF"],
        ])
        builder = DefineBuilder(_make_empty_datasets(documents=ds))
        leaves = builder._build_documents()
        self.assertEqual(len(leaves), 2)
        self.assertEqual(leaves[0].ID, "LF.blankcrf")
        self.assertEqual(leaves[0].href, "blankcrf.pdf")
        self.assertEqual(leaves[0].title._content, "Blank CRF")

    def test_build_documents_empty(self):
        builder = DefineBuilder(_make_empty_datasets())
        leaves = builder._build_documents()
        self.assertEqual(len(leaves), 0)


class TestDefineBuilderComments(TestCase):
    """Test _build_comments()."""

    def test_build_comments(self):
        ds = _make_test_dataset("comments",
                                ["OID", "DescriptionText", "DocumentRefLeafIDs"],
                                [["COM.1", "Test comment", "LF.1, LF.2"]])
        builder = DefineBuilder(_make_empty_datasets(comments=ds))
        comments = builder._build_comments()
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].OID, "COM.1")
        self.assertEqual(comments[0].Description.TranslatedText[0]._content,
                         "Test comment")
        self.assertEqual(len(comments[0].DocumentRef), 2)
        self.assertEqual(comments[0].DocumentRef[0].leafID, "LF.1")
        self.assertEqual(comments[0].DocumentRef[1].leafID, "LF.2")

    def test_build_comments_no_doc_refs(self):
        ds = _make_test_dataset("comments",
                                ["OID", "DescriptionText", "DocumentRefLeafIDs"],
                                [["COM.1", "Just text", None]])
        builder = DefineBuilder(_make_empty_datasets(comments=ds))
        comments = builder._build_comments()
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].OID, "COM.1")


class TestDefineBuilderMethods(TestCase):
    """Test _build_methods()."""

    def test_build_methods_single_expression(self):
        ds = _make_test_dataset("methods", [
            "OID", "Name", "Type", "DescriptionText",
            "FormalExpressionContext", "FormalExpressionText",
            "DocumentRefLeafIDs",
        ], [
            ["MT.1", "Method1", "Computation", "Compute age",
             "SAS", "age = today - dob;", None],
        ])
        builder = DefineBuilder(_make_empty_datasets(methods=ds))
        methods = builder._build_methods()
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0].OID, "MT.1")
        self.assertEqual(methods[0].Type, "Computation")
        self.assertEqual(len(methods[0].FormalExpression), 1)
        self.assertEqual(methods[0].FormalExpression[0].Context, "SAS")

    def test_build_methods_multiple_expressions(self):
        ds = _make_test_dataset("methods", [
            "OID", "Name", "Type", "DescriptionText",
            "FormalExpressionContext", "FormalExpressionText",
            "DocumentRefLeafIDs",
        ], [
            ["MT.1", "Method1", "Computation", "Compute age",
             "SAS", "age = today - dob;", None],
            ["MT.1", "Method1", "Computation", "Compute age",
             "R", "age <- today - dob", None],
        ])
        builder = DefineBuilder(_make_empty_datasets(methods=ds))
        methods = builder._build_methods()
        self.assertEqual(len(methods), 1)
        self.assertEqual(len(methods[0].FormalExpression), 2)
        self.assertEqual(methods[0].FormalExpression[1].Context, "R")

    def test_build_methods_no_expressions(self):
        ds = _make_test_dataset("methods", [
            "OID", "Name", "Type", "DescriptionText",
            "FormalExpressionContext", "FormalExpressionText",
            "DocumentRefLeafIDs",
        ], [
            ["MT.1", "Method1", "Computation", "Compute age",
             None, None, None],
        ])
        builder = DefineBuilder(_make_empty_datasets(methods=ds))
        methods = builder._build_methods()
        self.assertEqual(len(methods), 1)
        fe = getattr(methods[0], "FormalExpression", None) or []
        self.assertEqual(len(fe), 0)


class TestDefineBuilderWhereClauses(TestCase):
    """Test _build_where_clauses()."""

    def test_build_where_clauses(self):
        ds = _make_test_dataset("where_clauses", [
            "WhereClauseOID", "WhereClauseCommentOID", "Comparator",
            "SoftHard", "ItemOID", "CheckValues",
        ], [
            ["WC.1", None, "EQ", "Soft", "IT.PARAMCD", "SYSBP"],
            ["WC.1", None, "EQ", "Soft", "IT.AVISIT", "WEEK 4"],
        ])
        builder = DefineBuilder(_make_empty_datasets(where_clauses=ds))
        wcs = builder._build_where_clauses()
        self.assertEqual(len(wcs), 1)
        self.assertEqual(wcs[0].OID, "WC.1")
        self.assertEqual(len(wcs[0].RangeCheck), 2)
        self.assertEqual(wcs[0].RangeCheck[0].Comparator, "EQ")
        self.assertEqual(wcs[0].RangeCheck[0].ItemOID, "IT.PARAMCD")
        self.assertEqual(wcs[0].RangeCheck[0].CheckValue[0]._content, "SYSBP")

    def test_build_where_clauses_multiple_check_values(self):
        ds = _make_test_dataset("where_clauses", [
            "WhereClauseOID", "WhereClauseCommentOID", "Comparator",
            "SoftHard", "ItemOID", "CheckValues",
        ], [
            ["WC.1", None, "IN", "Soft", "IT.PARAMCD", "SYSBP, DIABP"],
        ])
        builder = DefineBuilder(_make_empty_datasets(where_clauses=ds))
        wcs = builder._build_where_clauses()
        rc = wcs[0].RangeCheck[0]
        self.assertEqual(len(rc.CheckValue), 2)
        self.assertEqual(rc.CheckValue[0]._content, "SYSBP")
        self.assertEqual(rc.CheckValue[1]._content, "DIABP")


class TestDefineBuilderCodeLists(TestCase):
    """Test _build_codelists()."""

    def test_build_codelist_with_items(self):
        cl_ds = _make_test_dataset("codelists", [
            "OID", "Name", "DataType", "IsNonStandard", "StandardOID",
            "SASFormatName", "CommentOID", "DescriptionText",
            "ExternalDictionary", "ExternalVersion", "ExternalRef", "ExternalHref",
        ], [
            ["CL.SEX", "Sex", "text", None, None, "SEX.", None, None,
             None, None, None, None],
        ])
        term_ds = _make_test_dataset("codelist_terms", [
            "CodeListOID", "CodedValue", "Rank", "OrderNumber",
            "ExtendedValue", "DecodedText",
        ], [
            ["CL.SEX", "M", None, 1, None, "Male"],
            ["CL.SEX", "F", None, 2, None, "Female"],
        ])
        builder = DefineBuilder(_make_empty_datasets(
            codelists=cl_ds, codelist_terms=term_ds))
        codelists = builder._build_codelists()
        self.assertEqual(len(codelists), 1)
        cl = codelists[0]
        self.assertEqual(cl.OID, "CL.SEX")
        self.assertEqual(len(cl.CodeListItem), 2)
        self.assertEqual(cl.CodeListItem[0].CodedValue, "M")
        self.assertEqual(cl.CodeListItem[0].Decode.TranslatedText[0]._content,
                         "Male")

    def test_build_codelist_enumerated_items(self):
        cl_ds = _make_test_dataset("codelists", [
            "OID", "Name", "DataType", "IsNonStandard", "StandardOID",
            "SASFormatName", "CommentOID", "DescriptionText",
            "ExternalDictionary", "ExternalVersion", "ExternalRef", "ExternalHref",
        ], [
            ["CL.NY", "No Yes", "text", None, None, None, None, None,
             None, None, None, None],
        ])
        term_ds = _make_test_dataset("codelist_terms", [
            "CodeListOID", "CodedValue", "Rank", "OrderNumber",
            "ExtendedValue", "DecodedText",
        ], [
            ["CL.NY", "N", None, 1, None, None],
            ["CL.NY", "Y", None, 2, None, None],
        ])
        builder = DefineBuilder(_make_empty_datasets(
            codelists=cl_ds, codelist_terms=term_ds))
        codelists = builder._build_codelists()
        cl = codelists[0]
        self.assertEqual(len(cl.EnumeratedItem), 2)
        self.assertEqual(cl.EnumeratedItem[0].CodedValue, "N")

    def test_build_codelist_external(self):
        cl_ds = _make_test_dataset("codelists", [
            "OID", "Name", "DataType", "IsNonStandard", "StandardOID",
            "SASFormatName", "CommentOID", "DescriptionText",
            "ExternalDictionary", "ExternalVersion", "ExternalRef", "ExternalHref",
        ], [
            ["CL.MED", "MedDRA", "text", None, None, None, None, None,
             "MedDRA", "25.0", None, None],
        ])
        term_ds = _make_test_dataset("codelist_terms", [
            "CodeListOID", "CodedValue", "Rank", "OrderNumber",
            "ExtendedValue", "DecodedText",
        ], [])
        builder = DefineBuilder(_make_empty_datasets(
            codelists=cl_ds, codelist_terms=term_ds))
        codelists = builder._build_codelists()
        cl = codelists[0]
        self.assertEqual(cl.ExternalCodeList.Dictionary, "MedDRA")
        self.assertEqual(cl.ExternalCodeList.Version, "25.0")


class TestDefineBuilderStandards(TestCase):
    """Test _build_standards()."""

    def test_build_standards(self):
        ds = _make_test_dataset("standards", [
            "OID", "Name", "Type", "PublishingSet", "Version",
            "Status", "CommentOID",
        ], [
            ["STD.1", "SDTMIG", "IG", "SDTM", "3.3", "Final", None],
        ])
        builder = DefineBuilder(_make_empty_datasets(standards=ds))
        standards = builder._build_standards()
        self.assertIsNotNone(standards)
        self.assertEqual(len(standards.Standard), 1)
        self.assertEqual(standards.Standard[0].OID, "STD.1")
        self.assertEqual(standards.Standard[0].Name, "SDTMIG")

    def test_build_standards_empty(self):
        builder = DefineBuilder(_make_empty_datasets())
        standards = builder._build_standards()
        self.assertIsNone(standards)


class TestDefineBuilderBuild(TestCase):
    """Test the full build() method."""

    def test_minimal_build(self):
        """Build with just study metadata and no child elements."""
        builder = DefineBuilder(_make_empty_datasets())
        odm = builder.build()
        self.assertEqual(odm.FileType, "Snapshot")
        self.assertEqual(odm.FileOID, "F.TEST")
        self.assertEqual(odm.ODMVersion, "1.3.2")
        self.assertEqual(odm.Context, "Submission")
        self.assertEqual(odm.Study.OID, "S.TEST")
        self.assertEqual(odm.Study.GlobalVariables.StudyName._content, "Test Study")
        self.assertEqual(odm.Study.MetaDataVersion.OID, "MDV.TEST")
        self.assertEqual(odm.Study.MetaDataVersion.DefineVersion, "2.1.0")


class TestDefineBuilderRoundtrip(TestCase):
    """Integration tests: flatten -> rebuild -> compare."""

    def _load_define(self, filename):
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(filename)
        return loader.root()

    def test_roundtrip_sdtm_metadata(self):
        original = self._load_define("tests/data/defineV21-SDTM-metadata.xml")
        flat = DefineFlattener(original).flatten_all()
        rebuilt = DefineBuilder(flat).build()

        orig_mdv = original.Study.MetaDataVersion
        rebuilt_mdv = rebuilt.Study.MetaDataVersion

        # Element counts
        self.assertEqual(len(rebuilt_mdv.ItemGroupDef),
                         len(orig_mdv.ItemGroupDef))
        self.assertEqual(len(rebuilt_mdv.CodeList), len(orig_mdv.CodeList))
        self.assertEqual(len(rebuilt_mdv.MethodDef), len(orig_mdv.MethodDef))

        # OIDs match
        orig_igd_oids = {igd.OID for igd in orig_mdv.ItemGroupDef}
        rebuilt_igd_oids = {igd.OID for igd in rebuilt_mdv.ItemGroupDef}
        self.assertEqual(orig_igd_oids, rebuilt_igd_oids)

        # Key attributes
        self.assertEqual(rebuilt.FileOID, original.FileOID)
        self.assertEqual(rebuilt.Study.OID, original.Study.OID)
        self.assertEqual(rebuilt_mdv.DefineVersion, orig_mdv.DefineVersion)

    def test_roundtrip_adam(self):
        original = self._load_define("tests/data/definev21-adam.xml")
        flat = DefineFlattener(original).flatten_all()
        rebuilt = DefineBuilder(flat).build()

        orig_mdv = original.Study.MetaDataVersion
        rebuilt_mdv = rebuilt.Study.MetaDataVersion

        self.assertEqual(len(rebuilt_mdv.ItemGroupDef),
                         len(orig_mdv.ItemGroupDef))
        self.assertEqual(len(rebuilt_mdv.CodeList), len(orig_mdv.CodeList))
        self.assertEqual(len(rebuilt_mdv.MethodDef), len(orig_mdv.MethodDef))

    def test_roundtrip_write_xml(self):
        """Verify rebuilt Define-XML writes valid XML."""
        original = self._load_define("tests/data/defineV21-SDTM-metadata.xml")
        flat = DefineFlattener(original).flatten_all()
        rebuilt = DefineBuilder(flat).build()

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            tmpfile = f.name
        try:
            rebuilt.write_xml(tmpfile)
            self.assertTrue(os.path.exists(tmpfile))
            self.assertGreater(os.path.getsize(tmpfile), 0)
        finally:
            os.unlink(tmpfile)

    def test_roundtrip_itemref_counts(self):
        """Verify ItemRef counts match per ItemGroupDef."""
        original = self._load_define("tests/data/defineV21-SDTM-metadata.xml")
        flat = DefineFlattener(original).flatten_all()
        rebuilt = DefineBuilder(flat).build()

        orig_mdv = original.Study.MetaDataVersion
        rebuilt_mdv = rebuilt.Study.MetaDataVersion

        for orig_igd in orig_mdv.ItemGroupDef:
            rebuilt_igd = None
            for r in rebuilt_mdv.ItemGroupDef:
                if r.OID == orig_igd.OID:
                    rebuilt_igd = r
                    break
            self.assertIsNotNone(rebuilt_igd,
                                 f"Missing ItemGroupDef {orig_igd.OID}")
            orig_refs = getattr(orig_igd, "ItemRef", None) or []
            rebuilt_refs = getattr(rebuilt_igd, "ItemRef", None) or []
            self.assertEqual(
                len(rebuilt_refs), len(orig_refs),
                f"ItemRef count mismatch for {orig_igd.OID}")


class TestDefineBuilderEdgeCases(TestCase):
    """Edge case tests for DefineBuilder (Issue 2.6)."""

    def test_empty_codelist(self):
        """A codelist with no terms should still build without error."""
        cl_ds = _make_test_dataset("codelists", [
            "OID", "Name", "DataType", "IsNonStandard", "StandardOID",
            "SASFormatName", "CommentOID", "DescriptionText",
            "ExternalDictionary", "ExternalVersion", "ExternalRef", "ExternalHref",
        ], [
            ["CL.EMPTY", "Empty List", "text", None, None, None, None, None,
             None, None, None, None],
        ])
        # No terms at all for CL.EMPTY
        term_ds = _make_test_dataset("codelist_terms", [
            "CodeListOID", "CodedValue", "Rank", "OrderNumber",
            "ExtendedValue", "DecodedText",
        ], [])
        builder = DefineBuilder(_make_empty_datasets(
            codelists=cl_ds, codelist_terms=term_ds))
        codelists = builder._build_codelists()
        self.assertEqual(len(codelists), 1)
        cl = codelists[0]
        self.assertEqual(cl.OID, "CL.EMPTY")
        # No CodeListItem or EnumeratedItem
        cli = getattr(cl, "CodeListItem", None) or []
        eni = getattr(cl, "EnumeratedItem", None) or []
        self.assertEqual(len(cli), 0)
        self.assertEqual(len(eni), 0)

    def test_missing_optional_fields(self):
        """Build succeeds when no Comment or Method datasets have rows."""
        datasets = _make_empty_datasets()
        # comments and methods datasets exist but have no rows (empty)
        builder = DefineBuilder(datasets)
        odm = builder.build()
        mdv = odm.Study.MetaDataVersion
        # No CommentDef or MethodDef should be created
        comment_defs = getattr(mdv, "CommentDef", None) or []
        method_defs = getattr(mdv, "MethodDef", None) or []
        self.assertEqual(len(comment_defs), 0)
        self.assertEqual(len(method_defs), 0)

    def test_single_variable_dataset(self):
        """A dataset with a single variable should build correctly."""
        # Column names must match what DefineFlattener produces
        ds_ds = _make_test_dataset("datasets", [
            "OID", "Name", "Repeating", "IsReferenceData",
            "SASDatasetName", "Domain", "Purpose", "Structure",
            "ArchiveLocationID", "CommentOID", "IsNonStandard",
            "StandardOID", "HasNoData", "DescriptionText",
            "ClassName", "SubClassName", "leafID", "leafHref", "leafTitle",
        ], [
            ["IG.SINGLE", "SINGLE", "No", "No",
             "SINGLE", None, "Tabulation", "One Record Per Subject",
             None, None, None,
             None, None, None,
             "SPECIAL PURPOSE", None, None, None, None],
        ])
        var_ds = _make_test_dataset("variables", [
            "DatasetOID", "ItemOID", "OrderNumber", "Mandatory",
            "KeySequence", "MethodOID", "Role", "RoleCodeListOID",
            "IsNonStandard", "HasNoData", "Name", "DataType",
            "Length", "SignificantDigits", "SASFieldName",
            "DisplayFormat", "CommentOID", "DescriptionText",
            "CodeListOID", "ValueListOID", "OriginType", "OriginSource",
        ], [
            ["IG.SINGLE", "IT.SINGLE.VAR1", "1", "Yes",
             "1", None, None, None,
             None, None, "VAR1", "text",
             "20", None, "VAR1",
             None, None, None,
             None, None, "Collected", "Sponsor"],
        ])
        builder = DefineBuilder(_make_empty_datasets(
            datasets=ds_ds, variables=var_ds))
        odm = builder.build()
        mdv = odm.Study.MetaDataVersion
        self.assertEqual(len(mdv.ItemGroupDef), 1)
        igd = mdv.ItemGroupDef[0]
        self.assertEqual(igd.OID, "IG.SINGLE")
        item_refs = getattr(igd, "ItemRef", None) or []
        self.assertEqual(len(item_refs), 1)
        self.assertEqual(item_refs[0].ItemOID, "IT.SINGLE.VAR1")
        # Should also have one ItemDef
        self.assertEqual(len(mdv.ItemDef), 1)
        self.assertEqual(mdv.ItemDef[0].OID, "IT.SINGLE.VAR1")


class TestDefineBuilderFileIO(TestCase):
    """Test write_all + read_all + build roundtrip."""

    def test_write_read_build(self):
        original = LD.ODMLoader(
            DL.XMLDefineLoader(model_package="define_2_1"))
        original.open_odm_document("tests/data/defineV21-SDTM-metadata.xml")
        odm = original.root()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write flattened datasets
            flattener = DefineFlattener(odm)
            flattener.write_all(tmpdir)

            # Read them back and rebuild
            datasets = DefineBuilder.read_all(tmpdir)
            rebuilt = DefineBuilder(datasets).build()

            self.assertEqual(rebuilt.FileOID, odm.FileOID)
            self.assertEqual(
                len(rebuilt.Study.MetaDataVersion.ItemGroupDef),
                len(odm.Study.MetaDataVersion.ItemGroupDef))
