import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from bcrypt import checkpw
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime, timezone

from script.db_connection import (
    Base,
    Role,
    Login,
    User,
    HealthcareRecord,
    populate_example_data,
    get_single_user,
    get_all_users,
    get_health_records,
    add_user,
    add_health_record,
    update_health_record,
)

# Expected data from populate_example_data
EXPECTED_ROLES = {
    "Patient": "A patient user, can read own records.",
    "Doctor": "A medical doctor, can read/edit patient records.",
    "Nurse": "A nurse, can read/edit patient records.",
    "Admin": "An administrator, can manage users and roles."
}

EXPECTED_USERS_DATA = [
    {"username": "patient_alice", "password": "password123", "full_name": "Alice Wonderland", "address": "123 Rabbit Hole", "hospital_designation": "Patient", "role": "Patient"},
    {"username": "doctor_bob", "password": "password123", "full_name": "Dr. Bob Smith", "address": "456 Health St", "hospital_designation": "General Practitioner", "role": "Doctor"},
    {"username": "nurse_carol", "password": "password123", "full_name": "Carol Danvers", "address": "789 Care Ave", "hospital_designation": "Registered Nurse", "role": "Nurse"},
    {"username": "admin_dave", "password": "password123", "full_name": "Dave Administrator", "address": "1 Admin Plaza", "hospital_designation": "System Admin", "role": "Admin"},
]

EXPECTED_HEALTH_RECORD_PATIENT_USERNAME = "patient_alice"
EXPECTED_HEALTH_RECORD_UPDATER_USERNAME = "doctor_bob"
EXPECTED_HEALTH_RECORD_DATA = {
    "allergies": ["Penicillin"],
    "conditions": ["Hypertension"],
    "medications": [{"name": "Lisinopril", "dosage": "10mg", "frequency": "daily"}],
    "notes": "Patient presented with high blood pressure."
}

def test_populate_creates_roles(db_engine):
    populate_example_data(db_engine)
    with Session(db_engine) as session:
        roles_in_db = session.execute(select(Role)).scalars().all()
        assert len(roles_in_db) == len(EXPECTED_ROLES), "Incorrect number of roles created."

        for role_name, description in EXPECTED_ROLES.items():
            role = session.execute(
                select(Role).where(Role.role_name == role_name)
            ).scalar_one_or_none()
            assert role is not None, f"Role '{role_name}' not found."
            assert role.description == description, f"Description for role '{role_name}' is incorrect."

def test_populate_creates_users_and_logins(db_engine):
    populate_example_data(db_engine)
    with Session(db_engine) as session:
        users_in_db = session.execute(select(User)).scalars().all()
        logins_in_db = session.execute(select(Login)).scalars().all()

        assert len(users_in_db) == len(EXPECTED_USERS_DATA), "Incorrect number of users created."
        assert len(logins_in_db) == len(EXPECTED_USERS_DATA), "Incorrect number of logins created."

        for user_data in EXPECTED_USERS_DATA:
            # Check Login entry
            login_entry = session.execute(
                select(Login).where(Login.user_name == user_data["username"])
            ).scalar_one_or_none()
            assert login_entry is not None, f"Login entry for '{user_data['username']}' not found."
            assert checkpw(user_data["password"].encode('utf-8'), login_entry.hashed_password), \
                f"Password for '{user_data['username']}' does not match."
            assert login_entry.salt is not None, f"Salt for '{user_data['username']}' is missing."

            # Check User entry
            user_entry = session.execute(
                select(User).where(User.user_name == user_data["username"])
            ).scalar_one_or_none()
            assert user_entry is not None, f"User entry for '{user_data['username']}' not found."
            
            assert user_entry.full_name == user_data["full_name"]
            assert user_entry.address == user_data["address"]
            assert user_entry.hospital_designation == user_data["hospital_designation"]
            assert isinstance(user_entry.system_wide_identifier, uuid.UUID)
            assert isinstance(user_entry.last_updated_at, datetime)
            
            # Check User-Login relationship
            assert user_entry.login_details == login_entry
            assert login_entry.user == user_entry

            # Check User-Role relationship
            assert user_entry.role is not None, f"Role not assigned for user '{user_data['username']}'."
            assert user_entry.role.role_name == user_data["role"]
            assert user_entry.user_role_name == user_data["role"] # Check FK column too

