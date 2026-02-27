from __future__ import annotations
from typing import Any, Optional
import odmlib.document_loader as DL
import odmlib.odm_parser as P
import odmlib.ns_registry as NS
import json
import importlib
import xml.etree.ElementTree as ET
from odmlib.exceptions import OdmlibLoaderStateError


class XMLDefineLoader(DL.DocumentLoader):
    def __init__(self, model_package: str = "define_2_0", ns_uri: str = "http://www.cdisc.org/ns/def/v2.0",
                 local_model: bool = False) -> None:
        self.filename: Optional[str] = None
        self.parser: Optional[Any] = None
        if local_model:
            self.DEF = importlib.import_module(f"{model_package}.model")
        else:
            self.DEF = importlib.import_module(f"odmlib.{model_package}.model")
        self.ns_uri = ns_uri
        self.nsr = NS.NamespaceRegistry()

    def load_document(self, elem: ET.Element, *args: Any) -> Any:
        elem_name = elem.tag[elem.tag.find('}') + 1:]
        elem_class = getattr(self.DEF, elem_name)
        if elem.text and not elem.text.isspace():
            attrib = {**elem.attrib, **{"_content": elem.text}}
            odm_obj = elem_class(**attrib)
        else:
            odm_obj = elem_class(**elem.attrib)
        odm_obj_dict = elem_class.__dict__.items()
        for k, v in odm_obj_dict:
            if type(v).__name__ == "ODMObject":
                namespace = self.nsr.get_ns_entry_dict(v.namespace)
                e = elem.find(v.namespace + ":" + k, namespace)
                if e is not None:
                    odm_child_obj = self.load_document(e)
                    setattr(odm_obj, k, odm_child_obj)
            elif type(v).__name__ == "ODMListObject":
                namespace = self.nsr.get_ns_entry_dict(v.namespace)
                for e in elem.findall(v.namespace + ":" + k, namespace):
                    odm_child_obj = self.load_document(e)
                    getattr(odm_obj, k).append(odm_child_obj)
        return odm_obj

    def create_document(self, filename: str, namespace_registry: Optional[Any] = None) -> ET.Element:
        self.filename = filename
        self._set_registry(namespace_registry)
        self.parser = P.ODMParser(self.filename, self.nsr)
        root = self.parser.parse()
        return root

    def create_document_from_string(self, odm_string: str, namespace_registry: Optional[Any] = None) -> ET.Element:
        self._set_registry(namespace_registry)
        self.parser = P.ODMStringParser(odm_string, self.nsr)
        root = self.parser.parse()
        return root

    def _set_registry(self, namespace_registry: Optional[Any]) -> None:
        if namespace_registry:
            self.nsr = namespace_registry
        else:
            NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
            self.nsr = NS.NamespaceRegistry(prefix="def", uri=self.ns_uri)

    def load_odm(self) -> Any:
        root = self.parser.ODM()
        root_odmlib = self.load_document(root)
        return root_odmlib

    def load_metadataversion(self, idx: int = 0) -> Any:
        mdv = self.parser.MetaDataVersion()
        mdv_odmlib = self.load_document(mdv[idx])
        return mdv_odmlib

    def load_study(self, idx: int = 0) -> Any:
        study = self.parser.Study()
        study_odmlib = self.load_document(study[0])
        return study_odmlib


class JSONDefineLoader(DL.DocumentLoader):
    def __init__(self, model_package: str = "define_2_0") -> None:
        self.filename: Optional[str] = None
        self.odm_dict: dict = {}
        self.DEF = importlib.import_module(f"odmlib.{model_package}.model")

    def load_document(self, odm_dict: dict, key: str) -> Any:
        attrib = {k: value for k, value in odm_dict.items() if not isinstance(value, (list, dict))}
        elem_class = getattr(self.DEF, key)
        odm_obj = elem_class(**attrib)
        odm_obj_items = elem_class.__dict__.items()
        for k, v in odm_obj_items:
            if type(v).__name__ == "ODMObject":
                if k in odm_dict:
                    odm_child_obj = self.load_document(odm_dict[k], k)
                    setattr(odm_obj, k, odm_child_obj)
            elif type(v).__name__ == "ODMListObject":
                if k in odm_dict:
                    for val in odm_dict[k]:
                        odm_child_obj = self.load_document(val, k)
                        getattr(odm_obj, k).append(odm_child_obj)
        return odm_obj

    def create_document(self, filename: str) -> dict:
        self.filename = filename
        with open(self.filename) as json_in:
            self.odm_dict = json.load(json_in)
        return self.odm_dict

    def create_document_from_string(self, odm_string: str) -> dict:
        self.odm_dict = json.loads(odm_string)
        return self.odm_dict

    def load_odm(self) -> Any:
        if not self.odm_dict:
            raise OdmlibLoaderStateError(
                "create_document must be used to create the document before executing load_odm",
                hint="Call loader.open_odm_document(filename) or loader.load_odm_string(json_string) first",
            )
        odm_odmlib = self.load_document(self.odm_dict, "ODM")
        return odm_odmlib

    def load_metadataversion(self, idx: int = 0) -> Any:
        if not self.odm_dict:
            raise OdmlibLoaderStateError(
                "create_document must be used to create the document before executing load_metadataversion",
                hint="Call loader.open_odm_document(filename) first",
            )
        if "MetaDataVersion" in self.odm_dict:
            mdv_dict = self.odm_dict["MetaDataVersion"]
        elif "Study" in self.odm_dict and "MetaDataVersion" in self.odm_dict["Study"]:
            mdv_dict = self.odm_dict["Study"]["MetaDataVersion"]
        else:
            raise OdmlibLoaderStateError(
                "MetaDataVersion not found in ODM dictionary",
                hint="Ensure the document contains a MetaDataVersion element",
            )
        mdv_odmlib = self.load_document(mdv_dict, "MetaDataVersion")
        return mdv_odmlib

    def load_study(self, idx: int = 0) -> Any:
        if not self.odm_dict:
            raise OdmlibLoaderStateError(
                "create_document must be used to create the document before executing load_study",
                hint="Call loader.open_odm_document(filename) first",
            )
        elif "Study" in self.odm_dict:
            study_dict = self.odm_dict["Study"]
        else:
            raise OdmlibLoaderStateError(
                "Study not found in ODM dictionary",
                hint="Ensure the document contains a Study element",
            )
        study_odmlib = self.load_document(study_dict, "Study")
        return study_odmlib
