import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from bcrypt import gensalt, hashpw
from script.db_connection import Role, Login, User, HealthcareRecord, continuum_utils


#Tests for role table
def test_create_role(db_engine):
    """
    Test creating a new Role and persisting it to the database.
    """
    role_name = "TestRole"
    description = "A role for testing purposes."

    with Session(db_engine) as session:
        new_role = Role(role_name=role_name, description=description)
        session.add(new_role)
        session.commit()

        # Retrieve the role from the database
        retrieved_role = session.get(Role, role_name)

        assert retrieved_role is not None
        assert retrieved_role.role_name == role_name
        assert retrieved_role.description == description
        assert isinstance(retrieved_role.users, list) # users should be an empty list initially
        assert len(retrieved_role.users) == 0

def test_role_repr(db_engine):
    """
    Test the __repr__ method of the Role model.
    """
    role_name = "ReprRole"
    description = "Testing representation."
    
    # No need to add to session for __repr__ test if not checking DB state
    role = Role(role_name=role_name, description=description)
    
    expected_repr = f"<Role(role_name='{role_name}')>"
    assert repr(role) == expected_repr

def test_role_primary_key_uniqueness(db_engine):
    """
    Test that the role_name (primary key) enforces uniqueness.
    Attempting to add a role with an existing role_name should fail.
    """
    role_name = "UniqueRole"
    description1 = "First instance of UniqueRole."
    description2 = "Second instance of UniqueRole, should fail."

    with Session(db_engine) as session:
        # Add the first role
        role1 = Role(role_name=role_name, description=description1)
        session.add(role1)
        session.commit()

        # Attempt to add another role with the same role_name
        role2 = Role(role_name=role_name, description=description2)
        session.add(role2)
        with pytest.raises(IntegrityError):
            session.commit() # This should fail due to primary key constraint


#Tests for login table
def test_login_repr_method():
    """Tests the __repr__ method of the Login model."""
    salt = gensalt()
    hashed_password = hashpw(b"testpassword_repr", salt)
    login = Login(user_name="repr_user", hashed_password=hashed_password, salt=salt)
    assert repr(login) == "<Login(user_name='repr_user')>"


def test_login_username_primary_key_constraint(db_engine):
    """Tests that the user_name in Login is a primary key and must be unique."""
    salt = gensalt()
    hashed_password = hashpw(b"password123_pk", salt)
    
    login1_username = "unique_pk_user_test"

    with Session(db_engine) as session:
        # Add the first login
        login1 = Login(user_name=login1_username, hashed_password=hashed_password, salt=salt)
        session.add(login1)
        session.commit()

        # Attempt to add another login with the same username
        login2 = Login(user_name=login1_username, hashed_password=hashed_password, salt=salt)
        session.add(login2)
        
        # This commit should fail due to primary key violation
        with pytest.raises(IntegrityError):
            session.commit()


def test_login_user_relationship_cascade_delete(db_engine):
    """Tests that deleting a Login instance cascades to delete the associated User."""
    login_username = "user_for_cascade_delete"
    salt = gensalt()
    hashed_password = hashpw(b"cascade_pass_test", salt)

    with Session(db_engine) as session:
        # 1. Ensure a Role exists for the User, as User.user_role_name is a ForeignKey
        role_name = "TestRoleForCascadeLogin" # Use a distinct role name to avoid conflicts
        role = session.query(Role).filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name=role_name, description="A test role for login cascade delete")
            session.add(role)
            session.commit() 
            role = session.merge(role) 

        # 2. Create Login and User instances
        new_login = Login(user_name=login_username, hashed_password=hashed_password, salt=salt)
        new_user = User(
            full_name="Cascade Delete User via Login",
            address="123 Cascade Lane",
            hospital_designation="Test Subject",
            user_role_name=role.role_name 
        )
        new_user.login_details = new_login 
        
        session.add(new_user) 
        session.commit()

        retrieved_login = session.query(Login).filter_by(user_name=login_username).one()
        user_id_to_check = retrieved_login.user.user_id

        session.delete(retrieved_login)
        session.commit()

        assert session.query(Login).filter_by(user_name=login_username).one_or_none() is None
        assert session.query(User).filter_by(user_id=user_id_to_check).one_or_none() is None, \
            "User associated with the deleted Login should also have been deleted by cascade."
        
