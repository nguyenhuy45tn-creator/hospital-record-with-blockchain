import pytest
from script.deploy import deploy
from script.rights import READ_PATIENT_BASIC_DATA, WRITE_PATIENT_BASIC_DATA, READ_PATIENT_HEALTHCARE_RECORD_DATA, WRITE_PATIENT_HEALTHCARE_RECORD_DATA
from script.roles import PATIENT, DOCTOR
from script.db_connection import Base, initialize_database

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
