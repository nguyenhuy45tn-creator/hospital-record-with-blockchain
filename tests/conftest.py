import pytest
from script.deploy import deploy
from script.rights import READ_PATIENT_BASIC_DATA, WRITE_PATIENT_BASIC_DATA, READ_PATIENT_HEALTHCARE_RECORD_DATA, WRITE_PATIENT_HEALTHCARE_RECORD_DATA
from script.roles import PATIENT, DOCTOR

@pytest.fixture
def role_right_checker():
    contract = deploy()
    contract.add_role(PATIENT)
    contract.add_right(READ_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= READ_PATIENT_HEALTHCARE_RECORD_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= WRITE_PATIENT_HEALTHCARE_RECORD_DATA)
    return contract