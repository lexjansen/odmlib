import unittest
import os
import odmlib.odm_2_0.model as ODM
import datetime
from odmlib import odm_loader as OL, loader as LO
import odmlib.ns_registry as NS
import odmlib.odm_parser as P


class TestOdmV2Model(unittest.TestCase):
    def test_load_example(self):
        self.nsr = NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0", is_default=True, is_reset=True)
        odm_v2_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'odmv2_example.xml')
        loader = LO.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0", ns_uri="http://www.cdisc.org/ns/odm/v2.0", local_model=False, nsr=self.nsr))
        loader.open_odm_document(odm_v2_file)
        study = loader.Study()
        mdv = loader.MetaDataVersion()
        print(f"Study OID is {study.OID}")
        print(f"Study Name is {study.StudyName}")
        print(f"Protocol Name is {study.ProtocolName}")
        print(f"MDV OID is {mdv.OID}")
        self.assertEqual(study.OID, "ODM.COSA.STUDY")  # add assertion here

    def test_load_example_cdash(self):
        self.nsr = NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0", is_default=True, is_reset=True)
        loader = LO.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0", ns_uri="http://www.cdisc.org/ns/odm/v2.0", local_model=False, nsr=self.nsr))
        loader.open_odm_document(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash_demo_v20.xml'))
        study = loader.Study()
        mdv = loader.MetaDataVersion()
        print(f"Study OID is {study.OID}")
        print(f"Study Name is {study.StudyName}")
        print(f"Protocol Name is {study.ProtocolName}")
        print(f"MDV OID is {mdv.OID}")
        self.assertEqual(study.OID, "ODM.CDASH.STUDY")  # add assertion here


if __name__ == '__main__':
    unittest.main()
