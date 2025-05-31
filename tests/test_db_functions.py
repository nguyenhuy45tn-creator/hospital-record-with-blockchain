import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from bcrypt import checkpw
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime, timezone
from script import db_connection
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
    "patient": "A patient user, can read own records.",
    "doctor": "A medical doctor, can read/edit patient records.",
    "nurse": "A nurse, can read/edit patient records.",
    "admin": "An administrator, can manage users and roles."
}

EXPECTED_USERS_DATA = [
    {"username": "patient_alice", "password": "password123", "full_name": "Alice Wonderland", "address": "123 Rabbit Hole", "hospital_designation": "Patient", "role": "patient"},
    {"username": "doctor_bob", "password": "password123", "full_name": "Dr. Bob Smith", "address": "456 Health St", "hospital_designation": "General Practitioner", "role": "doctor"},
    {"username": "nurse_carol", "password": "password123", "full_name": "Carol Danvers", "address": "789 Care Ave", "hospital_designation": "Registered Nurse", "role": "nurse"},
    {"username": "admin_dave", "password": "password123", "full_name": "Dave Administrator", "address": "1 Admin Plaza", "hospital_designation": "System Admin", "role": "admin"},
]

EXPECTED_HEALTH_RECORD_patient_USERNAME = "patient_alice"
EXPECTED_HEALTH_RECORD_UPDATER_USERNAME = "doctor_bob"
EXPECTED_HEALTH_RECORD_DATA = {
    "allergies": ["Penicillin"],
    "conditions": ["Hypertension"],
    "medications": [{"name": "Lisinopril", "dosage": "10mg", "frequency": "daily"}],
    "notes": "Patient presented with high blood pressure."
}

def test_populate_creates_roles(db_engine):
    db_connection.engine = db_engine
    populate_example_data()
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
    db_connection.engine = db_engine
    populate_example_data()
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
    db_connection.engine = db_engine
    populate_example_data()
    with Session(db_engine) as session:
        patient_user = session.execute(
            select(User).where(User.user_name == EXPECTED_HEALTH_RECORD_patient_USERNAME)
        ).scalar_one_or_none()
        assert patient_user is not None, f"patient user '{EXPECTED_HEALTH_RECORD_patient_USERNAME}' not found."

        updater_user = session.execute(
            select(User).where(User.user_name == EXPECTED_HEALTH_RECORD_UPDATER_USERNAME)
        ).scalar_one_or_none()
        assert updater_user is not None, f"Updater user '{EXPECTED_HEALTH_RECORD_UPDATER_USERNAME}' not found."

        health_records = session.execute(
            select(HealthcareRecord).where(HealthcareRecord.patient_user_id == patient_user.user_id)
        ).scalars().all()

        assert len(health_records) == 1, f"Incorrect number of health records for patient '{EXPECTED_HEALTH_RECORD_patient_USERNAME}'."
        
        record = health_records[0]
        assert record.patient_user_id == patient_user.user_id
        assert record.last_updated_by_user_id == updater_user.user_id
        assert isinstance(record.last_updated_at, datetime)
        
        assert record.record_data == EXPECTED_HEALTH_RECORD_DATA

def test_populate_is_idempotent(db_engine):
    db_connection.engine = db_engine
    # First run
    populate_example_data()
    
    with Session(db_engine) as session:
        count_roles1 = session.query(Role).count()
        count_users1 = session.query(User).count()
        count_logins1 = session.query(Login).count()
        count_records1 = session.query(HealthcareRecord).count()

    # Second run
    populate_example_data()

    with Session(db_engine) as session:
        count_roles2 = session.query(Role).count()
        count_users2 = session.query(User).count()
        count_logins2 = session.query(Login).count()
        count_records2 = session.query(HealthcareRecord).count()

    assert count_roles1 == count_roles2, "Role count changed on second run."
    assert count_users1 == count_users2, "User count changed on second run."
    assert count_logins1 == count_logins2, "Login count changed on second run."
    assert count_records1 == count_records2, "HealthcareRecord count changed on second run."

