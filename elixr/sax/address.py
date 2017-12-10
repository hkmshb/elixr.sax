"""Defines models which ease defining, storing and working with Addresses within
an application.
"""
from collections import namedtuple
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, Float, ForeignKey, Integer, String, \
        UniqueConstraint
from sqlalchemy.orm import relationship
from elixr.base import AttrDict, Coordinates
from .mixins import IdsMixin
from . import meta, types



class Country(meta.Model, IdsMixin):
    """A model for storing Country data.
    """
    __tablename__ = 'countries'

    code = Column(String(3), nullable=False)
    name = Column(String(50), nullable=False, unique=True)
    states = relationship("State", back_populates="country")

    def __str__(self):
        return self.name


class State(meta.Model, IdsMixin):
    """A model for storing State data.
    """
    __tablename__ = 'states'
    __table_args__ = (
        UniqueConstraint('name', 'country_id', name='uq_states_name_country_id'),
    )

    code = Column(String(3), nullable=False)
    name = Column(String(50), nullable=False)
    country_id = Column(types.UUID, ForeignKey("countries.uuid"), nullable=False)
    country = relationship("Country", back_populates="states")

    def __str__(self):
        value = self.name
        if self.country:
            if value:
                value += ', '
            value += self.country.name
        return value


class AddressMixin(object):
    """A mixin which defines address fields for use within other models.
    """
    addr_raw = Column(String(200))
    addr_street = Column(String(100))
    addr_town = Column(String(50))
    addr_landmark = Column(String(100))
    postal_code = Column(String(10))

    @declared_attr
    def addr_state_id(cls):
        return Column(Integer, ForeignKey("states.id"), nullable=True)

    @declared_attr
    def addr_state(cls):
        return relationship("State")

    @property
    def address_dict(self):
        return self.to_dict(self)

    @property
    def address_str(self):
        return self.to_str(self)

    @staticmethod
    def to_dict(addr):
        addr_dict = dict(
            landmark=addr.addr_landmark,
            street=addr.addr_street,
            town=addr.addr_town,
            raw=addr.addr_raw,
        )
        if addr.addr_state:
            addr_dict['state'] = addr.addr_state.name
            addr_dict['state_code'] = addr.addr_state.code
            addr_dict['postal_code'] = addr.postal_code
            if addr.addr_state.country:
                addr_dict['country'] = addr.addr_state.country.name
                addr_dict['country_code'] = addr.addr_state.country.code
        return addr_dict

    @staticmethod
    def to_str(addr):
        value = ''
        if addr.addr_state:
            if addr.addr_street:
                value = addr.addr_street
            if addr.addr_town:
                if value:
                    value += ', '
                value += addr.addr_town
                if addr.postal_code:
                    value += ' %s' % addr.postal_code
            if value:
                value += ', '
            value += str(addr.addr_state)
            if addr.addr_landmark:
                if value:
                    value += ' '
                value += '(closest landmark: %s)' % addr.addr_landmark
        else:
            value = addr.addr_raw
        return value


class CoordinatesMixin(object):
    """A mixin which defines coordinate fields for use within other models.
    """
    longitude = Column(Float)
    latitude = Column(Float)
    altitude = Column(Float)
    gps_error = Column(Integer)

    @property
    def coordinates(self):
        return Coordinates(
            lng=self.longitude or 0.0,
            lat=self.latitude or 0.0,
            alt=self.altitude,
            error=self.gps_error)


class LocatableMixin(AddressMixin, CoordinatesMixin):
    """A convenience mixin which combines the fields defined by both the
    AddressMixin and CoordinatesMixin.
    """
    pass


class Address(meta.Model, IdsMixin, CoordinatesMixin):
    """A model for storing Address data.
    """
    __tablename__ = 'addresses'

    raw = Column(String(200), nullable=False)
    street = Column(String(100))
    town = Column(String(50))
    landmark = Column(String(100))
    postal_code = Column(String(10))
    state_id = Column(types.UUID, ForeignKey("states.uuid"), nullable=True)
    state = relationship("State", backref="addresses")

    def as_attrd(self):
        return AttrDict({
            'addr_raw': self.raw,
            'addr_street': self.street,
            'addr_town': self.town,
            'addr_state': self.state,
            'addr_landmark': self.landmark,
            'postal_code': self.postal_code,
        })

    def as_dict(self):
        return AddressMixin.to_dict(self.as_attrd())

    def __str__(self):
        return AddressMixin.to_str(self.as_attrd())
