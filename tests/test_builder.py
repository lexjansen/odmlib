"""Tests for the ODMBuilder fluent API.

Covers:
- Building a minimal valid ODM document.
- Adding MetaDataVersion, ItemGroupDef, ItemRef, ItemDef, CodeList.
- Error handling for out-of-order calls.
- XML and JSON round-trip from a builder-produced document.
- with_description() helper.
"""
import os
import tempfile
from unittest import TestCase
from odmlib.builder import ODMBuilder


class TestODMBuilderMinimal(TestCase):
    """Tests for the most basic builder usage."""

    def test_build_returns_odm_object(self):
        """build() returns an object with the expected file attributes."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.001", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .build())
        self.assertEqual(odm.FileOID, "F.001")
        self.assertEqual(odm.FileType, "Snapshot")

    def test_build_with_no_studies(self):
        """build() works even with no studies added."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.EMPTY", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .build())
        self.assertEqual(odm.Study, [])

    def test_add_study_creates_one_study(self):
        """add_study() adds exactly one Study with GlobalVariables."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.001", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.001", study_name="Test Study",
                          study_description="A test", protocol_name="P.001")
               .build())
        self.assertEqual(len(odm.Study), 1)
        self.assertEqual(odm.Study[0].OID, "S.001")

    def test_global_variables_populated(self):
        """GlobalVariables is correctly populated by add_study()."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.001", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.001", study_name="My Study",
                          study_description="Desc", protocol_name="PROT-001")
               .build())
        gv = odm.Study[0].GlobalVariables
        self.assertEqual(gv.StudyName._content, "My Study")
        self.assertEqual(gv.StudyDescription._content, "Desc")
        self.assertEqual(gv.ProtocolName._content, "PROT-001")

    def test_add_multiple_studies(self):
        """Multiple calls to add_study() create multiple Study elements."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.001", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.001", study_name="Study 1",
                          study_description="D1", protocol_name="P1")
               .add_study(OID="S.002", study_name="Study 2",
                          study_description="D2", protocol_name="P2")
               .build())
        self.assertEqual(len(odm.Study), 2)
        self.assertEqual(odm.Study[1].OID, "S.002")


class TestODMBuilderMetaData(TestCase):
    """Tests for MetaDataVersion, ItemGroupDef, ItemRef, and ItemDef."""

    def _minimal_odm(self):
        return (ODMBuilder()
                .set_file(FileOID="F.001", FileType="Snapshot",
                          CreationDateTime="2024-01-01T00:00:00")
                .add_study(OID="S.001", study_name="Test",
                           study_description="Desc", protocol_name="P.001"))

    def test_add_metadata_version(self):
        """add_metadata_version() creates a MetaDataVersion in the Study."""
        odm = (self._minimal_odm()
               .add_metadata_version(OID="MDV.001", Name="Version 1")
               .build())
        mdv = odm.Study[0].MetaDataVersion
        self.assertEqual(len(mdv), 1)
        self.assertEqual(mdv[0].OID, "MDV.001")
        self.assertEqual(mdv[0].Name, "Version 1")

    def test_add_item_group_def(self):
        """add_item_group_def() adds an ItemGroupDef to the current MDV."""
        odm = (self._minimal_odm()
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_group_def(OID="IG.DM", Name="Demographics",
                                   Repeating="No")
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(len(mdv.ItemGroupDef), 1)
        self.assertEqual(mdv.ItemGroupDef[0].OID, "IG.DM")

    def test_add_item_refs(self):
        """add_item_ref() appends ItemRefs to the current ItemGroupDef."""
        odm = (self._minimal_odm()
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
               .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1)
               .add_item_ref(ItemOID="IT.AGE", Mandatory="No", OrderNumber=2)
               .build())
        igd = odm.Study[0].MetaDataVersion[0].ItemGroupDef[0]
        self.assertEqual(len(igd.ItemRef), 2)
        self.assertEqual(igd.ItemRef[0].ItemOID, "IT.SUBJID")
        self.assertEqual(igd.ItemRef[1].ItemOID, "IT.AGE")

    def test_item_refs_go_to_current_igd_only(self):
        """add_item_ref() only targets the most recently added ItemGroupDef."""
        odm = (self._minimal_odm()
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
               .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes")
               .add_item_group_def(OID="IG.AE", Name="Adverse Events", Repeating="Yes")
               .add_item_ref(ItemOID="IT.AETRT", Mandatory="Yes")
               .add_item_ref(ItemOID="IT.AEDTC", Mandatory="No")
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(len(mdv.ItemGroupDef[0].ItemRef), 1)
        self.assertEqual(len(mdv.ItemGroupDef[1].ItemRef), 2)

    def test_add_item_def(self):
        """add_item_def() appends an ItemDef to the current MDV."""
        odm = (self._minimal_odm()
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_def(OID="IT.AGE", Name="Age", DataType="integer")
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(len(mdv.ItemDef), 1)
        self.assertEqual(mdv.ItemDef[0].OID, "IT.AGE")
        self.assertEqual(mdv.ItemDef[0].DataType, "integer")

    def test_add_multiple_item_defs(self):
        """Multiple add_item_def() calls accumulate in the MDV."""
        odm = (self._minimal_odm()
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_def(OID="IT.SUBJID", Name="Subject ID", DataType="text")
               .add_item_def(OID="IT.AGE", Name="Age", DataType="integer")
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(len(mdv.ItemDef), 2)


class TestODMBuilderCodeList(TestCase):
    """Tests for add_code_list()."""

    def _base_builder(self):
        return (ODMBuilder()
                .set_file(FileOID="F.001", FileType="Snapshot",
                          CreationDateTime="2024-01-01T00:00:00")
                .add_study(OID="S.001", study_name="T", study_description="D",
                           protocol_name="P")
                .add_metadata_version(OID="MDV.001", Name="V1"))

    def test_add_code_list_no_items(self):
        """add_code_list() with no items creates an empty CodeList."""
        odm = (self._base_builder()
               .add_code_list(OID="CL.YN", Name="Yes/No", DataType="text")
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(len(mdv.CodeList), 1)
        self.assertEqual(mdv.CodeList[0].OID, "CL.YN")
        self.assertEqual(mdv.CodeList[0].CodeListItem, [])

    def test_add_code_list_enumerated_items(self):
        """Items without Decode key create EnumeratedItems."""
        items = [{"CodedValue": "Y"}, {"CodedValue": "N"}]
        odm = (self._base_builder()
               .add_code_list(OID="CL.YN", Name="Yes/No", DataType="text",
                              items=items)
               .build())
        cl = odm.Study[0].MetaDataVersion[0].CodeList[0]
        self.assertEqual(len(cl.EnumeratedItem), 2)
        self.assertEqual(cl.EnumeratedItem[0].CodedValue, "Y")

    def test_add_code_list_coded_items(self):
        """Items with Decode key create CodeListItems."""
        items = [
            {"CodedValue": "Y", "Decode": "Yes"},
            {"CodedValue": "N", "Decode": "No"},
        ]
        odm = (self._base_builder()
               .add_code_list(OID="CL.YN", Name="Yes/No", DataType="text",
                              items=items)
               .build())
        cl = odm.Study[0].MetaDataVersion[0].CodeList[0]
        self.assertEqual(len(cl.CodeListItem), 2)
        self.assertEqual(cl.CodeListItem[0].CodedValue, "Y")
        self.assertEqual(cl.CodeListItem[0].Decode.TranslatedText[0]._content, "Yes")


class TestODMBuilderDescription(TestCase):
    """Tests for the with_description() helper."""

    def test_with_description_on_item_group_def(self):
        """with_description() after add_item_group_def sets its Description."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.001", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.001", study_name="T", study_description="D",
                          protocol_name="P")
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
               .with_description("Demographic dataset", lang="en")
               .build())
        igd = odm.Study[0].MetaDataVersion[0].ItemGroupDef[0]
        self.assertIsNotNone(igd.Description)
        self.assertEqual(igd.Description.TranslatedText[0]._content,
                         "Demographic dataset")

    def test_with_description_on_item_def(self):
        """with_description() after add_item_def sets that ItemDef's Description."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.001", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.001", study_name="T", study_description="D",
                          protocol_name="P")
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_def(OID="IT.AGE", Name="Age", DataType="integer")
               .with_description("Subject age in years")
               .build())
        item = odm.Study[0].MetaDataVersion[0].ItemDef[0]
        self.assertIsNotNone(item.Description)
        self.assertEqual(item.Description.TranslatedText[0]._content,
                         "Subject age in years")


class TestODMBuilderErrors(TestCase):
    """Tests for RuntimeError on out-of-order calls."""

    def test_add_metadata_version_before_study_raises(self):
        """add_metadata_version() before add_study() raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            ODMBuilder().add_metadata_version(OID="MDV.001", Name="V1")

    def test_add_item_group_def_before_mdv_raises(self):
        """add_item_group_def() before add_metadata_version() raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            (ODMBuilder()
             .add_study(OID="S.001", study_name="T", study_description="D",
                        protocol_name="P")
             .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No"))

    def test_add_item_ref_before_igd_raises(self):
        """add_item_ref() before add_item_group_def() raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            (ODMBuilder()
             .add_study(OID="S.001", study_name="T", study_description="D",
                        protocol_name="P")
             .add_metadata_version(OID="MDV.001", Name="V1")
             .add_item_ref(ItemOID="IT.AGE", Mandatory="Yes"))

    def test_add_item_def_before_mdv_raises(self):
        """add_item_def() before add_metadata_version() raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            (ODMBuilder()
             .add_study(OID="S.001", study_name="T", study_description="D",
                        protocol_name="P")
             .add_item_def(OID="IT.AGE", Name="Age", DataType="integer"))

    def test_add_code_list_before_mdv_raises(self):
        """add_code_list() before add_metadata_version() raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            (ODMBuilder()
             .add_study(OID="S.001", study_name="T", study_description="D",
                        protocol_name="P")
             .add_code_list(OID="CL.YN", Name="Yes/No", DataType="text"))


