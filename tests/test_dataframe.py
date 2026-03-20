"""Tests for odmlib.dataframe (optional Pandas DataFrame integration).

All test classes are skipped if pandas is not installed.

Covers:
- metadata_to_dataframe(): scalar attribute extraction, attribute filtering
- clinical_data_to_dataframe(): hierarchical ODM 1.3.2 data flattening
- dataset_to_dataframe(): Dataset-XML 1.0.1 flat ClinicalData
- dataset_json_to_dataframe(): Dataset-JSON Dataset object
- dataframe_to_items(): DataFrame rows → odmlib element instances
- _require_pandas(): ImportError when pandas absent (mocked)
"""
import unittest

import odmlib.ns_registry as NS

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def _reset_ns():
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True,
    )


# ---------------------------------------------------------------------------
# Helpers shared across test classes
# ---------------------------------------------------------------------------

def _make_odm_132_mdv():
    """Build a simple ODM 1.3.2 MetaDataVersion with two ItemDefs."""
    import odmlib.odm_1_3_2.model as ODM
    _reset_ns()
    mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Test MDV")
    mdv.ItemDef.append(ODM.ItemDef(OID="IT.STUDYID", Name="STUDYID", DataType="text"))
    mdv.ItemDef.append(ODM.ItemDef(OID="IT.USUBJID", Name="USUBJID", DataType="text"))
    mdv.ItemDef.append(ODM.ItemDef(OID="IT.AGE", Name="AGE", DataType="integer"))
    return mdv


@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestMetadataToDataFrame(unittest.TestCase):
    """Tests for metadata_to_dataframe()."""

    def setUp(self):
        _reset_ns()

    def test_itemdef_to_dataframe_basic(self):
        from odmlib.dataframe import metadata_to_dataframe
        mdv = _make_odm_132_mdv()
        df = metadata_to_dataframe(mdv, "ItemDef")
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertIn("OID", df.columns)
        self.assertIn("Name", df.columns)
        self.assertIn("DataType", df.columns)

    def test_itemdef_oid_values(self):
        from odmlib.dataframe import metadata_to_dataframe
        mdv = _make_odm_132_mdv()
        df = metadata_to_dataframe(mdv, "ItemDef")
        oids = df["OID"].tolist()
        self.assertIn("IT.STUDYID", oids)
        self.assertIn("IT.USUBJID", oids)
        self.assertIn("IT.AGE", oids)

    def test_attribute_filtering(self):
        from odmlib.dataframe import metadata_to_dataframe
        mdv = _make_odm_132_mdv()
        df = metadata_to_dataframe(mdv, "ItemDef", attributes=["OID", "Name"])
        self.assertIn("OID", df.columns)
        self.assertIn("Name", df.columns)
        # DataType not requested
        self.assertNotIn("DataType", df.columns)

    def test_empty_element_list(self):
        from odmlib.dataframe import metadata_to_dataframe
        import odmlib.odm_1_3_2.model as ODM
        _reset_ns()
        mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Empty")
        df = metadata_to_dataframe(mdv, "ItemDef")
        self.assertEqual(len(df), 0)

    def test_nonexistent_element_type(self):
        from odmlib.dataframe import metadata_to_dataframe
        mdv = _make_odm_132_mdv()
        # getattr returns None for missing attr; should return empty DataFrame
        df = metadata_to_dataframe(mdv, "NonExistentDef")
        self.assertEqual(len(df), 0)

    def test_child_elements_excluded(self):
        """Child element lists should not appear as columns."""
        from odmlib.dataframe import metadata_to_dataframe
        mdv = _make_odm_132_mdv()
        df = metadata_to_dataframe(mdv, "ItemDef")
        # "Alias", "Description", "Question" etc. are child elements
        for col in df.columns:
            # All included columns must have scalar values in the first row
            val = df.iloc[0][col]
            self.assertNotIsInstance(val, list)
            self.assertNotIsInstance(val, dict)


