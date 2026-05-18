"""Pinned ODM 2.0 structural model/XSD gaps deferred to v0.2.1.

Each test asserts the *desired*, XSD-aligned post-fix state and is marked
``xfail(strict=True)``. While the gap exists the test xfails (documenting
the known state in CI). When the v0.2.1 structural fix lands the test
xpasses -- and ``strict=True`` turns an unexpected pass into a CI failure,
forcing whoever fixes the gap to remove the marker (and keep this file in
sync with ROADMAP "v0.2.1 -- ODM v2.0 Model/XSD Alignment").

See ``ODM20-MODEL-XSD-DIFFERENCES_PLAN.md`` §3.1-§3.5 and §6. (§3.7,
the ItemDef attribute set, was resolved in v0.2.1 — its test below
remains as a passing regression guard, not an xfail.)
"""
from unittest import TestCase

import pytest

import odmlib.odm_2_0.model as ODM2
import odmlib.ns_registry as NS


def _setup_odm2_namespaces():
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
        is_default=True, is_reset=True,
    )


class TestDeferredODM2StructuralGaps(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    @pytest.mark.xfail(strict=True,
                       reason="v0.2.1 (plan §3.1): ConditionDef lacks the "
                              "XSD-required MethodSignature child")
    def test_conditiondef_has_methodsignature(self):
        self.assertIn("MethodSignature", ODM2.ConditionDef._elems)

    @pytest.mark.xfail(strict=True,
                       reason="v0.2.1 (plan §3.2): FormalExpression is "
                              "text-based; XSD is element-based "
                              "(Code | ExternalCodeLib)")
    def test_formalexpression_is_element_based(self):
        self.assertNotIn("_content", ODM2.FormalExpression._fields)
        self.assertTrue(hasattr(ODM2, "Code"))
        self.assertTrue(hasattr(ODM2, "ExternalCodeLib"))

    @pytest.mark.xfail(strict=True,
                       reason="v0.2.1 (plan §3.3): Protocol.StudyEventRef was "
                              "removed in the ODM 2.0 XSD (StudyEventGroupRef)")
    def test_protocol_matches_xsd(self):
        self.assertNotIn("StudyEventRef", ODM2.Protocol._elems)
        self.assertIn("StudyEventGroupRef", ODM2.Protocol._elems)

    @pytest.mark.xfail(strict=True,
                       reason="v0.2.1 (plan §3.4): MetaDataVersion.StudyTiming "
                              "is not an allowed MDV child (XSD: "
                              "Protocol/StudyTimings)")
    def test_mdv_has_no_studytiming(self):
        self.assertNotIn("StudyTiming", ODM2.MetaDataVersion._elems)

    @pytest.mark.xfail(strict=True,
                       reason="v0.2.1 (plan §3.5): StudyEventGroupDef cannot "
                              "satisfy its required "
                              "(StudyEventGroupRef?, StudyEventRef?) group")
    def test_studyeventgroupdef_has_required_group(self):
        elems = ODM2.StudyEventGroupDef._elems
        self.assertTrue(
            "StudyEventGroupRef" in elems or "StudyEventRef" in elems)

    def test_itemdef_attribute_set_matches_xsd(self):
        # Resolved in v0.2.1 (plan §3.7): the xfail marker was removed when
        # the ItemDef attribute set was aligned with the ODM 2.0 XSD. This
        # now stands as a passing regression guard. See CHANGELOG and
        # UPDATE_ODM20_ITEMDEF.md.
        fields = set(ODM2.ItemDef._fields)
        self.assertNotIn("FractionDigits", fields)
        self.assertNotIn("DatasetVarName", fields)
        self.assertNotIn("SDSVarName", fields)
        self.assertIn("DisplayFormat", fields)
        self.assertIn("VariableSet", fields)
