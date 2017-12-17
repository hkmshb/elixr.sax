import colander as col
from colander import Invalid
from elixr.base._compat import string_types



def _create_schema(schema_nodes):
    """Creates a Schema where root node is a Mapping SchemaNode.

    The outline for a sample definition for a schema_nodes is provided below,
    note that field_name and validator are mere placehoders here

    schema_nodes = {
        # required field
        'field_name': (col.Str,)

        # optional field
        'field_name': (col.Str, node.not_required)

        # required field with validator
        'field_name': (col.Str, node.validator(validator))

        # optional field with validator
        'field_name': (col.Int, node.not_required, node.validator(validator))
    }
    """
    schema = col.SchemaNode(col.Mapping())
    for name, node_def in schema_nodes.items():
        data_type = node_def[0]
        arg_funcs = node_def[1:]

        kw = {'name': name}
        for func in arg_funcs:
            kw = func(kw)

        node = col.SchemaNode(data_type(), **kw)
        schema.add(node)
    return schema


def validate(schema_nodes, data_dict):
    """Validates given `data_dict` using schema build from the provided
    `schema_nodes`.
    """
    data, errors = ({}, None)
    try:
        schema = _create_schema(schema_nodes)
        data = schema.deserialize(data_dict)
    except col.Invalid as ex:
        errors = ex.asdict()
    return (data, errors)


def one_of_enum(enum_type):
    """Checks to make sure that provided value is within set of values defined
    for the specifed enum_type.
    """
    class_name = enum_type.__class__.__name__

    def validator(node, value):
        if isinstance(value, string_types):
            expected = [str(et.name) for et in list(enum_type)]
            if value not in expected:
                err_msg_fmt = "%r is not a valid %s"
                raise Invalid(err_msg_fmt % (value, class_name))
            value = enum_type[value].value
            return value

        expected = [et.value for et in list(enum_type)]
        if value not in expected:
            err_msg_fmt = "%r is not a valid value for %s"
            raise Invalid(err_msg_fmt % (value, class_name))

        return value
