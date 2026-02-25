import odmlib.descriptor as DESC
import re
import odmlib.valueset as VS
import datetime
from validators import email as valid_email, url as valid_url
from pathvalidate import is_valid_filename
from odmlib.exceptions import OdmlibTypeError, OdmlibValidationError


class Typed(DESC.Descriptor):
    odm_type = object

    def __set__(self, instance, value):
        if (value is not None) and not isinstance(value, self.odm_type):
            raise OdmlibTypeError(
                f"Expected type {str(self.odm_type)} for {self.name} with value {str(value)}",
                attribute=self.name,
                expected_type=str(self.odm_type),
                actual_value=value,
                hint=f"Provide a value of type {self.odm_type.__name__}",
            )
        # often does not call parent, calls next on __mro__ which maybe influenced by multiple inheritance
        super().__set__(instance, value)


class Integer(DESC.Descriptor):
    def __set__(self, instance, value):
        # in XML integers are presented as strings e.g. OrderNumber="1"
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                raise OdmlibTypeError(
                    f"Expected string to convert to integer for {self.name} with a value {str(value)}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Provide a string that represents a valid integer, e.g., '42'",
                )
        odm_type = int
        if (value is not None) and not isinstance(value, odm_type):
            raise OdmlibTypeError(
                f"Expected type {str(odm_type)} for {self.name} with value {str(value)}",
                attribute=self.name,
                expected_type=str(odm_type),
                actual_value=value,
                hint="Provide an integer or a string that can be converted to an integer",
            )
        super().__set__(instance, value)


class Float(DESC.Descriptor):
    def __set__(self, instance, value):
        # in XML floats are presented as strings
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                raise OdmlibTypeError(
                    f"Expected string to convert to float for {self.name} with a value {str(value)}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Provide a string that represents a valid float, e.g., '3.14'",
                )
        # convert integer into a float (e.g. 1 to 1.0)
        elif isinstance(value, int):
            value = float(value)
        if (value is not None) and not isinstance(value, float):
            raise OdmlibTypeError(
                f"Expected type float for {self.name} with value {str(value)}",
                attribute=self.name,
                expected_type="float",
                actual_value=value,
                hint="Provide a float, integer, or a string convertible to a float",
            )
        super().__set__(instance, value)


class String(Typed):
    odm_type = str


class OID(Typed):
    odm_type = str


class OIDRef(Typed):
    odm_type = str


class Name(Typed):
    odm_type = str


class ID(Typed):
    odm_type = str


class IDRef(Typed):
    odm_type = str


class List(Typed):
    odm_type = list


class Dictionary(Typed):
    odm_type = dict


