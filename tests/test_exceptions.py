"""Tests for the odmlib exception hierarchy (Phase 1)."""
import warnings
from unittest import TestCase

import odmlib
from odmlib.exceptions import (
    OdmlibError,
    OdmlibValidationError,
    OdmlibRequiredAttributeError,
    OdmlibOIDError,
    OdmlibConformanceError,
    OdmlibElementOrderError,
    OdmlibTypeError,
    OdmlibParsingError,
    OdmlibLoaderStateError,
    OdmlibSerializationError,
    OdmlibNamespaceError,
    OdmlibWarning,
    OdmlibDeprecationWarning,
    OdmlibInteroperabilityWarning,
    ErrorCollector,
)


class TestExceptionHierarchy(TestCase):
    """Verify exception class relationships."""

    # --- OdmlibValidationError ---

    def test_validation_error_is_odmlib_error(self):
        self.assertTrue(issubclass(OdmlibValidationError, OdmlibError))

    def test_validation_error_is_value_error_for_backward_compat(self):
        self.assertTrue(issubclass(OdmlibValidationError, ValueError))

    def test_required_attribute_error_is_validation_error(self):
        self.assertTrue(issubclass(OdmlibRequiredAttributeError, OdmlibValidationError))

    def test_required_attribute_error_is_value_error(self):
        self.assertTrue(issubclass(OdmlibRequiredAttributeError, ValueError))

    def test_oid_error_is_validation_error(self):
        self.assertTrue(issubclass(OdmlibOIDError, OdmlibValidationError))

    def test_conformance_error_is_validation_error(self):
        self.assertTrue(issubclass(OdmlibConformanceError, OdmlibValidationError))

    def test_element_order_error_is_validation_error(self):
        self.assertTrue(issubclass(OdmlibElementOrderError, OdmlibValidationError))

    # --- OdmlibTypeError ---

    def test_type_error_is_odmlib_error(self):
        self.assertTrue(issubclass(OdmlibTypeError, OdmlibError))

    def test_type_error_is_builtin_type_error_for_backward_compat(self):
        self.assertTrue(issubclass(OdmlibTypeError, TypeError))

    # --- OdmlibLoaderStateError ---

    def test_loader_state_error_is_parsing_error(self):
        self.assertTrue(issubclass(OdmlibLoaderStateError, OdmlibParsingError))

    def test_loader_state_error_is_value_error_for_backward_compat(self):
        self.assertTrue(issubclass(OdmlibLoaderStateError, ValueError))

    # --- OdmlibNamespaceError ---

    def test_namespace_error_is_odmlib_error(self):
        self.assertTrue(issubclass(OdmlibNamespaceError, OdmlibError))

    def test_namespace_error_is_value_error_for_backward_compat(self):
        self.assertTrue(issubclass(OdmlibNamespaceError, ValueError))

    # --- Warnings ---

    def test_odmlib_warning_is_user_warning(self):
        self.assertTrue(issubclass(OdmlibWarning, UserWarning))

    def test_deprecation_warning_is_odmlib_warning(self):
        self.assertTrue(issubclass(OdmlibDeprecationWarning, OdmlibWarning))

    def test_deprecation_warning_is_deprecation_warning(self):
        self.assertTrue(issubclass(OdmlibDeprecationWarning, DeprecationWarning))

    def test_interop_warning_is_odmlib_warning(self):
        self.assertTrue(issubclass(OdmlibInteroperabilityWarning, OdmlibWarning))


