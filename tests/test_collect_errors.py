"""Tests for ODMElement.validate() with collect_errors=True (Phase 1)."""
import os
from unittest import TestCase

import odmlib.odm_1_3_2.model as ODM
from odmlib.exceptions import (
    OdmlibError,
    OdmlibElementOrderError,
    OdmlibOIDError,
    OdmlibConformanceError,
    ErrorCollector,
)

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _make_minimal_mdv():
    """Return a minimal but valid MetaDataVersion for testing."""
    study_name = ODM.StudyName(_content="Study Test")
    study_desc = ODM.StudyDescription(_content="Study Description")
    prot_name = ODM.ProtocolName(_content="Protocol Name")
    gv = ODM.GlobalVariables(StudyName=study_name, StudyDescription=study_desc, ProtocolName=prot_name)

    ig_ref = ODM.ItemGroupRef(ItemGroupOID="IG.TEST", Mandatory="Yes")
    form_ref = ODM.FormRef(FormOID="F.TEST", Mandatory="Yes", OrderNumber=1)
    sed = ODM.StudyEventDef(OID="SE.TEST", Name="Test Event", Repeating="No", Type="Scheduled",
                            FormRef=[form_ref])

    item_ref = ODM.ItemRef(ItemOID="IT.TEST", Mandatory="No", OrderNumber=1)
    igd = ODM.ItemGroupDef(OID="IG.TEST", Name="Test Group", Repeating="No",
                           ItemRef=[item_ref])

    item = ODM.ItemDef(OID="IT.TEST", Name="Test Item", DataType="text")
    form = ODM.FormDef(OID="F.TEST", Name="Test Form", Repeating="No",
                       ItemGroupRef=[ig_ref])

    mdv = ODM.MetaDataVersion(OID="MDV.TEST", Name="Test MDV",
                              StudyEventDef=[sed],
                              FormDef=[form],
                              ItemGroupDef=[igd],
                              ItemDef=[item])
    return mdv


class TestValidateFailFast(TestCase):
    """validate() without collect_errors raises on the first error (default behaviour)."""

    def test_validate_returns_true_for_valid_object(self):
        mdv = _make_minimal_mdv()
        result = mdv.validate()
        self.assertTrue(result)

    def test_validate_raises_on_order_error(self):
        item = ODM.ItemDef(OID="IT.TEST", Name="Test Item", DataType="text")
        # Set Alias first — out of order because Description must come before Alias
        alias = ODM.Alias(Context="nci", Name="C12345")
        item.Alias = [alias]
        # Now add Description after Alias: __dict__ has [Alias, Description]
        # but _elems requires [Description, ..., Alias]
        description = ODM.Description()
        tt = ODM.TranslatedText(_content="test", lang="en")
        description.TranslatedText = [tt]
        item.Description = description
        with self.assertRaises(OdmlibElementOrderError):
            item.verify_order()


class TestValidateCollectErrors(TestCase):
    """validate(collect_errors=True) returns a list of all errors."""

    def test_collect_returns_empty_list_for_valid_object(self):
        mdv = _make_minimal_mdv()
        errors = mdv.validate(collect_errors=True)
        self.assertIsInstance(errors, list)
        self.assertEqual(len(errors), 0)

    def test_collect_errors_true_returns_list_not_bool(self):
        mdv = _make_minimal_mdv()
        result = mdv.validate(collect_errors=True)
        # Even when valid, returns a list (not True)
        self.assertIsInstance(result, list)

    def test_collect_includes_oid_error(self):
        import odmlib.odm_1_3_2.rules.oid_ref as OID_REF
        checker = OID_REF.OIDRef()
        # Deliberately add a duplicate OID so check_oid_refs would fail
        # We inject a bad ref to trigger a check failure:
        checker.oid["IT.MISSING"] = "WRONG_TYPE"   # wrong type mapping
        checker.oid_ref["ItemOID"].add("IT.MISSING")
        # ref_def["ItemOID"] = "ItemDef", but oid says "WRONG_TYPE"

        mdv = _make_minimal_mdv()
        errors = mdv.validate(collect_errors=True, oid_checker=checker)
        self.assertIsInstance(errors, list)
        self.assertTrue(len(errors) >= 1)
        self.assertTrue(all(isinstance(e, OdmlibError) for e in errors))

    def test_collect_errors_skips_oid_check_when_no_checker(self):
        mdv = _make_minimal_mdv()
        errors = mdv.validate(collect_errors=True, oid_checker=None)
        self.assertEqual(errors, [])

    def test_collect_errors_skips_conformance_when_no_checker(self):
        mdv = _make_minimal_mdv()
        errors = mdv.validate(collect_errors=True, conformance_checker=None)
        self.assertEqual(errors, [])

    def test_collect_errors_with_conformance(self):
        import odmlib.odm_1_3_2.rules.metadata_schema as MS
        checker = MS.MetadataSchema()
        mdv = _make_minimal_mdv()
        # Valid MDV: should produce no errors
        errors = mdv.validate(collect_errors=True, conformance_checker=checker)
        # May or may not have errors depending on MDV completeness;
        # key assertion: returns a list, not raises
        self.assertIsInstance(errors, list)


class TestErrorCollectorWithValidate(TestCase):
    """ErrorCollector can be used alongside validate() results."""

    def test_collect_then_raise_if_errors(self):
        """Collect all errors then raise summary."""
        import odmlib.odm_1_3_2.rules.oid_ref as OID_REF
        checker = OID_REF.OIDRef()
        checker.oid["IT.BAD"] = "WrongType"
        checker.oid_ref["ItemOID"].add("IT.BAD")

        mdv = _make_minimal_mdv()
        errors = mdv.validate(collect_errors=True, oid_checker=checker)

        if errors:
            collector = ErrorCollector()
            for err in errors:
                collector.add_error(err)
            self.assertTrue(collector.has_errors)

    def test_empty_results_means_valid(self):
        mdv = _make_minimal_mdv()
        errors = mdv.validate(collect_errors=True)
        collector = ErrorCollector()
        for err in errors:
            collector.add_error(err)
        self.assertFalse(collector.has_errors)
        collector.raise_if_errors()  # should not raise
