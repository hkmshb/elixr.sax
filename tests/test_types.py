import pytest
from enum import Enum
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String
from elixr_db.meta import Model
from elixr_db.types import Choice



class Gender(Enum):
    male   = 1
    female = 2


class MockPerson(Model):
    __tablename__ = 'mock_persons'
    id     = Column(Integer, primary_key=True)
    name   = Column(String(50), nullable=False)
    gender = Column(Choice(Gender), nullable=False)


@pytest.fixture(scope='module')
def db():
    # setup
    engine = create_engine('sqlite:///:memory:') #, echo=True)
    Model.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    yield session

    # teardown
    Model.metadata.drop_all(engine)


class TestChoiceType(object):
    def test_can_save_mock_person(self, db):
        person = MockPerson(name='john', gender=Gender.male)
        assert person.id == None
        db.add(person)
        db.commit()

        assert person.id != None
    
    def test_gender_stored_as_integer(self, db):
        # this save succeeds ...
        db.add(MockPerson(name='jane', gender=Gender.female))
        db.add(MockPerson(name='tom', gender=Gender.male))
        db.flush()

        # perform assertion
        self._assert_gender_column_stores_integer(db)
        
    def _assert_gender_column_stores_integer(self, db):
        # perform direct dbapi access of `mock_persons` table
        conn = db.connection()
        result = conn.execute('SELECT * FROM mock_persons WHERE name=?', ('jane',))
        record = result.fetchone()
        assert record \
           and record[1] == 'jane' \
           and record[2] == 2

        result = conn.execute('SELECT * FROM mock_persons WHERE name=?', ('tom',))
        record = result.fetchone()
        assert record \
           and record[1] == 'tom' \
           and record[2] == 1
