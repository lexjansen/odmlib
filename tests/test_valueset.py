from unittest import TestCase
import odmlib.valueset as VS
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_2_0.model as ODM2


class TestValueSetLoader(TestCase):
    """Test ValueSetLoader functionality"""

    def setUp(self):
        # Clear cache before each test for isolation
        VS.ValueSetLoader._cache = None
        VS.ValueSetLoader._version_map = None
        VS.ValueSet._compiled_regex_cache.clear()

    def test_load_valuesets_caching(self):
        """Test that valuesets are loaded once and cached"""
        # First load
        valuesets1 = VS.ValueSetLoader.load_valuesets()
        self.assertIsNotNone(valuesets1)
        self.assertIn('odm_1_3_2', valuesets1)
        self.assertIn('odm_2_0', valuesets1)

        # Second load should return same cached object
        valuesets2 = VS.ValueSetLoader.load_valuesets()
        self.assertIs(valuesets1, valuesets2, "Should return cached object")

    def test_version_map_built(self):
        """Test that version map is built correctly"""
        VS.ValueSetLoader.load_valuesets()
        self.assertIsNotNone(VS.ValueSetLoader._version_map)
        self.assertEqual(VS.ValueSetLoader._version_map['odmlib.odm_1_3_2.model'], 'odm_1_3_2')
        self.assertEqual(VS.ValueSetLoader._version_map['odmlib.odm_2_0.model'], 'odm_2_0')

    def test_get_version_for_module_exact_match(self):
        """Test version detection with exact module match"""
        version = VS.ValueSetLoader.get_version_for_module('odmlib.odm_1_3_2.model')
        self.assertEqual(version, 'odm_1_3_2')

        version = VS.ValueSetLoader.get_version_for_module('odmlib.odm_2_0.model')
        self.assertEqual(version, 'odm_2_0')

        version = VS.ValueSetLoader.get_version_for_module('odmlib.define_2_1.model')
        self.assertEqual(version, 'define_2_1')

    def test_get_version_for_module_pattern_match(self):
        """Test version detection with pattern matching"""
        # Custom local models using pattern matching
        version = VS.ValueSetLoader.get_version_for_module('custom.odm_2_0.extended_model')
        self.assertEqual(version, 'odm_2_0')

        version = VS.ValueSetLoader.get_version_for_module('my_package.define_2_1.custom')
        self.assertEqual(version, 'define_2_1')

    def test_get_version_for_module_default(self):
        """Test version detection defaults to odm_1_3_2"""
        version = VS.ValueSetLoader.get_version_for_module('unknown.module.path')
        self.assertEqual(version, 'odm_1_3_2', "Should default to odm_1_3_2")


