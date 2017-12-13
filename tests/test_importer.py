import os
import uuid
import pytest
import openpyxl
from datetime import date
from sqlalchemy.orm import exc
from elixr.base import AttrDict
from elixr.sax import utils
from elixr.sax.address import Country, State
from elixr.sax.party import (
    Gender, EmailContact, PhoneContact, Organization, OrganizationType
)
from elixr.sax.export.importer import (
    XRefResolver, ImporterBase, AdminBoundaryImporter, OrganizationImporter,
    OrganizationTypeImporter, ExactTextMatcher, PrefixedTextMatcher, 
    SuffixedTextMatcher
)


@pytest.fixture(scope='module')
def imp_vr():
    from conftest import wb
    return ValueReader({'wb': wb()})


@pytest.fixture(scope='module')
def imp_adb():
    from conftest import db, cache
    _db = next(db())
    cache = XRefResolver(_db)
    return AdminBoundaryImporter({'db': _db, 'cache': cache})


class ValueReader(ImporterBase):
    sheet_name = 'types'

    def __init__(self, context):
        self.context = AttrDict(context)
        self.wb = context.pop('wb')


class TestXRefResolver(object):

    @pytest.mark.parametrize("model_type, filters, expected", [
        (State, {'code':'AB'}, 'state_id#'),
        (Country, {'code':'NG'}, 'country_id#'),
        (State, {'code':'AB', 'country':'NG'}, 'state_id#')])
    def test_genkey_startswith_MODELNAME_ID_if_retrieving_only_id(self, 
            model_type, filters, expected):
        key = XRefResolver.generate_key(model_type, only_id=True, **filters)
        assert key.startswith(expected) == True

    @pytest.mark.parametrize("model_type, filters, expected", [
        (State, {'code':'AB'}, 'state#'),
        (Country, {'code':'NG'}, 'country#'),
        (State, {'code':'AB', 'country':'NG'}, 'state#')])
    def test_genkey_startswith_MODELNAME_if_retrieving_entire_model(self,
            model_type, filters, expected):
        key = XRefResolver.generate_key(model_type, only_id=False, **filters)
        assert key.startswith(expected) == True

    @pytest.mark.parametrize("model_type, filters, expected", [
        (State, {'code':'AB'}, 'state_id#code=ab'),
        (Country, {'code':'NG'}, 'country_id#code=ng'),
        (State, {'code':'AB', 'country':'NG'}, 'state_id#code=ab#country=ng')])
    def test_genkey_contacts_key_value_pairs_of_filter(self, 
            model_type, filters, expected):
        key = XRefResolver.generate_key(model_type, only_id=True, **filters)
        assert expected == key

    @pytest.mark.parametrize("model_type, filters, expected", [
        (State, {'code':'AB'}, 'state#code=ab'),
        (Country, {'code':'NG'}, 'country#code=ng'),
        (State, {'code':'AB', 'country':'NG'}, 'state#code=ab#country=ng')])
    def test_genkey_contacts_key_value_pairs_of_filter2(self,
            model_type, filters, expected):
        key = XRefResolver.generate_key(model_type, only_id=False, **filters)
        assert expected == key

    def test_ok_when_filter_matches_single_record(self, cache):
        id = cache.resolve(Country, code='NG')
        assert id != None and type(id) is uuid.UUID

    def test_fails_when_filter_matches_multiple_records(self, cache):
        with pytest.raises(exc.MultipleResultsFound):
            id = cache.resolve(State, code='BC')

    def test_results_are_also_stored_in_internal_cache(self, cache):
        cache.clear_cache()
        id = cache.resolve(Country, only_id=True, code='NG')
        key = cache.generate_key(Country, only_id=True, code='NG')
        assert id != None \
           and id == cache._XRefResolver__cache[key]

    def test_cache_result_used_if_already_exists(self, cache):
        # mock an existing entry
        key = cache.generate_key(Country, only_id=True, code='NZ')
        cache._XRefResolver__cache[key] = 'oops!'
        id = cache.resolve(Country, only_id=True, code='NZ')
        assert id == 'oops!'

    def test_returns_object_when_only_id_FALSE(self, cache):
        cache.clear_cache()
        country = cache.resolve(Country, only_id=False, code='NG')
        assert country is not None \
           and country.id != 0 \
           and isinstance(country, Country)

    def test_returns_id_when_only_id_TRUE(self, cache):
        cache.clear_cache()
        country_id = cache.resolve(Country, only_id=True, code='NG')
        assert country_id \
           and type(country_id) is uuid.UUID


