from unittest import TestCase
import odmlib.define_loader as OL
import odmlib.loader as LD
import odmlib.arm_loader as ARM
import odmlib.ns_registry as NS
import os


class TestODMLoader(TestCase):
    def setUp(self) -> None:
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
        NS.NamespaceRegistry(prefix="arm", uri="http://www.cdisc.org/ns/arm/v1.0")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")
        NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
        self.odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'definev21-adam.xml')
        self.loader = LD.ODMLoader(ARM.XMLArmLoader(model_package="arm_1_0", ns_uri="http://www.cdisc.org/ns/arm/v1.0"))
        self.jloader = LD.ODMLoader(OL.JSONDefineLoader())

    def test_unknown_loader(self):
        with self.assertRaises(TypeError):
            loader = LD.ODMLoader(self.test_mdv_find_by_OID())

    def test_open_odm_document(self):
        root = self.loader.open_odm_document(self.odm_file)
        elem_name = root.tag[root.tag.find('}') + 1:]
        self.assertEqual("ODM", elem_name)
        self.assertEqual("www.cdisc.org/CDISC-Sample/ADaM/1/Define-XML_2.1.0", root.attrib["FileOID"])

    def test_load_odm(self):
        root = self.loader.open_odm_document(self.odm_file)
        odm = self.loader.load_odm()
        self.assertEqual("www.cdisc.org/CDISC-Sample/ADaM/1/Define-XML_2.1.0", odm.FileOID)

    def test_load_missing(self):
        root = self.loader.open_odm_document(self.odm_file)
        with self.assertRaises(AttributeError):
            odm = self.loader.load_standard()

    def test_load_study(self):
        root = self.loader.open_odm_document(self.odm_file)
        study = self.loader.load_study()
        self.assertEqual("STDY.www.cdisc.org/CDISC-Sample/ADaM", study.OID)

    def test_meta_data_version(self):
        self.loader.open_odm_document(self.odm_file)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(mdv.Name, "Study CDISC-Sample, Data Definitions")
        self.assertEqual(mdv.AnalysisResultDisplays[0].OID, "RD.Table_14-3.01")

    def test_mdv_find_by_OID(self):
        # loader = LD.ODMLoader(OL.XMLDefineLoader(model_package="define_2_1", ns_uri="http://www.cdisc.org/ns/def/v2.1"))
        self.loader.open_odm_document(self.odm_file)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(mdv.Name, "Study CDISC-Sample, Data Definitions")
        ir = mdv.ItemGroupDef[0].find("ItemRef", "ItemOID", "IT.ADSL.USUBJID")
        self.assertEqual(ir.ItemOID, mdv.ItemGroupDef[0].ItemRef[1].ItemOID)
        it = mdv.find("ItemDef", "OID", "IT.ADAE.AESEV")
        self.assertEqual(it.CodeListRef.CodeListOID, "CL.AESEV")
        cli = mdv.CodeList[27].find("CodeListItem", "CodedValue", "MODERATE")
        self.assertEqual(cli.Decode.TranslatedText[0]._content, "Grade 2")
        ir = mdv.ValueListDef[2].find("ItemRef", "ItemOID", "IT.ADQSADAS.QSSEQ.ACTOT")
        self.assertEqual(ir.WhereClauseRef[0].WhereClauseOID, "WC.ADQSADAS.QSSEQ.ACTOT")

    def test_odm_round_trip(self):
        root = self.loader.open_odm_document(self.odm_file)
        odm = self.loader.create_odmlib(root)
        odm_json = odm.to_json()
        odm_json_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'adam_define21_test.json')
        with open(odm_json_file, "w") as odm_in:
            odm_in.write(odm_json)
        json_loader = LD.ODMLoader(OL.JSONDefineLoader(model_package="define_2_1"))
        odm_dict = json_loader.open_odm_document(odm_json_file)
        rt_odm = json_loader.create_odmlib(odm_dict, "ODM")
        def_xml_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'adam_def_test_roundtrip.xml')
        rt_odm.write_xml(def_xml_file)
        # loader = LD.ODMLoader(OL.XMLDefineLoader(model_package="define_2_0", ns_uri="http://www.cdisc.org/ns/def/v2.0"))
        root2 = self.loader.open_odm_document(def_xml_file)
        odm2 = self.loader.create_odmlib(root2)
        self.assertEqual(odm2.Study.MetaDataVersion.OID, "MDV.CDISC01.ADaMIG.1.1.ADaM.2.1")
        print(f"ItemRefs = {len(odm2.Study.MetaDataVersion.ItemGroupDef[1])}")
        self.assertEqual(len(odm2.Study.MetaDataVersion.ItemGroupDef[1]), 40)