def test_get_single_user_success(db_engine, role_right_checker_db_connection):
    """Tests retrieving an existing user by system_wide_identifier."""
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    populate_example_data() # Ensure requestee 'doctor_bob' and roles exist
    requestee_username = "doctor_bob" # Has READ_PATIENT_BASIC_DATA

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
    retrieved_user = get_single_user(requestee_username, user_swid)

    assert retrieved_user is not None
    assert retrieved_user.system_wide_identifier == user_swid
    assert retrieved_user.full_name == "Get Single Test User"
    assert retrieved_user.user_name == login_username

def test_get_single_user_not_found(db_engine, role_right_checker_db_connection):
    """Tests that ValueError is raised when user with SWID does not exist."""
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    populate_example_data() # Ensure requestee 'doctor_bob' exists
    requestee_username = "doctor_bob"

    non_existent_swid = uuid.uuid4() # Generate a random UUID that won't exist
    with pytest.raises(ValueError, match=f"User with SWID '{non_existent_swid}' not found."):
        get_single_user(requestee_username, non_existent_swid)


def test_get_all_users_with_data(db_engine, role_right_checker_db_connection):
    """Tests retrieving all users when some users exist."""
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    populate_example_data() # Populates users, including doctor_bob
    requestee_username = "doctor_bob" # Has READ_PATIENT_BASIC_DATA

    # Data is populated by populate_example_data, let's check against that
    # Or add more users if needed for the test's specific scenario
    # For this test, populate_example_data provides enough users.

    retrieved_users = get_all_users(requestee_username)

    assert isinstance(retrieved_users, list)
    assert len(retrieved_users) == len(EXPECTED_USERS_DATA)
    
    retrieved_usernames = {user.user_name for user in retrieved_users}
    expected_usernames = {data["username"] for data in EXPECTED_USERS_DATA}
    assert retrieved_usernames == expected_usernames

def test_get_health_records_user_not_found(db_engine, role_right_checker_db_connection):
    """Tests that ValueError is raised when the patient user SWID does not exist."""
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    populate_example_data() # For requestee doctor_bob
    requestee_username = "doctor_bob" # Has READ_PATIENT_HEALTHCARE_RECORD_DATA

    non_existent_swid = uuid.uuid4()
    with pytest.raises(ValueError, match=f"Patient with SWID '{non_existent_swid}' not found."):
        get_health_records(requestee_username, non_existent_swid)

def test_get_health_records_user_exists_no_records(db_engine, role_right_checker_db_connection):
    """Tests that an empty list is returned when the user exists but has no health records."""
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    populate_example_data() # For requestee doctor_bob and "patient" role
    requestee_username = "doctor_bob"

    with Session(db_engine) as session:
        # Ensure "patient" role exists for the new patient user (populated by populate_example_data)
        patient_role_obj = session.query(Role).filter_by(role_name="patient").first()
        assert patient_role_obj is not None, "Patient role not found from populate_example_data"

        login = Login(user_name="patient_no_records", hashed_password=b"pw", salt=b"s")
        session.add(login)
        session.commit()
        login = session.merge(login)

        patient_user = User(full_name="No Records patient", login_details=login, role=patient_role_obj)
        session.add(patient_user)
        session.commit()
        patient_swid = patient_user.system_wide_identifier

    records = get_health_records(requestee_username, patient_swid)
    assert isinstance(records, list)
    assert len(records) == 0

def test_get_health_records_user_exists_with_one_record(db_engine, role_right_checker_db_connection):
    """Tests retrieving a single health record for an existing user."""
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    populate_example_data() # For requestee doctor_bob and "patient" role
    requestee_username = "doctor_bob"


    with Session(db_engine) as session:
        patient_role_obj = session.query(Role).filter_by(role_name="patient").first()
        assert patient_role_obj is not None

        patient_login = Login(user_name="patient_with_record", hashed_password=b"pw", salt=b"s")
        session.add(patient_login)
        session.commit()
        patient_login = session.merge(patient_login)

        patient_user = User(full_name="patient With Record", login_details=patient_login, role=patient_role_obj)
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

    retrieved_records = get_health_records(requestee_username, patient_swid)
    assert isinstance(retrieved_records, list)
    assert len(retrieved_records) == 1
    assert retrieved_records[0].record_id == record_id
    assert retrieved_records[0].record_data == record_data
    assert retrieved_records[0].patient_user_id == patient_id