#Tests for user table
def test_user_repr_method(db_engine):
    """Tests the __repr__ method of the User model."""
    user_name = "repr_user_for_user_model"
    with Session(db_engine) as session:
        # Minimal setup for User repr
        salt = gensalt()
        hashed_password = hashpw(b"password", salt)
        login = Login(user_name=user_name, hashed_password=hashed_password, salt=salt)
        
        # Role is needed
        role = Role(role_name="TestRoleForUserRepr", description="Test role")
        session.add_all([login, role])
        session.commit()
        role = session.merge(role) # Ensure role has ID

        user = User(
            full_name="Repr Test User", 
            login_details=login, # This sets user.user_name
            role=role
        )
        session.add(user)
        session.commit()
        
        # The 'user' instance is now persistent and in the session.
        # Refresh its state from the database to pick up any server-side changes
        # or attributes populated by extensions like Continuum.
        session.refresh(user)

        expected_repr = f"<User(user_name='{user_name}', system_id='{user.system_wide_identifier}', version=0)>"
        # Version is 0 for new unversioned object or first version of versioned.
        # If __versioned__ = {} is active and it's the first save, it should be 0.
        assert repr(user) == expected_repr
        # Additional check using continuum_utils
        assert continuum_utils.is_versioned(user)
        assert continuum_utils.count_versions(user) == 1 # Initial version means 1 total version

def test_user_creation_and_attributes(db_engine):
    """Tests basic creation of a User and its attributes."""
    user_name = "new_user_creation"
    full_name = "New User Full Name"
    address = "123 New St"
    hospital_designation = "Tester"
    role_name = "TestRoleForUserCreation"

    with Session(db_engine) as session:
        salt = gensalt()
        hashed_password = hashpw(b"securepass", salt)
        login = Login(user_name=user_name, hashed_password=hashed_password, salt=salt)
        
        role = session.query(Role).filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name=role_name, description="Test role for user creation")
            session.add(role)
            session.commit()
            role = session.merge(role)

        user = User(
            full_name=full_name,
            address=address,
            hospital_designation=hospital_designation,
        )
        user.login_details = login # This sets user.user_name
        user.role = role # This sets user.user_role_name

        session.add(user)
        session.commit()

        retrieved_user = session.query(User).filter_by(user_name=user_name).one()
        
        assert retrieved_user.full_name == full_name
        assert retrieved_user.address == address
        assert retrieved_user.hospital_designation == hospital_designation
        assert retrieved_user.user_name == user_name
        assert isinstance(retrieved_user.system_wide_identifier, uuid.UUID)
        assert isinstance(retrieved_user.last_updated_at, datetime)
        assert retrieved_user.role == role
        assert retrieved_user.user_role_name == role_name
        assert retrieved_user.login_details == login
        assert login.user == retrieved_user

def test_user_system_wide_identifier_uniqueness(db_engine):
    """Tests that system_wide_identifier is unique and auto-generated."""
    with Session(db_engine) as session:
        role = Role(role_name="GenericRoleForUniqueness", description="...")
        login1 = Login(user_name="user1_uniq_swid", hashed_password=b"...", salt=b"...")
        login2 = Login(user_name="user2_uniq_swid", hashed_password=b"...", salt=b"...")
        session.add_all([role, login1, login2])
        session.commit()
        role = session.merge(role)

        user1 = User(full_name="User One", login_details=login1, role=role)
        user2 = User(full_name="User Two", login_details=login2, role=role)
        session.add_all([user1, user2])
        session.commit()

        assert user1.system_wide_identifier is not None
        assert user2.system_wide_identifier is not None
        assert user1.system_wide_identifier != user2.system_wide_identifier

def test_user_last_updated_at_on_update(db_engine):
    """Tests that last_updated_at is updated when a user record changes."""
    with Session(db_engine) as session:
        role = Role(role_name="RoleForUpdateTest", description="...")
        login = Login(user_name="user_update_test", hashed_password=b"...", salt=b"...")
        session.add_all([role, login])
        session.commit()
        role = session.merge(role)

        user = User(full_name="Initial Name", login_details=login, role=role)
        session.add(user)
        session.commit()
        
        initial_update_time = user.last_updated_at
        
        # Make a change and commit
        # To ensure time difference, can sleep or just rely on DB precision
        user.full_name = "Updated Name"
        session.commit()
        session.refresh(user) # Refresh to get the new timestamp from DB

        assert user.last_updated_at > initial_update_time

