from moccasin.config import get_config
from boa.contracts.abi.abi_contract import ABIContract
import boa
from eth_account import Account
from script.interface import RoleRightChecker

# from deploy import UserRightChecker
# from boa.deployments import Deployment

config = get_config()
active_network = config.get_active_network()
# Get the latest counter of the Counter contract
user_right_checker = RoleRightChecker(
                        active_network
                        .get_latest_contract_unchecked("RoleRightChecker"))

# if user_right_checker is None:
#     boa.set_network_env("http://127.0.0.1:8545")
#     boa.env.add_account(Account.from_key("0x646f1ce2fdad0e6deeeb5c7e8e5543bdde65e86029e2fd9fc169899c440a7913"))
#     user_right_checker: UserRightChecker = boa.load_partial("src/UserRightChecker_deployer.vy").at("0x0290FB167208Af455bB137780163b7B7a9a10C16")

print("creating user with id: 2")
user_right_checker.add_role('patient')

print("add right")
user_right_checker.add_right("read_patient_data")

print("check user right to read_patient_information. Should be true(code 1).")
result = user_right_checker.check_right("nurse", "read_patient_data")
print(f"Code: {result}.")


#user_right_checker.add_role_w_right("doctor", "write_patient_data")
print("check user right to read_patient_information. Should be false (code 0).")
result = user_right_checker.check_right("patient","read_patient_data")
print(f"Code: {result}.")
print()
user_right_checker.add_role_w_right("nurse", "read_patient_data")
print("check user right to read_patient_information. Should be true(code 1).")
result = user_right_checker.check_right("nurse", "read_patient_data")
print(f"Code: {result}.")

print("role list")
print(user_right_checker.role_list)
print(type(user_right_checker.role_list))


