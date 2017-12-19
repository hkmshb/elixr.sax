import pytest
from elixr.sax.logic import action, schemas, validators as _val
from elixr.sax import logic, address as addr, party
from elixr.sax.logic import action



class TestBase(object):

    def _get_country_dict(self, code='NG', name='Nigeria'):
        return {'code': code, 'name': name}

    def _get_address_dict(self, is_mixin=True):
        prefix = 'addr_' if is_mixin else ''
        return {
            prefix + 'raw': 'Addr Raw', prefix + 'street': 'Addr Street',
            prefix + 'town': 'Addr Town', prefix + 'landmark': 'Addr Landmark',
            'postal_code': '10001'
        }

    def _get_person_dict(self, name='John', last_name='Doe', gender='MALE'):
        return {
            'title':'Mr', 'name':name, 'last_name':last_name, 'gender':gender,
            'date_born':'2017-12-01', 'marital_status':'SINGLE'
        }

    def _get_organization_type_dict(self, name='org-type', title='Org Type',
                                    is_root=False):
        return {
            'name': name, 'title': title, 'is_root': is_root
        }

    def _get_organization_dict(self, code='01', name='Organization', type_id=None,
                               parent_id=None):
        return {
            'code': code, 'name': name, 'type_id': type_id, 'parent_id': parent_id
        }

    def _get_organization_type(self, db, name='org-type', title='Org Type',
                               is_root=False, commit=True):
        data_dict = self._get_organization_type_dict(name, title, is_root)
        org_type = party.OrganizationType(**data_dict)
        if commit:
            db.add(org_type)
            db.commit()
        return org_type

    def _get_organization(self, db, code='01', name='Organization', type_id=None,
                          parent_id=None, commit=True):
        data_dict = self._get_organization_dict(code, name, type_id, parent_id)
        if type_id is None:
            org_type = self._get_organization_type(db)
            data_dict['type_id'] = str(org_type.uuid)

        org = party.Organization(**data_dict)
        if commit:
            db.add(org)
            db.commit()
        return org



