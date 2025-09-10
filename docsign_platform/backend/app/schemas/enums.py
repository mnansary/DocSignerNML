import enum

class FieldTypeEnum(str, enum.Enum):
    SIGNATURE = "signature"
    INITIAL = "initial"
    DATE = "date"
    TEXT = "text"
    CHECKBOX = "checkbox"