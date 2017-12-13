import pytest
from elixr.sax import utils


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