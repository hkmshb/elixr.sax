"""Defines models which ease defining, storing and working with Organisational
structures within an application.
"""
import enum
from sqlalchemy import (
    Column, Boolean, Date, ForeignKey, Integer, String, Table, UniqueConstraint
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, backref

from .mixins import EntityMixin, EntityWithDeletedMixin
from .address import AddressMixin, CoordinatesMixin
from . import meta, types



## ENUMS
class ContactType(enum.Enum):
    EMAIL = 1
    PHONE = 2


class PartyType(enum.Enum):
    PERSON = 1
    ORGANIZATION = 2


class Gender(enum.Enum):
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2


class MaritalStatus(enum.Enum):
    UNKNOWN = 0
    SINGLE = 1
    MARRIED = 2
    DIVORCED = 3
    WIDOWED = 4



## MODELS
# many-to-many relation between contact details and party
parties_contact_details_table = Table(
    'parties_contact_details',
    meta.metadata,
    Column('party_id', types.UUID, ForeignKey('parties.uuid')),
    Column('contact_detail_id', types.UUID, ForeignKey('contact_details.uuid'))
)


class ContactDetail(meta.Model, EntityWithDeletedMixin):
    """A Single-Table Inheritance model for storing all forms of contact details.
    """
    __tablename__ = 'contact_details'

    usage = Column(String(30))
    subtype = Column(types.Choice(ContactType), nullable=False)
    is_confirmed = Column(Boolean(create_constraint=False), default=False)
    is_preferred = Column(Boolean(create_constraint=False), default=False)
    __mapper_args__ = {
        'polymorphic_identity': 'contact_details',
        'polymorphic_on': subtype
    }


class EmailContact(ContactDetail):
    """A model for storing Email contact details.
    """
    __mapper_args__ = {
        'polymorphic_identity': ContactType.EMAIL
    }
    address = Column(String(150), unique=True)


class PhoneContact(ContactDetail):
    """A model for storing Phone contact details.
    """
    __mapper_args__ = {
        'polymorphic_identity': ContactType.PHONE
    }
    number = Column(String(15), unique=True)
    extension = Column(String(10))


class Party(meta.Model, EntityWithDeletedMixin, AddressMixin):
    """A Joined Table inheritance model for storing the named parts of a Party
    derived inheritance model relationship.
    """
    __tablename__ = 'parties'
    __table_args__ = (
        UniqueConstraint('name', 'subtype', name='uq_parties_name_subtype'),
    )
    __mapper_args__ = {
        'polymorphic_identity': 'parties',
        'polymorphic_on': 'subtype'
    }

    name = Column(String(50), nullable=False)
    subtype = Column(types.Choice(PartyType), nullable=False)
    contacts = relationship("ContactDetail", lazy="joined",
                            secondary="parties_contact_details")


class Person(Party):
    """A model for storing Person details.
    """
    __tablename__ = 'people'
    __mapper_args__ = {
        'polymorphic_identity': PartyType.PERSON
    }

    uuid = Column(types.UUID, ForeignKey("parties.uuid"), primary_key=True)
    title = Column(String(20))
    middle_name = Column(String(50))
    last_name = Column(String(50))
    gender = Column(types.Choice(Gender))
    date_born = Column(Date)
    marital_status = Column(types.Choice(MaritalStatus))
    state_origin_id = Column(types.UUID, ForeignKey("states.uuid"))
    state_origin = relationship("State")
    nationality_id = Column(types.UUID, ForeignKey("countries.uuid"))
    nationality = relationship("Country")

    @property
    def first_name(self):
        return self.name

    @first_name.setter
    def set_first_name(self, value):
        self.name = value


class OrganizationType(meta.Model, EntityWithDeletedMixin):
    """A model to define the classifications for Organizations.
    """
    __tablename__ = 'organization_types'
    name = Column(String(30), nullable=False, unique=True)
    title = Column(String(30), nullable=False)
    is_root = Column(Boolean(create_constraint=False), default=False)
    organizations = relationship('Organization', back_populates='type',
                                 cascade='all, delete')


class Organization(Party, CoordinatesMixin):
    """A model for storing Organization details.

    :hint: fncode (function code) can be used to indicate the organisation
    function implemented via an enum. e.g HQ, Branch, SalesOffice, ServicePoint
    etc. Its left open to accomodate any int based enum declaration.

    :known issue: deleting a parent organization does not cascade delete to
    child organizations; however setting `cascade='all, delete'` on backref
    for the children relationship gets this working but breaks cascade delete
    for organization type. So working organization type behaviour was settled
    for.
    """
    __tablename__ = 'organizations'
    __mapper_args__ = {
        'polymorphic_identity': PartyType.ORGANIZATION
    }

    uuid = Column(types.UUID, ForeignKey("parties.uuid"), primary_key=True)
    parent_id = Column(types.UUID, ForeignKey("organizations.uuid"))
    code = Column(String(30), nullable=False, unique=True)
    short_name = Column(String(15), unique=True)
    description = Column(String(255))
    date_established = Column(Date)
    website_url = Column(String(150))
    type_id = Column(types.UUID, ForeignKey("organization_types.uuid"), nullable=False)
    type = relationship("OrganizationType", back_populates="organizations")
    children = relationship("Organization", foreign_keys=[parent_id],
                            backref=backref("parent", remote_side=[uuid]))
