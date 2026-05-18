"""ODM 2.0 model: construction, round-trip, and v0.2.0 safe-subset coverage.

Dedicated odm_2_0 element suite added with the v0.2.0 ODM 2.0 Model/XSD
remediation (``ODM20-MODEL-XSD-DIFFERENCES_PLAN.md``). Covers:

- 3.6  ``TranslatedText.Type`` is required (XSD-aligned) + permissive escape.
- 3.8  ``Arm`` / ``CheckValue`` de-duplication (descriptor-consistent).
- 3.9  the 12 newly-registered odm_2_0 value-set keys (accept + strict
       reject + permissive bypass).
- general construction + XML/JSON/dict round-trip for the major classes.

The conftest autouse fixture resets the NamespaceRegistry before each test,
so every setUp re-registers the ODM 2.0 namespace set.
"""
import json
from unittest import TestCase

import odmlib.odm_2_0.model as ODM2
import odmlib.ns_registry as NS
from odmlib.mode import permissive, ValidationMode
from odmlib.exceptions import OdmlibRequiredAttributeError, OdmlibTypeError


def _setup_odm2_namespaces():
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
        is_default=True, is_reset=True,
    )
    NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
    NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
    NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


def _tt(content="text", lang="en"):
    return ODM2.TranslatedText(_content=content, lang=lang, Type="text/plain")


# ---------------------------------------------------------------------------
# 3.6 -- TranslatedText.Type required
# ---------------------------------------------------------------------------