class TestODMBuilderRoundTrip(TestCase):
    """Tests that builder-produced documents serialize and deserialize correctly."""

    def setUp(self):
        self.odm = (ODMBuilder()
                    .set_file(FileOID="F.BUILDER", FileType="Snapshot",
                              CreationDateTime="2024-01-01T00:00:00")
                    .add_study(OID="S.001", study_name="Builder Test",
                               study_description="Round-trip test",
                               protocol_name="P.001")
                    .add_metadata_version(OID="MDV.001", Name="Version 1")
                    .add_item_group_def(OID="IG.DM", Name="Demographics",
                                       Repeating="No")
                    .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes",
                                  OrderNumber=1)
                    .add_item_ref(ItemOID="IT.AGE", Mandatory="No", OrderNumber=2)
                    .add_item_def(OID="IT.SUBJID", Name="Subject ID",
                                  DataType="text")
                    .add_item_def(OID="IT.AGE", Name="Age", DataType="integer")
                    .build())

    def test_to_json_round_trip(self):
        """Builder document can be serialised to JSON and back to dict."""
        import json
        json_str = self.odm.to_json()
        d = json.loads(json_str)
        self.assertEqual(d["FileOID"], "F.BUILDER")
        self.assertEqual(len(d["Study"]), 1)
        self.assertEqual(d["Study"][0]["OID"], "S.001")

    def test_to_xml_round_trip(self):
        """Builder document can be serialised to XML."""
        import xml.etree.ElementTree as ET
        xml_elem = self.odm.to_xml()
        self.assertIsNotNone(xml_elem)
        elem_name = xml_elem.tag[xml_elem.tag.find("}") + 1:]
        self.assertEqual(elem_name, "ODM")

    def test_write_xml_file(self):
        """Builder document can be written to an XML file."""
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            out_path = f.name
        try:
            self.odm.write_xml(out_path)
            self.assertTrue(os.path.getsize(out_path) > 0)
            # Sanity-check: the file starts with an XML declaration
            with open(out_path, "rb") as fh:
                header = fh.read(5)
            self.assertEqual(header, b"<?xml")
        finally:
            os.unlink(out_path)

    def test_write_json_file(self):
        """Builder document can be written to a JSON file."""
        import json
        with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False) as f:
            out_path = f.name
        try:
            self.odm.write_json(out_path)
            with open(out_path) as fh:
                d = json.load(fh)
            self.assertEqual(d["FileOID"], "F.BUILDER")
        finally:
            os.unlink(out_path)


class TestODMBuilderAlternatePackage(TestCase):
    """Tests that ODMBuilder respects the model_package argument."""

    def test_odm_2_0_builder(self):
        """ODMBuilder works with model_package='odm_2_0'."""
        import odmlib.ns_registry as NS
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")

        builder = ODMBuilder("odm_2_0")
        builder.set_file(FileOID="F.V2", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
        # ODM v2 model doesn't have GlobalVariables in the same way, so just
        # verify the builder constructs without errors at the ODM level
        odm = builder.build()
        self.assertEqual(odm.FileOID, "F.V2")
