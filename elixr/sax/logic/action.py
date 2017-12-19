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


def organization_type_create(context, data_dict):
    """Create and return an organization type.
    """
    assert 'dbsession' in context
    model = party.OrganizationType
    dbsession = context['dbsession']

    # extensive checks required only if not to allow_multiroot
    allow_multiroot = context.get('allow_multiroot', True)
    if not allow_multiroot:
        is_root = to_bool(data_dict.get('is_root', False))
        if is_root:
            # check that no root organization type already exist
            try:
                query = dbsession.query(model)
                found = query.filter(model.is_root == True).one_or_none()
            except exc.MultipleResultsError:
                err_msg = ('Single root Organization type expected however '
                           'multiple root types already defined')
                raise logic.MultipleResultsError(err_msg)

            if found:
                err_msg = ('Single root Organization type expected and one '
                           'already exist')
                raise logic.MultipleResultsError(err_msg)

    schema = schemas.default_organization_type_schema()
    return _entity_create(dbsession, model, schema, data_dict)


def organization_create(context, data_dict):
    """Create and return an organization.
    """
    assert 'dbsession' in context
    assert 'type_id' in data_dict
    dbsession = context['dbsession']
    model = party.Organization

    # retrieve org type to know if root or non-root to be created 
    type_id = data_dict['type_id']
    if not type_id:
        raise logic.ValidationError({'type_id': 'Required'})

    org_type = organization_type_show(dbsession, {'id': type_id})

    # extensive checks required only if not to allow_multiroot
    allow_multiroot = context.get('allow_multiroot', True)
    if not allow_multiroot and org_type.is_root:
        # check that no root organization already exist
        try:
            query = dbsession.query(model)
            found = query.filter(model.parent_id.is_(None)).one_or_none()
        except exc.MultipleResultsError:
            err_msg = ('Single root Organization expected however multiple '
                       'roots already deifned.')
            raise logic.MultipleResultsError(err_msg)

        if found:
            err_msg = ('Single Organization type expedted and one already '
                       'exist')
            raise logic.MultipleResultsError(err_msg)

    schema = schemas.default_organization_schema(org_type.is_root)
    return _entity_create(dbsession, model, schema, data_dict)


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
    return _entity_show(dbsession, party.Organization, data_dict)


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
