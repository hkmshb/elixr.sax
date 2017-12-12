import uuid
from sqlalchemy import Column, DateTime, Integer, Sequence, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func
from . import types



class IdMixin(object):
    """A mixin which defines an Id field to uniquely identify records within an
    application space.
    """
    id = Column(Integer, autoincrement=True, primary_key=True)


class TimestampMixin(object):
    """A mixin which defines fields to record timestamp for record creation and
    modification.
    """
    date_created = Column(DateTime, nullable=False, default=func.now())
    last_updated = Column(DateTime, nullable=True, onupdate=func.now())


class IdTimestampMixin(IdMixin, TimestampMixin):
    """A mixin which provides Id and timestamp fields for a records.
    """
    pass


class UUIDMixin(object):
    """A mixin which defines a globally unique identifier field for a record
    that can possibly be used to track an entity across applications.
    """
    @declared_attr
    def uuid(cls):
        return Column(types.UUID, nullable=False, unique=True, default=uuid.uuid4)


class IdsMixin(IdMixin, UUIDMixin):
    """A mixin which defines two globally unique identifier fields for a record
    that can be used individually to identify records within an application space.
    """
    pass
