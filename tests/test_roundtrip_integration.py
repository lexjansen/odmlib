"""Integration tests: full round-trip XML → objects → JSON → objects → XML.

These tests load real-world documents, convert them through all serialisation
formats, and verify structural equivalence.  They serve as regression tests
for the entire serialisation pipeline and catch subtle regressions that unit
tests on individual elements cannot.
"""
import json
import os
import tempfile
from unittest import TestCase
import odmlib.odm_loader as OL
import odmlib.define_loader as DL
import odmlib.loader as LD
import odmlib.ns_registry as NS


DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


# ---------------------------------------------------------------------------
# ODM 1.3.2 round-trips
# ---------------------------------------------------------------------------

class TestODM132RoundTrip(TestCase):
    """Round-trip tests for ODM 1.3.2 documents."""

    def setUp(self):
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")
        self.cdash_xml = os.path.join(DATA_DIR, "cdash-odm-test.xml")

    # -- XML → objects -------------------------------------------------------

    def test_xml_loads_to_objects(self):
        loader = LD.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(self.cdash_xml)
        odm = loader.root()
        self.assertIsNotNone(odm)
        self.assertEqual(odm.FileOID, "CDASH_File_2011-10-24")
        self.assertGreater(len(odm.Study), 0)

    def test_xml_metadata_version_elements(self):
        loader = LD.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(self.cdash_xml)
        mdv = loader.MetaDataVersion()
        self.assertGreater(len(mdv.ItemDef), 0)
        self.assertGreater(len(mdv.ItemGroupDef), 0)
        self.assertGreater(len(mdv.StudyEventDef), 0)

    # -- XML → JSON ----------------------------------------------------------

    def test_xml_to_json_structure(self):
        loader = LD.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(self.cdash_xml)
        odm = loader.root()
        json_str = odm.to_json()
        self.assertGreater(len(json_str), 0)
        data = json.loads(json_str)
        self.assertIn("FileOID", data)
        self.assertEqual(data["FileOID"], odm.FileOID)
        self.assertIn("Study", data)
        self.assertIsInstance(data["Study"], list)

    def test_xml_to_json_preserves_item_defs(self):
        loader = LD.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(self.cdash_xml)
        mdv = loader.MetaDataVersion()
        n_items = len(mdv.ItemDef)

        odm = loader.root()
        data = json.loads(odm.to_json())
        mdv_data = data["Study"][0]["MetaDataVersion"][0]
        self.assertIn("ItemDef", mdv_data)
        self.assertEqual(len(mdv_data["ItemDef"]), n_items)

    # -- XML → dict ----------------------------------------------------------

    def test_xml_to_dict(self):
        loader = LD.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(self.cdash_xml)
        odm = loader.root()
        d = odm.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("FileOID", d)
        self.assertIn("Study", d)
        self.assertIsInstance(d["Study"], list)

    # -- write & reload ------------------------------------------------------

    def test_write_xml_and_reload(self):
        loader = LD.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(self.cdash_xml)
        odm = loader.root()

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            temp_path = f.name
        try:
            odm.write_xml(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            self.assertGreater(os.path.getsize(temp_path), 0)

            loader2 = LD.ODMLoader(OL.XMLODMLoader())
            loader2.open_odm_document(temp_path)
            odm2 = loader2.root()
            self.assertEqual(odm.FileOID, odm2.FileOID)
            self.assertEqual(odm.FileType, odm2.FileType)
        finally:
            os.unlink(temp_path)

    def test_write_xml_preserves_item_content(self):
        loader = LD.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(self.cdash_xml)
        odm    = loader.root()
        mdv    = loader.MetaDataVersion()
        first_item_oid  = mdv.ItemDef[0].OID
        first_item_name = mdv.ItemDef[0].Name

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            temp_path = f.name
        try:
            odm.write_xml(temp_path)
            loader2 = LD.ODMLoader(OL.XMLODMLoader())
            loader2.open_odm_document(temp_path)
            mdv2 = loader2.MetaDataVersion()
            self.assertEqual(mdv2.ItemDef[0].OID,  first_item_oid)
            self.assertEqual(mdv2.ItemDef[0].Name, first_item_name)
        finally:
            os.unlink(temp_path)

    # -- write & reload JSON -------------------------------------------------

    def test_json_round_trip_via_file(self):
        loader = LD.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(self.cdash_xml)
        odm = loader.root()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            temp_path = f.name
            f.write(odm.to_json())
        try:
            json_loader = LD.ODMLoader(OL.JSONODMLoader())
            odm_dict = json_loader.open_odm_document(temp_path)
            rt_odm   = json_loader.create_odmlib(odm_dict, "ODM")
            self.assertEqual(rt_odm.FileOID, odm.FileOID)
        finally:
            os.unlink(temp_path)


# ---------------------------------------------------------------------------
# Define-XML 2.1 round-trips
# ---------------------------------------------------------------------------

class TestDefine21RoundTrip(TestCase):
    """Round-trip tests for Define-XML 2.1 documents."""

    def setUp(self):
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(prefix="def",   uri="http://www.cdisc.org/ns/def/v2.1")
        NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")
        self.define21_xml = os.path.join(DATA_DIR, "defineV21-SDTM.xml")

    def test_xml_loads_to_objects(self):
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(self.define21_xml)
        odm = loader.root()
        self.assertIsNotNone(odm)
        # Define-XML ODM has Study as a single ODMObject (not a list)
        self.assertIsNotNone(odm.Study)

    def test_metadata_version_has_define_elements(self):
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(self.define21_xml)
        mdv = loader.MetaDataVersion()
        self.assertGreater(len(mdv.ItemGroupDef), 0)
        self.assertGreater(len(mdv.ItemDef), 0)

    def test_xml_to_json_structure(self):
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(self.define21_xml)
        odm = loader.root()
        data = json.loads(odm.to_json())
        self.assertIn("FileOID", data)
        self.assertIn("Study", data)

    def test_xml_to_json_preserves_item_defs(self):
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(self.define21_xml)
        mdv = loader.MetaDataVersion()
        n_items = len(mdv.ItemDef)

        odm  = loader.root()
        data = json.loads(odm.to_json())
        # Define-XML ODM serialises Study as a single dict, not a list
        study_data = data["Study"]
        mdv_data = study_data["MetaDataVersion"]
        self.assertIn("ItemDef", mdv_data)
        self.assertEqual(len(mdv_data["ItemDef"]), n_items)

    def test_xml_to_dict(self):
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(self.define21_xml)
        odm = loader.root()
        d = odm.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("FileOID", d)

    def test_write_xml_and_reload(self):
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(self.define21_xml)
        odm = loader.root()

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            temp_path = f.name
        try:
            odm.write_xml(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            self.assertGreater(os.path.getsize(temp_path), 0)

            loader2 = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
            loader2.open_odm_document(temp_path)
            odm2 = loader2.root()
            self.assertEqual(odm.FileOID, odm2.FileOID)
        finally:
            os.unlink(temp_path)


# ---------------------------------------------------------------------------
# Define-XML 2.0 round-trips
# ---------------------------------------------------------------------------

class TestDefine20RoundTrip(TestCase):
    """Round-trip tests for Define-XML 2.0 documents."""

    def setUp(self):
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(prefix="def",   uri="http://www.cdisc.org/ns/def/v2.0")
        NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")
        self.define20_xml = os.path.join(DATA_DIR, "define2-0-0-sdtm-test.xml")

    def test_xml_loads_to_objects(self):
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_0"))
        loader.open_odm_document(self.define20_xml)
        odm = loader.root()
        self.assertIsNotNone(odm)

    def test_metadata_version_populated(self):
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_0"))
        loader.open_odm_document(self.define20_xml)
        mdv = loader.MetaDataVersion()
        self.assertGreater(len(mdv.ItemDef), 0)

    def test_xml_to_json_structure(self):
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_0"))
        loader.open_odm_document(self.define20_xml)
        odm  = loader.root()
        data = json.loads(odm.to_json())
        self.assertIn("FileOID", data)
        self.assertIn("Study", data)


# ---------------------------------------------------------------------------
# Dataset-XML 1.0.1 round-trips
# ---------------------------------------------------------------------------

class TestDatasetXMLRoundTrip(TestCase):
    """Basic round-trip tests for Dataset-XML 1.0.1 documents."""

    def setUp(self):
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")
        self.ae_xml = os.path.join(DATA_DIR, "ae_test.xml")

    def test_xml_loads(self):
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="dataset_1_0_1",
                                              ns_uri="http://www.cdisc.org/ns/odm/v1.3"))
        loader.open_odm_document(self.ae_xml)
        odm = loader.root()
        self.assertIsNotNone(odm)

    def test_xml_to_json(self):
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="dataset_1_0_1",
                                              ns_uri="http://www.cdisc.org/ns/odm/v1.3"))
        loader.open_odm_document(self.ae_xml)
        odm  = loader.root()
        data = json.loads(odm.to_json())
        self.assertIn("FileOID", data)