def test_get_health_records_user_exists_with_multiple_records(db_engine, role_right_checker_db_connection):
    """Tests retrieving multiple health records for an existing user."""
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    populate_example_data() # For requestee doctor_bob and "patient" role
    requestee_username = "doctor_bob"

    with Session(db_engine) as session:
        patient_role_obj = session.query(Role).filter_by(role_name="patient").first()
        assert patient_role_obj is not None

        patient_login = Login(user_name="patient_multi_records", hashed_password=b"pw", salt=b"s")
        session.add(patient_login)
        session.commit()
        patient_login = session.merge(patient_login)

        patient_user = User(full_name="patient Multi Records", login_details=patient_login, role=patient_role_obj)
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

    retrieved_records = get_health_records(requestee_username, patient_swid)
    assert isinstance(retrieved_records, list)
    assert len(retrieved_records) == 2

    retrieved_record_ids = {rec.record_id for rec in retrieved_records}
    assert record1_id in retrieved_record_ids
    assert record2_id in retrieved_record_ids

    # Optional: Check data if needed, though IDs are usually sufficient for "all"
    # assert any(rec.record_data == record_data1 for rec in retrieved_records)
    # assert any(rec.record_data == record_data2 for rec in retrieved_records)

def test_add_user_success(db_engine, role_right_checker_db_connection):
    """Tests successfully adding a new user."""
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    populate_example_data() # For requestee doctor_bob and "patient" role
    requestee_username = "doctor_bob" # Has WRITE_PATIENT_BASIC_DATA

    full_name = "New Test User Fullname"
    address = "123 Test Street"
    hospital_designation = "Test Designee"
    role_for_new_user = "patient" # Role name must exist in Roles table

    # Call the function under test
    generated_username, generated_password = add_user(
        requestee_username,
        full_name, address, hospital_designation, role_for_new_user
    )

    assert isinstance(generated_username, str) and len(generated_username) > 0
    assert isinstance(generated_password, str) and len(generated_password) > 0

    with Session(db_engine) as session:
        # Role object for assertion
        patient_role_obj = session.query(Role).filter_by(role_name=role_for_new_user).one()

        # Check Login entry
        login_entry = session.query(Login).filter_by(user_name=generated_username).one_or_none()
        assert login_entry is not None, "Login entry was not created."
        assert login_entry.user_name == generated_username
        assert login_entry.salt is not None
        assert checkpw(generated_password.encode('utf-8'), login_entry.hashed_password), "Password verification failed."

        # Check User entry
        user_entry = session.query(User).filter_by(user_name=generated_username).one_or_none()
        assert user_entry is not None, "User entry was not created."
        assert user_entry.full_name == full_name
        assert user_entry.address == address
        assert user_entry.hospital_designation == hospital_designation
        assert user_entry.user_name == generated_username
        assert user_entry.login_details == login_entry
        assert login_entry.user == user_entry
        assert user_entry.role == patient_role_obj, "User role was not assigned correctly."
        assert user_entry.user_role_name == role_for_new_user

def test_add_health_record_success(db_engine, role_right_checker_db_connection):
    """Tests successfully adding a new health record for a user."""
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    with Session(db_engine) as session:
        # Setup: Create a patient user and a creator user
        role_name = "TestRoleForHealthRecordAdd"
        role = session.query(Role).filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name=role_name, description="Test role for adding health records")
            session.add(role)
        # Ensure 'doctor' role for creator user
        doctor_role_name = "doctor"
        doctor_role = session.query(Role).filter_by(role_name=doctor_role_name).first()
        if not doctor_role:
            doctor_role = Role(role_name=doctor_role_name, description="Doctor role for testing")
            session.add(doctor_role)
        session.commit()
        role = session.merge(role) # patient role
        doctor_role = session.merge(doctor_role) # doctor role

        patient_login = Login(user_name="patient_hr_add", hashed_password=b"pw1", salt=b"s1")
        creator_login = Login(user_name="creator_hr_add", hashed_password=b"pw2", salt=b"s2")
        session.add_all([patient_login, creator_login])
        session.commit()
        patient_login, creator_login = session.merge(patient_login), session.merge(creator_login)

        patient_user = User(full_name="patient For HR Add", login_details=patient_login, role=role)
        creator_user = User(full_name="Creator For HR Add", login_details=creator_login, role=doctor_role) # Assign doctor role
        session.add_all([patient_user, creator_user])
        session.commit()

        patient_user_id = patient_user.user_id
        creator_user_id = creator_user.user_id
        requestee_username = "creator_hr_add" # This is the username of the creator

    record_data = {"symptoms": "headache", "diagnosis": "stress"}
    add_health_record(requestee_username, patient_user_id, record_data)

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

