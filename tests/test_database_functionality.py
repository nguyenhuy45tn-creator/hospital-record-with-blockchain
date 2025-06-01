from script.db_connection import get_single_user, Role, Login, User, get_health_records, HealthcareRecord, add_user, add_health_record
from script import db_connection
from sqlalchemy.orm import Session
from bcrypt import gensalt, hashpw
import uuid
import pytest
from sqlalchemy import select


def test_get_single_user(db_engine, role_right_checker_db_connection):
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection

    with Session(db_engine) as session:
        role_name="patient"
        role =session.query(Role).filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name = role_name, description="Test Role")
            session.add(role)
            session.commit()
            role = session.merge(role)

        login_user_name="testusername"
        salt=gensalt()
        password=b"873eh"
        hashed_password = hashpw(password,salt)
        login =session.query(Login).filter_by(user_name=login_user_name).first()
        if not login:
            login = Login(user_name=login_user_name,hashed_password=hashed_password,salt=salt)
            session.add(login)
            session.commit()
            login = session.merge(login)


        test_user = User(full_name="Test User", address="test street", hospital_designation="Test_des")
        test_user.login_details = login
        test_user.role = role
        session.add(test_user)
        session.commit()
        user_sswi = test_user.system_wide_identifier
    
    retrieved_user = get_single_user(login_user_name, user_sswi)
    assert retrieved_user is not None
    assert retrieved_user.system_wide_identifier == user_sswi
    assert retrieved_user.full_name == "Test User"
    assert retrieved_user.address == "test street"
    
def test_get_health_records(db_engine, role_right_checker_db_connection):
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection

    
    with Session(db_engine) as session:
        # Add a role for the testusers
        role_name="nurse"
        role = session.query(Role).filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name = role_name, description="Test Role")
            session.add(role)
            session.commit()
            role = session.merge(role)

        # Login for the user with health records
        login_name_health_user = "testusername_health"
        salt_health_user = gensalt()
        password_health_user = b"873eh_health"
        hashed_password_health_user = hashpw(password_health_user, salt_health_user)
        login_health_user = session.query(Login).filter_by(user_name=login_name_health_user).first()
        if not login_health_user:
            login_health_user = Login(user_name=login_name_health_user, hashed_password=hashed_password_health_user, salt=salt_health_user)
            session.add(login_health_user)
            session.commit()
            login_health_user = session.merge(login_health_user)

        # Login for the user with no health records
        login_name_empty_user = "empty_testusername_no_records"
        salt_empty_user = gensalt()
        password_empty_user = b"873eh_empty"
        hashed_password_empty_user = hashpw(password_empty_user, salt_empty_user)
        login_empty_user = session.query(Login).filter_by(user_name=login_name_empty_user).first()
        if not login_empty_user:
            login_empty_user = Login(user_name=login_name_empty_user, hashed_password=hashed_password_empty_user, salt=salt_empty_user)
            session.add(login_empty_user)
            session.commit()
            login_empty_user = session.merge(login_empty_user)


        # Add a user and associated health records
        user_sswi = uuid.uuid4()
        test_user = User(full_name="Health User", address="Health St", hospital_designation="Clinic", system_wide_identifier=user_sswi)
        test_user.role = role
        test_user.login_details = login_health_user
        session.add(test_user)
        session.commit()

        # Add healthcare records for the user
        record1 = HealthcareRecord(patient_user_id=test_user.user_id, record_data={"diagnosis": "Cough", "treatment": "Cough Syrup"})
        record2 = HealthcareRecord(patient_user_id=test_user.user_id, record_data={"diagnosis": "Headache", "treatment": "Painkillers"})
        session.add_all([record1, record2])
        session.commit()

        # Retrieve healthcare records
        records = get_health_records(login_name_health_user, user_sswi)
        assert len(records) == 2
        assert records[0].record_data["diagnosis"] == "Cough"
        assert records[1].record_data["diagnosis"] == "Headache"

        # Test no records for a non-existent user
        non_existent_sswi = uuid.uuid4()
        with pytest.raises(ValueError, match=f"Patient with SWID '{non_existent_sswi}' not found."):
            no_records = get_health_records(login_name_health_user, non_existent_sswi)

        # Test user exists but has no records
        empty_user_sswi = uuid.uuid4()
        empty_user = User(full_name="No Records User", address="Empty St", hospital_designation="None", system_wide_identifier=empty_user_sswi)
        empty_user.role = role
        empty_user.login_details = login_empty_user
        session.add(empty_user)
        session.commit()

        empty_records = get_health_records(login_name_health_user, empty_user_sswi)
        assert empty_records == []

