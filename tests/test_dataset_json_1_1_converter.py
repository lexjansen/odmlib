"""Tests for odmlib.dataset_json_1_1.converter.

Tests the new Dataset-XML ↔ Dataset-JSON v1.1 converter which produces
one DatasetJSON per ItemGroupOID (matching the v1.1 spec).

Covers:
- dataset_xml_to_dataset_json(): basic conversion, multi-row merge,
  multi-group separation, column union, OID name derivation,
  file attribute propagation, no ClinicalData handling
- dataset_json_to_dataset_xml(): round-trip, structure, item data
- _map_data_type(): known and unknown types
"""
import unittest

import odmlib.dataset_1_0_1.model as DSX
import odmlib.ns_registry as NS

from odmlib.dataset_json_1_1.converter import (
    dataset_xml_to_dataset_json,
    dataset_json_to_dataset_xml,
    _map_data_type,
)
from odmlib.dataset_json_1_1.model import DatasetJSON, Column


class TestDatasetXMLToDatasetJSON(unittest.TestCase):
    """Tests for dataset_xml_to_dataset_json()."""

    def setUp(self):
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(
            prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0"
        )

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
        """Build an ItemGroupData row."""
        igd = DSX.ItemGroupData(ItemGroupOID=oid, ItemGroupDataSeq=seq)
        for ioid, val in item_values.items():
            igd.ItemData.append(DSX.ItemData(ItemOID=ioid, Value=val))
        return igd

    def test_empty_clinical_data(self):
        odm = self._make_odm()
        result = dataset_xml_to_dataset_json(odm)
        self.assertEqual(len(result), 0)

    def test_no_clinical_data(self):
        odm = DSX.ODM(
            FileOID="F.001", FileType="Snapshot",
            CreationDateTime="2024-01-01T00:00:00",
            DatasetXMLVersion="1.0.1",
        )
        result = dataset_xml_to_dataset_json(odm)
        self.assertEqual(len(result), 0)

    def test_single_row(self):
        igd = self._make_igd("IG.AE", "1", {
            "IT.STUDYID": "CDISC01",
            "IT.AETERM": "Headache",
        })
        odm = self._make_odm([igd])
        result = dataset_xml_to_dataset_json(odm)
        self.assertEqual(len(result), 1)
        self.assertIn("AE", result)
        ds = result["AE"]
        self.assertIsInstance(ds, DatasetJSON)
        self.assertEqual(ds.name, "AE")
        self.assertEqual(ds.itemGroupOID, "IG.AE")
        self.assertEqual(ds.records, 1)
        self.assertEqual(len(ds.columns), 2)
        self.assertEqual(ds.rows[0], ["CDISC01", "Headache"])

    def test_multiple_rows_same_group(self):
        igd1 = self._make_igd("IG.AE", "1", {
            "IT.STUDYID": "CDISC01", "IT.AETERM": "Headache"
        })
        igd2 = self._make_igd("IG.AE", "2", {
            "IT.STUDYID": "CDISC01", "IT.AETERM": "Nausea"
        })
        odm = self._make_odm([igd1, igd2])
        result = dataset_xml_to_dataset_json(odm)
        self.assertEqual(len(result), 1)
        ds = result["AE"]
        self.assertEqual(ds.records, 2)
        self.assertEqual(ds.rows[0], ["CDISC01", "Headache"])
        self.assertEqual(ds.rows[1], ["CDISC01", "Nausea"])

    def test_multiple_groups(self):
        igd_ae = self._make_igd("IG.AE", "1", {"IT.AETERM": "Headache"})
        igd_dm = self._make_igd("IG.DM", "1", {"IT.USUBJID": "SUBJ001"})
        odm = self._make_odm([igd_ae, igd_dm])
        result = dataset_xml_to_dataset_json(odm)
        self.assertEqual(len(result), 2)
        self.assertIn("AE", result)
        self.assertIn("DM", result)

    def test_column_union_across_rows(self):
        igd1 = self._make_igd("IG.AE", "1", {"IT.A": "a1", "IT.B": "b1"})
        igd2 = self._make_igd("IG.AE", "2", {"IT.A": "a2", "IT.C": "c2"})
        odm = self._make_odm([igd1, igd2])
        result = dataset_xml_to_dataset_json(odm)
        ds = result["AE"]
        col_names = ds.column_names
        self.assertIn("A", col_names)
        self.assertIn("B", col_names)
        self.assertIn("C", col_names)
        # Row 1 missing C → None
        c_idx = col_names.index("C")
        self.assertIsNone(ds.rows[0][c_idx])
        # Row 2 missing B → None
        b_idx = col_names.index("B")
        self.assertIsNone(ds.rows[1][b_idx])

    def test_oid_name_derivation_no_dot(self):
        igd = self._make_igd("IGAE", "1", {"IT.A": "val"})
        odm = self._make_odm([igd])
        result = dataset_xml_to_dataset_json(odm)
        self.assertIn("IGAE", result)

    def test_file_attributes_propagated(self):
        odm = self._make_odm([
            self._make_igd("IG.DM", "1", {"IT.X": "val"})
        ])
        odm.Originator = "ACME"
        result = dataset_xml_to_dataset_json(odm)
        ds = result["DM"]
        self.assertEqual(ds.fileOID, "F.001")
        self.assertEqual(ds.studyOID, "S.001")
        self.assertEqual(ds.metaDataVersionOID, "MDV.001")

    def test_result_is_dataset_json_v11(self):
        igd = self._make_igd("IG.AE", "1", {"IT.A": "val"})
        odm = self._make_odm([igd])
        result = dataset_xml_to_dataset_json(odm)
        ds = result["AE"]
        self.assertEqual(ds.datasetJSONVersion, "1.1.0")
        self.assertIsInstance(ds.columns[0], Column)

    def test_column_data_type_fallback(self):
        """Without Define-XML, columns default to string type."""
        igd = self._make_igd("IG.AE", "1", {"IT.AETERM": "Headache"})
        odm = self._make_odm([igd])
        result = dataset_xml_to_dataset_json(odm)
        ds = result["AE"]
        self.assertEqual(ds.columns[0].dataType, "string")

    def test_to_json_serializable(self):
        """Converted DatasetJSON should produce valid JSON."""
        import json
        igd = self._make_igd("IG.AE", "1", {"IT.AETERM": "Headache"})
        odm = self._make_odm([igd])
        result = dataset_xml_to_dataset_json(odm)
        ds = result["AE"]
        json_str = ds.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["name"], "AE")