def test_populate_creates_health_record(db_engine):
    populate_example_data(db_engine)
    with Session(db_engine) as session:
        patient_user = session.execute(
            select(User).where(User.user_name == EXPECTED_HEALTH_RECORD_PATIENT_USERNAME)
        ).scalar_one_or_none()
        assert patient_user is not None, f"Patient user '{EXPECTED_HEALTH_RECORD_PATIENT_USERNAME}' not found."

        updater_user = session.execute(
            select(User).where(User.user_name == EXPECTED_HEALTH_RECORD_UPDATER_USERNAME)
        ).scalar_one_or_none()
        assert updater_user is not None, f"Updater user '{EXPECTED_HEALTH_RECORD_UPDATER_USERNAME}' not found."

        health_records = session.execute(
            select(HealthcareRecord).where(HealthcareRecord.patient_user_id == patient_user.user_id)
        ).scalars().all()

        assert len(health_records) == 1, f"Incorrect number of health records for patient '{EXPECTED_HEALTH_RECORD_PATIENT_USERNAME}'."
        
        record = health_records[0]
        assert record.patient_user_id == patient_user.user_id
        assert record.last_updated_by_user_id == updater_user.user_id
        assert isinstance(record.last_updated_at, datetime)
        
        assert record.record_data == EXPECTED_HEALTH_RECORD_DATA

def test_populate_is_idempotent(db_engine):
    # First run
    populate_example_data(db_engine)
    
    with Session(db_engine) as session:
        count_roles1 = session.query(Role).count()
        count_users1 = session.query(User).count()
        count_logins1 = session.query(Login).count()
        count_records1 = session.query(HealthcareRecord).count()

    # Second run
    populate_example_data(db_engine)

    with Session(db_engine) as session:
        count_roles2 = session.query(Role).count()
        count_users2 = session.query(User).count()
        count_logins2 = session.query(Login).count()
        count_records2 = session.query(HealthcareRecord).count()

    assert count_roles1 == count_roles2, "Role count changed on second run."
    assert count_users1 == count_users2, "User count changed on second run."
    assert count_logins1 == count_logins2, "Login count changed on second run."
    assert count_records1 == count_records2, "HealthcareRecord count changed on second run."

def test_get_single_user_success(db_engine):
    """Tests retrieving an existing user by system_wide_identifier."""
    with Session(db_engine) as session:
        # Setup: Create a role and login for the user
        role_name = "TestRoleForGetSingle"
        role = session.query(Role).filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name=role_name, description="Test role")
            session.add(role)
            session.commit()
            role = session.merge(role)

        login_username = "get_single_user_test"
        salt = b"test_salt_single" # Using bytes directly for simplicity in test
        hashed_password = b"test_hashed_password_single"
        login = session.query(Login).filter_by(user_name=login_username).first()
        if not login:
            login = Login(user_name=login_username, hashed_password=hashed_password, salt=salt)
            session.add(login)
            session.commit()
            login = session.merge(login)

        # Create the user
        test_user = User(
            full_name="Get Single Test User",
            address="789 Test Ave",
            hospital_designation="Tester",
        )
        test_user.login_details = login
        test_user.role = role
        session.add(test_user)
        session.commit()
        
        user_swid = test_user.system_wide_identifier # Get the auto-generated SWID

    # Call the function under test
    retrieved_user = get_single_user(db_engine, user_swid)

    assert retrieved_user is not None
    assert retrieved_user.system_wide_identifier == user_swid
    assert retrieved_user.full_name == "Get Single Test User"
    assert retrieved_user.user_name == login_username

def test_get_single_user_not_found(db_engine):
    """Tests that NoResultFound is raised when user with SWID does not exist."""
    non_existent_swid = uuid.uuid4() # Generate a random UUID that won't exist
    with pytest.raises(NoResultFound):
        get_single_user(db_engine, non_existent_swid)

def test_get_all_users_empty(db_engine):
    """Tests that get_all_users returns an empty list when no users exist."""
    # Ensure the database is clean for this test or that no users are added.
    # The db_engine fixture should provide a clean slate.
    users = get_all_users(db_engine)
    assert isinstance(users, list)
    assert len(users) == 0