class TestExceptionFormatting(TestCase):
    """Verify exception message formatting."""

    def test_validation_error_message_only(self):
        err = OdmlibValidationError("ItemRef missing required attribute 'ItemOID'")
        self.assertIn("ItemRef missing required attribute", str(err))

    def test_validation_error_with_context(self):
        err = OdmlibValidationError(
            "ItemRef missing required attribute 'ItemOID'",
            element_path="ODM > Study > MetaDataVersion > ItemGroupDef(OID='IG.VS') > ItemRef[3]",
            hint="Every ItemRef must include an ItemOID",
        )
        msg = str(err)
        self.assertIn("ItemRef missing required", msg)
        self.assertIn("Context:", msg)
        self.assertIn("IG.VS", msg)
        self.assertIn("Hint:", msg)
        self.assertIn("Every ItemRef must include", msg)

    def test_validation_error_attributes_stored(self):
        err = OdmlibValidationError(
            "bad value",
            element_path="ODM > Study",
            hint="fix it",
            attribute="OID",
            element_type="Study",
        )
        self.assertEqual(err.element_path, "ODM > Study")
        self.assertEqual(err.hint, "fix it")
        self.assertEqual(err.attribute, "OID")
        self.assertEqual(err.element_type, "Study")

    def test_type_error_with_context(self):
        err = OdmlibTypeError(
            "Expected type str for OID",
            attribute="OID",
            expected_type="str",
            actual_value=42,
            hint="Provide a string value",
        )
        msg = str(err)
        self.assertIn("Expected type str", msg)
        self.assertIn("Hint:", msg)
        self.assertEqual(err.attribute, "OID")
        self.assertEqual(err.expected_type, "str")
        self.assertEqual(err.actual_value, 42)

    def test_conformance_error_stores_cerberus_errors(self):
        cerberus_errors = {"OID": ["required field"], "Name": ["required field"]}
        err = OdmlibConformanceError(
            "Conformance failed for ItemDef",
            cerberus_errors=cerberus_errors,
            element_type="ItemDef",
        )
        self.assertEqual(err.cerberus_errors, cerberus_errors)
        self.assertIn("OID", err.cerberus_errors)

    def test_oid_error_attributes(self):
        err = OdmlibOIDError(
            "OID IT.AGE is not unique",
            attribute="OID",
            hint="Each OID must be unique",
        )
        self.assertEqual(err.attribute, "OID")
        self.assertIn("IT.AGE", str(err))


class TestBackwardCompatibility(TestCase):
    """Verify existing except ValueError / except TypeError patterns still work."""

    def test_odmlib_validation_error_caught_as_value_error(self):
        with self.assertRaises(ValueError):
            raise OdmlibValidationError("test")

    def test_odmlib_required_attribute_error_caught_as_value_error(self):
        with self.assertRaises(ValueError):
            raise OdmlibRequiredAttributeError("test", attribute="OID")

    def test_odmlib_oid_error_caught_as_value_error(self):
        with self.assertRaises(ValueError):
            raise OdmlibOIDError("duplicate OID")

    def test_odmlib_conformance_error_caught_as_value_error(self):
        with self.assertRaises(ValueError):
            raise OdmlibConformanceError("bad", cerberus_errors={})

    def test_odmlib_type_error_caught_as_type_error(self):
        with self.assertRaises(TypeError):
            raise OdmlibTypeError("wrong type")

    def test_odmlib_loader_state_error_caught_as_value_error(self):
        with self.assertRaises(ValueError):
            raise OdmlibLoaderStateError("loader not ready")

    def test_odmlib_namespace_error_caught_as_value_error(self):
        with self.assertRaises(ValueError):
            raise OdmlibNamespaceError("bad namespace")

    def test_odmlib_oid_error_also_caught_as_odmlib_error(self):
        with self.assertRaises(OdmlibError):
            raise OdmlibOIDError("duplicate OID")


