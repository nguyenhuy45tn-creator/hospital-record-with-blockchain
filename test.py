from script import roles, rights
from script.contract import create_role_right_checker

contract = create_role_right_checker()

print(contract.view_roles())
print(contract.view_rights())
print(contract.check_right(roles.ADMIN, right=rights.READ_PATIENT_BASIC_DATA))