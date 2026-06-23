"""Conformance tests for the ODM root element in Define-XML 2.0/2.1.

These tests cover the bug where ``MetadataSchema._set_metadata_registry()``
did not register an "ODM" key, so ``odm.validate(conformance_checker=...)``
crashed with Cerberus's ``SchemaError`` (not an ``OdmlibError``) at the
root before reaching any per-element schema.
"""
import os
from unittest import TestCase

import odmlib.define_2_0.model as DEF20
import odmlib.define_2_0.rules.metadata_schema as METADATA_20
import odmlib.define_2_1.model as DEF21
import odmlib.define_2_1.rules.metadata_schema as METADATA_21
import odmlib.define_loader as DL
import odmlib.loader as LD
from odmlib.exceptions import OdmlibConformanceError


DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


class TestDefine21RootConformance(TestCase):
    def setUp(self):
        self.validator = METADATA_21.MetadataSchema()
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(os.path.join(DATA_DIR, "defineV21-SDTM-metadata.xml"))
        self.odm = loader.root()

    def test_verify_conformance_on_root_passes(self):
        self.assertTrue(self.odm.verify_conformance(self.validator))

    def test_validate_with_conformance_checker_passes(self):
        self.assertTrue(self.odm.validate(conformance_checker=self.validator))

    def test_invalid_filetype_raises_odmlib_error(self):
        doc = self.odm.to_dict()
        doc["FileType"] = "Transactional"
        with self.assertRaises(OdmlibConformanceError) as ctx:
            self.validator.check_conformance(doc, "ODM")
        self.assertEqual(ctx.exception.element_type, "ODM")
        self.assertIn("FileType", ctx.exception.cerberus_errors)


class TestDefine20RootConformance(TestCase):
    def setUp(self):
        self.validator = METADATA_20.MetadataSchema()
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_0"))
        loader.open_odm_document(os.path.join(DATA_DIR, "define2-0-0-sdtm-test.xml"))
        self.odm = loader.root()

    def test_verify_conformance_on_root_passes(self):
        self.assertTrue(self.odm.verify_conformance(self.validator))

    def test_invalid_odmversion_raises_odmlib_error(self):
        doc = self.odm.to_dict()
        doc["ODMVersion"] = "2.0"
        with self.assertRaises(OdmlibConformanceError) as ctx:
            self.validator.check_conformance(doc, "ODM")
        self.assertEqual(ctx.exception.element_type, "ODM")
        self.assertIn("ODMVersion", ctx.exception.cerberus_errors)


class TestUnregisteredSchemaName(TestCase):
    """Graceful failure when a schema_name isn't in the registry — covers
    the odm_2_0 case (no MetadataSchema implementation) and any future gap.
    """

    def test_define21_unknown_schema_raises_odmlib_error(self):
        validator = METADATA_21.MetadataSchema()
        with self.assertRaises(OdmlibConformanceError) as ctx:
            validator.check_conformance({}, "DoesNotExist")
        self.assertEqual(ctx.exception.element_type, "DoesNotExist")
        self.assertIn("No conformance schema registered", str(ctx.exception))

    def test_define20_unknown_schema_raises_odmlib_error(self):
        validator = METADATA_20.MetadataSchema()
        with self.assertRaises(OdmlibConformanceError) as ctx:
            validator.check_conformance({}, "DoesNotExist")
        self.assertEqual(ctx.exception.element_type, "DoesNotExist")
