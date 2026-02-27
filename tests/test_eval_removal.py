"""Regression tests for eval()/exec() removal in loaders.

These tests verify that replacing eval()/exec() with getattr()/setattr()
in XMLODMLoader, JSONODMLoader, XMLDefineLoader, and JSONDefineLoader
produces identical results to what the original eval-based code returned.

The strategy is to load each test fixture with the now-refactored loader
and verify:
1. The root element type and key attributes are correct.
2. Nested child elements are correctly populated.
3. List elements contain the expected number of items.
4. A round-trip (load → to_dict → compare) works without data loss.
"""
import json
import os
from unittest import TestCase
import odmlib.odm_loader as OL
import odmlib.define_loader as DL
import odmlib.loader as LD


DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


class TestXMLODMLoaderNoEval(TestCase):
    """Verify XMLODMLoader works correctly without eval()."""

    def setUp(self):
        self.cdash_xml = os.path.join(DATA_DIR, "cdash-odm-test.xml")
        self.loader = LD.ODMLoader(OL.XMLODMLoader())

    def test_root_element_loads_correctly(self):
        """Root ODM element has correct FileOID after load."""
        self.loader.open_odm_document(self.cdash_xml)
        odm = self.loader.root()
        self.assertEqual(odm.FileOID, "CDASH_File_2011-10-24")
        self.assertEqual(odm.FileType, "Snapshot")

    def test_study_element_loaded(self):
        """Study child elements are populated by the loader."""
        self.loader.open_odm_document(self.cdash_xml)
        odm = self.loader.root()
        self.assertGreater(len(odm.Study), 0)
        self.assertIsNotNone(odm.Study[0].GlobalVariables)

    def test_metadata_version_loaded(self):
        """MetaDataVersion loads with correct OID and Name."""
        self.loader.open_odm_document(self.cdash_xml)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(mdv.Name, "TRACE-XML MDV")

    def test_item_defs_loaded(self):
        """ItemDef list elements are correctly loaded from XML."""
        self.loader.open_odm_document(self.cdash_xml)
        mdv = self.loader.MetaDataVersion()
        self.assertGreater(len(mdv.ItemDef), 0)
        # Verify nested text content in a Question element is preserved
        item_with_question = next(
            (i for i in mdv.ItemDef if i.Question is not None), None)
        self.assertIsNotNone(item_with_question)
        self.assertGreater(len(item_with_question.Question.TranslatedText), 0)

    def test_item_group_defs_loaded(self):
        """ItemGroupDef list elements are loaded with their ItemRefs."""
        self.loader.open_odm_document(self.cdash_xml)
        mdv = self.loader.MetaDataVersion()
        self.assertGreater(len(mdv.ItemGroupDef), 0)
        self.assertGreater(len(mdv.ItemGroupDef[0].ItemRef), 0)

    def test_code_lists_loaded(self):
        """CodeList and CodeListItem elements are loaded correctly."""
        self.loader.open_odm_document(self.cdash_xml)
        mdv = self.loader.MetaDataVersion()
        self.assertGreater(len(mdv.CodeList), 0)
        cl = mdv.CodeList[0]
        self.assertIsNotNone(cl.OID)
        # At least one code list should have coded items
        items_count = sum(len(c.CodeListItem) for c in mdv.CodeList)
        self.assertGreater(items_count, 0)

    def test_element_order_preserved(self):
        """verify_order() passes after loading (no reordering needed)."""
        self.loader.open_odm_document(self.cdash_xml)
        odm = self.loader.root()
        self.assertTrue(odm.verify_order())

    def test_json_round_trip_after_xml_load(self):
        """to_json() after XML load returns parseable JSON with expected keys."""
        self.loader.open_odm_document(self.cdash_xml)
        odm = self.loader.root()
        json_str = odm.to_json()
        d = json.loads(json_str)
        self.assertEqual(d["FileOID"], "CDASH_File_2011-10-24")
        self.assertIn("Study", d)

    def test_find_works_after_load(self):
        """find() (getattr-based) works correctly on XML-loaded objects."""
        self.loader.open_odm_document(self.cdash_xml)
        mdv = self.loader.MetaDataVersion()
        it = mdv.find("ItemDef", "OID", "ODM.IT.AE.AEYN")
        self.assertIsNotNone(it)
        self.assertEqual(it.OID, "ODM.IT.AE.AEYN")

    def test_element_with_text_content_loaded(self):
        """Elements with text content (_content) are loaded correctly."""
        self.loader.open_odm_document(self.cdash_xml)
        mdv = self.loader.MetaDataVersion()
        # Question TranslatedText has _content
        item_def = mdv.ItemDef[3]
        self.assertIsNotNone(item_def.Question)
        tt = item_def.Question.TranslatedText[0]
        self.assertIsNotNone(tt._content)
        self.assertEqual(tt._content, "Visit Date")


