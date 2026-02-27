from __future__ import annotations
from typing import Any, Optional, List
import odmlib.descriptor as DESC
import odmlib.typed as T
import odmlib.ns_registry as NS
import odmlib.oid_index as IDX
from collections import OrderedDict
import json
import warnings
import xml.etree.ElementTree as ET
from odmlib.exceptions import (
    OdmlibError,
    OdmlibTypeError,
    OdmlibRequiredAttributeError,
    OdmlibElementOrderError,
    OdmlibWarning,
    ErrorCollector,
)


class ODMMeta(type):
    @classmethod
    def __prepare__(cls, name, bases):
        """ preserves the order of declarations in each class """
        return OrderedDict()

    def __new__(cls, clsname, bases, clsdict):
        # variables created in classes become the class attributes
        # fields = [key for key, val in clsdict.items() if isinstance(val, (DESC.Descriptor, ODMMeta))]
        clsdict["_fields"] = []
        clsdict["_elems"] = {}
        clsdict["_attrs"] = {}
        clsdict["_attr_ns"] = {}
        for key, val in clsdict.items():
            if isinstance(val, (T.ODMObject, T.ODMListObject)):
                clsdict["_elems"][key] = val
                clsdict[key].name = key
                clsdict["_fields"].append(key)
            elif isinstance(val, (DESC.Descriptor, ODMMeta)):
                clsdict["_attrs"][key] = val
                clsdict[key].name = key
                clsdict["_fields"].append(key)
                if val.namespace != "odm":
                    clsdict["_attr_ns"][key] = val.namespace

        # for name in fields:
        #     clsdict[name].name = name

        #clsdict["_fields"] = fields
        # the default class namespace is odm
        if "namespace" not in clsdict:
            clsdict["namespace"] = "odm"
        # elems = {key: val for key, val in clsdict.items() if isinstance(val, (T.ODMObject, T.ODMListObject))}
        # clsdict["_elems"] = elems
        # add attribute non-default namespaces
        # ns = {key: val.namespace for key, val in clsdict.items() if isinstance(val, (DESC.Descriptor, ODMMeta))
        #       if val.namespace != "odm"}
        # clsdict["_attr_ns"] = ns

        clsobj = super().__new__(cls, clsname, bases, dict(clsdict))
        return clsobj


class ODMWriter:

    @staticmethod
    def write_odm(odm_file, odm_elem):
        """
        after converting ODMLIB to ElementTree, write the ElementTree to an ODM file
        :param odm_file: path and file to write the ODM XML
        :param odm_elem: Element object to write to ODM (presumably an ODM root)
        """
        tree = ET.ElementTree(odm_elem)
        root = tree.getroot()
        # workaround for elementtree NS bug - NamespaceRegistry assumes at least 1 default NS has been set
        nsr = NS.NamespaceRegistry()
        nsr.set_odm_namespace_attributes(root)
        tree.write(odm_file, xml_declaration=True, encoding='utf-8', method='xml', short_empty_elements=True)


