import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_1_3_2.rules.oid_ref as OID_REF
import odmlib.ns_registry as NS
from odmlib.exceptions import OdmlibOIDError

NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)

ig_ref = ODM.ItemGroupRef(ItemGroupOID="IG.TEST", Mandatory="Yes")
form_ref = ODM.FormRef(FormOID="F.TEST", Mandatory="Yes", OrderNumber=1)
sed = ODM.StudyEventDef(OID="SE.TEST", Name="Test Event", Repeating="No", Type="Scheduled",
                        FormRef=[form_ref])
item_ref = ODM.ItemRef(ItemOID="IT.TEST", Mandatory="No", OrderNumber=1)
igd = ODM.ItemGroupDef(OID="IG.TEST", Name="Test Group", Repeating="No", ItemRef=[item_ref])
item = ODM.ItemDef(OID="IT.TEST", Name="Test Item", DataType="text")
form = ODM.FormDef(OID="F.TEST", Name="Test Form", Repeating="No", ItemGroupRef=[ig_ref])
mdv = ODM.MetaDataVersion(OID="MDV.TEST", Name="Test MDV",
                          StudyEventDef=[sed], FormDef=[form],
                          ItemGroupDef=[igd], ItemDef=[item])

# Fail-fast (default): returns True when valid
result = mdv.validate()
assert result is True, f"Expected True, got {result}"

# Collect-all-errors: returns empty list when valid
errors = mdv.validate(collect_errors=True)
assert errors == [], f"Expected [], got {errors}"

# Inject an OID error
checker = OID_REF.OIDRef()
checker.oid["IT.MISSING"] = "WrongType"
checker.oid_ref["ItemOID"].add("IT.MISSING")

errors = mdv.validate(collect_errors=True, oid_checker=checker)
assert len(errors) >= 1
assert all(isinstance(e, OdmlibOIDError) for e in errors)
print(f"Collected {len(errors)} error(s): {errors[0]}")

print("validate() smoke tests passed.")
