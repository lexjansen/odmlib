"""Tests for the eval()-free find(), find_all(), and find_by() methods.

Verifies that:
1. Existing find() behaviour is unchanged after replacing eval() with getattr().
2. New find_all() returns *all* matching elements.
3. New find_by() supports multi-attribute keyword matching.
4. A malicious obj_name raises AttributeError instead of executing arbitrary
   code (regression test for the removed eval() call).
"""
import os
from unittest import TestCase
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_loader as OL
import odmlib.loader as LD


DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
CDASH_XML = os.path.join(DATA_DIR, "cdash-odm-test.xml")


class TestFindSafe(TestCase):
    """Tests for find() on in-memory objects (no loader required)."""

    def setUp(self):
        # Build a small in-memory model to test find methods.
        tt = ODM.TranslatedText(_content="Age", lang="en")
        q = ODM.Question(TranslatedText=[tt])
        self.item1 = ODM.ItemDef(OID="IT.AGE", Name="Age", DataType="integer",
                                 Question=q)

        tt2 = ODM.TranslatedText(_content="Sex", lang="en")
        q2 = ODM.Question(TranslatedText=[tt2])
        self.item2 = ODM.ItemDef(OID="IT.SEX", Name="Sex", DataType="text")

        tt3 = ODM.TranslatedText(_content="Visit Date", lang="en")
        q3 = ODM.Question(TranslatedText=[tt3])
        self.item3 = ODM.ItemDef(OID="IT.VDAT", Name="VISITDAT", DataType="date")

        self.ref1 = ODM.ItemRef(ItemOID="IT.AGE", Mandatory="Yes", OrderNumber=1)
        self.ref2 = ODM.ItemRef(ItemOID="IT.SEX", Mandatory="No", OrderNumber=2)
        self.ref3 = ODM.ItemRef(ItemOID="IT.VDAT", Mandatory="Yes", OrderNumber=3)

        self.igd = ODM.ItemGroupDef(
            OID="IG.DM", Name="Demographics", Repeating="No",
            ItemRef=[self.ref1, self.ref2, self.ref3],
        )

        include = ODM.Include(StudyOID="S.TEST", MetaDataVersionOID="MDV.001")
        self.mdv = ODM.MetaDataVersion(
            OID="MDV.001", Name="Version 1",
            ItemDef=[self.item1, self.item2, self.item3],
            ItemGroupDef=[self.igd],
            Include=include,
        )

    # ------------------------------------------------------------------
    # find() — identical API to original eval()-based implementation
    # ------------------------------------------------------------------

    def test_find_item_def_by_oid(self):
        """find() locates the correct ItemDef in a list."""
        result = self.mdv.find("ItemDef", "OID", "IT.AGE")
        self.assertIsNotNone(result)
        self.assertEqual(result.OID, "IT.AGE")

    def test_find_item_def_second_element(self):
        """find() returns the first match, not always index 0."""
        result = self.mdv.find("ItemDef", "OID", "IT.SEX")
        self.assertIsNotNone(result)
        self.assertEqual(result.OID, "IT.SEX")

    def test_find_returns_none_for_missing_value(self):
        """find() returns None when no element matches."""
        result = self.mdv.find("ItemDef", "OID", "IT.NONEXISTENT")
        self.assertIsNone(result)

    def test_find_item_ref_in_item_group_def(self):
        """find() works on ItemRef lists inside an ItemGroupDef."""
        result = self.igd.find("ItemRef", "ItemOID", "IT.SEX")
        self.assertIsNotNone(result)
        self.assertEqual(result.ItemOID, "IT.SEX")

    def test_find_item_ref_returns_none(self):
        """find() returns None for missing ItemRef."""
        result = self.igd.find("ItemRef", "ItemOID", "IT.MISSING")
        self.assertIsNone(result)

    def test_find_non_list_element_matches(self):
        """find() on a single (non-list) ODMObject returns it when attrs match."""
        result = self.mdv.find("Include", "StudyOID", "S.TEST")
        self.assertIsNotNone(result)
        self.assertEqual(result.StudyOID, "S.TEST")

    def test_find_non_list_element_no_match(self):
        """find() on a non-list element returns None when attrs don't match."""
        result = self.mdv.find("Include", "StudyOID", "S.WRONG")
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # Security: injection attempt raises AttributeError
    # ------------------------------------------------------------------

    def test_find_injection_raises_attribute_error(self):
        """find() with a malicious obj_name raises AttributeError.

        With eval(), `find('__class__.__bases__', ...)` would execute
        arbitrary Python.  With getattr() it raises AttributeError cleanly.
        """
        with self.assertRaises(AttributeError):
            self.mdv.find("__class__.__bases__", "OID", "x")

    def test_find_nonexistent_attr_raises_attribute_error(self):
        """find() with an unrecognised element name raises AttributeError."""
        with self.assertRaises(AttributeError):
            self.mdv.find("NonExistentElement", "OID", "x")

    # ------------------------------------------------------------------
    # find_all()
    # ------------------------------------------------------------------

    def test_find_all_returns_all_matches(self):
        """find_all() returns every ItemRef where Mandatory=='Yes'."""
        results = self.igd.find_all("ItemRef", "Mandatory", "Yes")
        self.assertEqual(len(results), 2)
        oids = {r.ItemOID for r in results}
        self.assertIn("IT.AGE", oids)
        self.assertIn("IT.VDAT", oids)

    def test_find_all_returns_empty_list_when_no_match(self):
        """find_all() returns [] when nothing matches."""
        results = self.igd.find_all("ItemRef", "Mandatory", "Maybe")
        self.assertEqual(results, [])

    def test_find_all_returns_list_type(self):
        """find_all() always returns a list."""
        results = self.igd.find_all("ItemRef", "ItemOID", "IT.AGE")
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)

    def test_find_all_single_object_match(self):
        """find_all() on a non-list element wraps match in a list."""
        results = self.mdv.find_all("Include", "StudyOID", "S.TEST")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].StudyOID, "S.TEST")

    def test_find_all_single_object_no_match(self):
        """find_all() on a non-list element returns [] on mismatch."""
        results = self.mdv.find_all("Include", "StudyOID", "S.WRONG")
        self.assertEqual(results, [])

    # ------------------------------------------------------------------
    # find_by()
    # ------------------------------------------------------------------

    def test_find_by_single_kwarg(self):
        """find_by() with one kwarg is equivalent to find()."""
        result = self.igd.find_by("ItemRef", ItemOID="IT.AGE")
        self.assertIsNotNone(result)
        self.assertEqual(result.ItemOID, "IT.AGE")

    def test_find_by_multiple_kwargs(self):
        """find_by() with multiple kwargs requires all to match."""
        result = self.igd.find_by("ItemRef", ItemOID="IT.AGE", Mandatory="Yes")
        self.assertIsNotNone(result)
        self.assertEqual(result.ItemOID, "IT.AGE")

    def test_find_by_multiple_kwargs_no_match(self):
        """find_by() returns None when not all criteria match."""
        # IT.AGE is Mandatory=Yes but OrderNumber=1 — this combo DOES match
        result = self.igd.find_by("ItemRef", ItemOID="IT.AGE", Mandatory="No")
        self.assertIsNone(result)

    def test_find_by_returns_first_match(self):
        """find_by() returns the first element matching all criteria."""
        result = self.igd.find_by("ItemRef", Mandatory="Yes")
        self.assertIsNotNone(result)
        self.assertEqual(result.ItemOID, "IT.AGE")  # first Yes ref

    def test_find_by_returns_none_when_no_match(self):
        """find_by() returns None when no element satisfies all criteria."""
        result = self.igd.find_by("ItemRef", ItemOID="NONEXISTENT")
        self.assertIsNone(result)


