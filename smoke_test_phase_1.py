from odmlib.exceptions import (
    OdmlibError, OdmlibValidationError, OdmlibOIDError,
    OdmlibConformanceError, OdmlibTypeError, OdmlibElementOrderError,
    OdmlibRequiredAttributeError, OdmlibLoaderStateError, OdmlibNamespaceError,
    OdmlibWarning, ErrorCollector,
)

# --- Hierarchy ---
assert issubclass(OdmlibValidationError, OdmlibError)
assert issubclass(OdmlibValidationError, ValueError)      # backward compat
assert issubclass(OdmlibOIDError, OdmlibValidationError)
assert issubclass(OdmlibConformanceError, OdmlibValidationError)
assert issubclass(OdmlibElementOrderError, OdmlibValidationError)
assert issubclass(OdmlibRequiredAttributeError, OdmlibValidationError)
assert issubclass(OdmlibTypeError, OdmlibError)
assert issubclass(OdmlibTypeError, TypeError)             # backward compat
assert issubclass(OdmlibLoaderStateError, ValueError)     # backward compat
assert issubclass(OdmlibNamespaceError, ValueError)       # backward compat

# --- Attributes ---
err = OdmlibValidationError(
    "OID IT.AGE is not unique",
    element_path="ODM > Study > MetaDataVersion > ItemDef",
    hint="Each OID must be unique",
    attribute="OID",
    element_type="ItemDef",
)
assert "IT.AGE" in str(err)
assert "Context:" in str(err)
assert "Hint:" in str(err)
assert err.attribute == "OID"
assert err.hint == "Each OID must be unique"

# --- Conformance error cerberus_errors ---
cerr = OdmlibConformanceError(
    "Conformance failed",
    cerberus_errors={"OID": ["required field"]},
    element_type="ItemDef",
)
assert cerr.cerberus_errors == {"OID": ["required field"]}

# --- Backward compat catch ---
try:
    raise OdmlibOIDError("dup OID")
except ValueError:
    pass  # still works

# --- ErrorCollector ---
collector = ErrorCollector()
assert not collector.has_errors
collector.add_error(OdmlibOIDError("error 1"))
collector.add_error(OdmlibOIDError("error 2"))
assert collector.has_errors
assert len(collector.errors) == 2
try:
    collector.raise_if_errors()
    assert False, "should have raised"
except OdmlibValidationError as e:
    assert "2 validation errors" in str(e)

print("All smoke tests passed.")