class TestTranslatedTextV2(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_type_is_required(self):
        with self.assertRaises(OdmlibRequiredAttributeError):
            ODM2.TranslatedText(_content="Subject Age", lang="en")

    def test_with_type_constructs_and_serializes(self):
        tt = _tt("Subject Age")
        self.assertEqual(tt.Type, "text/plain")
        self.assertEqual(tt.to_xml().attrib["Type"], "text/plain")
        self.assertEqual(json.loads(tt.to_json())["Type"], "text/plain")

    def test_permissive_skip_required_allows_missing_type(self):
        # Construction must not raise under SKIP_REQUIRED; the required-check
        # also fires on *access*, so read Type while still permissive.
        with permissive(ValidationMode.SKIP_REQUIRED):
            tt = ODM2.TranslatedText(_content="x", lang="en")
            self.assertIsNone(tt.Type)
        self.assertEqual(tt._content, "x")

    def test_description_round_trip(self):
        desc = ODM2.Description(TranslatedText=[_tt("Hello")])
        data = json.loads(desc.to_json())
        self.assertEqual(data["TranslatedText"][0]["_content"], "Hello")
        self.assertEqual(data["TranslatedText"][0]["Type"], "text/plain")


# ---------------------------------------------------------------------------
# 3.8 -- Arm / CheckValue de-duplication
# ---------------------------------------------------------------------------

class TestArmCheckValueDedup(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_descriptor_classes_are_consistent(self):
        self.assertIs(ODM2.Arm,
                       ODM2.StudyStructure._elems["Arm"].element_class)
        self.assertIs(ODM2.CheckValue,
                       ODM2.RangeCheck._elems["CheckValue"].element_class)

    def test_single_class_definition(self):
        import inspect
        src = inspect.getsource(ODM2)
        self.assertEqual(src.count("class Arm(OE.ODMElement):"), 1)
        self.assertEqual(src.count("class CheckValue(OE.ODMElement):"), 1)

    def test_range_check_builds_with_check_value(self):
        rc = ODM2.RangeCheck(Comparator="GE",
                              CheckValue=[ODM2.CheckValue(_content="0")])
        self.assertEqual(rc.CheckValue[0]._content, "0")
        self.assertIsInstance(rc.CheckValue[0], ODM2.CheckValue)

    def test_study_structure_builds_with_arm(self):
        ss = ODM2.StudyStructure(
            Arm=[ODM2.Arm(OID="ARM.A", Name="Arm A")])
        self.assertEqual(ss.Arm[0].OID, "ARM.A")
        self.assertIsInstance(ss.Arm[0], ODM2.Arm)


# ---------------------------------------------------------------------------
# 3.9 -- the 12 newly-registered odm_2_0 value-set keys
# ---------------------------------------------------------------------------

class TestValueSetKeysV2(TestCase):
    """Each newly-registered key: a valid value constructs; an invalid value
    raises OdmlibTypeError in strict mode and is accepted under SKIP_VALUESET.
    """

    def setUp(self):
        _setup_odm2_namespaces()

    def _accept(self, factory):
        obj = factory()
        self.assertIsNotNone(obj)

    def _reject_strict_accept_permissive(self, factory):
        with self.assertRaises(OdmlibTypeError):
            factory()
        with permissive(ValidationMode.SKIP_VALUESET):
            self.assertIsNotNone(factory())

    def test_item_ref_core(self):
        self._accept(lambda: ODM2.ItemRef(ItemOID="I1", Mandatory="Yes", Core="Req"))
        self._reject_strict_accept_permissive(
            lambda: ODM2.ItemRef(ItemOID="I1", Mandatory="Yes", Core="BOGUS"))

    def test_item_ref_repeat_other_isnonstandard_hasnodata(self):
        for attr in ("Repeat", "Other", "IsNonStandard", "HasNoData"):
            self._accept(lambda a=attr: ODM2.ItemRef(
                ItemOID="I1", Mandatory="Yes", **{a: "Yes"}))
            self._reject_strict_accept_permissive(lambda a=attr: ODM2.ItemRef(
                ItemOID="I1", Mandatory="Yes", **{a: "No"}))

    def test_item_group_def_isnonstandard_hasnodata(self):
        for attr in ("IsNonStandard", "HasNoData"):
            self._accept(lambda a=attr: ODM2.ItemGroupDef(
                OID="IG1", Name="G", Repeating="No", Type="Dataset",
                **{a: "Yes"}))
            self._reject_strict_accept_permissive(lambda a=attr: ODM2.ItemGroupDef(
                OID="IG1", Name="G", Repeating="No", Type="Dataset",
                **{a: "No"}))

    def test_code_list_isnonstandard(self):
        self._accept(lambda: ODM2.CodeList(
            OID="CL1", Name="C", DataType="text", IsNonStandard="Yes"))
        self._reject_strict_accept_permissive(lambda: ODM2.CodeList(
            OID="CL1", Name="C", DataType="text", IsNonStandard="No"))

    def test_code_list_item_other(self):
        self._accept(lambda: ODM2.CodeListItem(CodedValue="C", Other="Yes"))
        self._reject_strict_accept_permissive(
            lambda: ODM2.CodeListItem(CodedValue="C", Other="No"))

    def test_telecom_type(self):
        self._accept(lambda: ODM2.Telecom(TelecomType="Email", value="a@b.c"))
        self._reject_strict_accept_permissive(
            lambda: ODM2.Telecom(TelecomType="Smoke", value="a@b.c"))

    def test_odm_context(self):
        self._accept(lambda: ODM2.ODM(
            FileOID="F1", FileType="Snapshot",
            CreationDateTime="2026-01-01T00:00:00", Context="Submission"))
        self._reject_strict_accept_permissive(lambda: ODM2.ODM(
            FileOID="F1", FileType="Snapshot",
            CreationDateTime="2026-01-01T00:00:00", Context="Nope"))

    def test_return_value_data_type(self):
        self._accept(lambda: ODM2.ReturnValue(Name="rv", DataType="integer"))
        self._reject_strict_accept_permissive(
            lambda: ODM2.ReturnValue(Name="rv", DataType="bogus"))


# ---------------------------------------------------------------------------
# General construction + round-trip
# ---------------------------------------------------------------------------

class TestRoundTripV2(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_item_def_xml_json_dict(self):
        item = ODM2.ItemDef(OID="IT.AGE", Name="Age", DataType="integer",
                            Description=ODM2.Description(
                                TranslatedText=[_tt("Subject Age")]))
        self.assertEqual(item.to_xml().attrib["OID"], "IT.AGE")
        self.assertEqual(json.loads(item.to_json())["DataType"], "integer")
        self.assertEqual(item.to_dict()["Name"], "Age")
        self.assertEqual(
            item.Description.TranslatedText[0]._content, "Subject Age")

    def test_item_group_def_round_trip(self):
        igd = ODM2.ItemGroupDef(OID="IG.AE", Name="AE", Repeating="No",
                                Type="Dataset")
        igd.ItemRef.append(ODM2.ItemRef(ItemOID="IT.AGE", Mandatory="Yes",
                                        Core="Req"))
        data = json.loads(igd.to_json())
        self.assertEqual(data["OID"], "IG.AE")
        self.assertEqual(data["ItemRef"][0]["Core"], "Req")

    def test_minimal_odm_document_round_trip(self):
        odm = ODM2.ODM(FileOID="F.TEST", FileType="Snapshot",
                       CreationDateTime="2026-01-01T00:00:00",
                       Context="Submission")
        study = ODM2.Study(OID="S.TEST", StudyName="S", ProtocolName="P",
                           Description=ODM2.Description(
                               TranslatedText=[_tt("A study")]))
        odm.Study.append(study)
        data = json.loads(odm.to_json())
        self.assertEqual(data["FileOID"], "F.TEST")
        self.assertEqual(data["Context"], "Submission")
        self.assertEqual(data["Study"][0]["OID"], "S.TEST")
        self.assertEqual(
            data["Study"][0]["Description"]["TranslatedText"][0]["Type"],
            "text/plain")
