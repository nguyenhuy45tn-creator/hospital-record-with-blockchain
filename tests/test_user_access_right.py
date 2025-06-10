import pytest
from script.deploy import deploy
from script.rights import READ_PATIENT_BASIC_DATA, WRITE_PATIENT_BASIC_DATA, READ_PATIENT_HEALTHCARE_RECORD_DATA, WRITE_PATIENT_HEALTHCARE_RECORD_DATA
from script.roles import PATIENT, DOCTOR

@pytest.fixture
def role_right_checker():
    contract = deploy()
    contract.add_role(PATIENT)
    contract.add_right(READ_PATIENT_BASIC_DATA)
    contract.add_right(WRITE_PATIENT_BASIC_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= READ_PATIENT_HEALTHCARE_RECORD_DATA)
    contract.add_role_w_right(role_name=DOCTOR, right= WRITE_PATIENT_HEALTHCARE_RECORD_DATA)
    return contract

@pytest.mark.ignore_isolation
def test_1(role_right_checker):
    """
    test: role exist, right exist, no access granted
    """
    result = role_right_checker.check_right(DOCTOR, READ_PATIENT_BASIC_DATA)

    #expect 0 since the right and roles exist, but role isn't granted right
    assert result == 0 

@pytest.mark.ignore_isolation
def test_2(role_right_checker):
    """
    test: role exist, right exist, access granted
    """
    result = role_right_checker.check_right(DOCTOR, READ_PATIENT_HEALTHCARE_RECORD_DATA)

    assert result == 1, f"contract return {result}"

@pytest.mark.ignore_isolation
def test_3(role_right_checker):
    """
    test: role doesn't exist, right exist, access not granted
    """
    result = role_right_checker.check_right("ersdf", READ_PATIENT_BASIC_DATA)

    assert result == -1, f"contract return {result}" # role doesn't exist

@pytest.mark.ignore_isolation
def test_4(role_right_checker):
    """
    test: role exists, right doens't exist, access not granted
    """
    result = role_right_checker.check_right(DOCTOR, "examine_patient")

    assert result == -2, f"contract return {result}" # role exist but right doesn't exist

@pytest.mark.ignore_isolation
def test_view_roles(role_right_checker):
    role_list = role_right_checker.view_roles()
    assert role_list == [PATIENT, DOCTOR], role_list

@pytest.mark.ignore_isolation
def test_view_rights(role_right_checker):
    right_list =  role_right_checker.view_rights()
    assert right_list == [READ_PATIENT_BASIC_DATA, WRITE_PATIENT_BASIC_DATA, READ_PATIENT_HEALTHCARE_RECORD_DATA, WRITE_PATIENT_HEALTHCARE_RECORD_DATA], right_list

@pytest.mark.ignore_isolation
def test_delete_role(role_right_checker):
    """
    test_deleting_right
    """

    if role_right_checker.delete_role(DOCTOR) == -1:
        raise "WRONG INDEX"
    
    assert role_right_checker.check_right(DOCTOR, READ_PATIENT_HEALTHCARE_RECORD_DATA) == -1

    assert role_right_checker.view_roles() == [PATIENT, ""], role_right_checker.view_roles()

    