class TestErrorCollector(TestCase):
    """Verify ErrorCollector accumulates errors correctly."""

    def test_empty_collector_has_no_errors(self):
        collector = ErrorCollector()
        self.assertFalse(collector.has_errors)
        self.assertEqual(len(collector.errors), 0)

    def test_add_error_increments_count(self):
        collector = ErrorCollector()
        collector.add_error(OdmlibOIDError("dup OID"))
        self.assertTrue(collector.has_errors)
        self.assertEqual(len(collector.errors), 1)

    def test_add_multiple_errors(self):
        collector = ErrorCollector()
        collector.add_error(OdmlibOIDError("dup OID 1"))
        collector.add_error(OdmlibOIDError("missing ref"))
        collector.add_error(OdmlibValidationError("bad conformance"))
        self.assertEqual(len(collector.errors), 3)

    def test_add_warning(self):
        collector = ErrorCollector()
        collector.add_warning(OdmlibWarning("potential issue"))
        self.assertEqual(len(collector.warnings), 1)
        self.assertFalse(collector.has_errors)

    def test_raise_if_errors_does_not_raise_when_empty(self):
        collector = ErrorCollector()
        collector.raise_if_errors()  # should not raise

    def test_raise_if_errors_raises_single_error_directly(self):
        collector = ErrorCollector()
        original = OdmlibOIDError("single error")
        collector.add_error(original)
        with self.assertRaises(OdmlibOIDError) as ctx:
            collector.raise_if_errors()
        self.assertIs(ctx.exception, original)

    def test_raise_if_errors_raises_summary_for_multiple(self):
        collector = ErrorCollector()
        collector.add_error(OdmlibOIDError("error 1"))
        collector.add_error(OdmlibValidationError("error 2"))
        with self.assertRaises(OdmlibValidationError) as ctx:
            collector.raise_if_errors()
        self.assertIn("2 validation errors", str(ctx.exception))

    def test_errors_are_stored_by_reference(self):
        err = OdmlibOIDError("test", attribute="OID")
        collector = ErrorCollector()
        collector.add_error(err)
        self.assertIs(collector.errors[0], err)


class TestPackageExports(TestCase):
    """Verify all exceptions are importable from odmlib package root."""

    def test_odmlib_error_exported(self):
        self.assertIs(odmlib.OdmlibError, OdmlibError)

    def test_odmlib_validation_error_exported(self):
        self.assertIs(odmlib.OdmlibValidationError, OdmlibValidationError)

    def test_odmlib_type_error_exported(self):
        self.assertIs(odmlib.OdmlibTypeError, OdmlibTypeError)

    def test_odmlib_oid_error_exported(self):
        self.assertIs(odmlib.OdmlibOIDError, OdmlibOIDError)

    def test_odmlib_conformance_error_exported(self):
        self.assertIs(odmlib.OdmlibConformanceError, OdmlibConformanceError)

    def test_odmlib_loader_state_error_exported(self):
        self.assertIs(odmlib.OdmlibLoaderStateError, OdmlibLoaderStateError)

    def test_error_collector_exported(self):
        self.assertIs(odmlib.ErrorCollector, ErrorCollector)

    def test_odmlib_warning_exported(self):
        self.assertIs(odmlib.OdmlibWarning, OdmlibWarning)


class TestExceptionRaisedByModel(TestCase):
    """Integration: verify model construction raises the right odmlib exceptions."""

    def test_missing_required_attribute_raises_odmlib_required_attr_error(self):
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(OdmlibRequiredAttributeError):
            ODM.ItemDef()  # OID and Name required

    def test_missing_required_attribute_still_raises_value_error(self):
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(ValueError):
            ODM.ItemDef()

    def test_unknown_kwarg_raises_odmlib_type_error(self):
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(OdmlibTypeError):
            ODM.ItemDef(OID="IT.TEST", Name="test", NonExistentAttr="x")

    def test_unknown_kwarg_still_raises_type_error(self):
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(TypeError):
            ODM.ItemDef(OID="IT.TEST", Name="test", NonExistentAttr="x")

    def test_wrong_type_raises_odmlib_type_error(self):
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(OdmlibTypeError):
            ODM.ItemDef(OID=123, Name="test")  # OID must be str

    def test_wrong_type_still_raises_type_error(self):
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(TypeError):
            ODM.ItemDef(OID=123, Name="test")

    def test_invalid_enum_raises_odmlib_type_error(self):
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(OdmlibTypeError):
            ODM.ItemDef(OID="IT.TEST", Name="test", DataType="invalid_type")

    def test_invalid_enum_still_raises_type_error(self):
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(TypeError):
            ODM.ItemDef(OID="IT.TEST", Name="test", DataType="invalid_type")

    def test_oid_error_has_hint(self):
        import odmlib.odm_1_3_2.rules.oid_ref as OID_REF
        checker = OID_REF.OIDRef()
        checker.add_oid("IT.AGE", "ItemDef")
        with self.assertRaises(OdmlibOIDError) as ctx:
            checker.add_oid("IT.AGE", "ItemDef")
        self.assertIsNotNone(ctx.exception.hint)
        self.assertIn("IT.AGE", str(ctx.exception))
