import odmlib
from odmlib.oid_generator import create_oid_checker, DynamicOIDRef

# Scenario 9 check (adjusted to be self-contained)
checker = create_oid_checker("odm_1_3_2", extra_skip_attrs=["CustomOID"])
print(f"Checker skip_attr: {checker.skip_attr}")
assert "CustomOID" in checker.skip_attr
assert "FileOID" in checker.skip_attr

# Scenario 10 check
print(f"odmlib has DynamicOIDRef: {hasattr(odmlib, 'DynamicOIDRef')}")
assert hasattr(odmlib, "DynamicOIDRef")
assert hasattr(odmlib, "create_oid_checker")

checker2 = odmlib.create_oid_checker("odm_1_3_2")
from odmlib.oid_generator import DynamicOIDRef
assert isinstance(checker2, DynamicOIDRef)
print("Package-level import works:", type(checker2).__name__)