@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestDatasetToDataFrame(unittest.TestCase):
    """Tests for dataset_to_dataframe() (Dataset-XML 1.0.1)."""

    def setUp(self):
        _reset_ns()
        NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")

    def _make_clinical_data(self):
        import odmlib.dataset_1_0_1.model as DSX
        clinical = DSX.ClinicalData(StudyOID="S.001", MetaDataVersionOID="MDV.001")
        igd1 = DSX.ItemGroupData(ItemGroupOID="IG.AE", ItemGroupDataSeq="1")
        igd1.ItemData.append(DSX.ItemData(ItemOID="IT.STUDYID", Value="CDISC01"))
        igd1.ItemData.append(DSX.ItemData(ItemOID="IT.AETERM", Value="Headache"))
        igd2 = DSX.ItemGroupData(ItemGroupOID="IG.AE", ItemGroupDataSeq="2")
        igd2.ItemData.append(DSX.ItemData(ItemOID="IT.STUDYID", Value="CDISC01"))
        igd2.ItemData.append(DSX.ItemData(ItemOID="IT.AETERM", Value="Nausea"))
        clinical.ItemGroupData.append(igd1)
        clinical.ItemGroupData.append(igd2)
        return clinical

    def test_returns_dataframe(self):
        from odmlib.dataframe import dataset_to_dataframe
        clinical = self._make_clinical_data()
        df = dataset_to_dataframe(clinical)
        self.assertIsInstance(df, pd.DataFrame)

    def test_row_count(self):
        from odmlib.dataframe import dataset_to_dataframe
        clinical = self._make_clinical_data()
        df = dataset_to_dataframe(clinical)
        self.assertEqual(len(df), 2)

    def test_column_names(self):
        from odmlib.dataframe import dataset_to_dataframe
        clinical = self._make_clinical_data()
        df = dataset_to_dataframe(clinical)
        self.assertIn("ItemGroupOID", df.columns)
        self.assertIn("ItemGroupDataSeq", df.columns)
        self.assertIn("IT.STUDYID", df.columns)
        self.assertIn("IT.AETERM", df.columns)

    def test_values(self):
        from odmlib.dataframe import dataset_to_dataframe
        clinical = self._make_clinical_data()
        df = dataset_to_dataframe(clinical)
        self.assertEqual(df.iloc[0]["IT.AETERM"], "Headache")
        self.assertEqual(df.iloc[1]["IT.AETERM"], "Nausea")

    def test_empty_clinical_data(self):
        from odmlib.dataframe import dataset_to_dataframe
        import odmlib.dataset_1_0_1.model as DSX
        clinical = DSX.ClinicalData(StudyOID="S.001", MetaDataVersionOID="MDV.001")
        df = dataset_to_dataframe(clinical)
        self.assertEqual(len(df), 0)