class TestValueSet(TestCase):
    """Test ValueSet class functionality"""

    def setUp(self):
        # Clear cache before each test
        VS.ValueSetLoader._cache = None
        VS.ValueSetLoader._version_map = None
        VS.ValueSet._compiled_regex_cache.clear()

    def test_value_set_backward_compatibility(self):
        """Test backward compatibility - calling without version defaults to odm_1_3_2"""
        values = VS.ValueSet.value_set("StudyEventDef.Repeating")
        self.assertEqual(values, ["Yes", "No"])

    def test_value_set_explicit_version(self):
        """Test explicit version specification"""
        # ODM 1.3.2
        values = VS.ValueSet.value_set("StudyEventDef.Repeating", version='odm_1_3_2')
        self.assertEqual(values, ["Yes", "No"])

        # ODM 2.0
        values = VS.ValueSet.value_set("StudyEventDef.Repeating", version='odm_2_0')
        self.assertEqual(values, ["Yes", "No"])

    def test_value_set_with_instance_odm_1_3_2(self):
        """Test automatic version detection from ODM 1.3.2 instance"""
        # Create an ODM 1.3.2 StudyEventDef instance
        sed = ODM.StudyEventDef(OID="SE.1", Name="Visit 1", Repeating="Yes", Type="Scheduled")

        # Get valueset using instance for automatic version detection
        values = VS.ValueSet.value_set("StudyEventDef.Repeating", instance=sed)
        self.assertEqual(values, ["Yes", "No"])

    def test_value_set_with_instance_odm_2_0(self):
        """Test automatic version detection from ODM 2.0 instance"""
        # Create an ODM 2.0 StudyEventDef instance
        sed = ODM2.StudyEventDef(OID="SE.1", Name="Visit 1", Repeating="Yes", Type="Scheduled")

        # Get valueset using instance for automatic version detection
        values = VS.ValueSet.value_set("StudyEventDef.Repeating", instance=sed)
        self.assertEqual(values, ["Yes", "No"])

    def test_odm_2_0_specific_attributes(self):
        """Test that ODM 2.0 has its specific attributes that ODM 1.3.2 doesn't have"""
        # ODM 2.0 specific attributes
        branching_values = VS.ValueSet.value_set("Branching.Type", version='odm_2_0')
        self.assertEqual(branching_values, ["Exclusive", "Parallel"])

        timing_values = VS.ValueSet.value_set("RelativeTimingConstraint.Type", version='odm_2_0')
        self.assertEqual(timing_values, ["StartToStart", "StartToFinish", "FinishToStart", "FinishToFinish"])

        ig_type_values = VS.ValueSet.value_set("ItemGroupDef.Type", version='odm_2_0')
        self.assertEqual(ig_type_values, ["Form", "Dataset", "Concept", "Section"])

        seg_ref_values = VS.ValueSet.value_set("StudyEventGroupRef.Mandatory", version='odm_2_0')
        self.assertEqual(seg_ref_values, ["Yes", "No"])

    def test_define_2_0_define_version_is_regex(self):
        """Test that DefineVersion is now a regex dict, not a list"""
        define_version = VS.ValueSet.value_set("MetaDataVersion.DefineVersion", version='define_2_1')
        self.assertIsInstance(define_version, dict)
        self.assertIn("_regex", define_version)
        self.assertIn("_description", define_version)

    def test_value_set_returns_regex_dict(self):
        """Test that value_set() returns dict for regex entries across all Define-XML versions"""
        for version in ['define_2_0', 'define_2_1']:
            entry = VS.ValueSet.value_set("MetaDataVersion.DefineVersion", version=version)
            self.assertIsInstance(entry, dict, f"Expected dict for {version}")
            self.assertIn("_regex", entry)

    def test_error_unknown_attribute(self):
        """Test error handling for unknown attribute"""
        with self.assertRaises(ValueError) as context:
            VS.ValueSet.value_set("UnknownClass.UnknownAttribute", version='odm_1_3_2')
        self.assertIn("Unknown value", str(context.exception))
        self.assertIn("UnknownClass.UnknownAttribute", str(context.exception))

    def test_error_unknown_version(self):
        """Test error handling for unknown version"""
        with self.assertRaises(ValueError) as context:
            VS.ValueSet.value_set("StudyEventDef.Repeating", version='unknown_version')
        self.assertIn("Unknown version", str(context.exception))
        self.assertIn("unknown_version", str(context.exception))

    def test_common_attributes_across_versions(self):
        """Test that common attributes exist in multiple versions"""
        # StudyEventDef.Repeating should be in both versions
        odm_1_3_2_values = VS.ValueSet.value_set("StudyEventDef.Repeating", version='odm_1_3_2')
        odm_2_0_values = VS.ValueSet.value_set("StudyEventDef.Repeating", version='odm_2_0')
        self.assertEqual(odm_1_3_2_values, odm_2_0_values)

        # RangeCheck.Comparator should be in both versions
        odm_1_3_2_comparators = VS.ValueSet.value_set("RangeCheck.Comparator", version='odm_1_3_2')
        odm_2_0_comparators = VS.ValueSet.value_set("RangeCheck.Comparator", version='odm_2_0')
        self.assertEqual(odm_1_3_2_comparators, odm_2_0_comparators)


