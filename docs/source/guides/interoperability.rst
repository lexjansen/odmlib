Interoperability: Dataset-JSON and Pandas
=========================================

odmlib v0.2.0 adds two new interoperability features:

1. **Dataset-JSON v1.1 support** — create, read, write, and convert CDISC
   Dataset-JSON documents
2. **Optional Pandas DataFrame integration** — export metadata and data to
   DataFrames, and import DataFrame rows back into odmlib objects

---

Working with Dataset-JSON
--------------------------

`CDISC Dataset-JSON <https://www.cdisc.org/standards/data-exchange/dataset-json>`_
is a column-oriented JSON format for regulatory submission datasets.
odmlib provides a pure-Python model that requires no additional dependencies.

Creating a Dataset-JSON document
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from odmlib.dataset_json import DatasetJSON, Dataset, ItemMetadata

    # Create the root document
    dsjson = DatasetJSON(
        fileOID="ODM.DATASET.001",
        creationDateTime="2024-01-15T12:00:00",
        studyOID="CDISC01",
        metaDataVersionOID="MDV.001",
        originator="ACME Corp",
    )

    # Define columns for the AE dataset
    items = [
        ItemMetadata(OID="IT.STUDYID", name="STUDYID", label="Study Identifier", type="string"),
        ItemMetadata(OID="IT.USUBJID", name="USUBJID", label="Unique Subject Identifier", type="string"),
        ItemMetadata(OID="IT.AETERM",  name="AETERM",  label="Reported Term for the AE", type="string"),
        ItemMetadata(OID="IT.AESEQ",   name="AESEQ",   label="Sequence Number", type="integer"),
    ]

    # Create the AE dataset and add data rows
    ae_ds = Dataset(name="AE", label="Adverse Events", items=items)
    ae_ds.add_record(["CDISC01", "CDISC01-001", "Headache", 1])
    ae_ds.add_record(["CDISC01", "CDISC01-001", "Nausea",   2])

    dsjson.add_dataset(ae_ds)

    # Write to file
    dsjson.write_json("ae_dataset.json", indent=2)

Reading a Dataset-JSON file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from odmlib.dataset_json import DatasetJSON

    dsjson = DatasetJSON.read_json("ae_dataset.json")
    print(f"File OID: {dsjson.fileOID}")
    print(f"Datasets: {[ds.name for ds in dsjson.datasets]}")

    ae = dsjson.get_dataset("AE")
    print(f"AE columns: {ae.item_names}")
    print(f"AE rows: {len(ae)}")
    print(f"First row: {ae.records[0].values}")

Converting from Dataset-XML
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use :func:`odmlib.dataset_json.converter.dataset_xml_to_json` to convert
an odmlib Dataset-XML 1.0.1 object to Dataset-JSON:

.. code-block:: python

    import odmlib.odm_loader as OL
    import odmlib.loader as LD
    import odmlib.ns_registry as NS
    from odmlib.dataset_json.converter import dataset_xml_to_json

    # Set up namespaces for Dataset-XML
    NS.NamespaceRegistry(prefix="odm",  uri="http://www.cdisc.org/ns/odm/v1.3",
                         is_default=True)
    NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")

    # Load the Dataset-XML file
    loader = LD.ODMLoader(OL.XMLODMLoader(
        model_package="dataset_1_0_1",
        ns_uri="http://www.cdisc.org/ns/Dataset-XML/v1.0",
    ))
    loader.open_odm_document("ae.xml")
    odm = loader.root()

    # Convert to Dataset-JSON
    dsjson = dataset_xml_to_json(odm)
    dsjson.write_json("ae_dataset.json")

Optionally pass a Define-XML MetaDataVersion to enrich column metadata
(labels, types, lengths):

.. code-block:: python

    from odmlib.dataset_json.converter import dataset_xml_to_json

    # Load Define-XML for metadata enrichment
    define_loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
    define_loader.open_odm_document("define.xml")
    mdv = define_loader.MetaDataVersion()

    # Convert with enriched metadata
    dsjson = dataset_xml_to_json(odm, define_mdv=mdv)

---

Using Pandas with odmlib
-------------------------

Install Pandas (optional dependency):

.. code-block:: bash

    pip install odmlib[dataframe]
    # or
    pip install pandas

Exporting metadata to a DataFrame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import odmlib.loader as LD
    import odmlib.define_loader as DL
    from odmlib.dataframe import metadata_to_dataframe

    loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
    loader.open_odm_document("define.xml")
    mdv = loader.MetaDataVersion()

    # All ItemDef attributes as a DataFrame
    df = metadata_to_dataframe(mdv, "ItemDef")
    print(df[["OID", "Name", "DataType", "Length"]].head(10))

    # Filter to specific columns only
    df_slim = metadata_to_dataframe(mdv, "ItemDef", attributes=["OID", "Name", "DataType"])

Exporting clinical data to a DataFrame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For ODM 1.3.2 hierarchical clinical data:

.. code-block:: python

    from odmlib.dataframe import clinical_data_to_dataframe

    # Flatten all VS records to a DataFrame
    df = clinical_data_to_dataframe(odm.ClinicalData, item_group_oid="IG.VS")
    print(df.head())

For Dataset-XML 1.0.1 (flat structure):

.. code-block:: python

    from odmlib.dataframe import dataset_to_dataframe

    df = dataset_to_dataframe(odm.ClinicalData)
    print(df.head())

For Dataset-JSON datasets:

.. code-block:: python

    from odmlib.dataset_json import DatasetJSON
    from odmlib.dataframe import dataset_json_to_dataframe

    dsjson = DatasetJSON.read_json("ae_dataset.json")
    ae = dsjson.get_dataset("AE")
    df = dataset_json_to_dataframe(ae)
    print(df.describe())

Importing from a DataFrame back into odmlib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import odmlib.define_2_1.model as DEF
    import pandas as pd
    from odmlib.dataframe import dataframe_to_items

    # Load item definitions from a spreadsheet or CSV
    df = pd.read_excel("items.xlsx")

    # Map spreadsheet columns to odmlib attribute names if needed
    mapping = {"Variable Name": "Name", "Item OID": "OID", "Type": "DataType"}

    items = dataframe_to_items(df, DEF, "ItemDef", column_mapping=mapping)
    for item in items:
        mdv.ItemDef.append(item)

.. note::

   :func:`~odmlib.dataframe.dataframe_to_items` skips rows that cannot
   be constructed as valid odmlib elements (e.g., rows with missing
   required attributes).  Check the returned list length against the
   input DataFrame length to detect skipped rows.
