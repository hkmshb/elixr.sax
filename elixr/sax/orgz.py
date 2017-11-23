"""Defines models which ease defining, storing and working with Organisational
structures within an application.
"""
import enum
from sqlalchemy import Column, Boolean, Date, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, backref

from .mixins import IdMixin, IdTimestampMixin, UUIDMixin
from .address import AddressMixin, CoordinatesMixin
from .types import Choice
from .meta import Model



## ENUMS
class ContactType(enum.Enum):
    email = 1
    phone = 2


class PartyType(enum.Enum):
    person = 1
    organisation = 2


class Gender(enum.Enum):
    unknown = 0
    male    = 1
    female  = 2


class MaritalStatus(enum.Enum):
    unknown  = 0
    single   = 1
    married  = 2
    divorced = 3
    widowed  = 4



## MODELS
# many-to-many relation between contact details and party
parties_contact_details = Table(
    'parties_contact_details',
    Model.metadata,
    Column('party_id', Integer, ForeignKey('parties.id')),
    Column('contact_detail_id', Integer, ForeignKey('contact_details.id'))
)


class ContactDetail(Model, IdMixin):
    """A Single-Table Inheritance model for storing all forms of contact details.
    """
    __tablename__ = 'contact_details'
    
    usage = Column(String(30))
    subtype = Column(Choice(ContactType), nullable=False)
    is_confirmed = Column(Boolean(create_constraint=False), default=False)
    is_preferred = Column(Boolean(create_constraint=False), default=False)
    deleted = Column(Boolean(create_constraint=False), default=False)
    __mapper_args__ = {
        'polymorphic_identity': 'contact_details',
        'polymorphic_on': subtype
    }

class EmailContact(ContactDetail):
    """A model for storing Email contact details.
    """
    __mapper_args__ = {
        'polymorphic_identity': ContactType.email
    }
    address = Column(String(150), unique=True)


class PhoneContact(ContactDetail):
    """A model for storing Phone contact details.
    """
    __mapper_args__ = {
        'polymorphic_identity': ContactType.phone
    }
    number = Column(String(15), unique=True)
    extension = Column(String(10))


class Party(Model, IdTimestampMixin, AddressMixin):
    """A Joined Table inheritance model for storing the named parts of a Party
    derived inheritance model relationship.
    """
    __tablename__ = 'parties'

    name = Column(String(50), nullable=False, unique=True)
    subtype = Column(Choice(PartyType), nullable=False)
    deleted = Column(Boolean(create_constraint=False), default=False)
    contacts = relationship("ContactDetail", secondary="parties_contact_details", 
                            lazy="joined")
    __mapper_args__ = {
        'polymorphic_identity': 'parties',
        'polymorphic_on': subtype
    }


class Person(Party):
    """A model for storing Person details.
    """
    __tablename__ = 'people'
    __mapper_args__ = {
        'polymorphic_identity': PartyType.person
    }

    id = Column(Integer, ForeignKey("parties.id"), primary_key=True)
    title = Column(String(20))
    middle_name = Column(String(50))
    last_name = Column(String(50))
    gender = Column(Choice(Gender))
    date_born = Column(Date)
    marital_status = Column(Choice(MaritalStatus))
    state_origin_id = Column(Integer, ForeignKey("states.id"))
    state_origin = relationship("State")
    nationality_id  = Column(Integer, ForeignKey("countries.id"))
    nationality = relationship("Country")

    @property
    def first_name(self):
        return self.name
    
    @first_name.setter
    def set_first_name(self, value):
        self.name = value


class Organisation(Party, UUIDMixin, CoordinatesMixin):
    """A model for storing Organisation details.
    
    :hint: fncode (function code) can be used to indicate the organisation 
    function implemented via an enum. e.g HQ, Branch, SalesOffice, ServicePoint
    etc. Its left open to accomodate any int based enum declaration.
    """
    __tablename__ = 'organisations'
    __mapper_args__ = {
        'polymorphic_identity': PartyType.organisation
    }

    id = Column(Integer, ForeignKey("parties.id"), primary_key=True)
    parent_id = Column(Integer, ForeignKey("organisations.id"))
    fncode = Column(Integer)                                         # function code
    identifier = Column(String(30), nullable=False, unique=True)     # org identifier
    short_name = Column(String(15), unique=True)
    description = Column(String(255))
    date_established = Column(Date)
    website_url = Column(String(150))
    children = relationship("Organisation", foreign_keys=[parent_id],
                backref=backref("parent", remote_side=[id]))
