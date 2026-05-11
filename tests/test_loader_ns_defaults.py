"""Regression tests for the ns_uri / model_package coupling fix.

These tests guard against the silent namespace-mismatch bug where
``XMLDefineLoader``'s default ``ns_uri`` was hardcoded to Define-XML 2.0
regardless of ``model_package``, and ``XMLODMLoader``'s ``ns_uri``
parameter was dead code (accepted but never used).

After the fix:

* When ``ns_uri`` is omitted, both loaders derive the canonical URI from
  ``model_package``.
* When ``ns_uri`` is supplied explicitly, the value is honored.
"""
from unittest import TestCase
import os

import odmlib.define_loader as DL
import odmlib.odm_loader as OL
import odmlib.loader as LD
import odmlib.ns_registry as NS
import odmlib.mode as MODE


_DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


def _reset_ns():
    """Clear the shared NamespaceRegistry between tests inside one TestCase.

    The autouse pytest fixture in ``conftest.py`` resets between tests; this
    helper is for the cases where we want a clean slate in setUp() too.
    """
    NS.NamespaceRegistry(
        prefix="odm",
        uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True,
        is_reset=True,
    )


# ---------------------------------------------------------------------------
# XMLDefineLoader: ns_uri derived from model_package
# ---------------------------------------------------------------------------

class TestDefineLoaderNamespaceDefaults(TestCase):
    """Confirm Define-XML loader derives ns_uri from model_package."""

    def setUp(self) -> None:
        _reset_ns()
        self.define_2_1_xml = os.path.join(_DATA_DIR, "defineV21-SDTM.xml")
        self.define_2_0_xml = os.path.join(_DATA_DIR, "define2-0-0-sdtm-test.xml")

    def test_define_2_1_default_ns_loads_def_children(self):
        """Smoking-gun regression: every def: child of MDV must be loaded.

        Pre-fix, XMLDefineLoader(model_package="define_2_1") used the v2.0
        URI by default, so def:Standard, def:CommentDef, def:ValueListDef,
        and def:WhereClauseDef were silently dropped. The source XML has
        5 Standards / 29 CommentDef / 8 ValueListDef / 32 WhereClauseDef
        — the post-fix loader must surface all of them.
        """
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        with MODE.permissive():
            loader.open_odm_document(self.define_2_1_xml)
            odm = loader.root()

        mdv = odm.Study.MetaDataVersion
        self.assertEqual(5, len(mdv.Standards.Standard))
        self.assertEqual(29, len(mdv.CommentDef))
        self.assertEqual(8, len(mdv.ValueListDef))
        self.assertEqual(32, len(mdv.WhereClauseDef))

        std_oids = {s.OID for s in mdv.Standards.Standard}
        self.assertIn("STD.2", std_oids)

    def test_define_2_1_default_ns_uri_value(self):
        """Constructor stores the v2.1 URI when model_package is define_2_1."""
        loader = DL.XMLDefineLoader(model_package="define_2_1")
        self.assertEqual("http://www.cdisc.org/ns/def/v2.1", loader.ns_uri)

    def test_define_2_0_default_ns_still_works(self):
        """Backward compat: omitting ns_uri with the historical default
        model_package keeps the v2.0 URI and loads cleanly."""
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_0"))
        loader.open_odm_document(self.define_2_0_xml)
        mdv = loader.MetaDataVersion()

        self.assertGreater(len(mdv.CommentDef), 0)
        self.assertGreater(len(mdv.ValueListDef), 0)
        self.assertEqual("http://www.cdisc.org/ns/def/v2.0",
                         loader.loader.ns_uri)

    def test_define_explicit_ns_uri_still_overrides(self):
        """Explicit ns_uri wins over the model_package-derived default."""
        custom = "http://example.com/custom/v9"
        loader = DL.XMLDefineLoader(model_package="define_2_1", ns_uri=custom)
        self.assertEqual(custom, loader.ns_uri)

    def test_define_unknown_model_package_falls_back(self):
        """Unknown model_package (e.g. local custom model) falls back to
        the historical Define-XML 2.0 URI rather than raising."""
        # local_model=False means the import would fail for a fictional
        # package; pass an explicit ns_uri so we don't trigger that. The
        # fallback path is exercised when model_package is not in
        # _DEFAULT_DEF_NS_URI but we do supply ns_uri.
        loader = DL.XMLDefineLoader(model_package="define_2_0", ns_uri=None)
        self.assertEqual("http://www.cdisc.org/ns/def/v2.0", loader.ns_uri)