def test_user_self_referential_updated_by(db_engine):
    """Tests the self-referential updated_by_user relationship."""
    with Session(db_engine) as session:
        role = Role(role_name="RoleForSelfRef", description="...")
        login_updater = Login(user_name="updater_user", hashed_password=b"...", salt=b"...")
        login_updated = Login(user_name="updated_user_ref", hashed_password=b"...", salt=b"...")
        session.add_all([role, login_updater, login_updated])
        session.commit()
        role = session.merge(role)

        updater_user = User(full_name="Updater User", login_details=login_updater, role=role)
        updated_user = User(full_name="User Being Updated", login_details=login_updated, role=role)
        session.add_all([updater_user, updated_user])
        session.commit() # Commit to assign user_ids

        updated_user.updated_by_user_id = updater_user.user_id
        session.commit()

        assert updated_user.updated_by_user == updater_user
        assert updater_user in [u.updated_by_user for u in session.query(User).filter(User.updated_by_user_id == updater_user.user_id).all()]
        # More direct check for users_they_updated
        session.refresh(updater_user) # Refresh to load the users_they_updated collection
        assert updated_user in updater_user.users_they_updated

def test_user_healthcare_record_relationships(db_engine):
    """Tests relationships to HealthcareRecord (patient_records and updated_records)."""
    with Session(db_engine) as session:
        role = Role(role_name="RoleForHealthRec", description="...")
        login_patient = Login(user_name="patient_user_hr", hashed_password=b"...", salt=b"...")
        login_doctor = Login(user_name="doctor_user_hr", hashed_password=b"...", salt=b"...")
        session.add_all([role, login_patient, login_doctor])
        session.commit()
        role = session.merge(role)

        patient_user = User(full_name="Patient For Record", login_details=login_patient, role=role)
        doctor_user = User(full_name="Doctor For Record", login_details=login_doctor, role=role)
        session.add_all([patient_user, doctor_user])
        session.commit() # Commit to assign user_ids

        record_data = {"notes": "Test record"}
        health_record = HealthcareRecord(
            patient_user_id=patient_user.user_id,
            record_data=record_data,
            last_updated_by_user_id=doctor_user.user_id
        )
        session.add(health_record)
        session.commit()

        session.refresh(patient_user)
        session.refresh(doctor_user)
        session.refresh(health_record)

        assert health_record in patient_user.patient_records
        assert health_record.patient == patient_user

        assert health_record in doctor_user.updated_records
        assert health_record.last_updated_by == doctor_user

def test_user_versioning_on_update(db_engine):
    """Tests that User version increments on update."""
    with Session(db_engine) as session:
        # 1. Setup: Role, Logins, and Users
        role_name = "TestRoleForUserVersioning"
        role = session.query(Role).filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name=role_name, description="Role for user versioning test")
            session.add(role)
            session.commit()
            role = session.merge(role) # Ensure it's in the session with its ID

        # User to be versioned
        user_to_version_username = "versioned_user_test"
        salt1 = gensalt()
        hashed_password1 = hashpw(b"pass_version1", salt1)
        login1 = Login(user_name=user_to_version_username, hashed_password=hashed_password1, salt=salt1)
        
        # Updater user
        updater_username = "updater_for_user_version_test"
        salt2 = gensalt()
        hashed_password2 = hashpw(b"pass_updater_version", salt2)
        login2 = Login(user_name=updater_username, hashed_password=hashed_password2, salt=salt2)

        session.add_all([login1, login2])
        session.commit()
        # login1 = session.merge(login1) # Not strictly necessary if using directly
        # login2 = session.merge(login2)

        user_to_version = User(
            full_name="Initial Versioned Name",
            address="123 Original St",
            hospital_designation="Junior Tester"
        )
        user_to_version.login_details = login1
        user_to_version.role = role

        updater_user = User(full_name="User Updater", hospital_designation="Admin")
        updater_user.login_details = login2
        updater_user.role = role

        session.add_all([user_to_version, updater_user])
        session.commit()
        session.refresh(user_to_version) # Refresh to get sa_version and other DB defaults

        # 2. Check initial version
        assert continuum_utils.is_versioned(user_to_version), "User should be versioned."
        initial_version_count = continuum_utils.count_versions(user_to_version)
        assert initial_version_count == 1, f"Initial version count should be 1, got {initial_version_count}"

        # 3. First update
        user_to_version.full_name = "Versioned Name - Updated"
        user_to_version.address = "456 New Address St"
        user_to_version.updated_by_user_id = updater_user.user_id # Set who updated it
        session.commit()
        # No need to refresh user_to_version for count_versions to work on persisted object
        first_update_version_count = continuum_utils.count_versions(user_to_version)
        assert first_update_version_count == 2, f"Version count after first update should be 2, got {first_update_version_count}"

        # 4. Second update
        user_to_version.hospital_designation = "Senior Tester"
        session.commit()
        # No need to refresh
        second_update_version_count = continuum_utils.count_versions(user_to_version)
        assert second_update_version_count == 3, f"Version count after second update should be 3, got {second_update_version_count}"

#Tests for healthcarerecord table

