from src import RoleRightChecker
from script.interface import RoleRightChecker as i_RoleRightChecker

def deploy() -> i_RoleRightChecker:
    user_right_checker = RoleRightChecker.deploy()
    return i_RoleRightChecker(user_right_checker)

def moccasin_main() -> i_RoleRightChecker:
    deploy()

    # from script.interface import RoleRightChecker
    # user_right_checker = RoleRightChecker(user_right_checker)

    # # if user_right_checker is None:
    # #     boa.set_network_env("http://127.0.0.1:8545")
    # #     boa.env.add_account(Account.from_key("0x646f1ce2fdad0e6deeeb5c7e8e5543bdde65e86029e2fd9fc169899c440a7913"))
    # #     user_right_checker: UserRightChecker = boa.load_partial("src/UserRightChecker_deployer.vy").at("0x0290FB167208Af455bB137780163b7B7a9a10C16")

    # print("creating user with id: 2")
    # user_right_checker.add_role('patient')

    # print("add right")
    # user_right_checker.add_right("read_patient_data")

    # print("check user right to read_patient_information. Should be true(code 1).")
    # result = user_right_checker.check_right("nurse", "read_patient_data")
    # print(f"Code: {result}.")

    # print(user_right_checker.user_right_checker.role_exists)
    # #user_right_checker.add_role_w_right("doctor", "write_patient_data")
    # print("check user right to read_patient_information. Should be false (code 0).")
    # result = user_right_checker.check_right("patient","read_patient_data")
    # print(f"Code: {result}.")
    
    
    # print("check user right to read_patient_information. Should be true(code 1).")
    # result = user_right_checker.check_right("nurse", "read_patient_data")
    # print(f"Code: {result}.")

