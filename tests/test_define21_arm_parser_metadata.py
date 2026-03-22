import unittest
import os
from typing import cast

import odmlib.odm_parser as P
import odmlib.ns_registry as NS
import odmlib.arm_loader as OL
import odmlib.loader as LD
from odmlib.arm_1_0.model import ResultDisplay, PDFPageRef, AnalysisResult, AnalysisDataset


class TestDefine21LoaderMetaData(unittest.TestCase):
    def setUp(self) -> None:
        self.odm_file_1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'definev21-adam.xml')
        NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
        NS.NamespaceRegistry(prefix="arm", uri="http://www.cdisc.org/ns/arm/v1.0")
        self.nsr = NS.NamespaceRegistry(prefix="nciodm", uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC")
        self.parser = P.ODMParser(self.odm_file_1, self.nsr)
        self.loader = LD.ODMLoader(OL.XMLArmLoader(model_package="arm_1_0", ns_uri="http://www.cdisc.org/ns/arm/v1.0"))
        self.root = self.loader.create_document(self.odm_file_1)
        self.odm = self.loader.load_odm()
        self.parser.parse()
        self.mdv = self.parser.MetaDataVersion()

    def test_MetaDataVersion(self):
        self.assertTrue(isinstance(self.mdv, list))
        # elementree does not support using the suffix for accessing attributes not in the default ns
        mdv_dict = {"OID": "MDV.CDISC01.ADaMIG.1.1.ADaM.2.1",
                    "Name": "Study CDISC-Sample, Data Definitions",
                    "Description": "Study CDISC-Sample, Data Definitions",
                    "{http://www.cdisc.org/ns/def/v2.1}DefineVersion": "2.1.0"}
        self.assertDictEqual(self.mdv[0].attrib, mdv_dict)
        self.assertEqual(mdv_dict["{http://www.cdisc.org/ns/def/v2.1}DefineVersion"],
                         self.mdv[0].attrib["{http://www.cdisc.org/ns/def/v2.1}DefineVersion"])
        # self.assertEqual(769, len([e.tag for e in self.mdv[0].getchildren()]))

    def test_Standards(self):
        # self.assertTrue(isinstance(self.mdv[0].Standards.Standard, list))
        # elementree does not support using the suffix for accessing attributes not in the default ns
        mdv = self.odm.Study.MetaDataVersion
        self.assertEqual(mdv.Standards.Standard[0].OID, "STD.01")

    def test_AnalysisResultsDisplays(self):
        mdv = self.odm.Study.MetaDataVersion
        self.assertEqual(len(mdv.AnalysisResultDisplays), 2)
        self.assertEqual(mdv.AnalysisResultDisplays.ResultDisplay[0].OID, "RD.Table_14-3.01")

    def test_ResultDisplay(self):
        mdv = self.odm.Study.MetaDataVersion
        rd = cast(ResultDisplay,mdv.AnalysisResultDisplays.ResultDisplay[0])
        self.assertEqual(rd.OID, "RD.Table_14-3.01")
        self.assertEqual(rd.Name,"Table 14-3.01")
        self.assertEqual(rd.Description.TranslatedText[0]._content,"Primary Endpoint Analysis: ADAS-Cog - Summary at Week 24 - LOCF (Efficacy Population)")
        self.assertEqual(rd.DocumentRef[0].leafID,"LF.CSR")
        self.assertEqual(len(rd.DocumentRef),1)
        self.assertEqual(len(rd.AnalysisResult), 2)
        self.assertEqual(rd.AnalysisResult[0].OID, "AR.Table_14-3.01.R.1")

    def test_ResultDisplay_DocumentRef(self):
        mdv = self.odm.Study.MetaDataVersion
        rd = cast(ResultDisplay,mdv.AnalysisResultDisplays.ResultDisplay[0])
        pdfpage = cast(PDFPageRef,rd.DocumentRef[0].PDFPageRef[0])
        self.assertEqual(pdfpage.Title,"Table 14-3.01")
        self.assertEqual(pdfpage.PageRefs,"2")
        self.assertEqual(pdfpage.Type,"PhysicalRef")

    def test_AnalysisResult(self):
        mdv = self.odm.Study.MetaDataVersion
        rd = cast(ResultDisplay,mdv.AnalysisResultDisplays.ResultDisplay[0])
        ar = cast(AnalysisResult,rd.AnalysisResult[0])
        self.assertEqual(ar.OID, "AR.Table_14-3.01.R.1")
        self.assertEqual(ar.ParameterOID, "IT.ADQSADAS.PARAMCD")
        self.assertEqual(ar.AnalysisReason, "SPECIFIED IN SAP")
        self.assertEqual(ar.AnalysisPurpose, "PRIMARY OUTCOME MEASURE")
        self.assertEqual(ar.Description.TranslatedText[0]._content,"Dose response analysis for ADAS-Cog changes from baseline")
        self.assertEqual(len(ar.AnalysisDatasets),1)

    def test_AnalysisResult_Documentation(self):
        mdv = self.odm.Study.MetaDataVersion
        rd = cast(ResultDisplay,mdv.AnalysisResultDisplays.ResultDisplay[0])
        ar = cast(AnalysisResult,rd.AnalysisResult[0])
        self.assertTrue(ar.Documentation.Description.TranslatedText[0]._content.startswith("Linear model analysis of CHG for dose response"))
        self.assertEqual(ar.Documentation.DocumentRef[0].leafID,"LF.CSR")
        self.assertEqual(len(ar.Documentation.DocumentRef[0].PDFPageRef),1)
        self.assertEqual(ar.Documentation.DocumentRef[0].PDFPageRef[0].PageRefs,"4")
        self.assertEqual(ar.Documentation.DocumentRef[0].PDFPageRef[0].Type,"PhysicalRef")
        self.assertEqual(ar.Documentation.DocumentRef[0].PDFPageRef[0].Title,"SAP Section 10.1.1")

    def test_AnalysisResult_ProgrammingCode(self):
        mdv = self.odm.Study.MetaDataVersion
        rd = cast(ResultDisplay,mdv.AnalysisResultDisplays.ResultDisplay[0])
        ar = cast(AnalysisResult,rd.AnalysisResult[0])
        self.assertEqual(ar.ProgrammingCode.Context,"SAS version 9.2")
        self.assertTrue(str(ar.ProgrammingCode.Code._content).startswith("\nproc glm data = ADQSADAS"))

    def test_AnalysisDataset(self):
        mdv = self.odm.Study.MetaDataVersion
        rd = cast(ResultDisplay,mdv.AnalysisResultDisplays.ResultDisplay[0])
        ar = cast(AnalysisResult,rd.AnalysisResult[0])
        self.assertTrue(len(ar.AnalysisDatasets),1)
        ad = cast(AnalysisDataset,ar.AnalysisDatasets.AnalysisDataset[0])
        self.assertEqual(ad.ItemGroupOID, "IG.ADQSADAS")
        self.assertEqual(ad.AnalysisVariable[0].ItemOID, "IT.ADQSADAS.CHG")
        self.assertEqual(ad.WhereClauseRef.WhereClauseOID,"WC.Table_14-3.01.R.1.ADQSADAS")

if __name__ == '__main__':
    unittest.main()
