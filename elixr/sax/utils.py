from collections import namedtuple
from .meta import Model, create_engine, sessionmaker



Resource = namedtuple('Resource', ['engine', 'session'])

def make_session(conn_str='sqlite:///:memory:', initdb_callback=None):
    engine = create_engine(conn_str)
    Model.metadata.create_all(engine)

    SASession = sessionmaker(bind=engine)
    session = SASession()

    if initdb_callback:
        initdb_callback(session)
    return Resource(engine, session)


def clear_tables(db, *table_names):
    tables = reversed(Model.metadata.sorted_tables)
    if table_names:
        tables = [t for t in tables if t.name in table_names]

    for table in tables:
        db.execute(table.delete())
    db.commit()


def drop_tables(engine):
    Model.metadata.drop_all(engine)
