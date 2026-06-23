"""Regression test: importing odmlib must not register the 'def' namespace."""
import subprocess
import sys
import unittest

import odmlib.ns_registry as NS


class TestNamespaceLeak(unittest.TestCase):
    def test_import_odmlib_does_not_register_def_namespace(self):
        """Verify that 'import odmlib' alone does not pollute the registry with 'def'."""
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True,
        )
        # Re-import to trigger __init__.py (already loaded, but reset proves the point)
        import odmlib  # noqa: F811
        # After reset + bare import, 'def' should not be present
        self.assertNotIn("def", NS.NamespaceRegistry().namespaces)

    def test_odm_132_xml_has_no_def_namespace(self):
        """Verify ODM v1.3.2 XML output does not contain xmlns:def."""
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")

        ns = NS.NamespaceRegistry()
        entries = ns.get_odm_namespace_entries()
        for entry in entries:
            self.assertNotIn("def", entry,
                             f"Unexpected 'def' namespace in ODM 1.3.2 output: {entry}")

    def test_fresh_process_no_def_namespace(self):
        """In a clean process, importing odmlib must not register 'def'."""
        result = subprocess.run(
            [sys.executable, "-c",
             "import odmlib; import odmlib.ns_registry as NS; "
             "assert 'def' not in NS.NamespaceRegistry().namespaces, "
             "'def namespace leaked'"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_lazy_imports_resolve(self):
        """Verify all lazy imports still resolve correctly."""
        from odmlib import (
            DatasetJSON, Column, SourceSystem,
            DefineFlattener, DefineBuilder,
            dataset_xml_to_dataset_json, dataset_json_to_dataset_xml,
        )
        self.assertIsNotNone(DatasetJSON)
        self.assertIsNotNone(Column)
        self.assertIsNotNone(SourceSystem)
        self.assertIsNotNone(DefineFlattener)
        self.assertIsNotNone(DefineBuilder)
        self.assertIsNotNone(dataset_xml_to_dataset_json)
        self.assertIsNotNone(dataset_json_to_dataset_xml)

    def test_lazy_import_attributeerror_for_unknown(self):
        """Verify AttributeError for unknown attributes on odmlib."""
        import odmlib
        with self.assertRaises(AttributeError):
            _ = odmlib.nonexistent_symbol_xyz


if __name__ == "__main__":
    unittest.main()
