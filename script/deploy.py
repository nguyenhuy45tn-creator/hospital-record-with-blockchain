from src import UserRightChecker
from moccasin.boa_tools import VyperContract

class uint128(int):
    # this is only for better notation
    pass 

class int8(int):
    # this is only for better notation
    pass

class String(list):
    # this is only for better notation
    pass

class State_of_Right:
    user_exist: bool
    right_exist: bool
    has_right: bool

class anno_UserRightChecker(VyperContract):
    def __init__(self, compiler_data, *args, value=0, env = None, override_address = None, skip_initcode=False, created_from = None, contract_name=None, filename = None, gas=None):
        super().__init__(compiler_data, *args, value=value, env=env, override_address=override_address, skip_initcode=skip_initcode, created_from=created_from, contract_name=contract_name, filename=filename, gas=gas)

    def create_user(self, user_id: int, right: str) -> State_of_Right:
        pass

    def modify_user_right(
        user_id: uint128, 
        access_right: String[20], 
        has_right: bool) -> int8:
        """ 
        The contract return 3 code:
                1: successfully changed the right
                -1: the user doesn't exist
                -2: the right doesn't exist for the user
        """
        pass

    def check_user_right(user_id: uint128, 
        access_right: String[20]) -> int8:
        """The contract return 4 code:
        1: user has the right
        0: user doesn't have the right
        -1: the user doesn't exist
        -2: the right doesn't exist for the user
        """
        pass

def deploy() -> anno_UserRightChecker:
    user_right_checker: anno_UserRightChecker = UserRightChecker.deploy()
    
    user_right_checker.create_user(1, "read_patient_data")
    print(user_right_checker.user_right_mapping(1, "read_patient_data"))

    print("status: ", user_right_checker.check_user_right(1, "read_patient_data"))
    # print("Ending count: ", counter.number())
    return user_right_checker

def moccasin_main() -> anno_UserRightChecker:
    return deploy()