def test_update_health_record_success(db_engine, role_right_checker_db_connection):
    """Tests successfully updating an existing health record."""
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    with Session(db_engine) as session:
        # Setup: Create patient, initial creator, and updater users
        # Use existing roles like "patient" and "doctor"
        patient_role_obj = session.query(Role).filter_by(role_name="patient").first()
        if not patient_role_obj:
            patient_role_obj = Role(role_name="patient", description="Patient role")
            session.add(patient_role_obj)
        doctor_role_obj = session.query(Role).filter_by(role_name="doctor").first()
        if not doctor_role_obj:
            doctor_role_obj = Role(role_name="doctor", description="Doctor role")
            session.add(doctor_role_obj)
        session.commit()
        patient_role_obj, doctor_role_obj = session.merge(patient_role_obj), session.merge(doctor_role_obj)

        patient_login = Login(user_name="patient_hr_update", hashed_password=b"pw_p", salt=b"s_p")
        initial_creator_login = Login(user_name="creator_hr_initial", hashed_password=b"pw_c", salt=b"s_c")
        updater_login = Login(user_name="updater_hr_final", hashed_password=b"pw_u", salt=b"s_u")
        session.add_all([patient_login, initial_creator_login, updater_login])
        session.commit()
        patient_login, initial_creator_login, updater_login = \
            session.merge(patient_login), session.merge(initial_creator_login), session.merge(updater_login)

        patient_user = User(full_name="patient For HR Update", login_details=patient_login, role=patient_role_obj)
        initial_creator_user = User(full_name="Initial HR Creator", login_details=initial_creator_login, role=doctor_role_obj)
        updater_user = User(full_name="Final HR Updater", login_details=updater_login, role=doctor_role_obj) # Updater is a doctor
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
        requestee_username = "updater_hr_final" # Username of the updater

    # Data for the update
    updated_record_data = {"condition": "recovered", "treatment": "none", "notes": "patient feels better."}

    # Call the function under test
    update_health_record(requestee_username, record_id_to_update, updated_record_data)

    # Verify the record was updated (updater_user_id is the DB ID of the user object 'updater_user')
    with Session(db_engine) as session:
        updated_record = session.query(HealthcareRecord).filter_by(record_id=record_id_to_update).one_or_none()

        assert updated_record is not None, "Health record not found after update attempt."
        assert updated_record.patient_user_id == patient_user_id, "patient ID should not change."
        assert updated_record.record_data == updated_record_data, "Record data was not updated correctly."
        assert updated_record.last_updated_by_user_id == updater_user_id, "Updater user ID was not set correctly."
        assert updated_record.last_updated_at is not None, "last_updated_at should be set."
        assert updated_record.last_updated_at > original_last_updated_at, "last_updated_at was not updated."

def test_update_health_record_not_found(db_engine, role_right_checker_db_connection):
    """Tests that updating a non-existent health record raises NoResultFound."""
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    populate_example_data() # For requestee doctor_bob
    requestee_username = "doctor_bob" # Has WRITE_PATIENT_HEALTHCARE_RECORD_DATA

    non_existent_record_id = 99999  # An ID that is unlikely to exist
    record_data_for_update = {"notes": "Attempting to update non-existent record."}

    with pytest.raises(NoResultFound):
        update_health_record(requestee_username, non_existent_record_id, record_data_for_update)