class TestEntityCreateAction(TestBase):

    @pytest.mark.parametrize('field,value', [
        ('name', 'Nigeria'), ('code', 'NG') ])
    def test_country_creation_fails_wo_required_field(self, db, field, value):
        data_dict = {field: value}
        with pytest.raises(logic.ValidationError):
            action.country_create(db, data_dict)

    def test_country_creation_passes_for_valid_fields(self, db):
        data_dict = self._get_country_dict()
        ng = action.country_create(db, data_dict)
        assert ng and ng.id and ng.uuid
        assert ng.name == 'Nigeria'

    @pytest.mark.parametrize('field,value', [
        ('name','Kano'), ('code','KN') ])
    def test_state_creation_fails_wo_required_fields(self, db, field, value):
        data_dict = {field: value}
        with pytest.raises(logic.ValidationError):
            action.state_create(db, data_dict)

    def test_state_creation_passes_for_valid_fields(self, db):
        ng = action.country_create(db, self._get_country_dict())
        data_dict = {'code':'KN', 'name':'Kano', 'country_id': str(ng.uuid)}
        kn = action.state_create(db, data_dict)
        assert kn and kn.id and kn.uuid
        assert kn.name == 'Kano'

    def test_address_creation_passes_for_valid_fields(self, db):
        ## ADDRESS
        data_dict = self._get_address_dict(False)
        data_dict['is_addr_mixin'] = False
        addr = action.address_create(db, data_dict)
        assert addr and addr.id and addr.uuid

        ## ADDRESS MIXIN as part of Organization
        data_dict = self._get_address_dict(True)
        data_dict.update(self._get_organization_dict())

        # organization type required to create organization
        org_type = party.OrganizationType(**self._get_organization_type_dict())
        data_dict['type'] = org_type

        org = party.Organization(**data_dict)
        db.add(org)
        db.commit()

        assert org and org.id and org.uuid
        assert org.addr_street == 'Addr Street'
        assert org.addr_town == 'Addr Town'
        assert org.addr_landmark == 'Addr Landmark'

    def test_person_creation_passes_for_valid_fields(self, db):
        data_dict = self._get_person_dict()
        person = action.person_create(db, data_dict)
        assert person and person.id and person.uuid
        assert person.name == 'John' and person.last_name == 'Doe'
        assert person.gender == party.Gender.MALE \
           and person.marital_status == party.MaritalStatus.SINGLE

    def test_organization_type_creation_passes_for_valid_fields(self, db):
        data_dict = self._get_organization_type_dict()
        org_type = action.organization_type_create({'dbsession': db}, data_dict)
        assert org_type and org_type.id and org_type.uuid
        assert org_type.name == 'org-type' \
           and org_type.title == 'Org Type'

    def test_organization_type_creation_fails_for_multi_isroot_record_when_not_allow_multiroot(self, db):
        # existing `is_root` org_type required
        db.add(party.OrganizationType(**self._get_organization_type_dict(is_root=True)))
        with pytest.raises(logic.MultipleResultsError):
            data_dict = self._get_organization_type_dict(name='org-type2', is_root=True)
            context = {'dbsession': db, 'allow_multiroot': False}
            action.organization_type_create(context, data_dict)

    def test_organization_type_creation_passes_for_multi_isroot_record_when_allow_multiroot(self, db):
        # existing `is_root` org_type required
        db.add(party.OrganizationType(**self._get_organization_type_dict(is_root=True)))
        data_dict = self._get_organization_type_dict(name='org-type2', is_root=True)
        context = {'dbsession': db, 'allow_multiroot': True}
        org_type = action.organization_type_create(context, data_dict)
        assert org_type and org_type.id and org_type.uuid
        assert db.query(party.OrganizationType).count() == 2

    def test_organization_type_creation_passes_for_mutliple_non_isroot(self, db):
        data_dict = self._get_organization_type_dict(name='org-type-1', is_root=False)
        db.add(party.OrganizationType(**data_dict))
        db.commit()

        data_dict2 = self._get_organization_type_dict(name='org-type-2')
        action.organization_type_create({'dbsession': db}, data_dict2)
        assert db.query(party.OrganizationType).count() == 2

    def test_organization_creation_fails_without_type(self, db):
        data_dict = self._get_organization_dict()
        with pytest.raises(logic.ValidationError):
            action.organization_create({'dbsession': db}, data_dict)

    def test_organization_creation_passes_for_isroot_type_when_no_root_exists(self, db):
        org_type = party.OrganizationType(**self._get_organization_type_dict(is_root=True))
        db.add(org_type)
        db.flush()

        data_dict = self._get_organization_dict(type_id=str(org_type.uuid))
        print(data_dict)
        org = action.organization_create({'dbsession': db}, data_dict)
        assert org and org.id and org.uuid
        assert org.code == '01' and org.name == 'Organization'

    def test_organization_creation_fails_for_isroot_type_with_multiroot_false(self, db):
        org_type = self._get_organization_type(db, is_root=True)

        # first root organization
        data_dict = self._get_organization_dict(type_id=str(org_type.uuid))
        context = {'dbsession': db, 'allow_multiroot': False}
        org = action.organization_create(context, data_dict)
        assert org and org.id and org.uuid

        with pytest.raises(logic.MultipleResultsError):
            # second root organization in a non-multiroot setting
            data_dict = self._get_organization_dict(code='02', name='Org2')
            data_dict['type_id'] = str(org_type.uuid)
            action.organization_create(context, data_dict)

    def test_organization_creation_passes_for_isroot_type_with_multiroot_true(self, db):
        org_type = self._get_organization_type(db, is_root=True)

        # first root organization
        data_dict = self._get_organization_dict(type_id=str(org_type.uuid))
        context = {'dbsession': db, 'allow_multiroot': True}
        org = action.organization_create(context, data_dict)
        assert org and org.id and org.uuid

        # second root organization in a multiroot setting
        data_dict = self._get_organization_dict(code='02', name='Org2')
        data_dict['type_id'] = str(org_type.uuid)
        org2 = action.organization_create(context, data_dict)
        assert org2 and org2.id and org2.uuid
        assert db.query(party.OrganizationType).count() == 1
        assert db.query(party.Organization).count() == 2


class TestEntityShowAction(TestBase):

    def test_retrieving_non_existing_country_raise_notfound(self, db):
        with pytest.raises(logic.NotFoundError):
            action.country_show(db, {'id': 1})

    def test_can_retrieve_existing_country(self, db):
        country = addr.Country(code='NG', name='Nigeria')
        db.add(country)
        db.commit()

        found = action.country_show(db, {'id': country.uuid})
        assert found and found.id and found.uuid
        assert found.code == 'NG' \
           and found.name == 'Nigeria'

    def test_retrieving_non_existing_state_raise_notfound(self, db):
        with pytest.raises(logic.NotFoundError):
            action.state_show(db, {'id': 1})

    def test_can_retrieve_existing_state(self, db):
        country = addr.Country(code='NG', name='Nigeria')
        state = addr.State(code='KN', name='Kano', country=country)
        db.add_all([country, state])
        db.commit()

        found = action.state_show(db, {'id': state.uuid})
        assert found and found.id and found.uuid
        assert found.code == 'KN' \
           and found.name == 'Kano'

    def test_retrieving_non_existing_address_raise_notfound(self, db):
        with pytest.raises(logic.NotFoundError):
            action.address_show(db, {'id': 1})

    def test_can_retrieve_existing_address(self, db):
        addy = addr.Address(raw='Addr Raw', street='Addr Street', town='Addr Town')
        db.add(addy)
        db.commit()

        found = action.address_show(db, {'id': addy.uuid})
        assert found and found.id and found.uuid
        assert found.raw == 'Addr Raw' \
           and found.street == 'Addr Street' \
           and found.town == 'Addr Town'

    def test_retrieving_non_existing_organization_type_raise_notfound(self, db):
        with pytest.raises(logic.NotFoundError):
            action.organization_type_show(db, {'id': 1})

    def test_can_retrieve_existing_organization_type(self, db):
        org_type = self._get_organization_type(db)
        found = action.organization_type_show(db, {'id': org_type.uuid})
        assert found and found.id and found.uuid
        assert found.name == 'org-type' \
           and found.title == 'Org Type'

    def test_retrieving_non_existing_organization_raise_notfound(self, db):
        with pytest.raises(logic.NotFoundError):
            action.organization_show(db, {'id': 1})

    def test_can_retrieve_existing_organization(self, db):
        organization = self._get_organization(db)
        found = action.organization_show(db, {'id': organization.uuid})
        assert found and found.id and found.uuid
        assert found.code == '01' \
           and found.name == 'Organization'


