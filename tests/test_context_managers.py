"""Tests for odmlib context managers (odmlib.context).

Covers:
- open_odm(): loading XML and JSON ODM documents.
- open_define(): loading Define-XML documents.
- Auto-save on clean exit.
- No-save when an exception propagates.
- Custom output_file parameter.
- Format auto-detection from file extension.
"""
import json
import os
import shutil
import tempfile
from unittest import TestCase
from odmlib.context import open_odm, open_define, ODMContext, DefineContext


DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
CDASH_XML = os.path.join(DATA_DIR, "cdash-odm-test.xml")
CDASH_JSON = os.path.join(DATA_DIR, "cdash_odm_test.json")
DEFINE_21_XML = os.path.join(DATA_DIR, "defineV21-SDTM.xml")


class TestOpenOdmXML(TestCase):
    """Tests for open_odm() with XML format."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_open_odm_loads_document(self):
        """open_odm() context manager yields a loaded ODM root object."""
        out_path = os.path.join(self.tmpdir, "out.xml")
        with open_odm(CDASH_XML, output_file=out_path) as odm:
            self.assertIsNotNone(odm)
            self.assertEqual(odm.FileOID, "CDASH_File_2011-10-24")

    def test_open_odm_writes_on_clean_exit(self):
        """open_odm() saves the document to output_file on clean exit."""
        out_path = os.path.join(self.tmpdir, "output.xml")
        with open_odm(CDASH_XML, output_file=out_path) as odm:
            self.assertEqual(odm.FileOID, "CDASH_File_2011-10-24")
        self.assertTrue(os.path.exists(out_path))
        self.assertGreater(os.path.getsize(out_path), 0)

    def test_open_odm_no_write_on_exception(self):
        """open_odm() does NOT save if an exception escapes the with block."""
        out_path = os.path.join(self.tmpdir, "should_not_exist.xml")
        with self.assertRaises(ValueError):
            with open_odm(CDASH_XML, output_file=out_path) as odm:
                raise ValueError("intentional test error")
        self.assertFalse(os.path.exists(out_path))

    def test_open_odm_exception_is_propagated(self):
        """open_odm() does not suppress exceptions."""
        with self.assertRaises(RuntimeError):
            with open_odm(CDASH_XML) as odm:
                raise RuntimeError("test error")

    def test_open_odm_modifies_and_saves(self):
        """Changes made inside the with block are persisted to disk."""
        out_path = os.path.join(self.tmpdir, "modified.xml")
        with open_odm(CDASH_XML, output_file=out_path) as odm:
            odm.SourceSystem = "TestSystem"
        # Read back and verify the change was saved
        with open_odm(out_path) as odm2:
            self.assertEqual(odm2.SourceSystem, "TestSystem")

    def test_open_odm_auto_detect_xml_format(self):
        """open_odm() detects XML format from .xml file extension."""
        ctx = open_odm(CDASH_XML)
        self.assertEqual(ctx.format, "xml")

    def test_open_odm_in_place_update(self):
        """open_odm() with no output_file writes back to the input file."""
        in_path = os.path.join(self.tmpdir, "inplace.xml")
        shutil.copy(CDASH_XML, in_path)
        with open_odm(in_path) as odm:
            odm.SourceSystem = "InPlaceTest"
        with open_odm(in_path) as odm2:
            self.assertEqual(odm2.SourceSystem, "InPlaceTest")


class TestOpenOdmJSON(TestCase):
    """Tests for open_odm() with JSON format."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_open_odm_json_loads_document(self):
        """open_odm() context manager yields a loaded ODM root from JSON."""
        out_path = os.path.join(self.tmpdir, "out.json")
        with open_odm(CDASH_JSON, output_file=out_path) as odm:
            self.assertIsNotNone(odm)
            # Verify it loaded a valid ODM object
            self.assertTrue(hasattr(odm, "FileOID"))

    def test_open_odm_json_auto_detect_format(self):
        """open_odm() detects JSON format from .json file extension."""
        ctx = open_odm(CDASH_JSON)
        self.assertEqual(ctx.format, "json")

    def test_open_odm_json_writes_on_clean_exit(self):
        """open_odm() saves JSON to output_file on clean exit."""
        out_path = os.path.join(self.tmpdir, "output.json")
        with open_odm(CDASH_JSON, output_file=out_path) as odm:
            pass  # no modifications
        self.assertTrue(os.path.exists(out_path))
        with open(out_path) as fh:
            d = json.load(fh)
        self.assertIn("FileOID", d)

    def test_open_odm_json_no_write_on_exception(self):
        """open_odm() does NOT save JSON if an exception escapes."""
        out_path = os.path.join(self.tmpdir, "should_not_exist.json")
        with self.assertRaises(ValueError):
            with open_odm(CDASH_JSON, output_file=out_path) as odm:
                raise ValueError("test error")
        self.assertFalse(os.path.exists(out_path))


