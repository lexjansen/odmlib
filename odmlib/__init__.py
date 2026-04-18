from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("odmlib")
except PackageNotFoundError:
    __version__ = "0.2.0.dev"

from odmlib.exceptions import (
    OdmlibError,
    OdmlibValidationError,
    OdmlibRequiredAttributeError,
    OdmlibOIDError,
    OdmlibConformanceError,
    OdmlibElementOrderError,
    OdmlibTypeError,
    OdmlibParsingError,
    OdmlibLoaderStateError,
    OdmlibSerializationError,
    OdmlibNamespaceError,
    OdmlibWarning,
    OdmlibDeprecationWarning,
    OdmlibInteroperabilityWarning,
    ErrorCollector,
)
from odmlib.mode import ValidationMode, permissive, get_mode, set_mode
from odmlib.context import open_odm, open_define
from odmlib.builder import ODMBuilder
from odmlib.oid_generator import DynamicOIDRef, create_oid_checker
from odmlib.dataset_json_1_1.model import DatasetJSON, Column, SourceSystem
from odmlib.dataset_json_1_1.define_flattener import DefineFlattener
from odmlib.dataset_json_1_1.converter import (
    dataset_xml_to_dataset_json,
    dataset_json_to_dataset_xml,
)