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
from odmlib.context import open_odm, open_define
from odmlib.builder import ODMBuilder