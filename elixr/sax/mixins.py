import uuid
from sqlalchemy import Column, DateTime, Integer, Sequence, String
from sqlalchemy.sql import func
from .types import UUID



class IdMixin(object):
    """A mixin which defines an Id field to uniquely identify records within an
    application space.
    """
    id = Column(Integer, primary_key=True)


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
    uuid = Column(UUID, nullable=False, unique=True, default=uuid.uuid4)
