# package: elixr.sax.logic.schema
import colander as col
from .types import node, ENUM, UUID
from .. import validators as _val



## ADDRESS SCHEMAS

def default_country_schema():
    return {
        'code': (col.Str,),
        'name': (col.Str,)
    }


def default_state_schema():
    schema = {
        'country_id': (UUID,)
    }
    schema.update(default_country_schema())
    return schema


def default_address_schema(is_mixin=True):
    prefix = 'addr_' if is_mixin else ''
    return {
        prefix + 'raw': (col.Str, node.optional()),
        prefix + 'street': (col.Str, node.optional()),
        prefix + 'town': (col.Str, node.optional()),
        prefix + 'landmark': (col.Str, node.optional()),
        prefix + 'state_id': (UUID, node.optional()),
        'postal_code': (col.Str, node.optional()),
    }


def coordinate_mixin_schema():
    return {
        'latitude': (col.Float, node.optional()),
        'longitude': (col.Float, node.optional()),
        'altitude': (col.Float, node.optional()),
        'gps_error': (col.Float, node.optional())
    }


def locatable_mixin_schema():
    schema = default_address_schema()
    schema.update(coordinate_mixin_schema())
    return schema


## PARTY SCHEMAS

def _default_party_schema():
    schema = {
        'name': (col.Str,)
    }
    schema.update(default_address_schema())
    return schema


def default_person_schema():
    from ...party import Gender, MaritalStatus
    schema = {
        'title': (col.Str, node.optional()),
        'middle_name': (col.Str, node.optional()),
        'last_name': (col.Str, node.optional()),
        'gender': (ENUM(Gender), node.optional()),
        'date_born': (col.Date, node.optional()),
        'marital_status': (ENUM(MaritalStatus), node.optional()),
        'state_origin_id': (UUID, node.optional()),
        'nationality_id': (UUID, node.optional())
    }
    schema.update(_default_party_schema())
    return schema


def default_organization_type_schema():
    return {
        'name': (col.Str,),
        'title': (col.Str,),
        'is_root': (col.Bool, node.optional()),
    }


def default_organization_schema(for_root=False):
    schema = {
        'code': (col.Str,),
        'short_name': (col.Str, node.optional()),
        'description': (col.Str, node.optional()),
        'type_id': (UUID,),
        'parent_id': (UUID,),
        'date_established': (col.Date, node.optional()),
        'website_url': (col.Str, node.optional(), node.validator(col.url)),
    }
    if for_root:
        del schema['parent_id']

    schema.update(_default_party_schema())
    schema.update(coordinate_mixin_schema())
    return schema
