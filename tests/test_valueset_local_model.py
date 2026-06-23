"""Regression tests for ValueSet resolution against local (custom) models.

These tests cover two related fixes:

1. **MRO walking** -- a local model class that subclasses a shipped odmlib
   model should resolve to that base model's valueset version, even when the
   local module path matches none of the known substring markers.

2. **Cross-version fallback** -- hybrid local models that extend an ODM 1.3.2
   base but add Define-XML 2.x attributes (e.g. ``DefineVersion``) need to
   resolve those attribute keys via fallback to a Define-XML valueset.

The motivating example is ``library_define_1_0`` in odmlib_examples, which
extends ``odmlib.odm_1_3_2.model`` for shared elements and grafts on the
Define-XML 2.1 ``def:`` namespace and ``DefineVersion`` attribute.
"""
from unittest import TestCase

import odmlib.odm_1_3_2.model as ODM
import odmlib.typed as T
import odmlib.valueset as VS
from odmlib.exceptions import OdmlibTypeError


# ---------------------------------------------------------------------------
# In-test "local model" — a faithful miniature of library_define_1_0.
# Defining these classes at module scope gives them a real __module__ path
# (``tests.test_valueset_local_model``) that exercises the MRO-walking branch
# of get_version_for_module.
# ---------------------------------------------------------------------------

# Class names deliberately mirror the bases: ValueSet looks up entries by
# ``type(instance).__name__``, so the local subclass must keep the same name
# as the shipped class to share its valueset entries (this matches how
# library_define_1_0 declares ``class MetaDataVersion(ODM.MetaDataVersion)``).
class MetaDataVersion(ODM.MetaDataVersion):
    """Hybrid: ODM 1.3.2 base + Define-XML 2.x DefineVersion attribute."""
    OID = ODM.MetaDataVersion.OID
    Name = ODM.MetaDataVersion.Name
    DefineVersion = T.ValueSetString(required=True)


class StudyEventDef(ODM.StudyEventDef):
    """Pure-extension: no new ValueSet attrs, just inherits ODM 1.3.2."""
    OID = ODM.StudyEventDef.OID
    Name = ODM.StudyEventDef.Name
    Repeating = ODM.StudyEventDef.Repeating
    Type = ODM.StudyEventDef.Type


class TestVersionResolutionWalksMRO(TestCase):
    """get_version_for_module should walk the MRO for unknown module paths."""

    def setUp(self):
        VS.ValueSetLoader._cache = None
        VS.ValueSetLoader._version_map = None
        VS.ValueSet._compiled_regex_cache.clear()

    def test_unknown_module_with_known_base_resolves_via_mro(self):
        """A local class subclassing ODM 1.3.2 should resolve to odm_1_3_2."""
        version = VS.ValueSetLoader.get_version_for_module(
            'totally.custom.path.with.no.markers',
            instance_class=StudyEventDef,
        )
        self.assertEqual(version, 'odm_1_3_2')

    def test_unknown_module_without_instance_class_falls_back(self):
        """Without an instance_class hint, unknown paths still default."""
        version = VS.ValueSetLoader.get_version_for_module(
            'totally.custom.path.with.no.markers',
        )
        self.assertEqual(version, 'odm_1_3_2')

    def test_known_module_short_circuits_mro_walk(self):
        """An exact-match module path must not consult the MRO."""
        version = VS.ValueSetLoader.get_version_for_module(
            'odmlib.odm_2_0.model',
            instance_class=StudyEventDef,  # MRO would say odm_1_3_2
        )
        self.assertEqual(version, 'odm_2_0')


class TestCrossVersionFallback(TestCase):
    """value_set should fall back across versions for hybrid local models."""

    def setUp(self):
        VS.ValueSetLoader._cache = None
        VS.ValueSetLoader._version_map = None
        VS.ValueSet._compiled_regex_cache.clear()

    def test_define_version_resolved_for_odm_1_3_2_base(self):
        """MetaDataVersion.DefineVersion lives only in Define-XML valuesets,
        but a hybrid local model with an ODM 1.3.2 base must still resolve it.
        """
        entry = VS.ValueSet.value_set(
            "MetaDataVersion.DefineVersion", version='odm_1_3_2',
        )
        self.assertIsInstance(entry, dict)
        self.assertIn("_regex", entry)

    def test_unknown_attribute_returns_sentinel(self):
        """Cross-version fallback must not mask genuinely unknown attributes.

        Per ODM20 plan §3.10 the contract changed: a genuinely unknown
        attribute now returns the UNKNOWN_ATTRIBUTE sentinel (instead of
        raising), but the fallback must still NOT resolve it to some other
        version's list — the sentinel proves it was not masked.
        """
        result = VS.ValueSet.value_set(
            "BogusClass.BogusAttr", version='odm_1_3_2')
        self.assertIs(result, VS.ValueSet.UNKNOWN_ATTRIBUTE)


class TestHybridLocalModelInstantiation(TestCase):
    """End-to-end: instantiating a hybrid local model must validate cleanly.

    This is the regression case behind the bug report: library_xml.py's
    library_define_1_0 model crashed at construction time because
    MetaDataVersion.DefineVersion failed valueset lookup under odm_1_3_2.
    """

    def setUp(self):
        VS.ValueSetLoader._cache = None
        VS.ValueSetLoader._version_map = None
        VS.ValueSet._compiled_regex_cache.clear()

    def test_valid_define_version_accepted(self):
        mdv = MetaDataVersion(
            OID="MDV.1", Name="Test", DefineVersion="2.1.0",
        )
        self.assertEqual(mdv.DefineVersion, "2.1.0")

    def test_valid_define_version_assignment_after_construction(self):
        mdv = MetaDataVersion(
            OID="MDV.1", Name="Test", DefineVersion="2.1.0",
        )
        mdv.DefineVersion = "2.1.18"
        self.assertEqual(mdv.DefineVersion, "2.1.18")

    def test_invalid_define_version_rejected(self):
        with self.assertRaises(OdmlibTypeError) as ctx:
            MetaDataVersion(
                OID="MDV.1", Name="Test", DefineVersion="3.0",
            )
        self.assertIn("Invalid value", str(ctx.exception))

    def test_inherited_attribute_still_validates(self):
        """Pure-extension local model: inherited Repeating still validates."""
        sed = StudyEventDef(
            OID="SE.1", Name="Visit 1", Repeating="Yes", Type="Scheduled",
        )
        self.assertEqual(sed.Repeating, "Yes")
        with self.assertRaises(OdmlibTypeError):
            StudyEventDef(
                OID="SE.1", Name="Visit 1",
                Repeating="Bogus", Type="Scheduled",
            )
