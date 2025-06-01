import pytest
from script.deploy import deploy
from script.rights import READ_OWN_PATIENT_BASIC_DATA, READ_PATIENT_BASIC_DATA, WRITE_PATIENT_BASIC_DATA, READ_PATIENT_HEALTHCARE_RECORD_DATA, WRITE_PATIENT_HEALTHCARE_RECORD_DATA,READ_OWN_HEALTHCARE_RECORD_RIGHT, ADD_USER_ROLE, CHANGE_OWN_PASSWORD_RIGHT, ADMIN_CHANGE_USER_PASSWORD_RIGHT
from script.roles import PATIENT, DOCTOR, NURSE, ADMIN
from script.rights import READ_OWN_PATIENT_BASIC_DATA, READ_PATIENT_BASIC_DATA, WRITE_PATIENT_BASIC_DATA, READ_PATIENT_HEALTHCARE_RECORD_DATA, WRITE_PATIENT_HEALTHCARE_RECORD_DATA,READ_OWN_HEALTHCARE_RECORD_RIGHT, ADD_USER_ROLE, CHANGE_OWN_PASSWORD_RIGHT, ADMIN_CHANGE_USER_PASSWORD_RIGHT
from script.roles import PATIENT, DOCTOR, NURSE, ADMIN
from script.db_connection import Base, initialize_database
from script.deploy import deploy

@pytest.fixture
def db_engine():
    """
    Fixture to set up a PostgreSQL database for each test function.
    Handles table creation (including versioned tables) and cleanup.
    """

    engine = initialize_database()
    yield engine  # Provide the engine to the test
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture
def role_right_checker_db_connection():
    """
    Fixture for test_db_functions
    """
    contract = deploy()
    contract.add_role_w_right(role_name=PATIENT, right= READ_OWN_HEALTHCARE_RECORD_RIGHT)
    contract.add_role_w_right(role_name=PATIENT, right= READ_OWN_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=PATIENT, right= CHANGE_OWN_PASSWORD_RIGHT)
    contract.add_role_w_right(role_name=DOCTOR, right= READ_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= WRITE_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= READ_OWN_HEALTHCARE_RECORD_RIGHT)
    contract.add_role_w_right(role_name=DOCTOR, right= READ_OWN_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= READ_PATIENT_HEALTHCARE_RECORD_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= WRITE_PATIENT_HEALTHCARE_RECORD_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= CHANGE_OWN_PASSWORD_RIGHT)
    contract.add_role_w_right(role_name=NURSE, right= READ_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=NURSE, right= WRITE_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=NURSE, right= READ_OWN_HEALTHCARE_RECORD_RIGHT)
    contract.add_role_w_right(role_name=NURSE, right= READ_OWN_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=NURSE, right= READ_PATIENT_HEALTHCARE_RECORD_DATA)
    contract.add_role_w_right(role_name=NURSE, right= WRITE_PATIENT_HEALTHCARE_RECORD_DATA)
    contract.add_role_w_right(role_name=NURSE, right= CHANGE_OWN_PASSWORD_RIGHT)
    contract.add_role_w_right(role_name=ADMIN, right= ADD_USER_ROLE)
    contract.add_role_w_right(role_name=ADMIN, right= WRITE_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=ADMIN, right= ADMIN_CHANGE_USER_PASSWORD_RIGHT)
    contract.add_role_w_right(role_name=ADMIN, right= CHANGE_OWN_PASSWORD_RIGHT)
    return contract

@pytest.fixture
def role_right_checker_db_connection():
    """
    Fixture for test_db_functions
    """
    contract = deploy()
    contract.add_role_w_right(role_name=PATIENT, right= READ_OWN_HEALTHCARE_RECORD_RIGHT)
    contract.add_role_w_right(role_name=PATIENT, right= READ_OWN_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=PATIENT, right= CHANGE_OWN_PASSWORD_RIGHT)
    contract.add_role_w_right(role_name=DOCTOR, right= READ_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= WRITE_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= READ_OWN_HEALTHCARE_RECORD_RIGHT)
    contract.add_role_w_right(role_name=DOCTOR, right= READ_OWN_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= READ_PATIENT_HEALTHCARE_RECORD_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= WRITE_PATIENT_HEALTHCARE_RECORD_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= CHANGE_OWN_PASSWORD_RIGHT)
    contract.add_role_w_right(role_name=NURSE, right= READ_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=NURSE, right= WRITE_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=NURSE, right= READ_OWN_HEALTHCARE_RECORD_RIGHT)
    contract.add_role_w_right(role_name=NURSE, right= READ_OWN_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=NURSE, right= READ_PATIENT_HEALTHCARE_RECORD_DATA)
    contract.add_role_w_right(role_name=NURSE, right= WRITE_PATIENT_HEALTHCARE_RECORD_DATA)
    contract.add_role_w_right(role_name=NURSE, right= CHANGE_OWN_PASSWORD_RIGHT)
    contract.add_role_w_right(role_name=ADMIN, right= ADD_USER_ROLE)
    contract.add_role_w_right(role_name=ADMIN, right= WRITE_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=ADMIN, right= ADMIN_CHANGE_USER_PASSWORD_RIGHT)
    contract.add_role_w_right(role_name=ADMIN, right= CHANGE_OWN_PASSWORD_RIGHT)
    return contract
