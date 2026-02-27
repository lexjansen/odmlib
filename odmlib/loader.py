from __future__ import annotations
from typing import Any, Optional
import odmlib.document_loader as DL
from odmlib.exceptions import OdmlibTypeError


class ODMLoader:
    """ loads an ODM-XML document into the object model """
    def __init__(self, odm_loader: DL.DocumentLoader) -> None:
        if not isinstance(odm_loader, DL.DocumentLoader):
            raise OdmlibTypeError(
                "odm_loader argument must implement DocumentLoader",
                expected_type="DocumentLoader",
                actual_value=type(odm_loader).__name__,
                hint="Pass an instance of XMLODMLoader, JSONODMLoader, XMLDefineLoader, or JSONDefineLoader",
            )
        self.loader = odm_loader

    def create_odmlib(self, odm_doc: Any, odm_key: Optional[str] = None) -> Any:
        odm_obj = self.loader.load_document(odm_doc, odm_key)
        return odm_obj

    def open_odm_document(self, filename: str) -> Any:
        root = self.loader.create_document(filename)
        return root

    def load_odm_string(self, odm_string: str) -> Any:
        root = self.loader.create_document_from_string(odm_string)
        return root

    def root(self) -> Any:
        odm = self.loader.load_odm()
        return odm

    def MetaDataVersion(self, idx: int = 0) -> Any:
        mdv = self.loader.load_metadataversion(idx)
        return mdv

    def Study(self, idx: int = 0) -> Any:
        study = self.loader.load_study(idx)
        return study

    def __getattr__(self, attr: str) -> Any:
        if hasattr(self.loader, attr):
            load_func = getattr(self.loader, attr, None)
            if callable(load_func):
                return load_func
            else:
                raise AttributeError(f"{attr} is not callable in the loader {self.loader.__class__.__name__}")
        else:
            raise AttributeError(f"The {attr} method does not exist in the loader {self.loader.__class__.__name__}")
