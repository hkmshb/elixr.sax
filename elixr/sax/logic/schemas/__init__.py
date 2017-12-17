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
        prefix + 'state_id': (col.Str, node.optional()),
        'postal_code': (UUID, node.optional()),
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
        'state_origin_id': (UUID, node.optional(), node.validator(col.uuid)),
        'nationality_id': (UUID, node.optional(), node.validator(col.uuid))
    }
    schema.update(_default_party_schema())
    return schema


def default_organization_type_schema():
    return {
        'name': (col.Str,),
        'title': (col.Str,)
    }


def default_organization_schema():
    schema = {
        'code': (col.Str,),
        'short_name': (col.Str, node.optional()),
        'description': (col.Str, node.optional()),
        'date_established': (col.Date, node.optional()),
        'website_url': (col.Str, node.optional(), node.validator(col.url)),
        'parent_id': (UUID, node.optional(), node.validator(col.uuid)),
        'type_id': (UUID, node.optional(), node.validator(col.uuid))
    }
    schema.update(_default_party_schema())
    schema.update(coordinate_mixin_schema())
    return schema
