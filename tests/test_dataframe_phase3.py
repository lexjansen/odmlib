"""Tests for Phase 3 Pandas integration additions to odmlib.dataframe.

Tests the new functions added in DSJ Phase 3:
- dataset_json_to_dataframe() with DatasetJSON v1.1 model
- define_metadata_to_dataframes() for Define-XML v2.1 → DataFrames
- dataframe_to_dataset_json() for DataFrame → DatasetJSON v1.1

All test classes are skipped if pandas is not installed.
"""
import json
import os
import tempfile
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


def _setup_define_ns():
    NS.NamespaceRegistry(
        prefix="def", uri="http://www.cdisc.org/ns/def/v2.1",
        is_default=False
    )


def _make_dataset_json_v11():
    """Create a DatasetJSON v1.1 instance for testing."""
    from odmlib.dataset_json_1_1.model import DatasetJSON, Column

    ds = DatasetJSON(
        datasetJSONCreationDateTime="2026-03-20T10:00:00+00:00",
        datasetJSONVersion="1.1.0",
        itemGroupOID="IG.DM",
        records=3,
        name="DM",
        label="Demographics",
        columns=[
            Column(itemOID="IT.STUDYID", name="STUDYID", label="Study ID",
                   dataType="string"),
            Column(itemOID="IT.USUBJID", name="USUBJID", label="Subject ID",
                   dataType="string"),
            Column(itemOID="IT.AGE", name="AGE", label="Age",
                   dataType="integer"),
            Column(itemOID="IT.WEIGHT", name="WEIGHT", label="Weight",
                   dataType="decimal"),
        ],
    )
    ds.rows = [
        ["CDISC01", "001", 65, 75.5],
        ["CDISC01", "002", 72, 80.0],
        ["CDISC01", "003", 58, None],
    ]
    return ds


def _build_programmatic_define():
    """Build a Define-XML v2.1 ODM root for flattener testing.

    Reuses the fixture from test_define_flattener.py.
    """
    import odmlib.define_2_1.model as DEFINE

    leaf1 = DEFINE.leaf(
        ID="LF.DM", href="dm.xpt",
        title=DEFINE.title(_content="dm.xpt")
    )

    std1 = DEFINE.Standard(
        OID="STD.1", Name="SDTMIG", Type="IG",
        Version="3.1.2", Status="Final"
    )
    standards = DEFINE.Standards(Standard=[std1])

    it_studyid = DEFINE.ItemDef(
        OID="IT.STUDYID", Name="STUDYID", DataType="text",
        Length=12, SASFieldName="STUDYID",
        Description=DEFINE.Description(
            TranslatedText=[DEFINE.TranslatedText(
                _content="Study Identifier", lang="en"
            )]
        ),
        Origin=[DEFINE.Origin(Type="Assigned", Source="Sponsor")]
    )
    it_domain = DEFINE.ItemDef(
        OID="IT.DM.DOMAIN", Name="DOMAIN", DataType="text",
        Length=2, SASFieldName="DOMAIN",
        Description=DEFINE.Description(
            TranslatedText=[DEFINE.TranslatedText(
                _content="Domain Abbreviation", lang="en"
            )]
        ),
    )

    ig_dm = DEFINE.ItemGroupDef(
        OID="IG.DM", Name="DM", Repeating="No",
        IsReferenceData="No", SASDatasetName="DM",
        Domain="DM", Purpose="Tabulation",
        Structure="One record per subject",
        ArchiveLocationID="LF.DM", StandardOID="STD.1",
        Description=DEFINE.Description(
            TranslatedText=[DEFINE.TranslatedText(
                _content="Demographics", lang="en"
            )]
        ),
        ItemRef=[
            DEFINE.ItemRef(
                ItemOID="IT.STUDYID", Mandatory="Yes",
                OrderNumber=1, KeySequence=1,
                WhereClauseRef=[]
            ),
            DEFINE.ItemRef(
                ItemOID="IT.DM.DOMAIN", Mandatory="Yes",
                OrderNumber=2,
                WhereClauseRef=[]
            ),
        ],
        Class=DEFINE.Class(Name="SPECIAL PURPOSE"),
        leaf=leaf1,
    )

    cl_domain = DEFINE.CodeList(
        OID="CL.DM.DOMAIN", Name="Domain Abbreviation (DM)",
        DataType="text", SASFormatName="$DOMAIN",
        CodeListItem=[DEFINE.CodeListItem(
            CodedValue="DM", OrderNumber=1,
            Decode=DEFINE.Decode(
                TranslatedText=[DEFINE.TranslatedText(
                    _content="Demographics", lang="en"
                )]
            ),
        )],
    )

    mdv = DEFINE.MetaDataVersion(
        OID="MDV.TEST.001", Name="Test MetaDataVersion",
        DefineVersion="2.1.0",
        Standards=standards,
        ItemGroupDef=[ig_dm],
        ItemDef=[it_studyid, it_domain],
        CodeList=[cl_domain],
        leaf=[leaf1],
    )

    study = DEFINE.Study(
        OID="STDY.TEST.001",
        GlobalVariables=DEFINE.GlobalVariables(
            StudyName=DEFINE.StudyName(_content="Test Study"),
            StudyDescription=DEFINE.StudyDescription(_content="A test study"),
            ProtocolName=DEFINE.ProtocolName(_content="TEST-001"),
        ),
        MetaDataVersion=mdv,
    )

    odm = DEFINE.ODM(
        FileType="Snapshot", FileOID="DEFINE.TEST.001",
        CreationDateTime="2026-03-20T12:00:00",
        ODMVersion="1.3.2",
        Originator="TestOrg",
        Context="Other",
        Study=study,
    )

    return odm


