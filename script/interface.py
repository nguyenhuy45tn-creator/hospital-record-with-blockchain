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

class UserRightChecker(VyperContract):
    def __init__(self, compiler_data, *args, value=0, env = None, override_address = None, skip_initcode=False, created_from = None, contract_name=None, filename = None, gas=None):
        super().__init__(compiler_data, *args, value=value, env=env, override_address=override_address, skip_initcode=skip_initcode, created_from=created_from, contract_name=contract_name, filename=filename, gas=gas)

    def  create_user(user_id: uint128):
        pass

    def create_user_w_right(
        user_id: uint128, 
        right: String[20]):
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
        """
        The contract return 4 code:
            1: user has the right
            0: user doesn't have the right
            -1: the user doesn't exist
        """
        pass