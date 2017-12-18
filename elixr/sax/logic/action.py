"""API functions with business logic for creating objects within Elixr.Sax.
"""
import colander
from sqlalchemy import exc, orm
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


def organization_type_create(dbsession, data_dict):
    """Create and return an organization type.
    """
    schema = schemas.default_organization_type_schema()
    return _entity_create(dbsession, party.OrganizationType,
                          schema, data_dict)


def organization_create(dbsession, data_dict):
    """Create and return an organization.
    """
    is_root = to_bool(data_dict.pop('is_root', False))
    multi_root = to_bool(data_dict.pop('multi_root', False))
    if is_root and not multi_root:
        # ensure no other root organization exists
        try:
            show_dict = {'is_root': is_root, 'multi_root': multi_root}
            org = organization_show(dbsession, show_dict)
            if org is not None:
                err_msg = 'Root organization already exist'
                raise logic.MultipleOrganizationError(err_msg)
        except logic.NotFoundError:
            # good thing org doesn't already exists
            pass

    schema = schemas.default_organization_schema(is_root)
    return _entity_create(dbsession, party.Organization, schema, data_dict)


## ++++++++++++++++
## ENTITY READ/SHOW

def _entity_show(dbsession, model, data_dict):
    """Returns the details of an entity of type specified in model.
    """
    assert 'id' in data_dict
    entity = model.get(dbsession, data_dict.get('id'))
    if entity is None:
        raise logic.NotFoundError()
    return entity


def country_show(dbsession, data_dict):
    """Returns the details of a country.
    """
    return _entity_show(dbsession, addr.Country, data_dict)


def state_show(dbsession, data_dict):
    """Returns the details of a state.
    """
    return _entity_show(dbsession, addr.State, data_dict)


def address_show(dbsession, data_dict):
    """Returns the details of an address.
    """
    return _entity_show(dbsession, addr.Address, data_dict)


def person_show(dbsession, data_dict):
    """Returns the details of a person.
    """
    return _entity_show(dbsession, party.Person, data_dict)


def organization_show(dbsession, data_dict):
    """Returns the details of an organization.
    """
    model = party.Organization
    multi_root = to_bool(data_dict.get('multi_root', False))
    if 'id' not in data_dict:
        if multi_root:
            err_msg = 'Id of Organization to show is required.'
            raise logic.ActionError(err_msg)

        try:
            query = dbsession.query(model)
            found = query.filter(model.parent_id.is_(None)).one_or_none()
            return found
        except orm.exc.MutipleResultsFound:
            raise logic.MultipleOrganizationError()
    return _entity_show(dbsession, model, data_dict)


def organization_type_show(dbsession, data_dict):
    """Returns the details of an organization type.
    """
    return _entity_show(dbsession, party.OrganizationType, data_dict)


## +++++++++++++
## ENTITY UPDATE

def _entity_update(dbsession, show_func, schema, data_dict):
    """Updates and returns an existing entity of type specified by model.
    """
    # record to update must exist
    assert 'id' in data_dict
    found = show_func(dbsession, data_dict)

    # validate entity
    data, errors = _val.validate(schema, data_dict)
    if errors:
        raise logic.ValidationError(errors)

    # perform entity update
    try:
        for field_name, value in data.items():
            setattr(found, field_name, value or None)

        dbsession.flush()
    except exc.IntegrityError as ex:
        raise logic.ActionError(str(ex))

    return found


def country_update(dbsession, data_dict):
    schema = schemas.default_country_schema()
    return _entity_update(dbsession, country_show, schema, data_dict)


def state_update(dbsession, data_dict):
    schema = schemas.default_state_schema()
    return _entity_update(dbsession, state_show, schema, data_dict)


def address_update(dbsession, data_dict):
    schema = schemas.default_address_schema()
    return _entity_update(dbsession, address_show, schema, data_dict)


def organization_type_update(dbsession, data_dict):
    schema = schemas.default_organization_type_schema()
    return _entity_update(dbsession, organization_type_show, schema, data_dict)


def organization_update(dbsession, data_dict):
    schema = schemas.default_organization_schema()
    return _entity_update(dbsession, organization_show, schema, data_dict)