class TestValueSetValidate(TestCase):
    """Test ValueSet.validate() method"""

    def setUp(self):
        VS.ValueSetLoader._cache = None
        VS.ValueSetLoader._version_map = None
        VS.ValueSet._compiled_regex_cache.clear()

    def test_validate_list_attribute_valid(self):
        """Test validate() returns True for valid list values"""
        self.assertTrue(VS.ValueSet.validate("StudyEventDef.Repeating", "Yes"))
        self.assertTrue(VS.ValueSet.validate("StudyEventDef.Repeating", "No"))

    def test_validate_list_attribute_invalid(self):
        """Test validate() returns False for invalid list values"""
        self.assertFalse(VS.ValueSet.validate("StudyEventDef.Repeating", "Invalid"))
        self.assertFalse(VS.ValueSet.validate("StudyEventDef.Repeating", ""))
        self.assertFalse(VS.ValueSet.validate("StudyEventDef.Repeating", "yes"))

    def test_validate_regex_valid(self):
        """Test validate() returns True for values matching DefineVersion regex"""
        valid_versions = ["2.1", "2.1.0", "2.1.18", "2.1.99", "2.1.101"]
        for ver in valid_versions:
            self.assertTrue(
                VS.ValueSet.validate("MetaDataVersion.DefineVersion", ver, version='define_2_1'),
                f"Expected '{ver}' to be valid"
            )

    def test_validate_regex_invalid(self):
        """Test validate() returns False for values not matching DefineVersion regex"""
        invalid_versions = ["abc", "1.0", "3.0.1", "3.0.0", "0.1.0", "3.0", ".1", "2.", "2.1.", ""]
        for ver in invalid_versions:
            self.assertFalse(
                VS.ValueSet.validate("MetaDataVersion.DefineVersion", ver, version='define_2_0'),
                f"Expected '{ver}' to be invalid"
            )

    def test_validate_regex_across_versions(self):
        """Test regex validation works for all versions that have DefineVersion"""
        for version in ['define_2_1']:
            self.assertTrue(
                VS.ValueSet.validate("MetaDataVersion.DefineVersion", "2.1.18", version=version),
                f"Expected '2.1.18' to be valid for {version}"
            )
            self.assertFalse(
                VS.ValueSet.validate("MetaDataVersion.DefineVersion", "3.0", version=version),
                f"Expected '3.0' to be invalid for {version}"
            )

    def test_validate_regex_cache(self):
        """Test that compiled regex patterns are cached"""
        VS.ValueSet.validate("MetaDataVersion.DefineVersion", "2.0", version='define_2_0')
        self.assertIn(('define_2_0', 'MetaDataVersion.DefineVersion'),
                       VS.ValueSet._compiled_regex_cache)

    def test_regex_cache_cleared_on_reset(self):
        """Test that clearing _cache also allows fresh regex cache"""
        VS.ValueSet.validate("MetaDataVersion.DefineVersion", "2.0", version='define_2_0')
        self.assertTrue(len(VS.ValueSet._compiled_regex_cache) > 0)

        # Simulating cache reset as done in setUp
        VS.ValueSet._compiled_regex_cache.clear()
        self.assertEqual(len(VS.ValueSet._compiled_regex_cache), 0)

        # Should still work after clearing
        self.assertTrue(VS.ValueSet.validate("MetaDataVersion.DefineVersion", "2.0", version='define_2_0'))