def test_get_all_users_with_data(db_engine):
    """Tests retrieving all users when some users exist."""
    with Session(db_engine) as session:
        # Setup: Create roles and logins for the users
        role_name1 = "TestRoleForAll1"
        role1 = session.query(Role).filter_by(role_name=role_name1).first()
        if not role1:
            role1 = Role(role_name=role_name1, description="Test role 1")
            session.add(role1)

        role_name2 = "TestRoleForAll2"
        role2 = session.query(Role).filter_by(role_name=role_name2).first()
        if not role2:
            role2 = Role(role_name=role_name2, description="Test role 2")
            session.add(role2)
        session.commit()
        role1 = session.merge(role1)
        role2 = session.merge(role2)

        login1 = Login(user_name="all_user1", hashed_password=b"pass1", salt=b"salt1")
        login2 = Login(user_name="all_user2", hashed_password=b"pass2", salt=b"salt2")
        session.add_all([login1, login2])
        session.commit()
        login1 = session.merge(login1)
        login2 = session.merge(login2)

        # Create users
        user1 = User(full_name="All User One", login_details=login1, role=role1)
        user2 = User(full_name="All User Two", login_details=login2, role=role2)
        session.add_all([user1, user2])
        session.commit()

        user1_swid = user1.system_wide_identifier
        user2_swid = user2.system_wide_identifier

    # Call the function under test
    retrieved_users = get_all_users(db_engine)

    assert isinstance(retrieved_users, list)
    assert len(retrieved_users) == 2
    
    retrieved_swids = {user.system_wide_identifier for user in retrieved_users}
    assert user1_swid in retrieved_swids
    assert user2_swid in retrieved_swids

def test_get_health_records_user_not_found(db_engine):
    """Tests that an empty list is returned when the user SWID does not exist."""
    non_existent_swid = uuid.uuid4()
    records = get_health_records(db_engine, non_existent_swid)
    assert isinstance(records, list)
    assert len(records) == 0

def test_get_health_records_user_exists_no_records(db_engine):
    """Tests that an empty list is returned when the user exists but has no health records."""
    with Session(db_engine) as session:
        role = Role(role_name="PatientRoleForNoRecords", description="Test role")
        login = Login(user_name="patient_no_records", hashed_password=b"pw", salt=b"s")
        session.add_all([role, login])
        session.commit()
        role = session.merge(role)

        patient_user = User(full_name="No Records Patient", login_details=login, role=role)
        session.add(patient_user)
        session.commit()
        patient_swid = patient_user.system_wide_identifier

    records = get_health_records(db_engine, patient_swid)
    assert isinstance(records, list)
    assert len(records) == 0

def test_get_health_records_user_exists_with_one_record(db_engine):
    """Tests retrieving a single health record for an existing user."""
    with Session(db_engine) as session:
        # Setup patient
        patient_role = Role(role_name="PatientRoleWithRecord", description="Test role")
        patient_login = Login(user_name="patient_with_record", hashed_password=b"pw", salt=b"s")
        session.add_all([patient_role, patient_login])
        session.commit()
        patient_role = session.merge(patient_role)

        patient_user = User(full_name="Patient With Record", login_details=patient_login, role=patient_role)
        session.add(patient_user)
        session.commit()
        patient_swid = patient_user.system_wide_identifier
        patient_id = patient_user.user_id

        # Setup updater (can be the same user or different)
        updater_user = patient_user # For simplicity, patient updates their own record

        # Create health record
        record_data = {"notes": "Single test record"}
        health_record = HealthcareRecord(
            patient_user_id=patient_id,
            record_data=record_data,
            last_updated_by_user_id=updater_user.user_id
        )
        session.add(health_record)
        session.commit()
        record_id = health_record.record_id

    retrieved_records = get_health_records(db_engine, patient_swid)
    assert isinstance(retrieved_records, list)
    assert len(retrieved_records) == 1
    assert retrieved_records[0].record_id == record_id
    assert retrieved_records[0].record_data == record_data
    assert retrieved_records[0].patient_user_id == patient_id