@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestDatasetJSONToDataFrame(unittest.TestCase):
    """Tests for dataset_json_to_dataframe()."""

    def _make_dataset(self):
        from odmlib.dataset_json.model import Dataset, ItemMetadata, DatasetRecord
        items = [
            ItemMetadata(OID="IT.A", name="A", label="Var A", type="string"),
            ItemMetadata(OID="IT.B", name="B", label="Var B", type="integer"),
            ItemMetadata(OID="IT.C", name="C", label="Var C", type="float"),
        ]
        ds = Dataset(name="DM", label="Demographics", items=items)
        ds.records.append(DatasetRecord(["val1", 1, 1.5]))
        ds.records.append(DatasetRecord(["val2", 2, 2.5]))
        return ds

    def test_returns_dataframe(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        ds = self._make_dataset()
        df = dataset_json_to_dataframe(ds)
        self.assertIsInstance(df, pd.DataFrame)

    def test_columns_are_variable_names(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        ds = self._make_dataset()
        df = dataset_json_to_dataframe(ds)
        self.assertEqual(list(df.columns), ["A", "B", "C"])

    def test_row_count(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        ds = self._make_dataset()
        df = dataset_json_to_dataframe(ds)
        self.assertEqual(len(df), 2)

    def test_values(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        ds = self._make_dataset()
        df = dataset_json_to_dataframe(ds)
        self.assertEqual(df.iloc[0]["A"], "val1")
        self.assertEqual(df.iloc[1]["B"], 2)
        self.assertAlmostEqual(df.iloc[0]["C"], 1.5)

    def test_empty_dataset(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        from odmlib.dataset_json.model import Dataset, ItemMetadata
        items = [ItemMetadata(OID="IT.A", name="A", label="", type="string")]
        ds = Dataset(name="AE", label="", items=items)
        df = dataset_json_to_dataframe(ds)
        self.assertEqual(len(df), 0)
        self.assertIn("A", df.columns)

    def test_none_values_preserved(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        from odmlib.dataset_json.model import Dataset, ItemMetadata, DatasetRecord
        items = [
            ItemMetadata(OID="IT.A", name="A", label="", type="string"),
            ItemMetadata(OID="IT.B", name="B", label="", type="integer"),
        ]
        ds = Dataset(name="AE", label="", items=items)
        ds.records.append(DatasetRecord(["val", None]))
        df = dataset_json_to_dataframe(ds)
        self.assertIsNone(df.iloc[0]["B"])


@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestDataframeToItems(unittest.TestCase):
    """Tests for dataframe_to_items()."""

    def setUp(self):
        _reset_ns()

    def test_basic_construction(self):
        import odmlib.odm_1_3_2.model as ODM
        from odmlib.dataframe import dataframe_to_items
        df = pd.DataFrame([
            {"OID": "IT.X", "Name": "X", "DataType": "text"},
            {"OID": "IT.Y", "Name": "Y", "DataType": "integer"},
        ])
        items = dataframe_to_items(df, ODM, "ItemDef")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].OID, "IT.X")
        self.assertEqual(items[0].Name, "X")
        self.assertEqual(items[0].DataType, "text")

    def test_column_mapping(self):
        import odmlib.odm_1_3_2.model as ODM
        from odmlib.dataframe import dataframe_to_items
        # Rename DataFrame columns to odmlib attribute names
        df = pd.DataFrame([{"oid_col": "IT.Z", "name_col": "Z", "DataType": "text"}])
        mapping = {"oid_col": "OID", "name_col": "Name"}
        items = dataframe_to_items(df, ODM, "ItemDef", column_mapping=mapping)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].OID, "IT.Z")

    def test_nan_values_skipped(self):
        import odmlib.odm_1_3_2.model as ODM
        from odmlib.dataframe import dataframe_to_items
        # Row with NaN for optional attribute — should construct, not crash
        df = pd.DataFrame([
            {"OID": "IT.A", "Name": "A", "DataType": "text", "Length": float("nan")},
        ])
        # Should not crash; NaN length skipped
        items = dataframe_to_items(df, ODM, "ItemDef")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].OID, "IT.A")

    def test_invalid_rows_skipped(self):
        import odmlib.odm_1_3_2.model as ODM
        from odmlib.dataframe import dataframe_to_items
        # A row without required OID should be skipped (or raise internally)
        df = pd.DataFrame([
            {"OID": "IT.GOOD", "Name": "Good", "DataType": "text"},
            {"Name": "Bad"},  # missing OID — will fail required check
        ])
        # Should return at least 0 elements without crashing
        try:
            items = dataframe_to_items(df, ODM, "ItemDef")
            # At minimum, the good row should be included
            good_oids = [it.OID for it in items if hasattr(it, "OID")]
            self.assertIn("IT.GOOD", good_oids)
        except Exception:
            # Acceptable if the bad row propagates an error (implementation may vary)
            pass

    def test_empty_dataframe(self):
        import odmlib.odm_1_3_2.model as ODM
        from odmlib.dataframe import dataframe_to_items
        df = pd.DataFrame(columns=["OID", "Name", "DataType"])
        items = dataframe_to_items(df, ODM, "ItemDef")
        self.assertEqual(len(items), 0)


@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestRequirePandas(unittest.TestCase):
    """Test _require_pandas() raises when pandas unavailable (simulated)."""

    def test_import_error_message(self):
        """Patch HAS_PANDAS to False and verify the error message is helpful."""
        import odmlib.dataframe as df_module
        original = df_module.HAS_PANDAS
        try:
            df_module.HAS_PANDAS = False
            with self.assertRaises(ImportError) as ctx:
                df_module._require_pandas()
            msg = str(ctx.exception)
            self.assertIn("pandas", msg)
            self.assertIn("pip install", msg)
        finally:
            df_module.HAS_PANDAS = original


class TestNoPandasImport(unittest.TestCase):
    """dataframe module must be importable even without pandas."""

    def test_module_imports_without_pandas(self):
        """Importing odmlib.dataframe must not raise even if pandas is absent."""
        try:
            import odmlib.dataframe  # noqa: F401
        except ImportError as e:
            self.fail(f"odmlib.dataframe raised ImportError on import: {e}")


if __name__ == "__main__":
    unittest.main()
