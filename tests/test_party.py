import pytest
from datetime import datetime
from sqlalchemy import exc
from elixr.sax.meta import Model
from elixr.sax import utils
from elixr.sax.party import (
    Gender, MaritalStatus, ContactType, PartyType,
    EmailContact, PhoneContact, Party, Person, Organization
)


@pytest.fixture(scope='function')
def db():
    ## setup
    resx = utils.make_session()
    return resx.session
    ## teardown
    utils.drop_tables(resx.engine)


class TestBase(object):
    def _clear_tables(self, db, *table_names):
        utils.clear_tables(db, *table_names)


class TestContactDetail(TestBase):
    def test_only_contact_details_table_created(self):
        table_names = [t.name for t in  Model.metadata.sorted_tables]
        all_names = ":#:".join([t for t in table_names if not 'auth_emails'])
        assert 'contact_details' in table_names \
           and 'email' not in all_names \
           and 'phone' not in all_names

    def test_can_save_email_contact(self, db):
        contact = EmailContact(address="john@doe.ea")
        db.add(contact)
        db.commit()
        assert contact and contact.id != None \
           and contact.usage is None \
           and contact.is_confirmed == False \
           and contact.is_preferred == False \
           and contact.subtype == ContactType.EMAIL

    def test_can_save_phone_contact(self, db):
        contact = PhoneContact(number='08020001000', extension='2')
        db.add(contact)
        db.commit()
        assert contact and contact.id != None \
           and contact.usage == None \
           and contact.is_confirmed == False \
           and contact.is_preferred == False \
           and contact.subtype == ContactType.PHONE


class TestPerson(TestBase):
    def _get_person(self):
        return Person(
            title='Mr', name='John', last_name='Doe',
            gender=Gender.MALE, marital_status=MaritalStatus.SINGLE,
            date_born=datetime.today().date()
        )

    def test_committed_person_has_party_entry(self, db):
        person = self._get_person()
        db.add(person)
        db.commit()
        assert person and person.id != None \
           and person.first_name == person.name

        party = db.query(Party).filter_by(id=person.id).one()
        assert party and party.name == person.first_name \
           and party.subtype == PartyType.PERSON \
           and party.deleted == False
        assert party.uuid == person.uuid

    def test_contacts_can_be_committed(self, db):
        self._clear_tables(db)
        person = self._get_person()
        person.contacts.append(EmailContact(address='john@doe.ea'))
        person.contacts.append(PhoneContact(number='08020001000'))
        db.add(person)
        db.commit()
        assert person and person.id != None \
           and person.contacts != None \
           and len(person.contacts) == 2 \
           and person.contacts[0].id != None \
           and person.contacts[1].id != None


class TestOrganisation(TestBase):
    def test_organisation_has_children_property(self, db):
        org = Organization(name='Hazeltek', code='01')
        assert org.children != None \
           and len(org.children) == 0

    def test_organization_can_ref_children(self, db):
        root = Organization(name='Hazeltek', code='01')
        child1 = Organization(name='Hazeltek Media', code='0101', parent=root)
        child2 = Organization(name='Hazeltek Beverages', code='0102', parent=root)
        db.add(root)
        db.commit()
        assert root.id is not None \
           and root.id != child1.id != child2.id
        assert child1.id != None and child2.id != None
        assert root.children != None and len(root.children) == 2 \
           and child1.parent_id == child2.parent_id
        assert child1.parent_id == root.uuid

    def test_fails_for_cyclic_relationship(self, db):
        self._clear_tables(db)
        root = Organization(name='Hazeltek', code='01')
        child1 = Organization(name='Hazeltek Media', code='0101', parent=root)
        with pytest.raises(exc.CircularDependencyError):
            root.children.append(root)
            db.add(root)
            db.commit()
        db.rollback()

    def test_commit_fails_for_missing_code(self, db):
        self._clear_tables(db)
        org = Organization(name='Hazeltek')
        with pytest.raises(exc.IntegrityError):
            db.add(org)
            db.commit()
        db.rollback()

    def test_commit_fails_for_non_d_code(self, db):
        self._clear_tables(db)
        db.add(Organization(name='Hazeltek', code="01"))
        db.commit()
        with pytest.raises(exc.IntegrityError):
            db.add(Organization(name="Hazel", code="01"))
            db.commit()
        db.rollback()
