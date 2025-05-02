import pytest
from script.deploy import deploy

@pytest.fixture
def user_right_checker():
    contract = deploy()
    contract.create_user(2)
    contract.create_user_w_right(1, "write_patient_data")
    contract.create_user_w_right(1, "read_patient_data")
    return contract