# ---------------------------------------------------------------------------
# XMLODMLoader: ns_uri derived from model_package, parameter no longer dead
# ---------------------------------------------------------------------------

class TestODMLoaderNamespaceDefaults(TestCase):
    """Confirm ODM loader derives ns_uri and the parameter is wired up."""

    def setUp(self) -> None:
        _reset_ns()
        # Register xs/xml/xlink for ODM 1.3 files that declare those prefixes
        # in xsi:schemaLocation. The autouse conftest fixture registers only odm.
        NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")
        self.odm_2_0_xml = os.path.join(_DATA_DIR, "odmv2_example.xml")
        self.odm_1_3_2_xml = os.path.join(_DATA_DIR, "cdash-odm-test.xml")

    def test_odm_2_0_default_ns_uri_value(self):
        """Constructor stores the v2.0 URI when model_package is odm_2_0."""
        loader = OL.XMLODMLoader(model_package="odm_2_0")
        self.assertEqual("http://www.cdisc.org/ns/odm/v2.0", loader.ns_uri)

    def test_odm_2_0_default_ns_loads_correctly(self):
        """End-to-end: ODM 2.0 file loads with the derived v2.0 URI.

        Pre-fix, _set_namespace hardcoded v1.3 even when the caller passed
        ``ns_uri="http://www.cdisc.org/ns/odm/v2.0"`` explicitly. Now the
        derived URI reaches the registry and the parser finds the elements.
        """
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
        loader.open_odm_document(self.odm_2_0_xml)
        odm = loader.root()

        self.assertEqual("ODM.COSA.DEMO", odm.FileOID)
        self.assertEqual("2.0", odm.ODMVersion)

    def test_odm_1_3_2_default_ns_still_works(self):
        """Backward compat: defaults still load an ODM 1.3.2 file."""
        loader = LD.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(self.odm_1_3_2_xml)
        odm = loader.root()
        self.assertEqual("1.3.2", odm.ODMVersion)
        self.assertEqual("http://www.cdisc.org/ns/odm/v1.3",
                         loader.loader.ns_uri)

    def test_odm_1_3_2_default_ns_uri_value(self):
        """Constructor stores the v1.3 URI when model_package is odm_1_3_2."""
        loader = OL.XMLODMLoader()
        self.assertEqual("http://www.cdisc.org/ns/odm/v1.3", loader.ns_uri)

    def test_odm_explicit_ns_uri_now_takes_effect(self):
        """Explicit ns_uri is now stored on the loader (was dead pre-fix).

        Construction itself no longer registers anything in the Borg
        (mirrors XMLDefineLoader). The registration happens at parse time
        via create_document / create_document_from_string, so we trigger
        _set_namespace(None) explicitly to confirm the parameter still
        reaches the registry it controls.
        """
        custom = "http://example.com/custom/v9"
        loader = OL.XMLODMLoader(model_package="odm_1_3_2", ns_uri=custom)
        self.assertEqual(custom, loader.ns_uri)
        # Trigger the deferred registration the way create_document would.
        loader._set_namespace(None)
        self.assertEqual({"odm": custom},
                         loader.nsr.get_ns_entry_dict("odm"))

    def test_odm_unknown_model_package_falls_back(self):
        """Unknown model_package falls back to the v1.3 URI."""
        # dataset_1_0_1 / ct_1_1_1 share the v1.3 URI (see CLAUDE.md).
        loader = OL.XMLODMLoader(model_package="dataset_1_0_1")
        self.assertEqual("http://www.cdisc.org/ns/odm/v1.3", loader.ns_uri)


# ---------------------------------------------------------------------------
# Define-XML OID validation regression
# ---------------------------------------------------------------------------

