"""Shared pytest fixtures for odmlib tests.

These fixtures provide common test setups that replace repetitive setUp()
methods across test files.  They also ensure proper namespace registry
cleanup between tests to prevent state leakage through the Borg singleton.
"""
import os
import pytest
import odmlib.ns_registry as NS


# ---------------------------------------------------------------------------
# Namespace management
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_namespace_registry():
    """Reset the NamespaceRegistry Borg singleton before each test.

    Prevents namespace state from leaking between tests.  The autouse=True
    ensures this runs for *every* test automatically without each test
    needing to opt in.

    After the reset a single default ODM 1.3.2 namespace is registered so
    that write_xml() (which requires at least one default namespace) works
    for tests that rely on the module-level registration.  Tests that need a
    different namespace set should call the appropriate ns_* fixture or
    re-register in their setUp().
    """
    NS.NamespaceRegistry(
        prefix="odm",
        uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True,
        is_reset=True,
    )
    yield


@pytest.fixture
def ns_odm_132():
    """Set up the full ODM 1.3.2 namespace set."""
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True,
    )
    NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
    NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
    NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


@pytest.fixture
def ns_odm_20():
    """Set up the full ODM 2.0 namespace set."""
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
        is_default=True, is_reset=True,
    )
    NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
    NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
    NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


@pytest.fixture
def ns_define_20():
    """Set up the full Define-XML 2.0 namespace set."""
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True,
    )
    NS.NamespaceRegistry(prefix="def",   uri="http://www.cdisc.org/ns/def/v2.0")
    NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
    NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
    NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


@pytest.fixture
def ns_define_21():
    """Set up the full Define-XML 2.1 namespace set."""
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True,
    )
    NS.NamespaceRegistry(prefix="def",   uri="http://www.cdisc.org/ns/def/v2.1")
    NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
    NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
    NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


@pytest.fixture
def ns_ct():
    """Set up namespaces for CT-XML 1.1.1 (includes nciodm)."""
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True,
    )
    NS.NamespaceRegistry(prefix="nciodm", uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC")
    NS.NamespaceRegistry(prefix="xs",     uri="http://www.w3.org/2001/XMLSchema-instance")
    NS.NamespaceRegistry(prefix="xml",    uri="http://www.w3.org/XML/1998/namespace")


@pytest.fixture
def ns_dataset():
    """Set up namespaces for Dataset-XML 1.0.1."""
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True,
    )
    NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")


# ---------------------------------------------------------------------------
# Test data path helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def test_data_dir():
    """Absolute path to the tests/data/ directory."""
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


@pytest.fixture
def cdash_odm_xml(test_data_dir):
    """Path to the primary CDASH ODM 1.3.2 test XML."""
    return os.path.join(test_data_dir, "cdash-odm-test.xml")


@pytest.fixture
def cdash_odm_json(test_data_dir):
    """Path to the primary CDASH ODM 1.3.2 test JSON."""
    return os.path.join(test_data_dir, "cdash_odm_test.json")


@pytest.fixture
def define21_xml(test_data_dir):
    """Path to the comprehensive Define-XML 2.1 SDTM test file."""
    return os.path.join(test_data_dir, "defineV21-SDTM.xml")


@pytest.fixture
def define21_json(test_data_dir):
    """Path to the Define-XML 2.1 SDTM JSON test file."""
    return os.path.join(test_data_dir, "defineV21-SDTM-test.json")


@pytest.fixture
def define20_xml(test_data_dir):
    """Path to the Define-XML 2.0 SDTM test file."""
    return os.path.join(test_data_dir, "define2-0-0-sdtm-test.xml")


@pytest.fixture
def odmv2_xml(test_data_dir):
    """Path to the ODM 2.0 example file."""
    return os.path.join(test_data_dir, "odmv2_example.xml")


# ---------------------------------------------------------------------------
# Permissive mode helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def permissive_mode():
    """Activate fully permissive mode for the duration of a test."""
    import odmlib.mode as _mode
    with _mode.permissive():
        yield


@pytest.fixture
def nonconformant_odm_xml(test_data_dir):
    """Path to intentionally broken ODM 1.3.2 XML test file."""
    return os.path.join(test_data_dir, "nonconformant_odm.xml")


@pytest.fixture
def nonconformant_odm_json(test_data_dir):
    """Path to intentionally broken ODM 1.3.2 JSON test file."""
    return os.path.join(test_data_dir, "nonconformant_odm.json")


@pytest.fixture
def nonconformant_define21_xml(test_data_dir):
    """Path to intentionally broken Define-XML 2.1 test file."""
    return os.path.join(test_data_dir, "nonconformant_define21.xml")


# ---------------------------------------------------------------------------
# Loader factories
# ---------------------------------------------------------------------------

@pytest.fixture
def xml_odm_loader():
    """An XMLODMLoader facade for ODM 1.3.2."""
    import odmlib.odm_loader as OL
    import odmlib.loader as LD
    return LD.ODMLoader(OL.XMLODMLoader())


@pytest.fixture
def json_odm_loader():
    """A JSONODMLoader facade for ODM 1.3.2."""
    import odmlib.odm_loader as OL
    import odmlib.loader as LD
    return LD.ODMLoader(OL.JSONODMLoader())


@pytest.fixture
def xml_define21_loader():
    """An XMLDefineLoader facade for Define-XML 2.1."""
    import odmlib.define_loader as DL
    import odmlib.loader as LD
    return LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