# ---------------------------------------------------------------------------
# DatasetJSON v1.1 → DataFrame
# ---------------------------------------------------------------------------

@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestDatasetJSON11ToDataFrame(unittest.TestCase):
    """Tests for dataset_json_to_dataframe() with the new DatasetJSON model."""

    def test_returns_dataframe(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        ds = _make_dataset_json_v11()
        df = dataset_json_to_dataframe(ds)
        self.assertIsInstance(df, pd.DataFrame)

    def test_column_names_match(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        ds = _make_dataset_json_v11()
        df = dataset_json_to_dataframe(ds)
        self.assertEqual(list(df.columns), ["STUDYID", "USUBJID", "AGE", "WEIGHT"])

    def test_row_count(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        ds = _make_dataset_json_v11()
        df = dataset_json_to_dataframe(ds)
        self.assertEqual(len(df), 3)

    def test_values(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        ds = _make_dataset_json_v11()
        df = dataset_json_to_dataframe(ds)
        self.assertEqual(df.iloc[0]["STUDYID"], "CDISC01")
        self.assertEqual(df.iloc[0]["AGE"], 65)
        self.assertAlmostEqual(df.iloc[1]["WEIGHT"], 80.0)

    def test_none_values(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        ds = _make_dataset_json_v11()
        df = dataset_json_to_dataframe(ds)
        self.assertTrue(pd.isna(df.iloc[2]["WEIGHT"]))

    def test_empty_rows(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        from odmlib.dataset_json_1_1.model import DatasetJSON, Column
        ds = DatasetJSON(
            datasetJSONCreationDateTime="2026-03-20T10:00:00+00:00",
            datasetJSONVersion="1.1.0",
            itemGroupOID="IG.AE",
            records=0,
            name="AE",
            label="Adverse Events",
            columns=[
                Column(itemOID="IT.AETERM", name="AETERM", label="AE Term",
                       dataType="string"),
            ],
        )
        df = dataset_json_to_dataframe(ds)
        self.assertEqual(len(df), 0)
        self.assertIn("AETERM", df.columns)

    def test_metadata_only_no_rows_attr(self):
        """DatasetJSON with rows=None should produce empty DataFrame."""
        from odmlib.dataframe import dataset_json_to_dataframe
        from odmlib.dataset_json_1_1.model import DatasetJSON, Column
        ds = DatasetJSON(
            datasetJSONCreationDateTime="2026-03-20T10:00:00+00:00",
            datasetJSONVersion="1.1.0",
            itemGroupOID="IG.AE",
            records=0,
            name="AE",
            label="Adverse Events",
            columns=[
                Column(itemOID="IT.AETERM", name="AETERM", label="AE Term",
                       dataType="string"),
            ],
        )
        df = dataset_json_to_dataframe(ds)
        self.assertEqual(len(df), 0)


# ---------------------------------------------------------------------------
# Define-XML → DataFrames
# ---------------------------------------------------------------------------

@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestDefineMetadataToDataFrames(unittest.TestCase):
    """Tests for define_metadata_to_dataframes()."""

    @classmethod
    def setUpClass(cls):
        _setup_define_ns()
        cls.odm = _build_programmatic_define()

    def test_returns_dict_of_dataframes(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        self.assertIsInstance(dfs, dict)
        for name, df in dfs.items():
            self.assertIsInstance(df, pd.DataFrame, f"{name} not a DataFrame")

    def test_all_table_names_present(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        from odmlib.dataset_json_1_1.define_flattener import DefineFlattener
        dfs = define_metadata_to_dataframes(self.odm)
        self.assertEqual(set(dfs.keys()), set(DefineFlattener.TABLE_NAMES))

    def test_study_dataframe(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        study_df = dfs["study"]
        self.assertEqual(len(study_df), 1)
        self.assertIn("FileOID", study_df.columns)
        self.assertIn("StudyName", study_df.columns)
        self.assertEqual(study_df.iloc[0]["StudyName"], "Test Study")
        self.assertEqual(study_df.iloc[0]["FileOID"], "DEFINE.TEST.001")

    def test_datasets_dataframe(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        ds_df = dfs["datasets"]
        self.assertEqual(len(ds_df), 1)
        self.assertEqual(ds_df.iloc[0]["OID"], "IG.DM")
        self.assertEqual(ds_df.iloc[0]["Name"], "DM")
        self.assertEqual(ds_df.iloc[0]["Domain"], "DM")

    def test_variables_dataframe(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        var_df = dfs["variables"]
        self.assertEqual(len(var_df), 2)  # 2 ItemRefs in DM
        self.assertIn("DatasetOID", var_df.columns)
        self.assertIn("ItemOID", var_df.columns)
        self.assertIn("Name", var_df.columns)

    def test_variables_values(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        var_df = dfs["variables"]
        studyid_row = var_df[var_df["ItemOID"] == "IT.STUDYID"].iloc[0]
        self.assertEqual(studyid_row["Name"], "STUDYID")
        self.assertEqual(studyid_row["DataType"], "text")
        self.assertEqual(studyid_row["Mandatory"], "Yes")

    def test_standards_dataframe(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        std_df = dfs["standards"]
        self.assertEqual(len(std_df), 1)
        self.assertEqual(std_df.iloc[0]["OID"], "STD.1")
        self.assertEqual(std_df.iloc[0]["Name"], "SDTMIG")

    def test_codelists_dataframe(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        cl_df = dfs["codelists"]
        self.assertEqual(len(cl_df), 1)
        self.assertEqual(cl_df.iloc[0]["OID"], "CL.DM.DOMAIN")

    def test_codelist_terms_dataframe(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        clt_df = dfs["codelist_terms"]
        self.assertEqual(len(clt_df), 1)
        self.assertEqual(clt_df.iloc[0]["CodedValue"], "DM")
        self.assertEqual(clt_df.iloc[0]["DecodedText"], "Demographics")

    def test_empty_tables_produce_empty_dataframes(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        for name in ["value_level", "where_clauses", "methods", "comments"]:
            self.assertEqual(len(dfs[name]), 0, f"{name} should be empty")
            # Even empty, should have columns
            self.assertGreater(len(dfs[name].columns), 0,
                               f"{name} should have column headers")

    def test_documents_dataframe(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        doc_df = dfs["documents"]
        self.assertEqual(len(doc_df), 1)
        self.assertEqual(doc_df.iloc[0]["ID"], "LF.DM")
        self.assertEqual(doc_df.iloc[0]["href"], "dm.xpt")


@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestDefineMetadataToDataFramesSDTM(unittest.TestCase):
    """Tests with the full SDTM Define-XML test fixture."""

    DEFINE_SDTM_PATH = os.path.join(
        os.path.dirname(__file__), "data", "defineV21-SDTM.xml"
    )

    @classmethod
    def setUpClass(cls):
        _setup_define_ns()
        import odmlib.define_loader as DL
        import odmlib.loader as LD
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(cls.DEFINE_SDTM_PATH)
        cls.odm = loader.root()

    def test_returns_all_tables(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        from odmlib.dataset_json_1_1.define_flattener import DefineFlattener
        dfs = define_metadata_to_dataframes(self.odm)
        self.assertEqual(set(dfs.keys()), set(DefineFlattener.TABLE_NAMES))

    def test_datasets_count(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        self.assertEqual(len(dfs["datasets"]), 11)

    def test_variables_count(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        self.assertEqual(len(dfs["variables"]), 155)

    def test_codelists_count(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        self.assertEqual(len(dfs["codelists"]), 40)

    def test_dataframe_filtering(self):
        """DataFrames support standard pandas filtering."""
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        dm_vars = dfs["variables"][dfs["variables"]["DatasetOID"] == "IG.DM"]
        self.assertEqual(len(dm_vars), 16)

    def test_study_values(self):
        from odmlib.dataframe import define_metadata_to_dataframes
        dfs = define_metadata_to_dataframes(self.odm)
        study = dfs["study"]
        self.assertEqual(study.iloc[0]["StudyName"], "CDISC01_1")
        self.assertEqual(study.iloc[0]["ProtocolName"], "CDISC01-1")


# ---------------------------------------------------------------------------
# DataFrame → DatasetJSON v1.1
# ---------------------------------------------------------------------------

@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestDataFrameToDatasetJSON(unittest.TestCase):
    """Tests for dataframe_to_dataset_json()."""

    def test_basic_conversion(self):
        from odmlib.dataframe import dataframe_to_dataset_json
        from odmlib.dataset_json_1_1.model import DatasetJSON
        df = pd.DataFrame({
            "STUDYID": ["CDISC01", "CDISC01"],
            "USUBJID": ["001", "002"],
            "AGE": [65, 72],
        })
        ds = dataframe_to_dataset_json(df, "DM", "Demographics", "IG.DM")
        self.assertIsInstance(ds, DatasetJSON)
        self.assertEqual(ds.name, "DM")
        self.assertEqual(ds.label, "Demographics")
        self.assertEqual(ds.itemGroupOID, "IG.DM")
        self.assertEqual(ds.records, 2)

    def test_column_names(self):
        from odmlib.dataframe import dataframe_to_dataset_json
        df = pd.DataFrame({
            "STUDYID": ["CDISC01"],
            "AGE": [65],
            "WEIGHT": [75.5],
        })
        ds = dataframe_to_dataset_json(df, "DM", "Demographics", "IG.DM")
        self.assertEqual(ds.column_names, ["STUDYID", "AGE", "WEIGHT"])

    def test_data_type_inference_string(self):
        from odmlib.dataframe import dataframe_to_dataset_json
        df = pd.DataFrame({"NAME": ["Alice", "Bob"]})
        ds = dataframe_to_dataset_json(df, "DM", "Demographics", "IG.DM")
        self.assertEqual(ds.columns[0].dataType, "string")

    def test_data_type_inference_integer(self):
        from odmlib.dataframe import dataframe_to_dataset_json
        df = pd.DataFrame({"AGE": [65, 72]})
        ds = dataframe_to_dataset_json(df, "DM", "Demographics", "IG.DM")
        self.assertEqual(ds.columns[0].dataType, "integer")

    def test_data_type_inference_decimal(self):
        from odmlib.dataframe import dataframe_to_dataset_json
        df = pd.DataFrame({"WEIGHT": [75.5, 80.0]})
        ds = dataframe_to_dataset_json(df, "DM", "Demographics", "IG.DM")
        self.assertEqual(ds.columns[0].dataType, "decimal")

    def test_row_values(self):
        from odmlib.dataframe import dataframe_to_dataset_json
        df = pd.DataFrame({
            "STUDYID": ["CDISC01", "CDISC01"],
            "AGE": [65, 72],
        })
        ds = dataframe_to_dataset_json(df, "DM", "Demographics", "IG.DM")
        self.assertEqual(ds.rows[0], ["CDISC01", 65])
        self.assertEqual(ds.rows[1], ["CDISC01", 72])

    def test_nan_converted_to_none(self):
        from odmlib.dataframe import dataframe_to_dataset_json
        import numpy as np
        df = pd.DataFrame({
            "STUDYID": ["CDISC01", "CDISC01"],
            "AGE": [65.0, np.nan],
        })
        ds = dataframe_to_dataset_json(df, "DM", "Demographics", "IG.DM")
        self.assertIsNone(ds.rows[1][1])

    def test_empty_dataframe(self):
        from odmlib.dataframe import dataframe_to_dataset_json
        df = pd.DataFrame({"STUDYID": pd.Series([], dtype=str)})
        ds = dataframe_to_dataset_json(df, "DM", "Demographics", "IG.DM")
        self.assertEqual(ds.records, 0)
        self.assertEqual(len(ds.columns), 1)

    def test_roundtrip_dataframe_to_dataset_json_to_dataframe(self):
        """DataFrame → DatasetJSON → DataFrame roundtrip."""
        from odmlib.dataframe import (
            dataframe_to_dataset_json, dataset_json_to_dataframe
        )
        original = pd.DataFrame({
            "STUDYID": ["CDISC01", "CDISC01"],
            "USUBJID": ["001", "002"],
            "AGE": [65, 72],
        })
        ds = dataframe_to_dataset_json(
            original, "DM", "Demographics", "IG.DM"
        )
        result = dataset_json_to_dataframe(ds)
        self.assertEqual(list(result.columns), list(original.columns))
        self.assertEqual(len(result), len(original))
        self.assertEqual(result.iloc[0]["STUDYID"], "CDISC01")
        self.assertEqual(result.iloc[0]["AGE"], 65)

    def test_roundtrip_json_file(self):
        """DataFrame → DatasetJSON → JSON file → DatasetJSON → DataFrame."""
        from odmlib.dataframe import (
            dataframe_to_dataset_json, dataset_json_to_dataframe
        )
        from odmlib.dataset_json_1_1.model import DatasetJSON

        original = pd.DataFrame({
            "STUDYID": ["CDISC01"],
            "AGE": [65],
        })
        ds = dataframe_to_dataset_json(
            original, "DM", "Demographics", "IG.DM"
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmppath = f.name
        try:
            ds.write_json(tmppath)
            ds2 = DatasetJSON.read_json(tmppath)
            result = dataset_json_to_dataframe(ds2)
            self.assertEqual(result.iloc[0]["STUDYID"], "CDISC01")
            self.assertEqual(result.iloc[0]["AGE"], 65)
        finally:
            os.unlink(tmppath)

    def test_custom_creation_datetime(self):
        from odmlib.dataframe import dataframe_to_dataset_json
        df = pd.DataFrame({"X": [1]})
        ds = dataframe_to_dataset_json(
            df, "DM", "Demographics", "IG.DM",
            creation_datetime="2026-01-01T00:00:00Z"
        )
        self.assertEqual(ds.datasetJSONCreationDateTime,
                         "2026-01-01T00:00:00Z")

    def test_custom_version(self):
        from odmlib.dataframe import dataframe_to_dataset_json
        df = pd.DataFrame({"X": [1]})
        ds = dataframe_to_dataset_json(
            df, "DM", "Demographics", "IG.DM",
            dataset_json_version="1.1.1"
        )
        self.assertEqual(ds.datasetJSONVersion, "1.1.1")

    def test_item_oid_generation(self):
        from odmlib.dataframe import dataframe_to_dataset_json
        df = pd.DataFrame({"STUDYID": ["X"], "AGE": [1]})
        ds = dataframe_to_dataset_json(df, "DM", "Demographics", "IG.DM")
        self.assertEqual(ds.columns[0].itemOID, "IT.DM.STUDYID")
        self.assertEqual(ds.columns[1].itemOID, "IT.DM.AGE")

    def test_to_dict_serializable(self):
        """Result should produce valid JSON via to_dict/to_json."""
        from odmlib.dataframe import dataframe_to_dataset_json
        df = pd.DataFrame({
            "STUDYID": ["CDISC01"],
            "AGE": [65],
            "WEIGHT": [75.5],
        })
        ds = dataframe_to_dataset_json(df, "DM", "Demographics", "IG.DM")
        json_str = ds.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["name"], "DM")
        self.assertEqual(parsed["rows"][0][0], "CDISC01")
        self.assertEqual(parsed["rows"][0][1], 65)


# ---------------------------------------------------------------------------
# Legacy model backward compatibility
# ---------------------------------------------------------------------------

@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestLegacyDatasetJSONBackwardCompat(unittest.TestCase):
    """Verify the old Dataset model still works with dataset_json_to_dataframe."""

    def _make_legacy_dataset(self):
        from odmlib.dataset_json.model import Dataset, ItemMetadata, DatasetRecord
        items = [
            ItemMetadata(OID="IT.A", name="A", label="Var A", type="string"),
            ItemMetadata(OID="IT.B", name="B", label="Var B", type="integer"),
        ]
        ds = Dataset(name="DM", label="Demographics", items=items)
        ds.records.append(DatasetRecord(["val1", 1]))
        ds.records.append(DatasetRecord(["val2", 2]))
        return ds

    def test_legacy_still_works(self):
        from odmlib.dataframe import dataset_json_to_dataframe
        ds = self._make_legacy_dataset()
        df = dataset_json_to_dataframe(ds)
        self.assertEqual(list(df.columns), ["A", "B"])
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["A"], "val1")


if __name__ == "__main__":
    unittest.main()