class TestDatasetJSONToDatasetXML(unittest.TestCase):
    """Tests for dataset_json_to_dataset_xml()."""

    def setUp(self):
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(
            prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0"
        )

    def _make_dataset_json(self):
        ds = DatasetJSON(
            datasetJSONCreationDateTime="2024-01-01T00:00:00",
            datasetJSONVersion="1.1.0",
            fileOID="F.001",
            studyOID="S.001",
            metaDataVersionOID="MDV.001",
            itemGroupOID="IG.AE",
            records=2,
            name="AE",
            label="Adverse Events",
            columns=[
                Column(itemOID="IT.STUDYID", name="STUDYID",
                       label="Study ID", dataType="string"),
                Column(itemOID="IT.AETERM", name="AETERM",
                       label="AE Term", dataType="string"),
            ],
            rows=[
                ["CDISC01", "Headache"],
                ["CDISC01", "Nausea"],
            ],
        )
        return ds

    def test_basic_structure(self):
        ds = self._make_dataset_json()
        odm = dataset_json_to_dataset_xml(ds, DSX)
        self.assertEqual(odm.FileOID, "F.001")
        self.assertIsNotNone(odm.ClinicalData)
        self.assertEqual(odm.ClinicalData.StudyOID, "S.001")
        self.assertEqual(odm.ClinicalData.MetaDataVersionOID, "MDV.001")

    def test_item_group_data_count(self):
        ds = self._make_dataset_json()
        odm = dataset_json_to_dataset_xml(ds, DSX)
        self.assertEqual(len(odm.ClinicalData.ItemGroupData), 2)

    def test_item_data_values(self):
        ds = self._make_dataset_json()
        odm = dataset_json_to_dataset_xml(ds, DSX)
        igd0 = odm.ClinicalData.ItemGroupData[0]
        self.assertEqual(igd0.ItemGroupOID, "IG.AE")
        item_values = {id.ItemOID: id.Value for id in igd0.ItemData}
        self.assertEqual(item_values["IT.STUDYID"], "CDISC01")
        self.assertEqual(item_values["IT.AETERM"], "Headache")

    def test_none_values_skipped(self):
        """None values in rows should not produce ItemData elements."""
        ds = DatasetJSON(
            datasetJSONCreationDateTime="2024-01-01T00:00:00",
            datasetJSONVersion="1.1.0",
            itemGroupOID="IG.AE",
            records=1,
            name="AE",
            label="AE",
            columns=[
                Column(itemOID="IT.A", name="A", label="A", dataType="string"),
                Column(itemOID="IT.B", name="B", label="B", dataType="string"),
            ],
            rows=[["val1", None]],
        )
        odm = dataset_json_to_dataset_xml(ds, DSX)
        igd = odm.ClinicalData.ItemGroupData[0]
        # Only IT.A should be present (IT.B is None)
        self.assertEqual(len(igd.ItemData), 1)
        self.assertEqual(igd.ItemData[0].ItemOID, "IT.A")

    def test_empty_rows(self):
        ds = DatasetJSON(
            datasetJSONCreationDateTime="2024-01-01T00:00:00",
            datasetJSONVersion="1.1.0",
            itemGroupOID="IG.AE",
            records=0,
            name="AE",
            label="AE",
            columns=[
                Column(itemOID="IT.A", name="A", label="A", dataType="string"),
            ],
        )
        odm = dataset_json_to_dataset_xml(ds, DSX)
        self.assertEqual(len(odm.ClinicalData.ItemGroupData), 0)

    def test_custom_study_oid(self):
        ds = self._make_dataset_json()
        odm = dataset_json_to_dataset_xml(
            ds, DSX, study_oid="CUSTOM.STUDY", mdv_oid="CUSTOM.MDV"
        )
        self.assertEqual(odm.ClinicalData.StudyOID, "CUSTOM.STUDY")
        self.assertEqual(odm.ClinicalData.MetaDataVersionOID, "CUSTOM.MDV")

    def test_seq_numbering(self):
        ds = self._make_dataset_json()
        odm = dataset_json_to_dataset_xml(ds, DSX)
        seqs = [str(igd.ItemGroupDataSeq) for igd in odm.ClinicalData.ItemGroupData]
        self.assertEqual(seqs, ["1", "2"])


