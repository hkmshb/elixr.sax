import pytest
from elixr.sax.logic import action, schemas, validators as _val
from elixr.sax.logic import action
from elixr.sax import logic, party


class TestEntityCreateAction(object):

    ## COUNTRY

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
        data_dict.update({'code':'org', 'name':'Org Type'})
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
