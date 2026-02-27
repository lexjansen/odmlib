"""Context managers for common odmlib load-modify-save workflows.

Provides :func:`open_odm` and :func:`open_define` context managers that
automatically load an ODM or Define-XML document on entry and write it
back on clean exit.

Example — read and modify an ODM file::

    from odmlib.context import open_odm

    with open_odm("study.xml") as odm:
        mdv = odm.Study[0].MetaDataVersion[0]
        mdv.ItemGroupDef.append(new_igd)
    # study.xml is automatically overwritten with the modified content

Example — read an ODM file, write to a different path::

    with open_odm("study.xml", output_file="study_updated.xml") as odm:
        odm.FileOID = "F.002"

Example — read a Define-XML 2.1 file::

    from odmlib.context import open_define

    with open_define("define.xml") as define:
        mdv = define.Study[0].MetaDataVersion[0]
        print(len(mdv.ItemDef))
"""
from __future__ import annotations
from typing import Any, Optional


class ODMContext:
    """Context manager for load-modify-save ODM workflows.

    The document is loaded when the ``with`` block is entered and
    written back to ``output_file`` when the block exits normally.
    If an exception propagates out of the ``with`` block the file is
    **not** written (the exception is re-raised unchanged).

    :param input_file: Path to the ODM file to load.
    :param output_file: Path to write on exit.  Defaults to
        ``input_file`` (in-place update).
    :param model_package: odmlib model package name.
        Defaults to ``"odm_1_3_2"``.
    :param format: ``"xml"`` or ``"json"``.  Auto-detected from the
        file extension when not specified.
    """

    def __init__(self, input_file: str,
                 output_file: Optional[str] = None,
                 model_package: str = "odm_1_3_2",
                 format: Optional[str] = None) -> None:
        self.input_file = input_file
        self.output_file = output_file or input_file
        self.model_package = model_package
        self.format = format or self._detect_format(input_file)
        self._odm: Any = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_format(filename: str) -> str:
        if filename.lower().endswith(".json"):
            return "json"
        return "xml"

    def _load(self) -> Any:
        import odmlib.odm_loader as OL
        import odmlib.loader as LD

        if self.format == "json":
            loader = LD.ODMLoader(OL.JSONODMLoader(model_package=self.model_package))
        else:
            loader = LD.ODMLoader(OL.XMLODMLoader(model_package=self.model_package))

        loader.open_odm_document(self.input_file)
        return loader.root()

    def _save(self, odm: Any) -> None:
        if self.format == "json":
            odm.write_json(self.output_file)
        else:
            odm.write_xml(self.output_file)

    # ------------------------------------------------------------------
    # Context protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> Any:
        self._odm = self._load()
        return self._odm

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if exc_type is None and self._odm is not None:
            self._save(self._odm)
        return False  # never suppress exceptions


class DefineContext(ODMContext):
    """Context manager for load-modify-save Define-XML workflows.

    Identical to :class:`ODMContext` but uses Define-XML loaders by
    default.

    :param input_file: Path to the Define-XML file to load.
    :param output_file: Path to write on exit.  Defaults to
        ``input_file``.
    :param model_package: odmlib model package name.
        Defaults to ``"define_2_1"``.
    :param format: ``"xml"`` or ``"json"``.
    """

    def __init__(self, input_file: str,
                 output_file: Optional[str] = None,
                 model_package: str = "define_2_1",
                 format: Optional[str] = None) -> None:
        super().__init__(input_file, output_file, model_package, format)

    def _load(self) -> Any:
        import odmlib.define_loader as DL
        import odmlib.loader as LD

        if self.format == "json":
            loader = LD.ODMLoader(DL.JSONDefineLoader(model_package=self.model_package))
        else:
            loader = LD.ODMLoader(DL.XMLDefineLoader(model_package=self.model_package))

        loader.open_odm_document(self.input_file)
        return loader.root()


# ---------------------------------------------------------------------------
# Convenience factory functions
# ---------------------------------------------------------------------------

def open_odm(input_file: str,
             output_file: Optional[str] = None,
             model_package: str = "odm_1_3_2",
             format: Optional[str] = None) -> ODMContext:
    """Open an ODM document as a context manager.

    :param input_file: Path to the ODM file.
    :param output_file: Write path on exit (defaults to ``input_file``).
    :param model_package: odmlib model package (default ``"odm_1_3_2"``).
    :param format: ``"xml"`` or ``"json"`` (auto-detected if omitted).
    :returns: An :class:`ODMContext` instance.

    Example::

        with open_odm("study.xml") as odm:
            print(odm.FileOID)
    """
    return ODMContext(input_file, output_file, model_package, format)


def open_define(input_file: str,
                output_file: Optional[str] = None,
                model_package: str = "define_2_1",
                format: Optional[str] = None) -> DefineContext:
    """Open a Define-XML document as a context manager.

    :param input_file: Path to the Define-XML file.
    :param output_file: Write path on exit (defaults to ``input_file``).
    :param model_package: odmlib model package (default ``"define_2_1"``).
    :param format: ``"xml"`` or ``"json"`` (auto-detected if omitted).
    :returns: A :class:`DefineContext` instance.

    Example::

        with open_define("define.xml") as define:
            mdv = define.Study[0].MetaDataVersion[0]
    """
    return DefineContext(input_file, output_file, model_package, format)
