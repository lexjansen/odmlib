from __future__ import annotations
from typing import Any, Optional
from odmlib.exceptions import OdmlibRequiredAttributeError


class Descriptor:
    def __init__(self, name: Optional[str] = None, required: bool = False,
                 element_class: Optional[type] = None,
                 valid_values: Optional[list] = None,
                 namespace: str = "odm") -> None:
        self.name = name
        self.required = required
        self.element_class = element_class
        self.valid_values = valid_values if valid_values is not None else []
        self.namespace = namespace

    def __get__(self, instance: Any, cls: type) -> Any:
        if instance is None:
            return self
        elif (self.name not in instance.__dict__) and (self.name != self.__dict__["name"]):
            raise OdmlibRequiredAttributeError(
                f"Missing attribute or element {self.name} in {cls.__name__}",
                attribute=self.name,
                element_type=cls.__name__,
                hint=f"Attribute '{self.name}' is required when constructing {cls.__name__}",
            )
        else:
            if self.name not in instance.__dict__:
                if isinstance(self, list):
                    self.__set__(instance, [])
                else:
                    if self.element_class is None:
                        instance.__dict__[self.name] = self.element_class
                    else:
                        try:
                            instance.__dict__[self.name] = self.element_class()
                        except ValueError:
                            instance.__dict__[self.name] = None
            return instance.__dict__[self.name]

    def __set__(self, instance: Any, value: Any) -> None:
        instance.__dict__[self.name] = value

    def __delete__(self, instance: Any) -> None:
        del instance.__dict__[self.name]