def test_healthcare_record_missing_patient_user_id(db_engine):
    """Tests that creating a HealthcareRecord without a patient_user_id raises IntegrityError."""
    with Session(db_engine) as session:
        # Minimal setup for a user who could be an updater
        role = Role(role_name="TestRoleForHRConstraint_NoPatient", description="Test role for HR constraint")
        login = Login(user_name="updater_hr_constraint_nopatient", hashed_password=b"dummy_hash", salt=b"dummy_salt")
        session.add_all([role, login])
        session.commit()
        # Re-fetch role to ensure it's bound to the session with its ID
        role = session.merge(role) 

        updater_user = User(full_name="Updater Only", login_details=login, role=role)
        session.add(updater_user)
        session.commit() # Commit to get updater_user.user_id

        record = HealthcareRecord(
            # patient_user_id is deliberately omitted (will be None by default if not assigned)
            record_data={"notes": "Test data, no patient"},
            last_updated_by_user_id=updater_user.user_id
        )
        session.add(record)
        with pytest.raises(IntegrityError, match=r'.*null value in column "patient_user_id".*'):
            session.commit() # patient_user_id is nullable=False

def test_healthcare_record_nullable_last_updated_by(db_engine):
    """Tests that HealthcareRecord can be created with last_updated_by_user_id as None."""
    with Session(db_engine) as session:
        # Minimal setup for a patient user
        role = Role(role_name="TestRoleForHRNullableUpdater", description="Test role for nullable updater")
        login_patient = Login(user_name="patient_hr_nullable_updater", hashed_password=b"dummy_hash", salt=b"dummy_salt")
        session.add_all([role, login_patient])
        session.commit()
        role = session.merge(role)

        patient_user = User(full_name="Patient Nullable Updater", login_details=login_patient, role=role)
        session.add(patient_user)
        session.commit() # Commit to get patient_user.user_id

        record = HealthcareRecord(
            patient_user_id=patient_user.user_id,
            record_data={"notes": "Test data with null updater"},
            last_updated_by_user_id=None # This should be allowed as column is nullable
        )
        session.add(record)
        session.commit() # Should not raise error

        retrieved_record = session.get(HealthcareRecord, record.record_id)
        assert retrieved_record is not None
        assert retrieved_record.last_updated_by_user_id is None
        assert retrieved_record.last_updated_by is None # Relationship should also be None

def test_healthcare_record_versioning_on_update(db_engine):
    """Tests that HealthcareRecord version increments on update."""
    with Session(db_engine) as session:
        # Setup: Role, Logins, Patient User, Doctor User
        role = Role(role_name="TestRoleForHRVersioning", description="Test role for HR versioning")
        login_patient = Login(user_name="patient_hr_versioning", hashed_password=b"dummy_hash_p", salt=b"dummy_salt_p")
        login_doctor = Login(user_name="doctor_hr_versioning", hashed_password=b"dummy_hash_d", salt=b"dummy_salt_d")
        session.add_all([role, login_patient, login_doctor])
        session.commit()
        role = session.merge(role)

        patient = User(full_name="Patient HR Versioning", login_details=login_patient, role=role)
        doctor = User(full_name="Doctor HR Versioning", login_details=login_doctor, role=role)
        session.add_all([patient, doctor])
        session.commit() # Commit to get user_ids

        # Create initial record
        record = HealthcareRecord(
            patient_user_id=patient.user_id,
            record_data={"visit": 1, "notes": "Initial visit"},
            last_updated_by_user_id=doctor.user_id
        )
        session.add(record)
        session.commit()
        session.refresh(record) # Refresh to get version and other db-generated values

        assert continuum_utils.is_versioned(record), "Record should be versioned."
        initial_version_count = continuum_utils.count_versions(record)
        assert initial_version_count == 1, f"Initial version count should be 1, got {initial_version_count}"

        # First update
        record.record_data = {"visit": 1, "notes": "Initial visit - updated notes"}
        # last_updated_at and last_updated_by_user_id should be updated by application logic
        # For this test, we manually set last_updated_by_user_id if it changes,
        # and last_updated_at is handled by onupdate=func.now()
        record.last_updated_by_user_id = doctor.user_id
        session.commit()
        # No need to refresh record for count_versions
        first_update_version_count = continuum_utils.count_versions(record)
        assert first_update_version_count == 2, f"Version count after first update should be 2, got {first_update_version_count}"

        # Second update
        record.record_data = {"visit": 2, "notes": "Second visit"}
        record.last_updated_by_user_id = doctor.user_id # Or a different user
        session.commit()
        # No need to refresh
        second_update_version_count = continuum_utils.count_versions(record)
        assert second_update_version_count == 3, f"Version count after second update should be 3, got {second_update_version_count}"
