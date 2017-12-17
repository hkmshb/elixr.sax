"""API functions with business logic for creating objects within Elixr.Sax.
"""
import colander
from sqlalchemy import exc
from elixr.base import to_bool
from elixr.sax import logic
from . import schemas, validators as _val
from .. import address as addr, party


## ++++++++++++++
## ENTITY CREATION

def _entity_create(dbsession, model, schema, data_dict):
    """Create and return an entity of type specified by model.
    """
    # validate entity
    data, errors = _val.validate(schema, data_dict)
    if errors:
        raise logic.ValidationError(errors)

    # perform entity creation
    entity = None
    try:
        entity = model(**data)
        dbsession.add(entity)
        dbsession.flush()
    except exc.IntegrityError as ex:
        raise logic.ActionError(str(ex))

    return entity


def country_create(dbsession, data_dict):
    """Create and return a country.
    """
    schema = schemas.default_country_schema()
    return _entity_create(dbsession, addr.Country, schema, data_dict)


def state_create(dbsession, data_dict):
    """Create and return a state.
    """
    schema = schemas.default_state_schema()
    return _entity_create(dbsession, addr.State, schema, data_dict)


def address_create(dbsession, data_dict):
    """Create and return an address.
    """
    is_mixin = to_bool(data_dict.get('is_addr_mixin', 'true'))
    schema = schemas.default_address_schema(is_mixin)
    return _entity_create(dbsession, addr.Address, schema, data_dict)


def person_create(dbsession, data_dict):
    """Create and return a person.
    """
    schema = schemas.default_person_schema()
    return _entity_create(dbsession, party.Person, schema, data_dict)


def organization_create(dbsession, data_dict):
    """Create and return an organization.
    """
    schema = schemas.default_organization_schema()
    return _entity_create(dbsession, party.Organization, schema, data_dict)
