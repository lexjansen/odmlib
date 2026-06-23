import os
from unittest import TestCase

import xmlschema

import odmlib.odm_parser as P


class TestODMValidator(TestCase):
    def setUp(self) -> None:
        self.define_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'defineV21-SDTM.xml')
        # Use packaged Define-XML v2.1 schema bundled with odmlib
        self.validator = P.ODMSchemaValidator(standard="define", version="2.1")

    def test_validate_tree_valid(self):
        self.parser = P.ODMParser(self.define_file)
        tree = self.parser.parse_tree()
        is_valid = self.validator.validate_tree(tree)
        self.assertTrue(is_valid)

    def test_validate_file(self):
        # validate file raises an exception if validation fails
        self.assertIsNone(self.validator.validate_file(self.define_file))

    def test_validate_file_invalid_class(self):
        define_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data',
                                   'defineV21-SDTM-invalid-class.xml')
        try:
            self.validator.validate_file(define_file)
        except xmlschema.validators.exceptions.XMLSchemaValidatorError as ex:
            self.assertIn("attribute Name='NONSENSE': value must be one of", ex.reason)

    def test_validate_file_send_class(self):
        define_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data',
                                   'defineV21-SEND-class.xml')
        try:
            self.validator.validate_file(define_file)
        except xmlschema.validators.exceptions.XMLSchemaValidatorError as ex:
            self.fail("Expected to pass validation with SEND class STUDY REFERENCE")
        else:
            self.assertTrue(True)

    def test_validate_file_invalid_msg(self):
        odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'defineV21-SDTM-invalid.xml')
        try:
            self.validator.validate_file(odm_file)
        except xmlschema.validators.exceptions.XMLSchemaValidationError as ex:
            self.assertIn("missing required attribute", ex.reason)
        else:
            self.fail("Expected XMLSchemaValidationError")

    # def test_validate_tree_invalid(self):
    #     odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-test-invalid.xml')
    #     self.parser = P.ODMParser(odm_file)
    #     tree = self.parser.parse_tree()
    #     is_valid = self.validator.validate_tree(tree)
    #     self.assertFalse(is_valid)
    #
    # def test_validate_string_tree_valid(self):
    #     with open(self.odm_file, "r", encoding="utf-8") as f:
    #         self.odm_string = f.read()
    #     self.parser = P.ODMStringParser(self.odm_string)
    #     tree = self.parser.parse_tree()
    #     is_valid = self.validator.validate_tree(tree)
    #     self.assertTrue(is_valid)