def test_get_health_records_user_exists_with_multiple_records(db_engine):
    """Tests retrieving multiple health records for an existing user."""
    with Session(db_engine) as session:
        # Setup patient
        patient_role = Role(role_name="PatientRoleMultiRecords", description="Test role")
        patient_login = Login(user_name="patient_multi_records", hashed_password=b"pw", salt=b"s")
        session.add_all([patient_role, patient_login])
        session.commit()
        patient_role = session.merge(patient_role)

        patient_user = User(full_name="Patient Multi Records", login_details=patient_login, role=patient_role)
        session.add(patient_user)
        session.commit()
        patient_swid = patient_user.system_wide_identifier
        patient_id = patient_user.user_id

        # Create health records
        record_data1 = {"notes": "Test record one"}
        record1 = HealthcareRecord(patient_user_id=patient_id, record_data=record_data1, last_updated_by_user_id=patient_id)
        
        record_data2 = {"notes": "Test record two"}
        record2 = HealthcareRecord(patient_user_id=patient_id, record_data=record_data2, last_updated_by_user_id=patient_id)
        
        session.add_all([record1, record2])
        session.commit()
        
        record1_id = record1.record_id
        record2_id = record2.record_id

    retrieved_records = get_health_records(db_engine, patient_swid)
    assert isinstance(retrieved_records, list)
    assert len(retrieved_records) == 2

    retrieved_record_ids = {rec.record_id for rec in retrieved_records}
    assert record1_id in retrieved_record_ids
    assert record2_id in retrieved_record_ids

    # Optional: Check data if needed, though IDs are usually sufficient for "all"
    # assert any(rec.record_data == record_data1 for rec in retrieved_records)
    # assert any(rec.record_data == record_data2 for rec in retrieved_records)

def test_add_user_success(db_engine):
    """Tests successfully adding a new user."""
    username = "new_test_user"
    password = "password123"
    full_name = "New Test User Fullname"
    address = "123 Test Street"
    hospital_designation = "Test Designee"

    add_user(db_engine, username, password, full_name, address, hospital_designation)

    with Session(db_engine) as session:
        # Check Login entry
        login_entry = session.query(Login).filter_by(user_name=username).one_or_none()
        assert login_entry is not None, "Login entry was not created."
        assert login_entry.user_name == username
        assert login_entry.salt is not None
        assert checkpw(password.encode('utf-8'), login_entry.hashed_password), "Password verification failed."

        # Check User entry
        user_entry = session.query(User).filter_by(user_name=username).one_or_none()
        assert user_entry is not None, "User entry was not created."
        assert user_entry.full_name == full_name
        assert user_entry.address == address
        assert user_entry.hospital_designation == hospital_designation
        assert user_entry.user_name == username
        assert user_entry.login_details == login_entry
        assert login_entry.user == user_entry
        assert user_entry.role is None, "User should not have a role assigned by default by add_user."
        assert user_entry.user_role_name is None

def test_add_user_duplicate_username(db_engine):
    """Tests that adding a user with a duplicate username raises ValueError."""
    username = "duplicate_user_test"
    password = "password123"
    full_name = "Duplicate User"
    address = "456 Duplicate Ave"
    hospital_designation = "Duplicate Designee"

    # Add the user for the first time
    add_user(db_engine, username, password, full_name, address, hospital_designation)

    # Attempt to add the same user again
    with pytest.raises(ValueError, match=f"Login username '{username}' already exists."):
        add_user(db_engine, username, "another_password", "Another Name", "Another Address", "Another Designation")

    # Verify only one user and login with that username exists
    with Session(db_engine) as session:
        assert session.query(Login).filter_by(user_name=username).count() == 1
        assert session.query(User).filter_by(user_name=username).count() == 1

