Validating ODM Documents
=========================

odmlib provides several validation mechanisms for ODM documents.

Element Order Verification
--------------------------

ODM specifies the required order of child elements in XML. odmlib can
verify and fix element ordering:

.. code-block:: python

    import warnings
    from odmlib.exceptions import OdmlibElementOrderError

    # Check order (raises OdmlibElementOrderError if out of order)
    try:
        odm.verify_order()
        print("Element order is correct")
    except OdmlibElementOrderError as e:
        print(f"Order error: {e}")
        # Fix automatically (issues OdmlibWarning)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            odm.reorder_object()

OID Uniqueness and Reference Integrity
---------------------------------------

odmlib can verify that all OIDs are unique and that all OID references
point to valid definitions:

Using the Dynamic OID Checker (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from odmlib import create_oid_checker

    # Create a dynamic checker for ODM 1.3.2
    checker = create_oid_checker("odm_1_3_2")

    # Verify OIDs (raises OdmlibOIDError on failure)
    is_valid = odm.verify_oids(checker)
    print(f"OIDs valid: {is_valid}")

    # Find unreferenced definitions (e.g., unused code lists)
    unreferenced = odm.unreferenced_oids(checker)
    for oid in unreferenced:
        print(f"Unreferenced: {oid}")

Using the Manual OID Checker (deprecated)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import odmlib.odm_1_3_2.rules.oid_ref as OR
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        checker = OR.OIDRef()

    is_valid = odm.verify_oids(checker)

Conformance Validation
-----------------------

Cerberus-based schema validation checks structural conformance:

.. code-block:: python

    import odmlib.odm_1_3_2.rules.metadata_schema as SC

    validator = SC.MetadataSchema()
    result = mdv.verify_conformance(validator)
    print(f"Conformance result: {result}")

Combined Validation with Error Collection
------------------------------------------

Use the ``validate()`` method to run all checks and collect all errors
instead of failing on the first one:

.. code-block:: python

    from odmlib import create_oid_checker
    import odmlib.odm_1_3_2.rules.metadata_schema as SC

    checker = create_oid_checker("odm_1_3_2")
    validator = SC.MetadataSchema()

    errors = odm.validate(
        collect_errors=True,
        oid_checker=checker,
        conformance_checker=validator
    )

    if not errors:
        print("Document is valid")
    else:
        for err in errors:
            print(f"Error: {err}")

This pattern is particularly useful after permissive loading, where a
non-conformant document has been loaded with validation bypassed.  After
fixing known issues, use ``validate(collect_errors=True)`` to confirm all
problems have been resolved.  See :doc:`permissive_loading` for the
complete workflow.

Schema Validation
-----------------

For XML Schema (XSD) validation, use the odmlib schema manager:

.. code-block:: python

    import odmlib.schema_manager as SM

    sm = SM.SchemaManager()
    result = sm.validate_file("study.xml", "odm_1_3_2")

Understanding Error Types
--------------------------

odmlib uses a custom exception hierarchy:

.. list-table::
   :header-rows: 1

   * - Exception
     - When raised
   * - :exc:`~odmlib.exceptions.OdmlibError`
     - Base class for all odmlib errors
   * - :exc:`~odmlib.exceptions.OdmlibTypeError`
     - Type validation failure (wrong type assigned to attribute)
   * - :exc:`~odmlib.exceptions.OdmlibValidationError`
     - Value validation failure (invalid format, out of range)
   * - :exc:`~odmlib.exceptions.OdmlibRequiredAttributeError`
     - Required attribute missing during construction
   * - :exc:`~odmlib.exceptions.OdmlibElementOrderError`
     - Element order does not match ODM specification
   * - :exc:`~odmlib.exceptions.OdmlibOIDError`
     - OID uniqueness or ref/def integrity failure
   * - :exc:`~odmlib.exceptions.OdmlibLoaderStateError`
     - Loader used before document opened
   * - :exc:`~odmlib.exceptions.OdmlibNamespaceError`
     - Invalid namespace URI or unregistered prefix