class TestMapDataType(unittest.TestCase):
    """Tests for _map_data_type()."""

    def test_known_types(self):
        pairs = [
            ("text", "string"),
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


class TestRoundTrip(unittest.TestCase):
    """Round-trip tests: Dataset-XML → Dataset-JSON → Dataset-XML."""

    def setUp(self):
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(
            prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0"
        )

    def test_roundtrip_values_preserved(self):
        """Dataset-XML → Dataset-JSON → Dataset-XML preserves values."""
        clinical = DSX.ClinicalData(
            StudyOID="S.001", MetaDataVersionOID="MDV.001"
        )
        igd1 = DSX.ItemGroupData(ItemGroupOID="IG.DM", ItemGroupDataSeq="1")
        igd1.ItemData.append(DSX.ItemData(ItemOID="IT.STUDYID", Value="CDISC01"))
        igd1.ItemData.append(DSX.ItemData(ItemOID="IT.AGE", Value="65"))
        clinical.ItemGroupData.append(igd1)

        odm = DSX.ODM(
            FileOID="F.001", FileType="Snapshot",
            CreationDateTime="2024-01-01T00:00:00",
            DatasetXMLVersion="1.0.1",
        )
        odm.ClinicalData = clinical

        # Forward: XML → JSON
        result = dataset_xml_to_dataset_json(odm)
        ds = result["DM"]
        self.assertEqual(ds.records, 1)
        self.assertEqual(ds.rows[0][0], "CDISC01")
        self.assertEqual(ds.rows[0][1], "65")

        # Reverse: JSON → XML
        odm2 = dataset_json_to_dataset_xml(ds, DSX)
        igd = odm2.ClinicalData.ItemGroupData[0]
        values = {id.ItemOID: id.Value for id in igd.ItemData}
        self.assertEqual(values["IT.STUDYID"], "CDISC01")
        self.assertEqual(values["IT.AGE"], "65")


if __name__ == "__main__":
    unittest.main()
