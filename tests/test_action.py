import pytest
from elixr.sax.logic import action, schemas, validators as _val
from elixr.sax import logic, address as addr, party
from elixr.sax.logic import action


class TestEntityCreateAction(object):

    def _get_address(self, is_mixin=True):
        prefix = 'addr_' if is_mixin else ''
        return {
            prefix + 'raw': 'Addr Raw', prefix + 'street': 'Addr Street',
            prefix + 'town': 'Addr Town', prefix + 'landmark': 'Addr Landmark',
            'postal_code': '10001'
        }

    def _get_person(self):
        return {
            'title':'Mr', 'name':'John', 'last_name':'Doe', 'gender':'MALE',
            'date_born':'2017-12-01', 'marital_status':'SINGLE'
        }

    @pytest.mark.parametrize('field,value', [
        ('name', 'Nigeria'), ('code', 'NG') ])
    def test_country_creation_fails_wo_required_field(self, db, field, value):
        data_dict = {field: value}
        with pytest.raises(logic.ValidationError):
            action.country_create(db, data_dict)

    def test_country_creation_passes_for_valid_fields(self, db):
        data_dict = {'code':'NG', 'name':'Nigeria'}
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
        ng = action.country_create(db, {'code':'NG', 'name':'Nigeria'})
        data_dict = {'code':'KN', 'name':'Kano', 'country_id': str(ng.uuid)}
        kn = action.state_create(db, data_dict)
        assert kn and kn.id and kn.uuid
        assert kn.name == 'Kano'

    def test_address_creation_passes_for_valid_fields(self, db):
        ## ADDRESS
        data_dict = self._get_address(False)
        data_dict['is_addr_mixin'] = False
        addr = action.address_create(db, data_dict)
        assert addr and addr.id and addr.uuid

        ## ADDRESS MIXIN as part of Organization
        data_dict = self._get_address(True)
        data_dict.update({
            'code':'org', 'name':'Org Type', 'is_root': True
        })
        org = action.organization_create(db, data_dict)
        assert org and org.id and org.uuid
        assert org.addr_street == 'Addr Street'
        assert org.addr_town == 'Addr Town'
        assert org.addr_landmark == 'Addr Landmark'

    def test_person_creation_passes_for_valid_fields(self, db):
        data_dict = self._get_person()
        person = action.person_create(db, data_dict)
        assert person and person.id and person.uuid
        assert person.name == 'John' and person.last_name == 'Doe'
        assert person.gender == party.Gender.MALE \
           and person.marital_status == party.MaritalStatus.SINGLE

    def test_non_root_organization_creation_fails_for_invalid_fields(self, db):
        # multi_root = False
        data_dict = {'is_root': False, 'code': 'org', 'name': 'Org'}
        with pytest.raises(logic.ValidationError):
            action.organization_create(db, data_dict)

    def test_multi_root_organization_creation_fails_for_ESRO(self, db):
        # ESRO: Expected Single Root Organization
        data_dict = {'is_root':True, 'code':'org', 'name':'Org'}
        action.organization_create(db, data_dict)
        with pytest.raises(logic.MultipleOrganizationError):
            data_dict.update({'is_root':True, 'code': 'org-1', 'name': 'Org 1'})
            action.organization_create(db, data_dict)

    def test_multi_root_organization_creation_passes_for_EMRO(self, db):
        # EMRO: Expected Multi Root Organization
        action.organization_create(db, {
            'is_root':True, 'multi_root':True, 'code':'org', 'name':'Org'
        })
        action.organization_create(db, {
            'is_root':True, 'multi_root':True, 'code':'org-1', 'name':'Org-1'
        })

        query = db.query(party.Organization)
        orgs = query.filter(party.Organization.parent_id.is_(None)).all()
        assert orgs and len(orgs) == 2


class TestEntityShowAction(object):

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
        org_type = party.OrganizationType(name='org-type', title='Org Type')
        db.add(org_type)
        db.commit()

        found = action.organization_type_show(db, {'id': org_type.uuid})
        assert found and found.id and found.uuid
        assert found.name == 'org-type' \
           and found.title == 'Org Type'

    def test_retrieving_non_existing_organization_raise_notfound(self, db):
        with pytest.raises(logic.NotFoundError):
            action.organization_show(db, {'id': 1})

    def test_can_retrieve_existing_organization(self, db):
        organization = party.Organization(code='01', name='Org')
        db.add(organization)
        db.commit()

        found = action.organization_show(db, {'id': organization.uuid})
        assert found and found.id and found.uuid
        assert found.code == '01' \
           and found.name == 'Org'
