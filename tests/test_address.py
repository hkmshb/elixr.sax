import pytest
from collections import namedtuple
from sqlalchemy import Column, Integer, String
from elixr.sax import utils
from elixr.sax.meta import Model
from elixr.sax.mixins import IdMixin
from elixr.sax.address import (
    Country, State, Address, AddressMixin,
    CoordinatesMixin, Coordinates
)

# why? `db.rollback()`
# because of error which occured above, and since session object `db` has module 
# scope, to ensure its usable in other tests, call below is necessary

#def dump(sql, *multiparams, **params):
#    print(sql)


class MockAddress(Model, IdMixin, AddressMixin):
    __tablename__ = 'mock_addresses'
    name = Column(String(20), nullable=False)


class MockLocation(Model, IdMixin, CoordinatesMixin):
    __tablename__ = 'mock_locations'
    name = Column(String(20), nullable=False)


class BaseTest(object):
    _country_ng, _state_ab = (None, None)

    def _country(self, db):
        if not BaseTest._country_ng:
            q = db.query(Country).filter(Country.name == 'Nigeria')
            BaseTest._country_ng = q.one()
        return BaseTest._country_ng

    def _state(self, db):
        if not BaseTest._state_ab:
            q = db.query(State).filter(State.name == 'Abuja')
            BaseTest._state_ab = q.one()
        return BaseTest._state_ab


class TestCountry(object):
    def test_string_repr(self):
        country = Country(name='Nigeria', code='NG')
        assert 'Nigeria' == str(country)

    def test_commit_fails_for_duplicate_name(self, addr_db):
        with pytest.raises(Exception):
            addr_db.add(Country(name='Nigeria', code='??'))
            addr_db.commit()

    def test_commit_fails_for_blank_name(self, addr_db):
        with pytest.raises(Exception):
            addr_db.add(Country(code='NG'))
            addr_db.commit()
        addr_db.rollback()   # why? see hint at module top

    def test_commit_fails_for_blank_code(self, addr_db):
        with pytest.raises(Exception):
            addr_db.add(Country(name='Kenya'))
            addr_db.commit()
        addr_db.rollback()

    def test_rel_states_empty_when_country_has_no_states(self, addr_db):
        country = addr_db.query(Country).filter(Country.name == 'Nigeria').one()
        assert country and country.name == 'Nigeria' \
           and country.states == []


class TestState(BaseTest):

    def test_string_repr_with_country(self, addr_db):
        ng = addr_db.query(Country).filter(Country.name == 'Nigeria').one()
        state = State(name='Abuja', code='AB', country=ng)
        assert 'Abuja, Nigeria' == str(state)

    def test_string_repr_without_country(self, addr_db):
        state = State(name='Abuja', code='AB')
        assert 'Abuja' == str(state)

    def test_commit_fails_for_omitted_country(self, addr_db):
        with pytest.raises(Exception):
            addr_db.add(State(name='Abuja', code='AB'))
            addr_db.commit()
        addr_db.rollback()   # why? see hint at module top

    def test_can_save_well_formed_state_object(self, addr_db):
        addr_db.add(State(name='Abuja', code='AB', country=self._country(addr_db)))
        addr_db.commit()

        state = addr_db.query(State).filter(State.name == 'Abuja').one()
        assert state and state.name == 'Abuja'

    def test_commit_fails_for_duplicate_name_for_same_country(self, addr_db):
        country = self._country(addr_db)
        addr_db.add(State(name='Lagos', code='LG', country=country))
        addr_db.commit()

        with pytest.raises(Exception):
            addr_db.add(State(name='Lagos', code='??', country=country))
            addr_db.commit()

        addr_db.rollback()   # why? see hint at the top

    def test_commit_fails_for_blank_name(self, addr_db):
        country = self._country(addr_db)
        with pytest.raises(Exception):
            addr_db.add(State(code='??', country=country))
            addr_db.commit()
        addr_db.rollback()   # why? see hint at the top

    def test_commit_fails_for_blank_code(self, addr_db):
        country = self._country(addr_db)
        with pytest.raises(Exception):
            addr_db.add(State(name='Rivers', country=country))
            addr_db.commit()
        addr_db.rollback()

    def test_relationships_traversable_within_state_object(self, addr_db):
        country = self._country(addr_db)
        addr_db.add(State(name='Kano', code='KN', country=country))
        addr_db.commit()

        state = addr_db.query(State).filter(State.name == 'Kano').one()
        assert state and state.country == country \
           and state.country.uuid == state.country_id \
           and state in state.country.states


