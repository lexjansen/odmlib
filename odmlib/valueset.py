import json
from pathlib import Path


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
    """Backward-compatible interface to valueset data"""

    @classmethod
    def value_set(cls, attribute, version=None, instance=None):
        """
        Get valid values for an attribute

        Args:
            attribute: "ClassName.AttributeName" format
            version: Explicit version (e.g., "odm_2_0") - optional
            instance: ODMElement instance for automatic version detection - optional

        Returns:
            List of valid values

        Raises:
            ValueError: If attribute not found in valueset
        """
        # Determine version
        if version is None and instance is not None:
            module_path = type(instance).__module__
            version = ValueSetLoader.get_version_for_module(module_path)
        elif version is None:
            # Backward compatibility: default to odm_1_3_2
            version = 'odm_1_3_2'

        # Load valuesets (cached)
        valuesets = ValueSetLoader.load_valuesets()

        # Get version-specific valueset
        if version not in valuesets:
            raise ValueError(f"Unknown version {version} in ValueSet")

        version_valueset = valuesets[version]

        # Get attribute values
        if attribute in version_valueset:
            return version_valueset[attribute]
        else:
            raise ValueError(f"Unknown value {attribute} in ValueSet for version {version}. Unable to check value.")