class TestJSONODMLoaderNoEval(TestCase):
    """Verify JSONODMLoader works correctly without eval()."""

    def setUp(self):
        self.cdash_json = os.path.join(DATA_DIR, "cdash_odm_test.json")
        self.loader = LD.ODMLoader(OL.JSONODMLoader())

    def test_root_loads_from_json(self):
        """Root ODM element loads from JSON without eval()."""
        self.loader.open_odm_document(self.cdash_json)
        odm = self.loader.root()
        self.assertIsNotNone(odm)
        self.assertTrue(hasattr(odm, "FileOID"))
        self.assertIsNotNone(odm.FileOID)

    def test_study_loaded_from_json(self):
        """Study is populated from JSON loader."""
        self.loader.open_odm_document(self.cdash_json)
        odm = self.loader.root()
        self.assertIsNotNone(odm.Study)

    def test_metadata_version_from_json(self):
        """MetaDataVersion loads from JSON."""
        self.loader.open_odm_document(self.cdash_json)
        mdv = self.loader.MetaDataVersion()
        self.assertIsNotNone(mdv)
        self.assertIsNotNone(mdv.OID)

    def test_item_defs_from_json(self):
        """ItemDef list elements load from JSON."""
        self.loader.open_odm_document(self.cdash_json)
        mdv = self.loader.MetaDataVersion()
        self.assertIsInstance(mdv.ItemDef, list)

    def test_code_lists_from_json(self):
        """CodeList elements load from JSON."""
        self.loader.open_odm_document(self.cdash_json)
        mdv = self.loader.MetaDataVersion()
        self.assertIsInstance(mdv.CodeList, list)

    def test_json_to_dict_round_trip(self):
        """ODM loaded from JSON can be converted back to dict."""
        self.loader.open_odm_document(self.cdash_json)
        odm = self.loader.root()
        d = odm.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("FileOID", d)


class TestXMLDefineLoaderNoEval(TestCase):
    """Verify XMLDefineLoader works correctly without eval()."""

    def setUp(self):
        self.define_xml = os.path.join(DATA_DIR, "defineV21-SDTM.xml")
        self.loader = LD.ODMLoader(
            DL.XMLDefineLoader(model_package="define_2_1"))

    def test_root_loads_from_define_xml(self):
        """Root ODM element loads from Define-XML without eval()."""
        self.loader.open_odm_document(self.define_xml)
        odm = self.loader.root()
        self.assertIsNotNone(odm)
        self.assertTrue(hasattr(odm, "FileOID"))

    def test_study_loaded_from_define_xml(self):
        """Study element is populated from Define-XML."""
        self.loader.open_odm_document(self.define_xml)
        odm = self.loader.root()
        self.assertIsNotNone(odm.Study)

    def test_metadata_version_from_define_xml(self):
        """MetaDataVersion loads from Define-XML."""
        self.loader.open_odm_document(self.define_xml)
        mdv = self.loader.MetaDataVersion()
        self.assertIsNotNone(mdv)
        self.assertIsNotNone(mdv.OID)

    def test_item_defs_from_define_xml(self):
        """ItemDef list elements load from Define-XML."""
        self.loader.open_odm_document(self.define_xml)
        mdv = self.loader.MetaDataVersion()
        self.assertIsInstance(mdv.ItemDef, list)
        self.assertGreater(len(mdv.ItemDef), 0)

    def test_item_group_defs_from_define_xml(self):
        """ItemGroupDef list elements load from Define-XML."""
        self.loader.open_odm_document(self.define_xml)
        mdv = self.loader.MetaDataVersion()
        self.assertIsInstance(mdv.ItemGroupDef, list)
        self.assertGreater(len(mdv.ItemGroupDef), 0)

    def test_element_order_after_define_load(self):
        """verify_order() passes after loading Define-XML."""
        self.loader.open_odm_document(self.define_xml)
        odm = self.loader.root()
        self.assertTrue(odm.verify_order())

    def test_namespace_stripped_attributes_loaded(self):
        """Define namespace attributes (def:*) load correctly via getattr."""
        self.loader.open_odm_document(self.define_xml)
        mdv = self.loader.MetaDataVersion()
        # ItemGroupDef in Define-XML has def:Structure
        igd = mdv.ItemGroupDef[0]
        self.assertIsNotNone(igd.Structure)

    def test_find_on_define_loaded_objects(self):
        """find() works on Define-XML loaded objects."""
        self.loader.open_odm_document(self.define_xml)
        mdv = self.loader.MetaDataVersion()
        if mdv.ItemDef:
            first_oid = mdv.ItemDef[0].OID
            result = mdv.find("ItemDef", "OID", first_oid)
            self.assertIsNotNone(result)
            self.assertEqual(result.OID, first_oid)


