"""Tests for the Dataset-JSON v1.1 model (odmlib.dataset_json.model).

Covers:
- Object creation (minimal and full)
- add_record() validation
- to_dict() / to_json() / from_dict() / from_json() round-trips
- write_json() / read_json() file round-trip
- get_dataset() helper
- repr / len
- Optional field omission in serialized output
"""
import json
import os
import tempfile
import unittest

from odmlib.dataset_json.model import DatasetJSON, Dataset, ItemMetadata, DatasetRecord


class TestItemMetadata(unittest.TestCase):
    """Unit tests for ItemMetadata."""

    def _make_item(self, **kwargs) -> ItemMetadata:
        defaults = dict(OID="IT.STUDYID", name="STUDYID", label="Study ID", type="string")
        defaults.update(kwargs)
        return ItemMetadata(**defaults)

    def test_create_minimal(self):
        item = self._make_item()
        self.assertEqual(item.OID, "IT.STUDYID")
        self.assertEqual(item.name, "STUDYID")
        self.assertEqual(item.label, "Study ID")
        self.assertEqual(item.type, "string")
        self.assertIsNone(item.length)
        self.assertIsNone(item.displayFormat)
        self.assertIsNone(item.keySequence)

    def test_to_dict_minimal(self):
        d = self._make_item().to_dict()
        self.assertIn("OID", d)
        self.assertIn("name", d)
        self.assertIn("label", d)
        self.assertIn("type", d)
        self.assertNotIn("length", d)
        self.assertNotIn("displayFormat", d)
        self.assertNotIn("keySequence", d)

    def test_to_dict_optional_fields_included(self):
        item = self._make_item(length=10, displayFormat="$20.", keySequence=1)
        d = item.to_dict()
        self.assertEqual(d["length"], 10)
        self.assertEqual(d["displayFormat"], "$20.")
        self.assertEqual(d["keySequence"], 1)

    def test_from_dict_round_trip(self):
        item = self._make_item(length=8, keySequence=2)
        item2 = ItemMetadata.from_dict(item.to_dict())
        self.assertEqual(item2.OID, item.OID)
        self.assertEqual(item2.name, item.name)
        self.assertEqual(item2.length, 8)
        self.assertEqual(item2.keySequence, 2)

    def test_repr(self):
        item = self._make_item()
        r = repr(item)
        self.assertIn("ItemMetadata", r)
        self.assertIn("STUDYID", r)


class TestDatasetRecord(unittest.TestCase):
    """Unit tests for DatasetRecord."""

    def test_create(self):
        rec = DatasetRecord(["val1", 42, None])
        self.assertEqual(rec.values, ["val1", 42, None])

    def test_repr(self):
        rec = DatasetRecord(["a", 1])
        self.assertIn("DatasetRecord", repr(rec))


class TestDataset(unittest.TestCase):
    """Unit tests for Dataset."""

    def _make_dataset(self) -> Dataset:
        items = [
            ItemMetadata(OID="IT.STUDYID", name="STUDYID", label="Study ID", type="string"),
            ItemMetadata(OID="IT.USUBJID", name="USUBJID", label="Subject ID", type="string"),
        ]
        return Dataset(name="DM", label="Demographics", items=items)

    def test_create(self):
        ds = self._make_dataset()
        self.assertEqual(ds.name, "DM")
        self.assertEqual(ds.label, "Demographics")
        self.assertEqual(len(ds.items), 2)
        self.assertEqual(len(ds.records), 0)

    def test_item_names(self):
        ds = self._make_dataset()
        self.assertEqual(ds.item_names, ["STUDYID", "USUBJID"])

    def test_add_record_valid(self):
        ds = self._make_dataset()
        ds.add_record(["STUDY1", "SUBJ001"])
        self.assertEqual(len(ds.records), 1)
        self.assertEqual(ds.records[0].values, ["STUDY1", "SUBJ001"])

    def test_add_record_too_many_values(self):
        ds = self._make_dataset()
        with self.assertRaises(ValueError):
            ds.add_record(["STUDY1", "SUBJ001", "extra"])

    def test_add_record_too_few_values(self):
        ds = self._make_dataset()
        with self.assertRaises(ValueError):
            ds.add_record(["STUDY1"])

    def test_add_multiple_records(self):
        ds = self._make_dataset()
        ds.add_record(["STUDY1", "SUBJ001"])
        ds.add_record(["STUDY1", "SUBJ002"])
        self.assertEqual(len(ds), 2)

    def test_to_dict_structure(self):
        ds = self._make_dataset()
        ds.add_record(["STUDY1", "SUBJ001"])
        ds.add_record(["STUDY1", "SUBJ002"])
        d = ds.to_dict()
        self.assertEqual(d["records"], 2)
        self.assertEqual(d["name"], "DM")
        self.assertEqual(d["label"], "Demographics")
        self.assertIsInstance(d["items"], list)
        self.assertEqual(len(d["items"]), 2)
        self.assertIsInstance(d["itemGroupDataSeq"], list)
        self.assertEqual(len(d["itemGroupDataSeq"]), 2)
        self.assertEqual(d["itemGroupDataSeq"][0], ["STUDY1", "SUBJ001"])

    def test_from_dict_round_trip(self):
        ds = self._make_dataset()
        ds.add_record(["STUDY1", "SUBJ001"])
        ds2 = Dataset.from_dict(ds.to_dict())
        self.assertEqual(ds2.name, ds.name)
        self.assertEqual(ds2.label, ds.label)
        self.assertEqual(len(ds2.items), len(ds.items))
        self.assertEqual(len(ds2.records), len(ds.records))
        self.assertEqual(ds2.records[0].values, ["STUDY1", "SUBJ001"])

    def test_from_dict_empty_records(self):
        d = {"name": "AE", "label": "AEs", "items": [], "itemGroupDataSeq": []}
        ds = Dataset.from_dict(d)
        self.assertEqual(len(ds), 0)
        self.assertEqual(ds.item_names, [])

    def test_repr(self):
        ds = self._make_dataset()
        r = repr(ds)
        self.assertIn("Dataset", r)
        self.assertIn("DM", r)

    def test_len(self):
        ds = self._make_dataset()
        self.assertEqual(len(ds), 0)
        ds.add_record(["A", "B"])
        self.assertEqual(len(ds), 1)

    def test_records_is_count_not_name(self):
        """records field in to_dict() must be the integer row count, not the dataset name."""
        ds = self._make_dataset()
        ds.add_record(["X", "Y"])
        d = ds.to_dict()
        self.assertIsInstance(d["records"], int)
        self.assertEqual(d["records"], 1)


