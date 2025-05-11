import pytest
from script.deploy import deploy

from script.db_connection import Base, initialize_database

@pytest.fixture
def user_right_checker():
    contract = deploy()
    contract.create_user(2)
    contract.create_user_w_right(1, "write_patient_data")
    contract.create_user_w_right(1, "read_patient_data")
    return contract

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