def test_add_health_record_success(db_engine):
    """Tests successfully adding a new health record for a user."""
    with Session(db_engine) as session:
        # Setup: Create a patient user and a creator user
        role_name = "TestRoleForHealthRecordAdd"
        role = session.query(Role).filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name=role_name, description="Test role for adding health records")
            session.add(role)
            session.commit()
            role = session.merge(role)

        patient_login = Login(user_name="patient_hr_add", hashed_password=b"pw1", salt=b"s1")
        creator_login = Login(user_name="creator_hr_add", hashed_password=b"pw2", salt=b"s2")
        session.add_all([patient_login, creator_login])
        session.commit()
        patient_login = session.merge(patient_login)
        creator_login = session.merge(creator_login)

        patient_user = User(full_name="Patient For HR Add", login_details=patient_login, role=role)
        creator_user = User(full_name="Creator For HR Add", login_details=creator_login, role=role)
        session.add_all([patient_user, creator_user])
        session.commit()

        patient_user_id = patient_user.user_id
        creator_user_id = creator_user.user_id

    record_data = {"symptoms": "headache", "diagnosis": "stress"}

    # Call the function under test
    add_health_record(db_engine, patient_user_id, record_data, creator_user_id)

    # Verify the record was added
    with Session(db_engine) as session:
        added_record = session.query(HealthcareRecord).filter_by(
            patient_user_id=patient_user_id,
            last_updated_by_user_id=creator_user_id
        ).one_or_none()

        assert added_record is not None, "Health record was not added."
        assert added_record.patient_user_id == patient_user_id
        assert added_record.record_data == record_data
        assert added_record.last_updated_by_user_id == creator_user_id
        assert isinstance(added_record.last_updated_at, datetime), "last_updated_at was not set."
        # Check if the timestamp is recent (e.g., within the last few seconds)
        assert (datetime.now(timezone.utc) - added_record.last_updated_at).total_seconds() < 5

def test_update_health_record_success(db_engine):
    """Tests successfully updating an existing health record."""
    with Session(db_engine) as session:
        # Setup: Create patient, initial creator, and updater users
        role = Role(role_name="TestRoleForUpdateHR", description="Test role for updating HR")
        session.add(role)
        session.commit()
        role = session.merge(role)

        patient_login = Login(user_name="patient_hr_update", hashed_password=b"pw_p", salt=b"s_p")
        initial_creator_login = Login(user_name="creator_hr_initial", hashed_password=b"pw_c", salt=b"s_c")
        updater_login = Login(user_name="updater_hr_final", hashed_password=b"pw_u", salt=b"s_u")
        session.add_all([patient_login, initial_creator_login, updater_login])
        session.commit()
        patient_login, initial_creator_login, updater_login = \
            session.merge(patient_login), session.merge(initial_creator_login), session.merge(updater_login)

        patient_user = User(full_name="Patient For HR Update", login_details=patient_login, role=role)
        initial_creator_user = User(full_name="Initial HR Creator", login_details=initial_creator_login, role=role)
        updater_user = User(full_name="Final HR Updater", login_details=updater_login, role=role)
        session.add_all([patient_user, initial_creator_user, updater_user])
        session.commit()

        patient_user_id = patient_user.user_id
        initial_creator_user_id = initial_creator_user.user_id
        updater_user_id = updater_user.user_id

        # Add an initial health record
        initial_record_data = {"condition": "flu", "treatment": "rest"}
        initial_record = HealthcareRecord(
            patient_user_id=patient_user_id,
            record_data=initial_record_data,
            last_updated_by_user_id=initial_creator_user_id
        )
        session.add(initial_record)
        session.commit()
        record_id_to_update = initial_record.record_id
        original_last_updated_at = initial_record.last_updated_at

    # Data for the update
    updated_record_data = {"condition": "recovered", "treatment": "none", "notes": "Patient feels better."}

    # Call the function under test
    update_health_record(db_engine, updater_user_id, record_id_to_update, updated_record_data)

    # Verify the record was updated
    with Session(db_engine) as session:
        updated_record = session.query(HealthcareRecord).filter_by(record_id=record_id_to_update).one_or_none()

        assert updated_record is not None, "Health record not found after update attempt."
        assert updated_record.patient_user_id == patient_user_id, "Patient ID should not change."
        assert updated_record.record_data == updated_record_data, "Record data was not updated correctly."
        assert updated_record.last_updated_by_user_id == updater_user_id, "Updater user ID was not set correctly."
        assert updated_record.last_updated_at is not None, "last_updated_at should be set."
        assert updated_record.last_updated_at > original_last_updated_at, "last_updated_at was not updated."

def test_update_health_record_not_found(db_engine):
    """Tests that updating a non-existent health record raises NoResultFound."""
    non_existent_record_id = 99999  # An ID that is unlikely to exist
    updater_user_id = 1 # A dummy user ID for the updater; doesn't matter as record won't be found
    record_data_for_update = {"notes": "Attempting to update non-existent record."}

    with pytest.raises(NoResultFound):
        update_health_record(db_engine, updater_user_id, non_existent_record_id, record_data_for_update)