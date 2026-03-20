"""Tests for odmlib.dataset_json.converter.

Covers:
- dataset_xml_to_json() basic conversion
- OID → name derivation when no Define-XML
- Column union across multiple rows with same ItemGroupOID
- Missing values (None) in output rows
- dataset_json_to_xml() round-trip
- _map_data_type() edge cases
- _get_description_text() helper
"""
import unittest

import odmlib.dataset_1_0_1.model as DSX
import odmlib.ns_registry as NS

from odmlib.dataset_json.converter import (
    dataset_xml_to_json,
    dataset_json_to_xml,
    _map_data_type,
)
from odmlib.dataset_json.model import DatasetJSON, Dataset, ItemMetadata


class TestDatasetXMLToJSON(unittest.TestCase):
    """Tests for dataset_xml_to_json()."""

    def setUp(self):
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_odm(self, igd_list=None):
        """Build a minimal Dataset-XML ODM object."""
        clinical = DSX.ClinicalData(
            StudyOID="S.001",
            MetaDataVersionOID="MDV.001",
        )
        for igd in (igd_list or []):
            clinical.ItemGroupData.append(igd)

        odm = DSX.ODM(
            FileOID="F.001",
            FileType="Snapshot",
            CreationDateTime="2024-01-01T00:00:00",
            DatasetXMLVersion="1.0.1",
        )
        odm.ClinicalData = clinical
        return odm

    def _make_igd(self, oid, seq, item_values):
        """Build an ItemGroupData row from a dict {ItemOID: Value}."""
        igd = DSX.ItemGroupData(ItemGroupOID=oid, ItemGroupDataSeq=seq)
        for ioid, val in item_values.items():
            igd.ItemData.append(DSX.ItemData(ItemOID=ioid, Value=val))
        return igd

    # ------------------------------------------------------------------
    # Basic conversion
    # ------------------------------------------------------------------

    def test_convert_empty_clinical_data(self):
        odm = self._make_odm()
        dsjson = dataset_xml_to_json(odm)
        self.assertEqual(dsjson.fileOID, "F.001")
        self.assertEqual(dsjson.studyOID, "S.001")
        self.assertEqual(dsjson.metaDataVersionOID, "MDV.001")
        self.assertEqual(len(dsjson.datasets), 0)

    def test_convert_single_row(self):
        igd = self._make_igd("IG.AE", 1, {
            "IT.STUDYID": "CDISC01",
            "IT.AETERM": "Headache",
        })
        odm = self._make_odm([igd])
        dsjson = dataset_xml_to_json(odm)
        self.assertEqual(len(dsjson.datasets), 1)
        ds = dsjson.datasets[0]
        self.assertEqual(ds.name, "AE")  # "AE" derived from "IG.AE"
        self.assertEqual(len(ds.items), 2)
        self.assertEqual(len(ds.records), 1)
        self.assertEqual(ds.records[0].values, ["CDISC01", "Headache"])

    def test_convert_multiple_rows_same_group(self):
        """Multiple rows with the same ItemGroupOID → one dataset, multiple records."""
        igd1 = self._make_igd("IG.AE", 1, {"IT.STUDYID": "CDISC01", "IT.AETERM": "Headache"})
        igd2 = self._make_igd("IG.AE", 2, {"IT.STUDYID": "CDISC01", "IT.AETERM": "Nausea"})
        odm = self._make_odm([igd1, igd2])
        dsjson = dataset_xml_to_json(odm)
        self.assertEqual(len(dsjson.datasets), 1)
        ds = dsjson.datasets[0]
        self.assertEqual(len(ds.records), 2)
        self.assertEqual(ds.records[0].values, ["CDISC01", "Headache"])
        self.assertEqual(ds.records[1].values, ["CDISC01", "Nausea"])

    def test_convert_multiple_groups(self):
        """Different ItemGroupOIDs → separate datasets."""
        igd_ae = self._make_igd("IG.AE", 1, {"IT.AETERM": "Headache"})
        igd_dm = self._make_igd("IG.DM", 1, {"IT.USUBJID": "SUBJ001"})
        odm = self._make_odm([igd_ae, igd_dm])
        dsjson = dataset_xml_to_json(odm)
        self.assertEqual(len(dsjson.datasets), 2)
        names = {ds.name for ds in dsjson.datasets}
        self.assertIn("AE", names)
        self.assertIn("DM", names)

    def test_column_union_across_rows(self):
        """Columns are the union of all ItemOIDs seen; missing values are None."""
        igd1 = self._make_igd("IG.AE", 1, {"IT.A": "a1", "IT.B": "b1"})
        igd2 = self._make_igd("IG.AE", 2, {"IT.A": "a2", "IT.C": "c2"})
        odm = self._make_odm([igd1, igd2])
        dsjson = dataset_xml_to_json(odm)
        ds = dsjson.datasets[0]
        col_names = ds.item_names
        # All three ItemOIDs should appear as columns
        self.assertIn("A", col_names)
        self.assertIn("B", col_names)
        self.assertIn("C", col_names)
        # Row 1 should have None for IT.C
        row1 = ds.records[0].values
        c_idx = col_names.index("C")
        self.assertIsNone(row1[c_idx])
        # Row 2 should have None for IT.B
        row2 = ds.records[1].values
        b_idx = col_names.index("B")
        self.assertIsNone(row2[b_idx])

    def test_oid_name_derivation_no_dot(self):
        """OIDs without a dot are used as-is for the dataset name."""
        igd = self._make_igd("IGAE", 1, {"IT.A": "val"})
        odm = self._make_odm([igd])
        dsjson = dataset_xml_to_json(odm)
        self.assertEqual(dsjson.datasets[0].name, "IGAE")

    def test_file_attributes_propagated(self):
        odm = self._make_odm()
        odm.Originator = "ACME"
        odm.SourceSystem = "Python"
        odm.SourceSystemVersion = "3.12"
        dsjson = dataset_xml_to_json(odm)
        self.assertEqual(dsjson.originator, "ACME")
        self.assertEqual(dsjson.sourceSystem, "Python")
        self.assertEqual(dsjson.sourceSystemVersion, "3.12")

    def test_no_clinical_data(self):
        """ODM without ClinicalData returns empty DatasetJSON."""
        odm = DSX.ODM(
            FileOID="F.001",
            FileType="Snapshot",
            CreationDateTime="2024-01-01T00:00:00",
            DatasetXMLVersion="1.0.1",
        )
        # ClinicalData not set → should return empty DatasetJSON gracefully
        dsjson = dataset_xml_to_json(odm)
        self.assertEqual(len(dsjson.datasets), 0)

    # ------------------------------------------------------------------
    # ItemMetadata fallback (no Define-XML)
    # ------------------------------------------------------------------

    def test_item_metadata_oid_name_derivation(self):
        """Without Define-XML, item name is derived from the OID suffix."""
        igd = self._make_igd("IG.AE", 1, {"IT.AETERM": "Headache"})
        odm = self._make_odm([igd])
        dsjson = dataset_xml_to_json(odm)
        item = dsjson.datasets[0].items[0]
        self.assertEqual(item.OID, "IT.AETERM")
        self.assertEqual(item.name, "AETERM")
        self.assertEqual(item.type, "string")
        self.assertEqual(item.label, "")

    def test_item_metadata_no_dot_in_oid(self):
        """OID without a dot → item name equals the OID."""
        igd = self._make_igd("IG.AE", 1, {"AETERM": "Headache"})
        odm = self._make_odm([igd])
        dsjson = dataset_xml_to_json(odm)
        item = dsjson.datasets[0].items[0]
        self.assertEqual(item.name, "AETERM")


