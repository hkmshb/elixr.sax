import os
import pytest
from elixr.sax import utils

DIR_FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')



@pytest.fixture(scope='function')
def db():
    # setup
    resx = utils.make_session()
    yield resx.session

    # teardown
    utils.drop_tables(resx.engine)


@pytest.fixture(scope='module')
def db2():
    def initdb(session):
        from elixr.sax.auth import AuthEmail, User, _hash_password
        user = User(username='scott', is_active=True)
        user.emails.append(AuthEmail(address='scott@tiger.ora'))
        user.set_password('tiger')

        user2 = User(username='mike', password=_hash_password('lion'))
        user2.emails.append(AuthEmail(address='mike@lion.ora'))

        session.add_all([user, user2])
        session.commit()

    ## setup
    resx = utils.make_session(initdb_callback=initdb)
    yield resx.session

    # teardown
    utils.drop_tables(resx.engine)


@pytest.fixture(scope='module')
def addr_db():
    def initdb(db):
        from elixr.sax.address import Country
        db.add(Country(name='Nigeria', code='NG'))
        db.add(Country(name='Algeria', code='AL'))
        db.commit()

    # setup & create records
    resx = utils.make_session(initdb_callback=initdb)
    yield resx.session

    # teardown
    utils.drop_tables(resx.engine)


@pytest.fixture(scope='module')
def cache():
    from elixr.sax.export.importer import XRefResolver

    def initdb(session):
        from elixr.sax.address import Country, State

        ca = Country(code='CA', name='Canada')
        ng = Country(code='NG', name='Nigeria')
        session.add_all([
            ca, ng,
            State(code='BC', name='British Columbia', country=ca),
            State(code='BC', name='Bauchi', country=ng),    # wrong code ;-D
        ])
        session.commit()

    ## setup
    resx = utils.make_session(initdb_callback=initdb)
    yield XRefResolver(resx.session)

    ## teardown
    utils.drop_tables(resx.engine)


@pytest.fixture(scope='module')
def cache2():
    from elixr.sax.export.importer import XRefResolver

    def initdb(session):
        from elixr.sax.address import Country, State
        ca = Country(code='CA', name='Canada')
        ng = Country(code='NG', name='Nigeria')
        session.add_all([
            ca, ng,
            State(code='KN', name='Kano', country=ng),    # wrong code ;-D
        ])

        from elixr.sax.party import OrganizationType
        ot1 = OrganizationType(name='hq', title='Headquarters', is_root=True)
        ot2 = OrganizationType(name='branch', title='Branch')
        session.add_all([ot1, ot2])
        session.commit()

    ## setup
    resx = utils.make_session(initdb_callback=initdb)
    yield XRefResolver(resx.session)

    ## teardown
    utils.drop_tables(resx.engine)


def wb():
    import openpyxl
    fp = os.path.join(DIR_FIXTURES, 'importer-data.xlsx')
    return openpyxl.load_workbook(fp, read_only=True)