# ---------------------------------------------------------------------------
# Cross-format equivalence
# ---------------------------------------------------------------------------

class TestCrossFormatEquivalence(TestCase):
    """Verify that XML and JSON representations carry the same key data."""

    def setUp(self):
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")

    def test_odm_odm_file_oid_in_both_formats(self):
        cdash_xml = os.path.join(DATA_DIR, "cdash-odm-test.xml")
        loader = LD.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(cdash_xml)
        odm = loader.root()

        xml_elem = odm.to_xml()
        json_data = json.loads(odm.to_json())

        self.assertEqual(xml_elem.attrib["FileOID"], odm.FileOID)
        self.assertEqual(json_data["FileOID"], odm.FileOID)

    def test_item_def_oid_round_trips_through_json(self):
        cdash_xml = os.path.join(DATA_DIR, "cdash-odm-test.xml")
        loader = LD.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(cdash_xml)
        mdv = loader.MetaDataVersion()

        original_oids = [item.OID for item in mdv.ItemDef]
        odm  = loader.root()
        data = json.loads(odm.to_json())
        mdv_data = data["Study"][0]["MetaDataVersion"][0]
        json_oids = [item["OID"] for item in mdv_data["ItemDef"]]

        self.assertEqual(original_oids, json_oids)

    def test_define21_item_group_count_preserved(self):
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
        define21_xml = os.path.join(DATA_DIR, "defineV21-SDTM.xml")
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(define21_xml)
        mdv = loader.MetaDataVersion()
        n_igd = len(mdv.ItemGroupDef)

        odm  = loader.root()
        data = json.loads(odm.to_json())
        # Define-XML ODM serialises Study as a single dict, not a list
        mdv_data = data["Study"]["MetaDataVersion"]
        self.assertEqual(len(mdv_data["ItemGroupDef"]), n_igd)