class TestEntityUpdateAction(object):

    def _get_country(self, db, commit=True):
        entity = addr.Country(code='ng', name='Nigeria')
        if commit:
            db.add(entity)
            db.commit()
        return entity

    def _get_state(self, db, country=None, commit=True):
        if not country:
            country = self._get_country(db, commit=False)

        entity = addr.State(code='kn', name='Kano', country=country)
        if commit:
            db.add(entity)
            db.commit()
        return entity

    def _get_organization_type(self, db, commit=True):
        org_type = party.OrganizationType(name='org-type', title='Title')
        if commit:
            db.add(org_type)
            db.commit()
        return org_type

    def _get_organization(self, db, type=None, commit=True):
        if not type:
            type = self._get_organization_type(db, False)

        org = party.Organization(code='01', name='org', type=type)
        if commit:
            db.add(org)
            db.commit()
        return org

    @pytest.mark.parametrize('field,value', [
        ('code', 'gh'), ('name', 'Ghana'), 
        ('code', 'sg'), ('name', 'Senegal') ])
    def test_country_update_fails_wo_required_fields(self, db, field, value):
        entity = self._get_country(db)
        with pytest.raises(logic.ValidationError):
            action.country_update(db, {'id': entity.uuid, field: value})

    def test_country_update_passes_for_valid_fields(self, db):
        entity = self._get_country(db)
        code, name = (entity.code, entity.name)
        rvalue = action.country_update(db, {
            'id': entity.uuid, 'code': 'gh', 'name': 'Ghana'
        })
        assert rvalue and rvalue.id and rvalue.uuid
        assert rvalue.code != code \
           and rvalue.name != name

    @pytest.mark.parametrize('field,value', [
        ('code', 'so'), ('name', 'Sokoto'), ('country_id', 1) ])
    def test_state_update_fails_wo_required_fields(self, db, field, value):
        entity = self._get_state(db)
        with pytest.raises(logic.ValidationError):
            action.state_update(db, {'id': entity.uuid, field: value})

    def test_state_update_passes_for_valid_fields(self, db):
        entity = self._get_state(db)
        code, name = (entity.code, entity.name)
        rvalue = action.state_update(db, {
            'id': entity.uuid, 'code': 'kd', 'name': 'Kaduna',
            'country_id': str(entity.country.uuid)
        })
        assert rvalue and rvalue.id and rvalue.uuid
        assert rvalue.code != code \
           and rvalue.name != name

    @pytest.mark.parametrize('field,value', [
        ('name', 'org-type'), ('title', 'Org Title') ])
    def test_organization_type_upate_fails_wo_required_fields(self, db, field, value):
        org_type = self._get_organization_type(db)
        with pytest.raises(logic.ValidationError):
            action.organization_type_update(db, {'id': org_type.uuid, field: value})

    def test_organization_type_update_passes_for_valid_fields(self, db):
        org_type = self._get_organization_type(db)
        name, title = (org_type.name, org_type.title)
        rvalue = action.organization_type_update(db, {
            'id': org_type.uuid, 'name': 'org-type-2', 'title': 'Org Title 2'
        })
        assert rvalue and rvalue.id and rvalue.uuid
        assert rvalue.name != name \
           and rvalue.title != title

    @pytest.mark.parametrize('field,value', [
        ('code', '01'), ('name', 'Organization') ])
    def test_organization_update_fails_wo_required_fields(self, db, field, value):
        org_type = self._get_organization_type(db, False)
        org = self._get_organization(db, org_type, True)
        with pytest.raises(logic.ValidationError):
            action.organization_update(db, {'id': org.uuid, field: value})

    # def test_organization_update_passes_for_valid_fields(self, db):
    #     org_type = self._get_organization_type(db, False)
    #     org = self._get_organization(db, org_type, True)
    #     code, name = (org.code, org.name)
        
    #     org2 = party.Organization(code='91', name='Org91', type=org_type)
    #     db.add(org2)
    #     db.flush()

    #     rvalue = action.organization_update(db, {
    #         'is_root': True, 'id': org.uuid, 'code': '017', 'type_id': str(org_type.uuid),
    #         'name': 'Organization-017', 'parent_id': str(org2.uuid)
    #     })
    #     assert rvalue and rvalue.id and rvalue.uuid
    #     assert rvalue.code != code \
    #        and rvalue.title != title