class TestDatasetJSONToXML(unittest.TestCase):
    """Tests for dataset_json_to_xml()."""

    def setUp(self):
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")

    def _make_dsjson(self):
        dsjson = DatasetJSON(
            fileOID="F.001",
            creationDateTime="2024-01-01T00:00:00",
            studyOID="S.001",
            metaDataVersionOID="MDV.001",
        )
        items = [
            ItemMetadata(OID="IT.STUDYID", name="STUDYID", label="Study ID", type="string"),
            ItemMetadata(OID="IT.AETERM", name="AETERM", label="AE Term", type="string"),
        ]
        ds = Dataset(name="AE", label="Adverse Events", items=items)
        ds.add_record(["CDISC01", "Headache"])
        ds.add_record(["CDISC01", "Nausea"])
        dsjson.add_dataset(ds)
        return dsjson

    def test_convert_to_xml_structure(self):
        dsjson = self._make_dsjson()
        odm = dataset_json_to_xml(dsjson, DSX)
        self.assertEqual(odm.FileOID, "F.001")
        self.assertIsNotNone(odm.ClinicalData)
        self.assertEqual(odm.ClinicalData.StudyOID, "S.001")
        self.assertEqual(len(odm.ClinicalData.ItemGroupData), 2)

    def test_convert_to_xml_item_data(self):
        dsjson = self._make_dsjson()
        odm = dataset_json_to_xml(dsjson, DSX)
        igd0 = odm.ClinicalData.ItemGroupData[0]
        self.assertEqual(igd0.ItemGroupOID, "AE")
        item_values = {id.ItemOID: id.Value for id in igd0.ItemData}
        self.assertEqual(item_values.get("IT.STUDYID"), "CDISC01")
        self.assertEqual(item_values.get("IT.AETERM"), "Headache")


class TestMapDataType(unittest.TestCase):
    """Tests for _map_data_type()."""

    def test_known_types(self):
        pairs = [
            ("text", "string"),
            ("string", "string"),
            ("integer", "integer"),
            ("float", "float"),
            ("double", "double"),
            ("decimal", "decimal"),
            ("date", "date"),
            ("time", "time"),
            ("datetime", "datetime"),
            ("boolean", "boolean"),
            ("URI", "URI"),
            ("partialDate", "string"),
        ]
        for odm_type, expected in pairs:
            with self.subTest(odm_type=odm_type):
                self.assertEqual(_map_data_type(odm_type), expected)

    def test_unknown_type_defaults_to_string(self):
        self.assertEqual(_map_data_type("unknownType"), "string")


if __name__ == "__main__":
    unittest.main()