class TestDatasetJSON(unittest.TestCase):
    """Unit tests for DatasetJSON."""

    def _make_document(self) -> DatasetJSON:
        return DatasetJSON(
            fileOID="F.001",
            creationDateTime="2024-01-01T00:00:00",
            studyOID="S.001",
            metaDataVersionOID="MDV.001",
        )

    def _make_ae_dataset(self) -> Dataset:
        items = [
            ItemMetadata(OID="IT.STUDYID", name="STUDYID", label="Study ID", type="string"),
            ItemMetadata(OID="IT.AETERM", name="AETERM", label="AE Term", type="string"),
            ItemMetadata(OID="IT.AESEQ", name="AESEQ", label="Sequence", type="integer"),
        ]
        ds = Dataset(name="AE", label="Adverse Events", items=items)
        ds.add_record(["STUDY1", "Headache", 1])
        ds.add_record(["STUDY1", "Nausea", 2])
        return ds

    def test_create_minimal(self):
        doc = self._make_document()
        self.assertEqual(doc.fileOID, "F.001")
        self.assertEqual(doc.datasetJSONVersion, "1.1.0")
        self.assertEqual(doc.datasets, [])
        self.assertIsNone(doc.asOfDateTime)
        self.assertIsNone(doc.originator)

    def test_create_full(self):
        doc = DatasetJSON(
            datasetJSONVersion="1.1.0",
            fileOID="F.002",
            creationDateTime="2024-01-15T12:00:00",
            studyOID="S.002",
            metaDataVersionOID="MDV.002",
            asOfDateTime="2024-01-14T00:00:00",
            originator="ACME Corp",
            sourceSystem="SAS",
            sourceSystemVersion="9.4",
            metaDataRef="define.xml",
        )
        self.assertEqual(doc.originator, "ACME Corp")
        self.assertEqual(doc.sourceSystem, "SAS")
        self.assertEqual(doc.metaDataRef, "define.xml")

    def test_add_dataset(self):
        doc = self._make_document()
        doc.add_dataset(self._make_ae_dataset())
        self.assertEqual(len(doc.datasets), 1)

    def test_get_dataset_found(self):
        doc = self._make_document()
        doc.add_dataset(self._make_ae_dataset())
        ae = doc.get_dataset("AE")
        self.assertIsNotNone(ae)
        self.assertEqual(ae.name, "AE")

    def test_get_dataset_not_found(self):
        doc = self._make_document()
        result = doc.get_dataset("DM")
        self.assertIsNone(result)

    def test_to_dict_structure(self):
        doc = self._make_document()
        doc.add_dataset(self._make_ae_dataset())
        d = doc.to_dict()
        self.assertEqual(d["datasetJSONVersion"], "1.1.0")
        self.assertEqual(d["fileOID"], "F.001")
        self.assertEqual(d["creationDateTime"], "2024-01-01T00:00:00")
        self.assertIn("clinicalData", d)
        cd = d["clinicalData"]
        self.assertEqual(cd["studyOID"], "S.001")
        self.assertEqual(cd["metaDataVersionOID"], "MDV.001")
        self.assertIn("itemGroupData", cd)
        self.assertIn("AE", cd["itemGroupData"])

    def test_to_dict_optional_fields_excluded_when_none(self):
        doc = self._make_document()
        d = doc.to_dict()
        self.assertNotIn("asOfDateTime", d)
        self.assertNotIn("originator", d)
        self.assertNotIn("sourceSystem", d)
        self.assertNotIn("sourceSystemVersion", d)

    def test_to_dict_optional_fields_included_when_set(self):
        doc = DatasetJSON(
            fileOID="F.001",
            creationDateTime="2024-01-01T00:00:00",
            studyOID="S.001",
            metaDataVersionOID="MDV.001",
            asOfDateTime="2024-01-01T00:00:00",
            originator="ACME",
            sourceSystem="Python",
            sourceSystemVersion="3.12",
            metaDataRef="define.xml",
        )
        d = doc.to_dict()
        self.assertIn("asOfDateTime", d)
        self.assertIn("originator", d)
        self.assertIn("sourceSystem", d)
        self.assertIn("sourceSystemVersion", d)
        self.assertIn("metaDataRef", d["clinicalData"])

    def test_to_json_valid_json(self):
        doc = self._make_document()
        doc.add_dataset(self._make_ae_dataset())
        json_str = doc.to_json()
        data = json.loads(json_str)
        self.assertEqual(data["datasetJSONVersion"], "1.1.0")
        self.assertIn("clinicalData", data)

    def test_from_dict_round_trip(self):
        doc = self._make_document()
        doc.add_dataset(self._make_ae_dataset())
        doc2 = DatasetJSON.from_dict(doc.to_dict())
        self.assertEqual(doc2.fileOID, "F.001")
        self.assertEqual(doc2.studyOID, "S.001")
        self.assertEqual(len(doc2.datasets), 1)
        self.assertEqual(doc2.datasets[0].name, "AE")
        self.assertEqual(len(doc2.datasets[0].records), 2)
        self.assertEqual(doc2.datasets[0].records[0].values, ["STUDY1", "Headache", 1])

    def test_from_json_round_trip(self):
        doc = self._make_document()
        doc.add_dataset(self._make_ae_dataset())
        json_str = doc.to_json()
        doc2 = DatasetJSON.from_json(json_str)
        self.assertEqual(doc2.fileOID, doc.fileOID)
        self.assertEqual(len(doc2.datasets), 1)

    def test_write_and_read_json_file(self):
        doc = self._make_document()
        doc.add_dataset(self._make_ae_dataset())

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name
        try:
            doc.write_json(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            doc2 = DatasetJSON.read_json(temp_path)
            self.assertEqual(doc2.fileOID, "F.001")
            self.assertEqual(len(doc2.datasets), 1)
            self.assertEqual(doc2.datasets[0].name, "AE")
            self.assertEqual(doc2.datasets[0].records[1].values, ["STUDY1", "Nausea", 2])
        finally:
            os.unlink(temp_path)

    def test_write_json_indent(self):
        doc = self._make_document()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name
        try:
            doc.write_json(temp_path, indent=4)
            with open(temp_path) as f:
                content = f.read()
            self.assertIn("    ", content)  # 4-space indentation
        finally:
            os.unlink(temp_path)

    def test_multiple_datasets(self):
        doc = self._make_document()
        doc.add_dataset(self._make_ae_dataset())
        dm_items = [ItemMetadata(OID="IT.USUBJID", name="USUBJID", label="Subject", type="string")]
        dm = Dataset(name="DM", label="Demographics", items=dm_items)
        dm.add_record(["SUBJ001"])
        doc.add_dataset(dm)
        self.assertEqual(len(doc.datasets), 2)
        d = doc.to_dict()
        self.assertIn("AE", d["clinicalData"]["itemGroupData"])
        self.assertIn("DM", d["clinicalData"]["itemGroupData"])

    def test_repr(self):
        doc = self._make_document()
        r = repr(doc)
        self.assertIn("DatasetJSON", r)
        self.assertIn("F.001", r)

    def test_from_dict_empty_clinical_data(self):
        d = {
            "datasetJSONVersion": "1.1.0",
            "fileOID": "F.001",
            "creationDateTime": "2024-01-01T00:00:00",
            "clinicalData": {
                "studyOID": "S.001",
                "metaDataVersionOID": "MDV.001",
                "itemGroupData": {},
            },
        }
        doc = DatasetJSON.from_dict(d)
        self.assertEqual(len(doc.datasets), 0)

    def test_none_values_in_records(self):
        """Records may contain None for missing values."""
        items = [
            ItemMetadata(OID="IT.A", name="A", label="", type="string"),
            ItemMetadata(OID="IT.B", name="B", label="", type="integer"),
        ]
        ds = Dataset(name="AE", label="", items=items)
        ds.add_record(["val1", None])
        doc = self._make_document()
        doc.add_dataset(ds)
        doc2 = DatasetJSON.from_dict(doc.to_dict())
        self.assertIsNone(doc2.datasets[0].records[0].values[1])


if __name__ == "__main__":
    unittest.main()