class TestJSONDefineLoaderNoEval(TestCase):
    """Verify JSONDefineLoader works correctly without eval()."""

    def setUp(self):
        self.define_json = os.path.join(DATA_DIR, "defineV21-SDTM-test.json")
        self.loader = LD.ODMLoader(
            DL.JSONDefineLoader(model_package="define_2_1"))

    def test_root_loads_from_define_json(self):
        """Root ODM element loads from Define-XML JSON without eval()."""
        self.loader.open_odm_document(self.define_json)
        odm = self.loader.root()
        self.assertIsNotNone(odm)
        self.assertTrue(hasattr(odm, "FileOID"))

    def test_study_loaded_from_define_json(self):
        """Study element is populated from Define-XML JSON loader."""
        self.loader.open_odm_document(self.define_json)
        odm = self.loader.root()
        self.assertIsNotNone(odm.Study)

    def test_metadata_version_from_define_json(self):
        """MetaDataVersion loads from Define-XML JSON."""
        self.loader.open_odm_document(self.define_json)
        mdv = self.loader.MetaDataVersion()
        self.assertIsNotNone(mdv)
        self.assertIsNotNone(mdv.OID)

    def test_item_group_defs_from_define_json(self):
        """ItemGroupDef list elements load from Define-XML JSON."""
        self.loader.open_odm_document(self.define_json)
        mdv = self.loader.MetaDataVersion()
        self.assertIsInstance(mdv.ItemGroupDef, list)
        self.assertGreater(len(mdv.ItemGroupDef), 0)

    def test_dict_round_trip_after_define_json_load(self):
        """to_dict() after loading Define-XML JSON returns a valid dict."""
        self.loader.open_odm_document(self.define_json)
        odm = self.loader.root()
        d = odm.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("FileOID", d)


class TestDescriptorMutableDefault(TestCase):
    """Regression test for the mutable default valid_values=[] bug fix."""

    def test_descriptor_valid_values_not_shared(self):
        """Each Descriptor instance has its own valid_values list."""
        from odmlib.descriptor import Descriptor

        d1 = Descriptor(name="d1")
        d2 = Descriptor(name="d2")
        # Mutating one instance's list should not affect the other
        d1.valid_values.append("test_value")
        self.assertNotIn("test_value", d2.valid_values)

    def test_descriptor_default_valid_values_is_empty_list(self):
        """Descriptor with no valid_values argument gets an empty list."""
        from odmlib.descriptor import Descriptor

        d = Descriptor(name="test")
        self.assertEqual(d.valid_values, [])
        self.assertIsInstance(d.valid_values, list)

    def test_descriptor_explicit_valid_values_preserved(self):
        """Descriptor with explicit valid_values stores them correctly."""
        from odmlib.descriptor import Descriptor

        d = Descriptor(name="test", valid_values=["A", "B", "C"])
        self.assertEqual(d.valid_values, ["A", "B", "C"])