class TestAddress(BaseTest):

    def _address(self, addr_db):
        return Address(
            raw='No 1 Bank Road, Bwari 720015, Abuja, Nigeria ::',
            street='No 1 Bank Road', town='Bwari', postal_code='720015',
            landmark='Bwari Post Office', state=self._state(addr_db))

    def test_string_repr_with_all_fields(self, addr_db):
        # hint: include '::' in raw to be sure raw is not used by str(addr)
        addr = self._address(addr_db)
        expected = ('No 1 Bank Road, Bwari 720015, Abuja, Nigeria '
                 +  '(closest landmark: Bwari Post Office)')
        assert expected == str(addr)

    def test_string_repr_with_only_raw_field(self):
        addr = Address(raw='1 Alu Avenue')
        assert '1 Alu Avenue' == str(addr)

    def test_commit_fails_for_blank_raw(self, addr_db):
        with pytest.raises(Exception):
            addr_db.add(Address(street='No 1 Bank Road', town='Bwari', 
                           postal_code='720015', state=self._state(addr_db)))
            addr_db.commit()
        addr_db.rollback()

    def test_dict_repr(self, addr_db):
        address = self._address(addr_db)
        addr_dict = address.as_dict()
        fields = ('raw', 'street', 'town', 'landmark', 'postal_code')
        for f in fields:
            assert getattr(address, f) == addr_dict.get(f)

        state = address.state
        assert state.name == addr_dict.get('state')
        assert state.code == addr_dict.get('state_code')

        country = address.state.country
        assert country.name == addr_dict.get('country')
        assert country.code == addr_dict.get('country_code')


class TestAddressMixinMock(BaseTest):
    def _mock(self, addr_db):
        return MockAddress(
            name='mock', 
            addr_raw='No 1 Bank Road, Bwari 720015, Abuja, Nigeria ::',
            addr_street='No 1 Bank Road', addr_town='Bwari', 
            addr_landmark='Bwari Post Office',
            postal_code='720015', addr_state=self._state(addr_db))

    def test_address_str_from_address_mixin(self, addr_db):
        mock = self._mock(addr_db)
        expected = ('No 1 Bank Road, Bwari 720015, Abuja, Nigeria '
                 +  '(closest landmark: Bwari Post Office)')
        assert expected == mock.address_str

    def test_addres_dict_from_address_mixin(self, addr_db):
        mock = self._mock(addr_db)
        addr_dict = mock.address_dict
        fields = ('addr_raw', 'addr_street', 'addr_town', 'addr_landmark', 'postal_code')
        for f in fields:
            assert getattr(mock, f) == addr_dict.get(f.replace('addr_', ''))

    def test_raw_and_other_address_fields_optional(self, addr_db):
        addr_db.add(MockAddress(name='mock'))
        addr_db.commit()

        mock = addr_db.query(MockAddress).filter(MockAddress.name == 'mock').one()
        assert mock and mock.name == 'mock' \
           and mock.addr_raw == None \
           and mock.addr_street == None \
           and mock.addr_town == None \
           and mock.addr_state == None \
           and mock.addr_landmark == None


class TestLocationMixinMock(BaseTest):
    @property
    def _location(self):
        return MockLocation(name='location',
            longitude=11.9976, latitude=8.5086,
            altitude=100, gps_error=2)

    def test_coordinate_as_namedtuple(self):
        coords = self._location.coordinates
        assert isinstance(coords, Coordinates) == True \
           and coords == (11.9976, 8.5086, 100, 2) \
           and self._location.longitude == coords.lng \
           and self._location.latitude == coords.lat \
           and self._location.altitude == coords.alt \
           and self._location.gps_error == coords.error

    def test_empty_coordinate_handle_well(self):
        mock = MockLocation(name='location')
        assert mock != None \
           and mock.coordinates == (0.0, 0.0, None, None)