class TestValueSetDescribe(TestCase):
    """Test ValueSet.describe() method"""

    def setUp(self):
        VS.ValueSetLoader._cache = None
        VS.ValueSetLoader._version_map = None
        VS.ValueSet._compiled_regex_cache.clear()

    def test_describe_list_attribute(self):
        """Test describe() for list-based attributes"""
        desc = VS.ValueSet.describe("StudyEventDef.Repeating", version='odm_1_3_2')
        self.assertIn("Value must be one of:", desc)
        self.assertIn("Yes", desc)
        self.assertIn("No", desc)

    def test_describe_regex_with_description(self):
        """Test describe() returns _description for regex entries"""
        desc = VS.ValueSet.describe("MetaDataVersion.DefineVersion", version='define_2_0')
        self.assertIn("Define-XML version 2.0", desc)

    def test_describe_regex_no_description(self):
        """Test describe() falls back to pattern when _description is absent"""
        # Temporarily modify the cached entry to remove _description
        VS.ValueSetLoader.load_valuesets()
        original = VS.ValueSetLoader._cache['define_2_0']['MetaDataVersion.DefineVersion']
        try:
            VS.ValueSetLoader._cache['define_2_0']['MetaDataVersion.DefineVersion'] = {
                "_regex": "^2\\.0(\\.\\d+)?$"
            }
            desc = VS.ValueSet.describe("MetaDataVersion.DefineVersion", version='define_2_0')
            self.assertIn("Value must match pattern:", desc)
            self.assertIn("^2\\.0", desc)
        finally:
            VS.ValueSetLoader._cache['define_2_0']['MetaDataVersion.DefineVersion'] = original


class TestValueSetIntegration(TestCase):
    """Integration tests with actual ODM model classes"""

    def setUp(self):
        # Clear cache before each test
        VS.ValueSetLoader._cache = None
        VS.ValueSetLoader._version_map = None
        VS.ValueSet._compiled_regex_cache.clear()

    def test_odm_1_3_2_validation(self):
        """Test that ODM 1.3.2 models validate correctly"""
        # Valid value should work
        sed = ODM.StudyEventDef(OID="SE.1", Name="Visit 1", Repeating="Yes", Type="Scheduled")
        self.assertEqual(sed.Repeating, "Yes")

        # Invalid value should raise error
        with self.assertRaises(TypeError) as context:
            ODM.StudyEventDef(OID="SE.1", Name="Visit 1", Repeating="Invalid", Type="Scheduled")
        self.assertIn("Invalid value", str(context.exception))

    def test_odm_2_0_validation(self):
        """Test that ODM 2.0 models validate correctly"""
        # Valid value should work
        sed = ODM2.StudyEventDef(OID="SE.1", Name="Visit 1", Repeating="Yes", Type="Scheduled")
        self.assertEqual(sed.Repeating, "Yes")

        # Invalid value should raise error
        with self.assertRaises(TypeError) as context:
            ODM2.StudyEventDef(OID="SE.1", Name="Visit 1", Repeating="Invalid", Type="Scheduled")
        self.assertIn("Invalid value", str(context.exception))

    def test_country_codes_present(self):
        """Test that country codes are present in valuesets"""
        country_codes = VS.ValueSet.value_set("Country._content", version='odm_1_3_2')
        self.assertIn("US", country_codes)
        self.assertIn("GB", country_codes)
        self.assertIn("CA", country_codes)
        self.assertGreater(len(country_codes), 200, "Should have many country codes")

    def test_data_types_complete(self):
        """Test that DataType valuesets are complete"""
        data_types = VS.ValueSet.value_set("ItemDef.DataType", version='odm_1_3_2')
        expected_types = ["text", "integer", "float", "date", "time", "datetime", "string", "boolean"]
        for expected_type in expected_types:
            self.assertIn(expected_type, data_types)

    def test_integration_define_version_regex(self):
        """Test DefineVersion regex validation via model instantiation"""
        import odmlib.define_2_1.model as DEF21

        # Valid DefineVersion values should work
        mdv = DEF21.MetaDataVersion(OID="MDV1", Name="Test", DefineVersion="2.1.0")
        self.assertEqual(mdv.DefineVersion, "2.1.0")

        mdv.DefineVersion = "2.1.18"
        self.assertEqual(mdv.DefineVersion, "2.1.18")

        mdv.DefineVersion = "2.1"
        self.assertEqual(mdv.DefineVersion, "2.1")

        mdv.DefineVersion = "2.1.99"
        self.assertEqual(mdv.DefineVersion, "2.1.99")

        # Invalid DefineVersion should raise error
        with self.assertRaises(TypeError):
            mdv.DefineVersion = "abc"

        with self.assertRaises(TypeError):
            mdv.DefineVersion = "3.0"

        with self.assertRaises(TypeError):
            mdv.DefineVersion = "1.0"
