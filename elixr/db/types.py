import uuid
from enum import Enum
from sqlalchemy.types import TypeDecorator, CHAR, Integer
from sqlalchemy.dialects.postgresql import UUID



class UUID(TypeDecorator):
    """Platform-independent UUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(32), storing as stringified
    hex values.

    # hint: adapted from sqlalchemy docs on 'Backend-agnostic GUID Type'
    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value)


class Choice(TypeDecorator):
    """Choice offers way of having fixed set of choices for given column. It 
    works with :mod:`enum` in the standard library of Python 3.4+ (the enum34_
    backported package on PyPi is compatible too for ``< 3.4``).

    # hint: adapted from sqlalchemy_utils ChoiceType.
    """
    impl = Integer
    
    def __init__(self, enum_class, *args, **kwargs):
        super(Choice, self).__init__(*args, **kwargs)
        self.enum_class = enum_class
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return self.enum_class(value).value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return self.enum_class(value)
