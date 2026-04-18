import json
import re
from pathlib import Path
from odmlib.exceptions import OdmlibValidationError


class ValueSetLoader:
    """Loads and caches valueset data from JSON file"""
    _cache = None  # Class variable for singleton cache
    _version_map = None  # Maps module paths to versions

    @classmethod
    def load_valuesets(cls):
        """Load JSON once, cache in memory (lazy loading)"""
        if cls._cache is None:
            data_dir = Path(__file__).parent / 'data'
            json_path = data_dir / 'valuesets.json'
            with open(json_path, 'r') as f:
                cls._cache = json.load(f)
            cls._build_version_map()
        return cls._cache

    @classmethod
    def _build_version_map(cls):
        """Map module paths to version keys"""
        cls._version_map = {
            'odmlib.odm_1_3_2.model': 'odm_1_3_2',
            'odmlib.odm_2_0.model': 'odm_2_0',
            'odmlib.define_2_0.model': 'define_2_0',
            'odmlib.define_2_1.model': 'define_2_1',
            'odmlib.ct_1_1_1.model': 'ct_1_1_1',
            'odmlib.dataset_1_0_1.model': 'dataset_1_0_1',
            # Add test models
            'tests.model_extended': 'odm_1_3_2',  # Test extension uses base
        }

    @classmethod
    def get_version_for_module(cls, module_path):
        """Determine version from module path"""
        if cls._version_map is None:
            cls.load_valuesets()

        # Exact match
        if module_path in cls._version_map:
            return cls._version_map[module_path]

        # Pattern matching for custom/local models
        if 'odm_2_0' in module_path:
            return 'odm_2_0'
        elif 'define_2_1' in module_path:
            return 'define_2_1'
        elif 'define_2_0' in module_path:
            return 'define_2_0'
        elif 'ct_1_1_1' in module_path:
            return 'ct_1_1_1'
        elif 'dataset_1_0_1' in module_path:
            return 'dataset_1_0_1'

        # Default to odm_1_3_2 for backward compatibility
        return 'odm_1_3_2'


class ValueSet:
    """Backward-compatible interface to valueset data.

    Supports two entry types in valuesets.json:
    - **list**: A list of allowed string values (e.g., ``["Yes", "No"]``)
    - **regex dict**: A dict with ``_regex`` key and optional ``_description``
      (e.g., ``{"_regex": "^2\\\\.[01](\\\\.\\\\d+)?$", "_description": "..."}``).
    """

    _compiled_regex_cache = {}  # (version, attribute) -> compiled re.Pattern

    @classmethod
    def _resolve_version(cls, version, instance):
        """Resolve the version string from explicit value or instance."""
        if version is None and instance is not None:
            module_path = type(instance).__module__
            return ValueSetLoader.get_version_for_module(module_path)
        elif version is None:
            return 'odm_1_3_2'
        return version

    @classmethod
    def value_set(cls, attribute, version=None, instance=None):
        """
        Get the raw valueset entry for an attribute.

        Args:
            attribute: "ClassName.AttributeName" format
            version: Explicit version (e.g., "odm_2_0") - optional
            instance: ODMElement instance for automatic version detection - optional

        Returns:
            list or dict: A list of valid values, or a dict with ``_regex`` key
            for pattern-based validation.

        Raises:
            OdmlibValidationError: If attribute or version not found in valueset
        """
        version = cls._resolve_version(version, instance)

        # Load valuesets (cached)
        valuesets = ValueSetLoader.load_valuesets()

        # Get version-specific valueset
        if version not in valuesets:
            raise OdmlibValidationError(
                f"Unknown version {version} in ValueSet",
                hint=f"Valid versions are: {list(valuesets.keys())}",
            )

        version_valueset = valuesets[version]

        # Get attribute values
        if attribute in version_valueset:
            return version_valueset[attribute]
        else:
            raise OdmlibValidationError(
                f"Unknown value {attribute} in ValueSet for version {version}. Unable to check value.",
                hint=f"Attribute '{attribute}' is not defined in the value set for {version}",
            )

    @classmethod
    def validate(cls, attribute, value, version=None, instance=None):
        """
        Check whether a value is valid for the given attribute.

        Args:
            attribute: "ClassName.AttributeName" format
            value: The string value to validate
            version: Explicit version (e.g., "odm_2_0") - optional
            instance: ODMElement instance for automatic version detection - optional

        Returns:
            bool: True if the value is valid, False otherwise.
        """
        version = cls._resolve_version(version, instance)
        entry = cls.value_set(attribute, version=version)

        if isinstance(entry, list):
            return value in entry

        # Regex dict entry
        if isinstance(entry, dict) and "_regex" in entry:
            cache_key = (version, attribute)
            if cache_key not in cls._compiled_regex_cache:
                cls._compiled_regex_cache[cache_key] = re.compile(entry["_regex"])
            pattern = cls._compiled_regex_cache[cache_key]
            return pattern.fullmatch(value) is not None

        return False

    @classmethod
    def describe(cls, attribute, version=None, instance=None):
        """
        Return a human-readable description of valid values for an attribute.

        Args:
            attribute: "ClassName.AttributeName" format
            version: Explicit version (e.g., "odm_2_0") - optional
            instance: ODMElement instance for automatic version detection - optional

        Returns:
            str: Description suitable for error messages.
        """
        version = cls._resolve_version(version, instance)
        entry = cls.value_set(attribute, version=version)

        if isinstance(entry, list):
            return f"Value must be one of: {', '.join(entry)}"

        if isinstance(entry, dict) and "_regex" in entry:
            if "_description" in entry:
                return entry["_description"]
            return f"Value must match pattern: {entry['_regex']}"

        return "Unknown valueset format"
