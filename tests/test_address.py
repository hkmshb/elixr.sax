import pytest
from collections import namedtuple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String
from elixr.db.meta import Model
from elixr.db.mixins import IdMixin
from elixr.db.address import Country, State, Address, AddressMixin, \
        CoordinatesMixin, Coordinates


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


@pytest.fixture(scope='module')
def db():
    # setup
    engine = create_engine('sqlite:///:memory:') #, strategy='mock', executor=dump)
    Model.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # create some records
    session.add(Country(name='Nigeria', code='NG'))
    session.add(Country(name='Algeria', code='AL'))
    session.commit()
    yield session

    # teardown
    Model.metadata.drop_all(engine)


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
    
    def test_commit_fails_for_duplicate_name(self, db):
        with pytest.raises(Exception):
            db.add(Country(name='Nigeria', code='??'))
            db.commit()
    
    def test_commit_fails_for_blank_name(self, db):
        with pytest.raises(Exception):
            db.add(Country(code='NG'))
            db.commit()
        db.rollback()   # why? see hint at module top
    
    def test_commit_fails_for_blank_code(self, db):
        with pytest.raises(Exception):
            db.add(Country(name='Kenya'))
            db.commit()
        db.rollback()
    
    def test_rel_states_empty_when_country_has_no_states(self, db):
        country = db.query(Country).filter(Country.name == 'Nigeria').one()
        assert country and country.name == 'Nigeria' \
           and country.states == []


class TestState(BaseTest):

    def test_string_repr_with_country(self, db):
        ng = db.query(Country).filter(Country.name == 'Nigeria').one()
        state = State(name='Abuja', code='AB', country=ng)
        assert 'Abuja, Nigeria' == str(state)
    
    def test_string_repr_without_country(self, db):
        state = State(name='Abuja', code='AB')
        assert 'Abuja' == str(state)
    
    def test_commit_fails_for_omitted_country(self, db):
        with pytest.raises(Exception):
            db.add(State(name='Abuja', code='AB'))
            db.commit()
        db.rollback()   # why? see hint at module top
    
    def test_can_save_well_formed_state_object(self, db):
        db.add(State(name='Abuja', code='AB', country=self._country(db)))
        db.commit()

        state = db.query(State).filter(State.name == 'Abuja').one()
        assert state and state.name == 'Abuja'
    
    def test_commit_fails_for_duplicate_name_for_same_country(self, db):
        country = self._country(db)
        db.add(State(name='Lagos', code='LG', country=country))
        db.commit()

        with pytest.raises(Exception):
            db.add(State(name='Lagos', code='??', country=country))
            db.commit()
        
        db.rollback()   # why? see hint at the top
    
    def test_commit_fails_for_blank_name(self, db):
        country = self._country(db)
        with pytest.raises(Exception):
            db.add(State(code='??', country=country))
            db.commit()
        db.rollback()   # why? see hint at the top
    
    def test_commit_fails_for_blank_code(self, db):
        country = self._country(db)
        with pytest.raises(Exception):
            db.add(State(name='Rivers', country=country))
            db.commit()
        db.rollback()
    
    def test_relationships_traversable_within_state_object(self, db):
        country = self._country(db)
        db.add(State(name='Kano', code='KN', country=country))
        db.commit()

        state = db.query(State).filter(State.name == 'Kano').one()
        assert state and state.country == country \
           and state.country.id == state.country_id \
           and state in state.country.states


class TestAddress(BaseTest):
    
    def _address(self, db):
        return Address(
            raw='No 1 Bank Road, Bwari 720015, Abuja, Nigeria ::',
            street='No 1 Bank Road', town='Bwari', postal_code='720015',
            state=self._state(db))
    
    def test_string_repr_with_all_fields(self, db):
        # hint: include '::' in raw to be sure raw is not used by str(addr)
        addr = self._address(db)
        assert 'No 1 Bank Road, Bwari 720015, Abuja, Nigeria' == str(addr)
    
    def test_string_repr_with_only_raw_field(self):
        addr = Address(raw='1 Alu Avenue')
        assert '1 Alu Avenue' == str(addr)
    
    def test_commit_fails_for_blank_raw(self, db):
        with pytest.raises(Exception):
            db.add(Address(street='No 1 Bank Road', town='Bwari', 
                            postal_code='720015', state=self._state(db)))
            db.commit()
        db.rollback()
    
    def test_dict_repr(self, db):
        address = self._address(db)
        addr_dict = address.as_dict()
        fields = ('raw', 'street', 'town', 'postal_code')
        for f in fields:
            assert getattr(address, f) == addr_dict.get(f)
        
        state = address.state
        assert state.name == addr_dict.get('state')
        assert state.code == addr_dict.get('state_code')

        country = address.state.country
        assert country.name == addr_dict.get('country')
        assert country.code == addr_dict.get('country_code')


class TestAddressMixinMock(BaseTest):
    def _mock(self, db):
        return MockAddress(name='mock', 
                addr_raw='No 1 Bank Road, Bwari 720015, Abuja, Nigeria ::',
                addr_street='No 1 Bank Road', addr_town='Bwari', 
                postal_code='720015', addr_state=self._state(db))
    
    def test_address_str_from_address_mixin(self, db):
        mock = self._mock(db)
        assert 'No 1 Bank Road, Bwari 720015, Abuja, Nigeria' == mock.address_str
    
    def test_addres_dict_from_address_mixin(self, db):
        mock = self._mock(db)
        addr_dict = mock.address_dict
        fields = ('addr_raw', 'addr_street', 'addr_town', 'postal_code')
        for f in fields:
            assert getattr(mock, f) == addr_dict.get(f.replace('addr_', ''))
    
    def test_raw_and_other_address_fields_optional(self, db):
        db.add(MockAddress(name='mock'))
        db.commit()

        mock = db.query(MockAddress).filter(MockAddress.name == 'mock').one()
        assert mock and mock.name == 'mock' \
           and mock.addr_raw == None \
           and mock.addr_street == None \
           and mock.addr_town == None \
           and mock.addr_state == None


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
    