class TestOpenDefine(TestCase):
    """Tests for open_define() context manager."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_open_define_loads_document(self):
        """open_define() loads a Define-XML 2.1 document successfully."""
        out_path = os.path.join(self.tmpdir, "define_out.xml")
        with open_define(DEFINE_21_XML, output_file=out_path) as define:
            self.assertIsNotNone(define)
            self.assertTrue(hasattr(define, "FileOID"))

    def test_open_define_writes_on_clean_exit(self):
        """open_define() saves to output_file on clean exit."""
        out_path = os.path.join(self.tmpdir, "define_out.xml")
        with open_define(DEFINE_21_XML, output_file=out_path) as define:
            pass
        self.assertTrue(os.path.exists(out_path))
        self.assertGreater(os.path.getsize(out_path), 0)

    def test_open_define_no_write_on_exception(self):
        """open_define() does NOT save if an exception escapes."""
        out_path = os.path.join(self.tmpdir, "no_output.xml")
        with self.assertRaises(RuntimeError):
            with open_define(DEFINE_21_XML, output_file=out_path) as define:
                raise RuntimeError("test error")
        self.assertFalse(os.path.exists(out_path))


class TestContextManagerClasses(TestCase):
    """Unit tests for ODMContext and DefineContext class behaviour."""

    def test_odmcontext_detect_xml(self):
        """ODMContext detects xml format from .xml extension."""
        ctx = ODMContext("file.xml")
        self.assertEqual(ctx.format, "xml")

    def test_odmcontext_detect_json(self):
        """ODMContext detects json format from .json extension."""
        ctx = ODMContext("file.json")
        self.assertEqual(ctx.format, "json")

    def test_odmcontext_explicit_format_overrides(self):
        """Explicit format parameter overrides auto-detection."""
        ctx = ODMContext("file.xml", format="json")
        self.assertEqual(ctx.format, "json")

    def test_odmcontext_output_file_default(self):
        """output_file defaults to input_file when not specified."""
        ctx = ODMContext("study.xml")
        self.assertEqual(ctx.output_file, "study.xml")

    def test_odmcontext_custom_output_file(self):
        """output_file is stored when specified."""
        ctx = ODMContext("study.xml", output_file="out.xml")
        self.assertEqual(ctx.output_file, "out.xml")

    def test_definecontext_default_package(self):
        """DefineContext defaults to define_2_1 model package."""
        ctx = DefineContext("define.xml")
        self.assertEqual(ctx.model_package, "define_2_1")

    def test_odmcontext_default_package(self):
        """ODMContext defaults to odm_1_3_2 model package."""
        ctx = ODMContext("study.xml")
        self.assertEqual(ctx.model_package, "odm_1_3_2")

    def test_open_odm_returns_odmcontext(self):
        """open_odm() returns an ODMContext instance."""
        ctx = open_odm("study.xml")
        self.assertIsInstance(ctx, ODMContext)

    def test_open_define_returns_definecontext(self):
        """open_define() returns a DefineContext instance."""
        ctx = open_define("define.xml")
        self.assertIsInstance(ctx, DefineContext)
