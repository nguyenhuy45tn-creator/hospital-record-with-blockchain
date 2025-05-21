from script.db_connection import get_single_user, Role, Login, User, get_health_records,HealthcareRecord,add_user
from sqlalchemy.orm import Session
from bcrypt import gensalt, hashpw
import uuid
import pytest
from sqlalchemy import select


def test_get_single_user(db_engine):
    with Session(db_engine) as session:
        role_name="testrole"
        role =session.query(Role).filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name = role_name, description="Test Role")
            session.add(role)
            session.commit()
            role = session.merge(role)

        login_user_name="testusername"
        salt=gensalt()
        password="873eh"
        hashed_password = hashpw(password,salt)
        login =session.query(Login).filter_by(user_name=login_user_name).first()
        if not login:
            login = Login(user_name=login_user_name,hashed_password=hashed_password,salt=salt)
            session.add(login_user_name)
            session.commit()
            login = session.merge(login)


        test_user = User(full_name="Test User", address="test street", hospital_designation="Test_des")
        test_user.login_details = login
        test_user.role = role
        session.add(test_user)
        session.commit()
        user_sswi = test_user.system_wide_identifier
    
    retrieved_user = get_single_user(db_engine, user_sswi)
    assert retrieved_user is not None
    assert retrieved_user.system_wide_identifier == user_sswi
    assert retrieved_user.full_name == "Test User"
    assert retrieved_user.address == "test street"
    
def test_get_health_records(db_engine):
    with Session(db_engine) as session:
        # Add a user and associated health records
        user_sswi = uuid.uuid4()
        test_user = User(full_name="Health User", address="Health St", hospital_designation="Clinic", system_wide_identifier=user_sswi)
        session.add(test_user)
        session.commit()

        # Add healthcare records for the user
        record1 = HealthcareRecord(patient_user_id=test_user.user_id, record_data={"diagnosis": "Cough", "treatment": "Cough Syrup"})
        record2 = HealthcareRecord(patient_user_id=test_user.user_id, record_data={"diagnosis": "Headache", "treatment": "Painkillers"})
        session.add_all([record1, record2])
        session.commit()

        # Retrieve healthcare records
        records = get_health_records(db_engine, user_sswi)
        assert len(records) == 2
        assert records[0].record_data["diagnosis"] == "Cough"
        assert records[1].record_data["diagnosis"] == "Headache"

        # Test no records for a non-existent user
        non_existent_sswi = uuid.uuid4()
        no_records = get_health_records(db_engine, non_existent_sswi)
        assert no_records == []

        # Test user exists but has no records
        empty_user_sswi = uuid.uuid4()
        empty_user = User(full_name="No Records User", address="Empty St", hospital_designation="None", system_wide_identifier=empty_user_sswi)
        session.add(empty_user)
        session.commit()

        empty_records = get_health_records(db_engine, empty_user_sswi)
        assert empty_records == []

def test_add_user(db_engine):
    # Test adding a valid user
    username = "testuser"
    password = "password123"
    full_name = "Test User"
    address = "123 Main St"
    hospital_designation = "General"

    with Session(db_engine) as session:
        # Add the user
        add_user(db_engine, username, password, full_name, address, hospital_designation)
        user = session.query(User).filter_by(full_name=full_name).first()
        assert user is not None
        assert user.full_name == full_name
        assert user.address == address

    # Test adding a duplicate user
    with pytest.raises(ValueError, match="Login username 'testuser' already exists."):
        add_user(db_engine, username, password, full_name, address, hospital_designation)

def test_add_health_record(db_engine):
    with Session(db_engine) as session:
        # Create a user to associate with the health record
        user_sswi = uuid.uuid4()
        creator_sswi = uuid.uuid4()
        test_user = User(full_name="Health User", address="Health St", hospital_designation="Clinic", system_wide_identifier=user_sswi)
        creator_user = User(full_name="Creator User", address="Creator St", hospital_designation="Admin", system_wide_identifier=creator_sswi)
        session.add_all([test_user, creator_user])
        session.commit()

        # Add a healthcare record
        record_data = {"diagnosis": "Flu", "treatment": "Bed Rest"}
        add_health_record(db_engine, test_user.user_id, record_data, creator_user.user_id)

        # Validate the record in the database
        record = session.query(HealthcareRecord).filter_by(patient_user_id=test_user.user_id).first()
        assert record is not None
        assert record.record_data["diagnosis"] == "Flu"
        assert record.record_data["treatment"] == "Bed Rest"
        assert record.last_updated_by_user_id == creator_user.user_id
       
