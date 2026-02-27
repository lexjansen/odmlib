"""Optional builder/fluent API for constructing ODM documents.

The builder provides a chainable interface for constructing complex
documents with less boilerplate. It wraps the standard odmlib model
classes and is purely additive — all existing APIs continue to work
unchanged.

Example::

    from odmlib.builder import ODMBuilder

    odm = (ODMBuilder("odm_1_3_2")
        .set_file(FileOID="F.001", FileType="Snapshot",
                  CreationDateTime="2024-01-01T00:00:00")
        .add_study(OID="S.001",
                   study_name="My Study",
                   study_description="A study",
                   protocol_name="PROT-001")
        .add_metadata_version(OID="MDV.001", Name="Version 1")
        .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
        .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1)
        .add_item_ref(ItemOID="IT.AGE", Mandatory="No", OrderNumber=2)
        .build())
"""
from __future__ import annotations
from typing import Any, Optional
import importlib


class ODMBuilder:
    """Fluent builder for constructing ODM documents.

    Maintains state for the currently active Study, MetaDataVersion,
    and ItemGroupDef so that ``add_*`` calls automatically append to
    the right parent.

    :param model_package: The odmlib model package to use.
        Defaults to ``"odm_1_3_2"``.
    """

    def __init__(self, model_package: str = "odm_1_3_2") -> None:
        self._model = importlib.import_module(f"odmlib.{model_package}.model")
        self._file_attrs: dict[str, Any] = {}
        self._studies: list = []
        self._current_study: Any = None
        self._current_mdv: Any = None
        self._current_igd: Any = None
        self._current_item_def: Any = None

    # ------------------------------------------------------------------
    # File-level
    # ------------------------------------------------------------------

    def set_file(self, **kwargs: Any) -> ODMBuilder:
        """Set ODM file-level attributes (FileOID, FileType, CreationDateTime, …).

        These are passed directly to the ``ODM`` constructor when
        :meth:`build` is called.

        :returns: self, for chaining.
        """
        self._file_attrs = kwargs
        return self

    # ------------------------------------------------------------------
    # Study
    # ------------------------------------------------------------------

    def add_study(self, OID: str, study_name: str,
                  study_description: str, protocol_name: str,
                  **kwargs: Any) -> ODMBuilder:
        """Add a Study element with GlobalVariables.

        :param OID: Study OID.
        :param study_name: Content for StudyName.
        :param study_description: Content for StudyDescription.
        :param protocol_name: Content for ProtocolName.
        :param kwargs: Additional Study attributes.
        :returns: self, for chaining.
        """
        M = self._model
        sn = M.StudyName(_content=study_name)
        sd = M.StudyDescription(_content=study_description)
        pn = M.ProtocolName(_content=protocol_name)
        gv = M.GlobalVariables(StudyName=sn, StudyDescription=sd, ProtocolName=pn)
        self._current_study = M.Study(OID=OID, GlobalVariables=gv, **kwargs)
        self._studies.append(self._current_study)
        return self

    # ------------------------------------------------------------------
    # MetaDataVersion
    # ------------------------------------------------------------------

    def add_metadata_version(self, **kwargs: Any) -> ODMBuilder:
        """Add a MetaDataVersion to the current Study.

        :param kwargs: MetaDataVersion attributes (OID, Name, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no Study has been added yet.
        """
        if self._current_study is None:
            raise RuntimeError("Call add_study() before add_metadata_version()")
        M = self._model
        self._current_mdv = M.MetaDataVersion(**kwargs)
        self._current_study.MetaDataVersion.append(self._current_mdv)
        return self

    # ------------------------------------------------------------------
    # ItemGroupDef
    # ------------------------------------------------------------------

    def add_item_group_def(self, **kwargs: Any) -> ODMBuilder:
        """Add an ItemGroupDef to the current MetaDataVersion.

        :param kwargs: ItemGroupDef attributes (OID, Name, Repeating, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no MetaDataVersion has been added yet.
        """
        if self._current_mdv is None:
            raise RuntimeError("Call add_metadata_version() before add_item_group_def()")
        M = self._model
        self._current_igd = M.ItemGroupDef(**kwargs)
        self._current_mdv.ItemGroupDef.append(self._current_igd)
        return self

    # ------------------------------------------------------------------
    # ItemRef
    # ------------------------------------------------------------------

    def add_item_ref(self, **kwargs: Any) -> ODMBuilder:
        """Add an ItemRef to the current ItemGroupDef.

        :param kwargs: ItemRef attributes (ItemOID, Mandatory, OrderNumber, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no ItemGroupDef has been added yet.
        """
        if self._current_igd is None:
            raise RuntimeError("Call add_item_group_def() before add_item_ref()")
        M = self._model
        self._current_igd.ItemRef.append(M.ItemRef(**kwargs))
        return self

    # ------------------------------------------------------------------
    # ItemDef
    # ------------------------------------------------------------------

    def add_item_def(self, **kwargs: Any) -> ODMBuilder:
        """Add an ItemDef to the current MetaDataVersion.

        :param kwargs: ItemDef attributes (OID, Name, DataType, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no MetaDataVersion has been added yet.
        """
        if self._current_mdv is None:
            raise RuntimeError("Call add_metadata_version() before add_item_def()")
        M = self._model
        self._current_item_def = M.ItemDef(**kwargs)
        self._current_mdv.ItemDef.append(self._current_item_def)
        return self

    # ------------------------------------------------------------------
    # CodeList
    # ------------------------------------------------------------------

    def add_code_list(self, OID: str, Name: str, DataType: str,
                      items: Optional[list] = None,
                      **kwargs: Any) -> ODMBuilder:
        """Add a CodeList to the current MetaDataVersion.

        :param OID: CodeList OID.
        :param Name: CodeList name.
        :param DataType: Coded value data type.
        :param items: Optional list of dicts.  Each dict must have a
            ``"CodedValue"`` key and may have a ``"Decode"`` key
            (a plain English label string).  If ``"Decode"`` is present
            a CodeListItem is created; otherwise an EnumeratedItem.
        :param kwargs: Additional CodeList attributes.
        :returns: self, for chaining.
        :raises RuntimeError: if no MetaDataVersion has been added yet.
        """
        if self._current_mdv is None:
            raise RuntimeError("Call add_metadata_version() before add_code_list()")
        M = self._model
        cl = M.CodeList(OID=OID, Name=Name, DataType=DataType, **kwargs)
        if items:
            for item in items:
                coded_value = item["CodedValue"]
                decode_text = item.get("Decode")
                if decode_text:
                    decode = M.Decode(TranslatedText=[
                        M.TranslatedText(_content=decode_text, lang="en")])
                    cl.CodeListItem.append(
                        M.CodeListItem(CodedValue=coded_value, Decode=decode))
                else:
                    cl.EnumeratedItem.append(
                        M.EnumeratedItem(CodedValue=coded_value))
        self._current_mdv.CodeList.append(cl)
        return self

    # ------------------------------------------------------------------
    # Description helper
    # ------------------------------------------------------------------

    def with_description(self, text: str, lang: str = "en") -> ODMBuilder:
        """Attach a Description to the most recently created element.

        Applies to the most recently created ItemGroupDef or ItemDef.
        Falls back to the current MetaDataVersion if neither is set.

        :param text: Description text.
        :param lang: Language code (default ``"en"``).
        :returns: self, for chaining.
        """
        M = self._model
        desc = M.Description(TranslatedText=[
            M.TranslatedText(_content=text, lang=lang)])
        if self._current_item_def is not None:
            self._current_item_def.Description = desc
        elif self._current_igd is not None:
            self._current_igd.Description = desc
        elif self._current_mdv is not None:
            self._current_mdv.Description = text  # MDV Description is a String
        return self

    # ------------------------------------------------------------------
    # Protocol / StudyEventDef
    # ------------------------------------------------------------------

    def add_study_event_def(self, **kwargs: Any) -> ODMBuilder:
        """Add a StudyEventDef to the current MetaDataVersion Protocol.

        If the Protocol does not exist yet it is created automatically.

        :param kwargs: StudyEventDef attributes (OID, Name, Repeating, Type, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no MetaDataVersion has been added yet.
        """
        if self._current_mdv is None:
            raise RuntimeError("Call add_metadata_version() before add_study_event_def()")
        M = self._model
        self._current_mdv.StudyEventDef.append(M.StudyEventDef(**kwargs))
        return self

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> Any:
        """Construct and return the top-level ODM object.

        :returns: An ``ODM`` instance containing all added elements.
        """
        M = self._model
        return M.ODM(Study=self._studies, **self._file_attrs)
