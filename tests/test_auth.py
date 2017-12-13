import pytest
from datetime import datetime
from elixr.sax import utils
from elixr.sax.meta import Model
from elixr.sax.auth import (
    _hash_password,
    User, Role, AuthEmail, Authenticator
)


class TestBase(object):
    def _clear_tables(self, db, *table_names):
        utils.clear_tables(db, *table_names)


class TestUser(TestBase):
    def test_only_username_adequate_for_creation(self, db):
        self._clear_tables(db)
        user = User(username='scott')
        db.add(user)
        db.commit()
        assert user.id != None and user.id > 0

    def test_commit_fails_for_non_unique_username(self, db):
        self._clear_tables(db)
        db.add(User(username='scott'))
        db.commit()
        with pytest.raises(Exception):
            db.add(User(username='scott'))
            db.commit()
        db.rollback()

    def test_created_inactive_by_default(self, db):
        self._clear_tables(db)
        user = User(username='scott')
        db.add(user)
        db.commit()
        assert user.id != None and user.is_active == False

    def test_date_join_set_on_creation(self, db):
        self._clear_tables(db)
        user = User(username='scott')
        db.add(user)
        db.commit()

        dt_joined = user.date_joined
        assert user.id != None and dt_joined.date() == datetime.now().date()

    def test_added_roles_gets_saved(self, db):
        self._clear_tables(db)
        user = User(username='scott')
        user.roles.append(Role(name='admin'))
        db.add(user)
        db.commit()
        assert user.id != None \
           and len(user.roles) == 1 \
           and user.roles[0].id != None

    def test_added_auth_email_gets_saved(self, db):
        self._clear_tables(db)
        user = User(username='scott')
        user.emails.append(AuthEmail(address='scott@tiger.ora'))
        db.add(user)
        db.commit()
        assert user.id != None \
           and len(user.emails) == 1 \
           and user.emails[0].id != None

    @pytest.mark.parametrize("roles, result", [
        ([Role(name='member')], False),
        ([Role(name='member'), Role(name='admin')], True)])
    def test_is_admin_correctness(self, db, roles, result):
        self._clear_tables(db)
        user = User(username='scott')
        user.roles.extend(roles)
        assert user.is_admin == result

    def test_can_get_confirmed_email_if_exists(self, db):
        self._clear_tables(db)
        user = User(username='scott', password=_hash_password('tiger'))
        user.emails.extend([
            AuthEmail(address='scott@tiger.ora', is_confirmed=True),
            AuthEmail(address='scott@lion.ora')
        ])
        db.add(user)
        db.commit()
        confirmed_emails = user.confirmed_emails
        assert confirmed_emails and len(confirmed_emails) == 1 \
           and confirmed_emails[0].address == 'scott@tiger.ora'

    def test_can_get_preferred_email_if_exists(self, db):
        self._clear_tables(db)
        user = User(username='scott')
        user.emails.extend([
            AuthEmail(address='scott@tiger.ora', is_preferred=True),
            AuthEmail(address='scott@lion.ora')
        ])
        db.add(user)
        db.commit()
        preferred_email = user.preferred_email
        assert preferred_email \
           and preferred_email.address == 'scott@tiger.ora'

    def test_password_can_be_changed(self, db):
        self._clear_tables(db)
        user = User(username='scott')
        db.add(user)
        db.commit()
        assert user and user.id != None \
           and user.password == None

        user.set_password('tiger')
        db.commit()
        assert user.password != None \
           and user.password != 'tiger'


class TestRole(TestBase):
    def test_only_name_adequate_for_creation(self, db):
        self._clear_tables(db)
        role = Role(name='member')
        db.add(role)
        db.commit()
        assert role.id != None and role.id > 0

    def test_commit_fails_for_non_unique_name(self, db):
        self._clear_tables(db)
        db.add(Role(name='member'))
        db.commit()
        with pytest.raises(Exception):
            db.add(Role(name='member'))
            db.commit()
        db.rollback()


class TestAuthEmail(TestBase):
    def test_only_address_adequate_for_creation_when_added_to_user(self, db):
        self._clear_tables(db)
        user = User(username='scott')
        email = AuthEmail(address='scott@tiger.ora')
        user.emails.append(email)
        db.add(user)
        db.commit()
        assert user.id != None \
           and email.id != None \
           and email.user_id == user.uuid

    def test_address_and_user_id_required_for_direct_creation(self, db):
        self._clear_tables(db)
        user = User(username='scott')
        db.add(user)
        db.commit()

        email = AuthEmail(address='scott@tiger.ora', user=user)
        db.add(email)
        db.commit()
        assert email.id != None \
           and email.user_id == user.uuid


class TestAuthenticator(TestBase):
    
    def test_authn_fails_for_non_existing_user(self, db2):
        user_count = db2.query(User).filter_by(username='allen').count()
        assert user_count == 0

        user = Authenticator(db2).authenticate('allen', 'skit')
        assert user == None

    def test_authn_fails_for_wrong_password(self, db2):
        user = Authenticator(db2).authenticate('scott', 'lion')
        assert user == None

    def test_authn_fails_for_wrong_username(self, db2):
        user = Authenticator(db2).authenticate('mike', 'tiger')
        assert user == None

    def test_authn_passes_for_valid_credentials(self, db2):
        user = Authenticator(db2).authenticate('scott', 'tiger')
        assert user != None and user.id != None

    def test_authn_fails_for_valid_creds_bcos_user_inactive(self, db2):
        user = Authenticator(db2).authenticate('mike', 'lion')
        assert user == None

    def test_authn_passes_for_valid_creds_using_email(self, db2):
        authr = Authenticator(db2, accept_email_as_username=True)
        user = authr.authenticate('scott@tiger.ora', 'tiger')
        assert user != None and user.id != None

    def test_authn_fails_for_valid_creds_using_email_bcos_user_inactive(self, db2):
        authr = Authenticator(db2, accept_email_as_username=True)
        user = authr.authenticate('mike@lion.ora', 'lion')
        assert user == None

    def test_can_authn_conveniently_with_valid_creds(seld, db2):
        authn = Authenticator(db2)
        user = authn('scott', 'tiger')
        assert user != None and user.id != None