class TestImporterBase(object):

    def test_resolve_xref_gets_id_for_xref_field_ending_with_id(self, cache):
        cache.clear_cache()
        data = {'country_id': 'NG'}
        session = cache._XRefResolver__dbsession
        imp = ValueReader(AttrDict(wb=None, db=session, cache=cache))
        imp.resolve_xref(data, ('country_id', 'code', Country))
        assert type(data['country_id']) is uuid.UUID

    def test_resolve_xref_gets_model_for_xref_field_ending_witout_id(self, cache):
        cache.clear_cache()
        data = {'country': 'NG'}
        session = cache._XRefResolver__dbsession
        imp = ValueReader(AttrDict(wb=None, db=session, cache=cache))
        imp.resolve_xref(data, ('country', 'code', Country))
        assert isinstance(data['country'], Country)

    @pytest.mark.parametrize("row, expected", [
        (1, True), (2, False), (3, False), (4, True)])
    def test_is_empty_row(self, imp_vr, row, expected):
        imp_vr.errors = [] # .clear fails for py2
        assert imp_vr.is_empty_row(imp_vr.sheet, row) == expected
        assert len(imp_vr.errors) == 0

    @pytest.mark.parametrize("row, col, expected", [
        (1, 1, None), (2, 1, 'blank'), (3, 2, 1),   # within data range
        (300, 300, None)                            # totally out of data range
    ])
    def test_get_cell_value(self, imp_vr, row, col, expected):
        imp_vr.errors = [] # .clear() fails for py2
        value = imp_vr.get_cell_value(imp_vr.sheet, row, col)
        assert len(imp_vr.errors) == 0
        assert expected == value
        ## and type(expected) in type(value)
        # commented out as type(expected) resulted in long for py2 and int
        # for py3 for same numeric value...

    @pytest.mark.parametrize("row, col, expected", [
        (1, 1, ('', False)), (2, 1, ('blank', True)), (3, 2, (1, True))])
    def test_get_cell_value_found(self, imp_vr, row, col, expected):
        imp_vr.errors = [] # .clear() fails for py2
        value, found = imp_vr.get_cell_and_found(imp_vr.sheet, row, col)
        assert len(imp_vr.errors) == 0
        assert expected[0] == value \
           and expected[1] == found 

    @pytest.mark.parametrize("row, col, expected", [
        (1, 1, ('', False, True)), (2, 1, ('blank', True, True)),
        (3, 2, ('1', True, True)), (3, 5, ('1', True, True))])
    def test_get_text_found_valid(self, imp_vr, row, col, expected):
        # cell(3,5) TRUE is read as 1
        imp_vr.errors = []
        value, found, valid = imp_vr.get_text_found_valid(imp_vr.sheet, row, col)
        assert len(imp_vr.errors) == 0
        assert expected[0] == value \
           and expected[1] == found \
           and expected[2] == valid

    @pytest.mark.parametrize("row, col, expected, err_count", [
        (1, 1, '', 1), (2, 1, 'blank', 0), (3, 2, '1', 0), 
        (3, 5, '1', 0)  # excel-value: TRUE is read as 1
    ])
    def test_get_required_text_from_cell(self, imp_vr, row, col, expected, err_count):
        imp_vr.errors = []
        value = imp_vr.get_required_text_from_cell(imp_vr.sheet, row, col)
        assert expected == value \
           and err_count == len(imp_vr.errors)

    @pytest.mark.parametrize("row, col, expected, err_count", [
        (3, 1, None, 0), (3, 2, True, 0),     # cell values:    , 1
        (3, 3, True, 0), (3, 4, None, 1),     # cell values: '1', 1.0
        (3, 5, True, 0), (3, 6, False, 0),    # cell values: TRUE, False
        (3, 7, True, 0), (3, 9, None, 1)      # cell values: T, 2017-01-aa
    ])
    def test_get_bool_from_cell(self, imp_vr, row, col, expected, err_count):
        imp_vr.errors = []
        value = imp_vr.get_bool_from_cell(imp_vr.sheet, row, col)
        assert expected == value \
           and err_count == len(imp_vr.errors)

    @pytest.mark.parametrize("row, col, expected, err_count", [
        (3, 1, None, 1), (3, 2, True, 0),     # cell values:    , 1
        (3, 3, True, 0), (3, 4, None, 1),     # cell values: '1', 1.0
        (3, 5, True, 0), (3, 6, False, 0),    # cell values: TRUE, False
        (3, 7, True, 0), (3, 9, None, 1)      # cell values: T, 2017-01-aa
    ])
    def test_get_required_bool_from_cell(self, imp_vr, row, col, expected, err_count):
        imp_vr.errors = []
        value = imp_vr.get_required_bool_from_cell(imp_vr.sheet, row, col)
        assert expected == value \
           and err_count == len(imp_vr.errors)

    @pytest.mark.parametrize("row, col, expected, err_count", [
        (3, 1, None, 0), (3, 9, None, 1),    # cv:  , '2017-01-aa'
        (3, 11, date(2017,1, 29), 0),        # cv: '2017-01-29'
        (3, 12, None, 1)                     # cv: '29-01-2017'
    ])
    def test_get_date_from_cell(self, imp_vr, row, col, expected, err_count):
        imp_vr.errors = []
        value = imp_vr.get_date_from_cell(imp_vr.sheet, row, col)
        assert expected == value \
           and err_count == len(imp_vr.errors)

    @pytest.mark.parametrize("row, col, expected, err_count", [
        (3, 13, Gender.MALE, 0), (3, 14, Gender.FEMALE, 0),
        (3, 15, None, 1), (3, 16, None, 1)])    # 3, none
    def test_get_enum_from_cell(self, imp_vr, row, col, expected, err_count):
        imp_vr.errors = []
        value = imp_vr.get_enum_from_cell(imp_vr.sheet, row, col, Gender)
        assert expected == value \
           and err_count == len(imp_vr.errors)

    @pytest.mark.parametrize("row, col, expected, err_count", [
        (3, 1, 0.0, 0), (3, 2, 1.0, 0),    # cv:    , 1
        (3, 3, 1.0, 0), (3, 4, 1.0, 0),    # cv: '1', 1.0
        (3, 6, None, 1)                     # cv: 'False'
    ])
    def test_get_float_from_cell(self, imp_vr, row, col, expected, err_count):
        imp_vr.errors = []
        value = imp_vr.get_float_from_cell(imp_vr.sheet, row, col)
        assert expected == value \
           and err_count == len(imp_vr.errors)

    @pytest.mark.parametrize("row, col, expected, err_count", [
        (3, 2,   1, 0), (3, 3,    1, 0),     # cv:    , 1
        (3, 4, 1.0, 0), (3, 6, None, 1),     # cv: 1.0, 'False'
    ])
    def test_get_int_from_cell(self, imp_vr, row, col, expected, err_count):
        imp_vr.errors = []
        value = imp_vr.get_int_from_cell(imp_vr.sheet, row, col)
        assert expected == value \
           and err_count == len(imp_vr.errors)

    @pytest.mark.parametrize("row, col, expected, err_count", [
        (3, 1, '', 0), (3, 2,   '1', 0),              # cv:    , 1
        (3, 3,  '1', 0), (3, 4, '1.0', 0),               # cv: '1', 1.0
        (3, 6, 'False', 0), (3, 9, '2017-01-aa', 0),
        (3, 11, '2017-01-29 00:00:00', 0)])
    def test_get_id_from_cell(self, imp_vr, row, col, expected, err_count):
        imp_vr.errors = []
        value = imp_vr.get_id_from_cell(imp_vr.sheet, row, col)
        assert expected == value \
           and err_count == len(imp_vr.errors)

    @pytest.mark.parametrize("row, col, expected, err_count", [
        (3, 1, [], 0), (3, 2,    ['1'], 0),      # cv:    , 1
        (3, 3, ['1'], 0), (3, 4, ['1.0'], 0),    # cv: '1', 1.0
        (3, 6, ['False'], 0), 
        (3, 9, ['2017-01-aa'], 0),
        (3, 11, ['2017-01-29 00:00:00'], 0)])
    def test_get_ids_from_cell(self, imp_vr, row, col, expected, err_count):
        imp_vr.errors = []
        value = imp_vr.get_ids_from_cell(imp_vr.sheet, row, col)
        assert expected == value \
           and err_count == len(imp_vr.errors)