class Positive(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and value <= 0:
            raise OdmlibTypeError(
                f"Expected value > 0 for type Positive for {self.name}",
                attribute=self.name,
                actual_value=value,
                hint="Provide a positive number (> 0)",
            )
        super().__set__(instance, value)


class NonNegative(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and value < 0:
            raise OdmlibTypeError(
                f"Expected value >= 0 for type Non-negative for {self.name}",
                attribute=self.name,
                actual_value=value,
                hint="Provide a non-negative number (>= 0)",
            )
        super().__set__(instance, value)


class PositiveInteger(Integer, Positive):
    pass


class NonNegativeInteger(Integer, NonNegative):
    pass


class PositiveFloat(Float, Positive):
    pass


class NonNegativeFloat(Float, NonNegative):
    pass


class Sized(DESC.Descriptor):
    def __init__(self, *args, max_length, **kwargs):
        # pulls out named arg max_length and passes the remaining arguments along
        self.max_length = max_length
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if (value is not None) and (len(value) > self.max_length):
            raise OdmlibValidationError(
                f"{self.name} has a length of {len(value)} and exceeds the maximum length of "
                f"{self.max_length}",
                attribute=self.name,
                actual_value=value,
                hint=f"Shorten the value to {self.max_length} characters or fewer",
            )
        super().__set__(instance, value)


class SizedString(String, Sized):
    pass


class Regex(DESC.Descriptor):
    """ pattern matching """
    def __init__(self, *args, pat, **kwargs):
        # takes a pattern arg named pat and passes the remaining arguments along
        self.pat = re.compile(pat)
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if (value is not None) and not self.pat.match(value):
            raise OdmlibValidationError(
                f"{self.name} has an invalid string of {value}",
                attribute=self.name,
                actual_value=value,
                hint=f"Value must match pattern: {self.pat.pattern}",
            )
        super().__set__(instance, value)


class SizedRegexString(SizedString, Regex):
    pass


class DateTimeString(DESC.Descriptor):
    def __set__(self, instance, value):
        iso_pat = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
        pat = re.compile(iso_pat)
        if (value is not None) and (not pat.match(value)):
            raise OdmlibValidationError(
                f"Expected type datetime for {self.name}, found value {value}",
                attribute=self.name,
                actual_value=value,
                hint="Use ISO 8601 datetime format: YYYY-MM-DDTHH:MM:SS[.sss][Z|±HH:MM]",
            )
        super().__set__(instance, value)


class PartialDateTimeString(DESC.Descriptor):
    def __set__(self, instance, value):
        part_pat = r'^((([0-9][0-9][0-9][0-9])((-(([0][1-9])|([1][0-2])))((-(([0][1-9])|([1-2][0-9])|([3][0-1])))(T((([0-1][0-9])|([2][0-3]))((:([0-5][0-9]))(((:([0-5][0-9]))((\.[0-9]+)?))?)?)?((((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|(Z)))?))?)?)?))$'
        compiled_part_pat = re.compile(part_pat)
        if (value is not None) and (not compiled_part_pat.match(value)):
            raise OdmlibValidationError(
                f"Expected type PartialDateTime for {self.name}, found value {value}",
                attribute=self.name,
                actual_value=value,
                hint="Use a valid partial datetime format per ISO 8601",
            )
        super().__set__(instance, value)


class PartialDateString(DESC.Descriptor):
    def __set__(self, instance, value):
        if value and value.count('-') == 2:
            try:
                datetime.datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                raise OdmlibValidationError(
                    f"Expected type PartialDate for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use YYYY-MM-DD date format",
                )
        else:
            part_pat = r'^(([0-9][0-9][0-9][0-9])(-(([0][1-9])|([1][0-2])))?)$'
            compiled_part_pat = re.compile(part_pat)
            if (value is not None) and (not compiled_part_pat.match(value)):
                raise OdmlibValidationError(
                    f"Expected type PartialDate for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use YYYY or YYYY-MM format for partial dates",
                )
        super().__set__(instance, value)


class PartialTimeString(DESC.Descriptor):
    def __set__(self, instance, value):
        time_pat = r'^(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
        compiled_time_pat = re.compile(time_pat)
        part_pat = r'^((([0-1][0-9])|([2][0-3]))(:[0-5][0-9])?(((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|(Z))?)$'
        compiled_part_pat = re.compile(part_pat)
        if (value is not None) and (not (compiled_time_pat.match(value) or compiled_part_pat.match(value))):
            raise OdmlibValidationError(
                f"Expected type IncompleteTime for {self.name}, found value {value}",
                attribute=self.name,
                actual_value=value,
                hint="Use a valid partial time format per ISO 8601",
            )
        super().__set__(instance, value)


class IncompleteDateTimeString(DESC.Descriptor):
    def __set__(self, instance, value):
        inc_pat = r'^(((([0-9][0-9][0-9][0-9]))|-)-(((([0][1-9])|([1][0-2])))|-)-(((([0][1-9])|([1-2][0-9])|([3][0-1])))|-)T(((([0-1][0-9])|([2][0-3])))|-):((([0-5][0-9]))|-):((([0-5][0-9](\.[0-9]+)?))|-)((((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|Z|-))?)$'
        compiled_inc_pat = re.compile(inc_pat)
        if (value is not None) and (not compiled_inc_pat.match(value)):
            raise OdmlibValidationError(
                f"Expected type IncompleteDateTime for {self.name}, found value {value}",
                attribute=self.name,
                actual_value=value,
                hint="Use an ISO 8601 incomplete datetime, replacing unknown parts with '-'",
            )
        super().__set__(instance, value)


class IncompleteDateString(DESC.Descriptor):
    def __set__(self, instance, value):
        inc_pat = r'^(((([0-9][0-9][0-9][0-9]))|-)-(((([0][1-9])|([1][0-2])))|-)-(((([0][1-9])|([1-2][0-9])|([3][0-1])))|-))$'
        compiled_inc_pat = re.compile(inc_pat)
        if (value is not None) and (not compiled_inc_pat.match(value)):
            raise OdmlibValidationError(
                f"Expected type IncompleteDate for {self.name}, found value {value}",
                attribute=self.name,
                actual_value=value,
                hint="Use an ISO 8601 incomplete date, e.g., 'YYYY--DD'",
            )
        super().__set__(instance, value)


class IncompleteTimeString(DESC.Descriptor):
    def __set__(self, instance, value):
        inc_pat = r'^((((([0-1][0-9])|([2][0-3])))|-):((([0-5][0-9]))|-):((([0-5][0-9](\.[0-9]+)?))|-)((((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|Z|-))?)$'
        compiled_inc_pat = re.compile(inc_pat)
        if (value is not None) and (not compiled_inc_pat.match(value)):
            raise OdmlibValidationError(
                f"Expected type IncompleteTime for {self.name}, found value {value}",
                attribute=self.name,
                actual_value=value,
                hint="Use an ISO 8601 incomplete time, replacing unknown parts with '-'",
            )
        super().__set__(instance, value)


class DurationDateTimeString(DESC.Descriptor):
    def __set__(self, instance, value):
        dur_pat = r'^((\+ | -)?P([0-9]([0-9]+)?)W)$'
        pat = re.compile(dur_pat)
        if (value is not None) and (not pat.match(value)):
            raise OdmlibValidationError(
                f"Expected type DurationDateTime for {self.name}, found value {value}",
                attribute=self.name,
                actual_value=value,
                hint="Use ISO 8601 duration format, e.g., 'P1W' or 'P2W'",
            )
        super().__set__(instance, value)


class DateString(DESC.Descriptor):
    def __set__(self, instance, value):
        try:
            if value is not None:
                datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise OdmlibValidationError(
                f"Expected type date (YYYY-MM-DD) for {self.name}, found value {value}",
                attribute=self.name,
                actual_value=value,
                hint="Use YYYY-MM-DD date format",
            )
        super().__set__(instance, value)


class SASName(DESC.Descriptor):
    def __set__(self, instance, value):
        pat = re.compile("[A-Za-z_][A-Za-z0-9_]*$")
        if (value is not None) and (not pat.match(value) or len(value) > 8):
            raise OdmlibValidationError(
                f"{self.name} has an invalid sasName of {value}",
                attribute=self.name,
                actual_value=value,
                hint="SAS names must start with a letter or underscore, contain only "
                     "alphanumerics/underscores, and be 8 characters or fewer",
            )
        super().__set__(instance, value)


class SASFormat(DESC.Descriptor):
    def __set__(self, instance, value):
        pat = re.compile("[A-Za-z_$][A-Za-z0-9_.]*$")
        if (value is not None) and (not pat.match(value) or len(value) > 8):
            raise OdmlibValidationError(
                f"{self.name} has an invalid sasFormat of {value}",
                attribute=self.name,
                actual_value=value,
                hint="SAS formats must start with a letter, underscore, or '$', and be 8 characters or fewer",
            )
        super().__set__(instance, value)


class Email(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and (not valid_email(value)):
            raise OdmlibValidationError(
                f"{self.name} has an invalid email format of {value}",
                attribute=self.name,
                actual_value=value,
                hint="Provide a valid email address, e.g., 'user@example.com'",
            )
        super().__set__(instance, value)


class Url(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and (not valid_url(value)):
            raise OdmlibValidationError(
                f"{self.name} has an invalid url format of {value}",
                attribute=self.name,
                actual_value=value,
                hint="Provide a valid URL, e.g., 'https://example.com'",
            )
        super().__set__(instance, value)


class FileName(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and (not is_valid_filename(value)):
            raise OdmlibValidationError(
                f"{self.name} has an invalid fileName of {value}",
                attribute=self.name,
                actual_value=value,
                hint="Provide a valid filename without illegal characters",
            )
        super().__set__(instance, value)


class ValidValues(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None):
            # Pass instance for automatic version detection
            valid_values = VS.ValueSet.value_set(
                type(instance).__name__ + "." + self.name,
                instance=instance
            )
            if value not in valid_values:
                raise OdmlibTypeError(
                    f"Invalid value {value} for {self.name}. Value must be one of "
                    f"{', '.join(valid_values)}",
                    attribute=self.name,
                    actual_value=value,
                    hint=f"Valid values are: {', '.join(valid_values)}",
                )
        super().__set__(instance, value)


class ExtendedValidValues(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and value not in self.valid_values:
            raise OdmlibTypeError(
                f"Invalid value {value} for {self.name}. Value must be one of "
                f"{', '.join(self.valid_values)}",
                attribute=self.name,
                actual_value=value,
                hint=f"Valid values are: {', '.join(self.valid_values)}",
            )
        super().__set__(instance, value)


class ValueSetString(ValidValues, String):
    pass


class ODMObject(DESC.Descriptor):
    def __init__(self, *args, element_class,  **kwargs):
        self.obj_type = element_class
        kwargs["element_class"] = element_class
        self.namespace = kwargs.get("namespace", "")
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, self.obj_type) and not isinstance(value, list):
            raise OdmlibTypeError(
                f"The {self.name} object must be of type {self.obj_type}",
                attribute=self.name,
                expected_type=str(self.obj_type),
                actual_value=value,
                hint=f"Assign an instance of {self.obj_type.__name__}",
            )
        super().__set__(instance, value)


class ODMListObject(ODMObject, list):
    def __set__(self, instance, value):
        if isinstance(value, list):
            for obj in value:
                if not isinstance(obj, self.obj_type):
                    raise OdmlibTypeError(
                        f"Every {self.name} object in the list must be of type {self.obj_type}",
                        attribute=self.name,
                        expected_type=str(self.obj_type),
                        actual_value=obj,
                        hint=f"Each element in {self.name} must be of type {self.obj_type.__name__}",
                    )
        else:
            raise OdmlibTypeError(
                f"The {self.name} object must be a list",
                attribute=self.name,
                actual_value=value,
                hint=f"Assign a list of {self.obj_type.__name__} objects",
            )
        super().__set__(instance, value)