class ODMElement(metaclass=ODMMeta):
    def __init__(self, **kwargs: Any) -> None:
        """
        abstract ODM element class used to set the properties of any ODM object
        """
        for name, val in kwargs.items():
            if name not in self.__class__.__dict__.keys():
                # strip out non-default elementtree namespaces from the XML to work with just the name e.g. xml:lang
                if "}" in name:
                    name = name[name.find('}') + 1:]
                else:
                    raise OdmlibTypeError(
                        f"Unknown keyword argument {name} in {self.__class__.__name__}",
                        attribute=name,
                        element_type=self.__class__.__name__,
                        hint=f"Valid attributes for {self.__class__.__name__}: "
                             f"{', '.join(k for k in self.__class__.__dict__ if not k.startswith('_'))}",
                    )
            setattr(self, name, val)
        for attr, obj in self.__class__.__dict__.items():
            if isinstance(obj, DESC.Descriptor) and (not isinstance(obj, T.ODMObject)) and (attr not in self.__dict__) and obj.required:
                raise OdmlibRequiredAttributeError(
                    f"Missing required keyword argument {attr} in {self.__class__.__name__}",
                    attribute=attr,
                    element_type=self.__class__.__name__,
                    hint=f"Attribute '{attr}' is required when constructing {self.__class__.__name__}",
                )

    def __setattr__(self, key, value):
        """ ensure the object being added is a type that belongs to the class """
        if not hasattr(self, key):
            raise OdmlibTypeError(
                f"Assignment error: {self.__class__.__name__} does not have a defined attribute {key}",
                attribute=key,
                element_type=self.__class__.__name__,
            )
        super().__setattr__(key, value)

    def to_json(self) -> str:
        """
        transforms odmlib hierarchy into a dict and converts that to JSON and returns it

        :return: JSON representation of odmlib hierarchy
        """
        return json.dumps(self.to_dict())

    def to_xml(self, parent_elem: Optional[ET.Element] = None, top_elem: Optional[ET.Element] = None) -> Optional[ET.Element]:
        """
        generates ElementTree XML from the odmlib object hierarchy

        :param parent_elem: (obj) Element that is the parent of the element to be created
        :param top_elem: (obj) Topmost element that has been created
        :return: top_elem: (obj) Topmost element created during the recursive calls
        """
        # create attributes
        attrs = {}
        for attr, obj in self.__dict__.items():
            if not isinstance(obj, (ODMElement, list)) and attr != "_content" and obj is not None:
                # add namespace if not the default namespace
                if attr in self.__class__.__dict__["_attr_ns"]:
                    attrs[self.__class__.__dict__["_attr_ns"][attr] + ":" + attr] = str(obj)
                else:
                    attrs[attr] = str(obj)

        # create element
        if isinstance(parent_elem, ET.Element):
            odm_elem = ET.SubElement(parent_elem, self.__class__.__name__ if self.namespace == "odm" else self.namespace + ":" + self.__class__.__name__, attrs)
        else:
            odm_elem = ET.Element(self.__class__.__name__ if self.namespace == "odm" else self.namespace + ":" + self.__class__.__name__, attrs)
            top_elem = odm_elem
        # add text to element if it exists
        if "_content" in self.__dict__:
            odm_elem.text = self.__dict__["_content"]
        for name, obj in self.__dict__.items():
            # process each element in a list of ELEMENTS
            if isinstance(obj, list) and obj:
                for o in obj:
                    o.to_xml(odm_elem, top_elem)
            elif isinstance(obj, ODMElement):
                obj.to_xml(odm_elem, top_elem)
        return top_elem

    def to_xml_string(self) -> str:
        elem = self.to_xml()
        xml_str = ET.tostring(elem, encoding='utf8', method='xml')
        return xml_str.decode("utf-8")

    def to_dict(self) -> dict:
        """
        transform odmlib object hierarchy into a Python dictionary and return it

        :return: dictionary serialization of odmlib hierarchy
        """
        # Note: namespaces used in the XML serialization are not part of the dictionary or json serializations
        property_dict = {}
        odm_content = {attr: obj for attr, obj in self.__dict__.items() if attr not in ["_fields", "_attr_ns", "_elems", "_attrs"]}
        for attr, obj in odm_content.items():
            if isinstance(obj, ODMElement):
                property_dict[attr] = obj.to_dict()                    # element
            elif isinstance(obj, list):
                property_dict[attr] = [o.to_dict() for o in obj]       # list of ELEMENTS
            elif obj is not None:
                property_dict[attr] = obj                              # attributes
        return property_dict

    def __repr__(self):
        args = ", ".join(name for name in self._fields)
        return type(self).__name__ + "(" + args + ")"

    def __str__(self):
        if "_content" in self._fields and self._content:
            return self._content
        elif "OID" in self._fields and self.OID:
            return type(self).__name__ + "(OID=" + self.OID + ")"
        else:
            args = ", ".join(name for name in self._fields)
            return type(self).__name__ + "(" + args + ")"

    def find(self, obj_name: str, attr: str, val: Any) -> Optional[ODMElement]:
        """Return the first odmlib object where attribute ``attr`` equals ``val``.

        Searches within the child element(s) named ``obj_name`` on this element.
        For list elements (ODMListObject), returns the first match.
        For single elements (ODMObject), returns the element if it matches.

        :param obj_name: text name of the ODM Element (case sensitive)
        :param attr: text name of the ODM Element Attribute (case sensitive)
        :param val: attribute value to search for
        :return: first matching odmlib object, or None if not found
        """
        obj_list = getattr(self, obj_name)
        if isinstance(obj_list, list):
            for o in obj_list:
                if o.__dict__.get(attr) == val:
                    return o
            return None
        else:
            if obj_list.__dict__.get(attr) == val:
                return obj_list
            return None

    def find_all(self, obj_name: str, attr: str, val: Any) -> List[ODMElement]:
        """Return all odmlib objects where attribute ``attr`` equals ``val``.

        Like find(), but returns all matches instead of just the first.

        :param obj_name: text name of the ODM Element (case sensitive)
        :param attr: text name of the ODM Element Attribute (case sensitive)
        :param val: attribute value to search for
        :return: list of matching odmlib objects (empty list if no matches)
        """
        obj_list = getattr(self, obj_name)
        if isinstance(obj_list, list):
            return [o for o in obj_list if o.__dict__.get(attr) == val]
        else:
            if obj_list.__dict__.get(attr) == val:
                return [obj_list]
            return []

    def find_by(self, obj_name: str, **kwargs: Any) -> Optional[ODMElement]:
        """Return the first odmlib object matching all keyword criteria.

        A more ergonomic alternative to find() for multi-attribute lookups.

        :param obj_name: text name of the ODM Element (case sensitive)
        :param kwargs: attribute name=value pairs to match
        :return: first matching odmlib object, or None
        """
        obj_list = getattr(self, obj_name)
        if not isinstance(obj_list, list):
            obj_list = [obj_list]
        for o in obj_list:
            if all(o.__dict__.get(k) == v for k, v in kwargs.items()):
                return o
        return None

    def write_xml(self, odm_file: str, odm_writer: type = ODMWriter) -> None:
        """
        write the odmlib hierarchy as an XML file

        :param odm_file: string ODM filename and path
        :param odm_writer: object used to write the elementree XML to a file
        """
        odm_elem = self.to_xml()
        odm_writer = odm_writer()
        odm_writer.write_odm(odm_file, odm_elem)

    def write_json(self, odm_file: str) -> None:
        """
        write the odmlib hierarchy as a JSON file

        :param odm_file: string ODM filename and path
        """
        with open(odm_file, 'w') as outfile:
            json.dump(self.to_dict(), outfile)

    def build_oid_index(self) -> IDX.OIDIndex:
        idx = IDX.OIDIndex()
        self._init_oid_index(idx)
        return idx

    def _init_oid_index(self, idx):
        """
        for odmlib object, loads all OIDs into a dict that functions as an OID index

        :return oid_index: object that provices a dictionary lookup based on OID
        """
        odm_content = {attr: obj for attr, obj in self.__dict__.items() if attr not in ["_fields", "_attr_ns", "_elems", "_attrs"]}
        for attr, obj in odm_content.items():
            if isinstance(obj, ODMElement):
                obj._init_oid_index(idx)                    # element
            elif isinstance(obj, list):
                for o in obj:
                    o._init_oid_index(idx)                  # list of ELEMENTS
            else:
                if attr == "OID" or "OID" in attr:
                    idx.add_oid(obj, self)
        return

    def verify_oids(self, oid_checker: Any) -> bool:
        """
        checks all the OIDs for uniqueness and Def/Ref integrity; oid_checker throws a ValueError on failure

        :param oid_checker: object that performs that checks OID uniqueness and Def/Ref checks
        """
        self._init_oid_check(oid_checker)
        return oid_checker.check_oid_refs()

    def unreferenced_oids(self, oid_checker: Any) -> list:
        if not oid_checker.is_oids_verified():
            self.verify_oids(oid_checker)
        return oid_checker.check_unreferenced_oids()

    def _init_oid_check(self, oid_checker):
        """
        for odmlib object, loads all OIDs and checks them for uniqueness; throws an error if uniqueness check fails

        :param oid_checker: object used to check OIDs for uniqueness and Def/Ref check
        """
        odm_content = {attr: obj for attr, obj in self.__dict__.items() if attr not in ["_fields", "_attr_ns", "_elems", "_attrs"]}
        for attr, obj in odm_content.items():
            if isinstance(obj, ODMElement):
                obj._init_oid_check(oid_checker)                    # element
            elif isinstance(obj, list):
                for o in obj:
                    o._init_oid_check(oid_checker)                  # list of ELEMENTS
            else:
                # assumes consistency in OID naming. Exceptions: FileOID and PriorFileOID in ODM
                if attr == "OID":
                    oid_checker.add_oid(obj, self.__class__.__name__)
                elif "OID" in attr:
                    oid_checker.add_oid_ref(obj, attr)
        return

    def verify_conformance(self, validator: Any) -> Any:
        """
        uses validator object to check object for conformance with the model

        :param validator: object that validates the odmlib object against the model
        """
        doc_dict = self.to_dict()
        result = validator.check_conformance(doc_dict, type(self).__name__)
        return result

    def verify_order(self) -> bool:
        odm_content = {attr: obj for attr, obj in self.__dict__.items() if attr not in ["_fields", "_attr_ns", "_elems", "_attrs"]}
        obj_list = [key for key in list(self.__dict__.keys()) if key != "_content" and key not in self._attrs]
        elem_list = [elem for elem in self._elems if elem in obj_list]
        if obj_list != elem_list:
            raise OdmlibElementOrderError(
                f"The order of elements in {self.__class__.__name__} should be "
                f"{', '.join(key for key in self._elems.keys())}",
                element_type=self.__class__.__name__,
                hint="Use reorder_object() to fix element ordering automatically",
            )
        for attr, obj in odm_content.items():
            if isinstance(obj, ODMElement):
                obj.verify_order()
            elif isinstance(obj, list):
                for o in obj:
                    o.verify_order()
        return True

    def reorder_object(self) -> None:
        warnings.warn(
            f"{self.__class__.__name__} elements are being reordered to match the ODM specification. "
            "Use verify_order() before reorder_object() to understand the ordering issue.",
            OdmlibWarning,
            stacklevel=2,
        )
        ordered_obj = OrderedDict()
        for model_elem_name, model_elem_obj in self._elems.items():
            if model_elem_name in self.__dict__:
                obj = self.__dict__.pop(model_elem_name)
                ordered_obj[model_elem_name] = obj
        for name, elem in ordered_obj.items():
            self.__dict__[name] = elem

    def validate(self, collect_errors=False, oid_checker=None, conformance_checker=None):
        """Validate this element and all children.

        Args:
            collect_errors: If True, accumulate all errors and return them as a
                list instead of raising on the first failure. Defaults to False
                (fail-fast, existing behaviour).
            oid_checker: Optional OIDRef instance for OID validation.
            conformance_checker: Optional MetadataSchema instance for
                conformance validation.

        Returns:
            If ``collect_errors=False``: ``True`` (or raises on first error).
            If ``collect_errors=True``: list of :class:`~odmlib.exceptions.OdmlibError`
            instances (empty list means valid).
        """
        if not collect_errors:
            # Fail-fast — preserves existing behaviour exactly
            self.verify_order()
            if oid_checker:
                self.verify_oids(oid_checker)
            if conformance_checker:
                self.verify_conformance(conformance_checker)
            return True

        collector = ErrorCollector()

        try:
            self.verify_order()
        except OdmlibError as e:
            collector.add_error(e)

        if oid_checker:
            try:
                self.verify_oids(oid_checker)
            except OdmlibError as e:
                collector.add_error(e)

        if conformance_checker:
            try:
                self.verify_conformance(conformance_checker)
            except OdmlibError as e:
                collector.add_error(e)

        return collector.errors

