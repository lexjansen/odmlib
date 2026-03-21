import warnings
import odmlib.odm_1_3_2.model as ODM
from odmlib.exceptions import OdmlibWarning

item = ODM.ItemDef(OID="IT.TEST", Name="Test Item", DataType="text")
alias = ODM.Alias(Context="nci", Name="C12345")
item.Alias = [alias]

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    item.reorder_object()
    assert len(w) == 1
    assert issubclass(w[0].category, OdmlibWarning)
    assert "reordered" in str(w[0].message).lower()

print("reorder_object() warning test passed.")