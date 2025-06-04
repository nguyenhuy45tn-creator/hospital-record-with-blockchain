from script import roles, rights
from script.contract import create_role_right_checker

contract = create_role_right_checker()

contract.add_right(roles.ADMIN)
contract.add_right(roles.DOCTOR)
contract.add_right(roles.PATIENT)
contract.add_right(roles.NURSE)

contract.add_role_w_right(roles.DOCTOR, rights.READ_OWN_PATIENT_BASIC_DATA)
contract.add_role_w_right(roles.DOCTOR, rights.READ_OWN_HEALTHCARE_RECORD_RIGHT)
contract.add_role_w_right(roles.DOCTOR, rights.READ_PATIENT_BASIC_DATA)
contract.add_role_w_right(roles.DOCTOR, rights.READ_PATIENT_HEALTHCARE_RECORD_DATA)

contract.add_role_w_right(roles.ADMIN, rights.READ_OWN_PATIENT_BASIC_DATA)
contract.add_role_w_right(roles.ADMIN, rights.READ_OWN_HEALTHCARE_RECORD_RIGHT)
contract.add_role_w_right(roles.ADMIN, rights.READ_PATIENT_BASIC_DATA)
contract.add_role_w_right(roles.ADMIN, rights.READ_PATIENT_HEALTHCARE_RECORD_DATA)
contract.add_role_w_right(roles.ADMIN, rights.ADMIN_CHANGE_USER_PASSWORD_RIGHT)

contract.add_role_w_right(roles.PATIENT, rights.READ_OWN_HEALTHCARE_RECORD_RIGHT)
contract.add_role_w_right(roles.PATIENT, rights.READ_PATIENT_BASIC_DATA)