def test_add_user(db_engine, role_right_checker_db_connection):
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    
    # Test adding a valid user
    username = "testuser"
    password = "password123"
    full_name = "Test User"
    address = "123 Main St"
    hospital_designation = "General"

    with Session(db_engine) as session:

        role_name="admin"
        role =session.query(Role).filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name = role_name, description="Test Role")
            session.add(role)
            session.commit()
            role = session.merge(role)

        login_user_name="testusername"
        salt=gensalt()
        password=b"873eh"
        hashed_password = hashpw(password,salt)
        login =session.query(Login).filter_by(user_name=login_user_name).first()
        if not login:
            login = Login(user_name=login_user_name,hashed_password=hashed_password,salt=salt)
            session.add(login)
            session.commit()
            login = session.merge(login)


        test_user = User(full_name="Creator User", address="test creator street", hospital_designation="Test_des_creator")
        test_user.login_details = login
        test_user.role = role
        session.add(test_user)
        session.commit()

        # Add the user
        add_user(requestee_username=login_user_name, full_name=full_name, address=address,hospital_designation= hospital_designation, role_for_new_user=role_name)
        user = session.query(User).filter_by(full_name=full_name).first()
        assert user is not None
        assert user.full_name == full_name
        assert user.address == address


def test_add_health_record(db_engine, role_right_checker_db_connection):
    db_connection.engine = db_engine
    db_connection.role_right_checker = role_right_checker_db_connection
    with Session(db_engine) as session:
        # Add a role for the testusers
        role_name="nurse"
        role = session.query(Role).filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name = role_name, description="Test Role")
            session.add(role)
            session.commit()
            role = session.merge(role)

        # Login for the test_user
        login_name_health_user = "testusername_health"
        salt_health_user = gensalt()
        password_health_user = b"873eh_health"
        hashed_password_health_user = hashpw(password_health_user, salt_health_user)
        login_health_user = session.query(Login).filter_by(user_name=login_name_health_user).first()
        if not login_health_user:
            login_health_user = Login(user_name=login_name_health_user, hashed_password=hashed_password_health_user, salt=salt_health_user)
            session.add(login_health_user)
            session.commit()
            login_health_user = session.merge(login_health_user)

        # Login for the creator user
        login_name_creator_user = "testusername_creator"
        salt_creator_user = gensalt()
        password_creator_user = b"873eh_creator"
        hashed_password_creator_user = hashpw(password_creator_user, salt_creator_user)
        login_creator_user = session.query(Login).filter_by(user_name=login_name_creator_user).first()
        if not login_creator_user:
            login_creator_user = Login(user_name=login_name_creator_user, hashed_password=hashed_password_creator_user, salt=salt_creator_user)
            session.add(login_creator_user)
            session.commit()
            login_creator_user = session.merge(login_creator_user)

        # Create a user to associate with the health record
        user_sswi = uuid.uuid4()
        creator_sswi = uuid.uuid4()
        test_user = User(full_name="Health User", address="Health St", hospital_designation="Clinic", system_wide_identifier=user_sswi)
        test_user.role = role
        test_user.login_details = login_health_user
        creator_user = User(full_name="Creator User", address="Creator St", hospital_designation="Admin", system_wide_identifier=creator_sswi)
        creator_user.role = role
        creator_user.login_details = login_creator_user
        session.add_all([test_user, creator_user])
        session.commit()

        # Add a healthcare record
        record_data = {"diagnosis": "Flu", "treatment": "Bed Rest"}
        add_health_record(requestee_username=login_name_creator_user, patient_user_id=test_user.user_id,record_data= record_data)

        # Validate the record in the database
        record = session.query(HealthcareRecord).filter_by(patient_user_id=test_user.user_id).first()
        assert record is not None
        assert record.record_data["diagnosis"] == "Flu"
        assert record.record_data["treatment"] == "Bed Rest"
        assert record.last_updated_by_user_id == creator_user.user_id
       
