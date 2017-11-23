import bcrypt
from datetime import datetime
from sqlalchemy.orm import exc as orm_exc
from .models import (
    _check_password, _hash_password,
    User, Role, AuthEmail
)


class Authenticator(object):
    """Encapsulates user authentication around an explicitly provided Session
    object. This seamlessly fits into whatever Session management strategy in
    use, and effectively `side-steps` whatever complexity that could arise from
    having to create a Session object locally.
    """
    def __init__(self, db_session, accept_email_as_username=False):
        if not db_session:
            raise ValueError('db_session is required.')

        self._db_session = db_session
        self._accept_email_as_username = accept_email_as_username

    def authenticate(self, username, password):
        db = self._db_session
        if self._accept_email_as_username and '@' in username:
            try:
                email = db.query(AuthEmail).filter_by(address=username).first()
                user = email.user if email and email.user and email.user.is_active else None
                if user and _check_password(password, user.password):
                    return user
                return None
            except orm_exc.NoResultFound:
                pass
            return None

        # if code gets this far it could be `accept_email_as_username=False` or
        # treatment of username as email failed thus need to treat username as 
        # just a username
        user = db.query(User).filter_by(username=username, is_active=True).first()
        if user and _check_password(password, user.password):
            return user
        return None

    def __call__(self, username, password):
        """Convenience method for calling `authenticate`.
        """
        return self.authenticate(username, password)
