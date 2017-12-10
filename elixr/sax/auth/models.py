"""Provides SQLAlchemy based model classes and utility functions which form the
base on which to implement a simple role based security for an applicatin.
"""
import bcrypt
from sqlalchemy import (
    Column, Boolean, DateTime, ForeignKey, Integer,
    String, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from elixr.base import generate_random_digest

from ..mixins import IdsMixin
from .. import meta, types



## FUNCS
def generate_confirmation_hash():
    return generate_random_digest(num_bytes=14)


def _check_password(passwd, passwd_hash):
    expected_hash = passwd_hash.encode('utf8')
    return bcrypt.checkpw(passwd.encode('utf8'), expected_hash)


def _hash_password(passwd):
    pwhash = bcrypt.hashpw(passwd.encode('utf8'), bcrypt.gensalt())
    return pwhash.decode('utf8')


## MODELS
# many-to-many relation between users and roles
auth_users_roles_table = Table(
    'auth_users_roles', meta.metadata,
    Column('user_id', types.UUID, ForeignKey('auth_users.uuid')),
    Column('role_id', types.UUID, ForeignKey('auth_roles.uuid'))
)


class User(meta.Model, IdsMixin):
    """A model for storing User data.
    """
    __tablename__ = 'auth_users'

    username = Column(String(32), nullable=False, unique=True)
    first_name = Column(String(30))
    last_name = Column(String(30))
    password = Column(String(150))
    is_active = Column(Boolean(create_constraint=False), nullable=False, default=False)
    date_joined = Column(DateTime, nullable=False, default=func.now())
    last_login = Column(DateTime, nullable=True)
    roles = relationship("Role", secondary="auth_users_roles", lazy="joined")
    emails = relationship("AuthEmail", lazy="joined", back_populates="user")

    @property
    def is_admin(self):
        """Does user have a role called 'admin'?
        """
        for role in self.roles:
            if role.name == 'admin':
                return True
        return False

    @property
    def confirmed_emails(self):
        """Returns a list of confirmed emails.
        """
        return [e for e in self.emails if e.is_confirmed]

    @property
    def has_confirmed_emails(self):
        """Indicates whether the user has got any confirmed emails.
        """
        return bool(self.confirmed_emails)

    @property
    def preferred_email(self):
        if self.emails:
            preferred = [e for e in self.emails if e.is_preferred]
            if preferred:
                return preferred[0]
            return self.emails[0]
        return None

    @preferred_email.setter
    def set_preferred_email(self, email):
        for em in self.emails:
            if em is not email:
                em.is_preferred = False
        email.is_preferred = True
        if not email in self.emails:
            self.emails.append(email)

    def check_password(self, raw_password):
        if self.password != None:
            return _check_password(raw_password, self.password)
        return False

    def set_password(self, raw_password):
        if raw_password != None:
            self.password = _hash_password(raw_password)


class Role(meta.Model, IdsMixin):
    """A model for storing Role data.
    """
    __tablename__ = 'auth_roles'

    name = Column(String(30), nullable=False, unique=True)
    description = Column(String(256))


class AuthEmail(meta.Model, IdsMixin):
    """A model for storing Email addresses associated to a User model.
    """
    __tablename__ = 'auth_emails'

    address = Column(String(150), nullable=False, unique=True)
    user_id = Column(types.UUID, ForeignKey('auth_users.uuid'), nullable=False)
    confirmation_hash = Column(String(32), default=generate_confirmation_hash)
    is_confirmed = Column(Boolean(create_constraint=False), default=False)
    is_preferred = Column(Boolean(create_constraint=False), default=False)
    user = relationship("User", back_populates="emails")