class TestFindSafeViaLoader(TestCase):
    """Tests that verify find() works correctly on loader-produced objects.

    This ensures the eval()-to-getattr() change in find() is compatible
    with real XML-loaded data.
    """

    def setUp(self):
        self.loader = LD.ODMLoader(OL.XMLODMLoader())
        self.loader.open_odm_document(CDASH_XML)
        self.mdv = self.loader.MetaDataVersion()

    def test_find_item_def_from_loaded_xml(self):
        """find() works on XML-loaded MetaDataVersion for ItemDef by OID."""
        it = self.mdv.find("ItemDef", "OID", "ODM.IT.AE.AEYN")
        self.assertIsNotNone(it)
        self.assertEqual(it.OID, "ODM.IT.AE.AEYN")

    def test_find_item_ref_in_loaded_item_group_def(self):
        """find() works on ItemRef list inside a loaded ItemGroupDef."""
        ir = self.mdv.ItemGroupDef[0].find("ItemRef", "ItemOID", "ODM.IT.Common.SiteID")
        self.assertIsNotNone(ir)
        self.assertEqual(ir.ItemOID, self.mdv.ItemGroupDef[0].ItemRef[1].ItemOID)

    def test_find_code_list_item_from_loaded_xml(self):
        """find() works on CodeListItem list."""
        cli = self.mdv.CodeList[2].find("CodeListItem", "CodedValue", "DOSE REDUCED")
        self.assertIsNotNone(cli)
        self.assertEqual(cli.Decode.TranslatedText[0]._content, "DOSE REDUCED")

    def test_find_all_returns_multiple_item_defs(self):
        """find_all() on loaded data returns all items with DataType=='text'."""
        text_items = self.mdv.find_all("ItemDef", "DataType", "text")
        self.assertIsInstance(text_items, list)
        self.assertGreater(len(text_items), 0)
        for item in text_items:
            self.assertEqual(item.DataType, "text")

    def test_find_by_on_loaded_data(self):
        """find_by() on loaded ItemGroupDef ItemRef list."""
        ref = self.mdv.ItemGroupDef[0].find_by("ItemRef", ItemOID="ODM.IT.Common.SiteID")
        self.assertIsNotNone(ref)
        self.assertEqual(ref.ItemOID, "ODM.IT.Common.SiteID")