class TestTextMatchers(object):
    TEXT = 'text.text1.text2.1text.2text.TextA.TextB.AText.BText'

    def _assert(self, target, expected, matcher):
        matches = matcher(self.TEXT.split('.'), target)
        assert expected == matches

    @pytest.mark.parametrize("target, expected", [
        ('text', ['text']), ('text2', ['text2']), ('none', [])])
    def test_exact_matcher(self, target, expected):
        self._assert(target, expected, ExactTextMatcher())

    @pytest.mark.parametrize("target, expected", [
        ('text', ['text', 'text1', 'text2', 'TextA', 'TextB'])])
    def test_prefixed_matcher(self, target, expected):
        self._assert(target, expected, PrefixedTextMatcher())

    @pytest.mark.parametrize("target, expected", [
        ('text', ['text', '1text', '2text', 'AText', 'BText'])])
    def test_suffixed_matcher(self, target, expected):
        self._assert(target, expected, SuffixedTextMatcher())


class TestAdminBoundaryImporter(object):

    def test_countries_import(self, imp_adb):
        from conftest import wb
        db = imp_adb.context.db
        utils.clear_tables(db, 'states', 'countries')

        imp_adb.errors = []
        imp_adb.sheet_name = 'countries'
        imp_adb.import_data(wb())

        assert len(imp_adb.errors) == 0
        found = db.query(Country).count()
        assert found == 2

    def test_states_import_without_existing_xref_fails(self, imp_adb):
        db = imp_adb.context.db
        utils.clear_tables(db, 'states', 'countries')

        imp_adb.errors = []
        imp_adb.sheet_name = 'states'

        from conftest import wb
        with pytest.raises(Exception):
            imp_adb.import_data(wb())
        db.rollback()

    def test_states_import_with_existing_xref_passes(self, imp_adb):
        from conftest import wb
        db, _wb = (imp_adb.context.db, wb())
        utils.clear_tables(db, 'states', 'countries')

        imp_adb.errors = []
        imp_adb.sheet_name = 'countries'
        imp_adb.import_data(_wb)

        assert len(imp_adb.errors) == 0
        imp_adb.sheet_name = 'states'
        imp_adb.import_data(_wb)

        assert len(imp_adb.errors) == 0
        found = db.query(State).count()
        assert found == 2

    def test_countries_states_import(self, imp_adb):
        from conftest import wb
        db, _wb = (imp_adb.context.db, wb())
        utils.clear_tables(db, 'states', 'countries')

        imp_adb.errors = []
        imp_adb.sheet_name = 'countries-states'
        imp_adb.import_data(_wb)

        assert len(imp_adb.errors) == 0
        found = db.query(Country).count()
        assert found == 3
        found2 = db.query(State).count()
        assert found2 == 4

    def test_countries_after_states_listings_not_processed(self, imp_adb):
        from conftest import wb
        db, _wb = (imp_adb.context.db, wb())
        utils.clear_tables(db, 'states', 'countries')

        imp_adb.errors = []
        imp_adb.sheet_name = 'countries'
        imp_adb.import_data(_wb)

        assert len(imp_adb.errors) == 0
        imp_adb.sheet_name = 'states-countries'
        imp_adb.import_data(_wb)

        assert len(imp_adb.errors) == 0
        found = db.query(State).count()
        assert found == 1
        found2 = db.query(Country).all()
        countries = db.query(Country).all()
        print([c.name for c in found2])
        assert len(found2) == 2

    def test_countries_after_states_listing_not_processed2(self, imp_adb):
        from conftest import wb
        db, _wb = (imp_adb.context.db, wb())
        utils.clear_tables(db, 'states', 'countries')

        imp_adb.errors = []
        imp_adb.sheet_name = 'countries-states-countries'
        imp_adb.import_data(_wb)

        assert len(imp_adb.errors) == 0
        found = db.query(Country).count()
        assert found == 1
        found2 = db.query(State).count()
        assert found2 == 3


class TestOrganizationTypeImporter(object):

    def test_organization_type_import(self, cache):
        from conftest import wb

        db = cache._XRefResolver__dbsession
        utils.clear_tables(db, 'organisation_types')

        context = AttrDict(db=db, cache=cache)
        importer = OrganizationTypeImporter(context)
        importer.import_data(wb())
        assert len(importer.errors) == 0
        found = db.query(OrganizationType).count()
        assert found == 2


class TestOrganizationImporter(object):

    def test_organisations_import(self, cache2):
        from enum import Enum
        from conftest import wb

        db = cache2._XRefResolver__dbsession
        utils.clear_tables(db, 'contact_details', 'organisations')

        context = AttrDict(db=db, cache=cache2)
        importer = OrganizationImporter(context)
        importer.import_data(wb())
        assert len(importer.errors) == 0
        found = db.query(Organization).count()
        assert found == 2
        found2 = db.query(EmailContact).count()
        assert found2 == 2
        found3 = db.query(PhoneContact).count()
        assert found3 == 1
