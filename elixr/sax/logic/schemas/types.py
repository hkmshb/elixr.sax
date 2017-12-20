import uuid
from colander import SchemaType, Invalid, null
from elixr.base._compat import string_types



class node:
    """Define helper functions which builds other arguments necessary to
    properly configure a SchemaNode during its creation. Each function
    updates a dictionary with a new key; this dictionary is passed to the
    SchemaNode initializer.
    """

    @staticmethod
    def optional(default=None):
        """Indicates that a SchemaNode is optional during deserialization.
        It updates the initializer dictionary with a `missing` key, and a
        value as specified by the default parameter.
        """
        def func(kw):
            kw['missing'] = default
            return kw
        return func

    @staticmethod
    def validator(validator):
        """Adds validators to a SchemaNode. It updates the initializer
        dictionary with a `validator` key, and a value as specified by
        the validator parameter.
        """
        def func(kw):
            if validator:
                kw['validator'] = validator
            return kw
        return func


class UUID(SchemaType):

    def serialize(self, node, appstruct):
        if appstruct is null:
            return null
        if not isinstance(appstruct, uuid.UUID):
            raise Invalid(node, '%r is not a UUID' % appstruct)
        return appstruct and 'true' or 'false'

    def deserialize(self, node, cstruct):
        if cstruct in (null, None):
            return null
        if not isinstance(cstruct, string_types):
            raise Invalid(node, '%r is not a string' % cstruct)
        try:
            value = uuid.UUID(cstruct)
        except ValueError:
            value = None
        return value


class ENUM(SchemaType):

    def __init__(self, enum_type):
        self.enum = enum_type

    def __call__(self):
        return self

    def serialize(self, node, appstruct):
        if appstruct is null:
            return null

        if not isinstance(appstruct, self.enum):
            args = (appstruct, self.enum.__class__.__name__)
            raise Invalid(node, '%r is not a valid %s' % args)
        return str(appstruct.name)

    def deserialize(self, node, cstruct):
        if cstruct is null:
            return null

        if not isinstance(cstruct, string_types):
            args = (cstruct, self.enum.__class__.__name__)
            raise Invalid(node, '%r is not a valid %s string' % args)
        try:
            value = self.enum[cstruct]
        except ValueError:
            value = None
        return value