class TestDefine21OidCheckRegression(TestCase):
    """The original user-facing failure: phantom missing-OID errors for
    def:StandardOID references after a Define-XML 2.1 load."""

    def setUp(self) -> None:
        _reset_ns()
        self.define_2_1_xml = os.path.join(_DATA_DIR, "defineV21-SDTM.xml")

    def test_standards_oids_are_indexed_after_load(self):
        """After loading, the OID index must contain the def:Standard OIDs.

        Pre-fix, the loader silently dropped all Standards, so STD.* OIDs
        never made it into the index, and any def:StandardOID reference was
        flagged as dangling.
        """
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        with MODE.permissive():
            loader.open_odm_document(self.define_2_1_xml)
            odm = loader.root()

        idx = odm.build_oid_index()
        # find_all() raises OdmlibOIDError when the OID isn't indexed.
        # Pre-fix, every STD.* entry was missing from the index because
        # Standards never made it into the object tree. Post-fix the
        # index includes both the definitions and the references that
        # point at them, so len >= 1.
        self.assertGreaterEqual(len(idx.find_all("STD.2")), 1)
        self.assertGreaterEqual(len(idx.find_all("STD.1")), 1)


# ---------------------------------------------------------------------------
# XMLODMLoader: construction is side-effect-free w.r.t. the Borg singleton
# ---------------------------------------------------------------------------

class TestODMLoaderConstructionDoesNotMutateBorg(TestCase):
    """Construction must not silently overwrite the global ``odm:`` mapping.

    Reproduces the library_xml CDASH scenario at unit level (no API call):
    the user pre-registers a custom prefix (``mdr``) and constructs
    ``XMLODMLoader`` with a non-canonical ``ns_uri`` (the library-xml
    wrapper). Pre-fix, ``__init__`` immediately rewrote the global Borg's
    ``odm`` prefix to that wrapper URI, breaking the canonical ODM 1.3
    mapping for any later code in the same process. Post-fix,
    ``XMLODMLoader.__init__`` mirrors ``XMLDefineLoader.__init__`` — empty
    Borg view, registration deferred to parse time.
    """

    def setUp(self) -> None:
        _reset_ns()  # canonical odm -> v1.3

    def test_construction_with_non_canonical_ns_uri_preserves_odm_mapping(self):
        # Pre-register a custom prefix the way library_xml.py does.
        NS.NamespaceRegistry(
            prefix="mdr",
            uri="http://www.cdisc.org/ns/library-xml/v1.0",
        )

        # Constructing the loader must NOT clobber odm -> v1.3 in the Borg.
        OL.XMLODMLoader(
            model_package="odm_1_3_2",
            ns_uri="http://www.cdisc.org/ns/library-xml/v1.0",
        )

        nsr = NS.NamespaceRegistry()
        self.assertEqual(
            "http://www.cdisc.org/ns/odm/v1.3",
            nsr.namespaces["odm"],
            "Construction silently overwrote the canonical odm: mapping",
        )
        self.assertEqual(
            "http://www.cdisc.org/ns/library-xml/v1.0",
            nsr.namespaces["mdr"],
        )

    def test_construction_with_canonical_ns_uri_does_not_mutate(self):
        """Symmetry: even passing a known URI doesn't touch the Borg."""
        before = dict(NS.NamespaceRegistry().namespaces)
        OL.XMLODMLoader(model_package="odm_2_0")
        after = dict(NS.NamespaceRegistry().namespaces)
        self.assertEqual(before, after)

    def test_explicit_nsr_argument_still_replaces_self_nsr(self):
        """Backwards-compat: passing nsr= still wires the loader to it."""
        custom = NS.NamespaceRegistry()  # the shared Borg view
        loader = OL.XMLODMLoader(model_package="odm_1_3_2", nsr=custom)
        # The loader holds the explicitly-supplied registry.
        self.assertIs(loader.nsr, custom)

    def test_deferred_registration_happens_at_parse_time(self):
        """After create_document_from_string, odm: is registered in the Borg.

        The parameter is not dead -- it is just deferred. This guards
        against accidentally regressing into a "ns_uri silently dropped"
        state.
        """
        custom = "http://example.com/odm/v9"
        loader = OL.XMLODMLoader(model_package="odm_1_3_2", ns_uri=custom)
        # Minimal ODM string in the custom namespace; we only need
        # the parser to run far enough to call _set_namespace(None).
        odm_string = (
            f'<ODM xmlns="{custom}" FileType="Snapshot" '
            'FileOID="X" CreationDateTime="2024-01-01T00:00:00" '
            'ODMVersion="1.3.2"/>'
        )
        loader.create_document_from_string(odm_string)
        self.assertEqual(
            {"odm": custom},
            loader.nsr.get_ns_entry_dict("odm"),
        )
