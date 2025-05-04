from moccasin.boa_tools import VyperContract
from boa.contracts.abi.abi_contract import ABIContract

class uint128(int):
    # this is only for better notation
    pass 

class int8(int):
    # this is only for better notation
    pass

class String(list):
    # this is only for better notation
    pass

class UserRightChecker:
    """
    A wrapper class for a Vyper contract that provides type-checked and boundary-checked
    methods to interact with a user rights management smart contract.

    This class provides Pythonic interface to perform operations like creating users,
    assigning rights to users, modifying user rights, and checking user rights.

    Attributes:
    -----------
    user_right_checker : ABIContract
        The ABI contract instance which the class wraps around.

    Methods:
    --------
    create_user(user_id: uint128):
        Creates a new user with the specified user ID. The user ID must be a non-negative
        integer less than 2**128.
    
    create_user_w_right(user_id: uint128, right: String[20]):
        Creates a new user with a specified user ID and assigns a right to the user.
        The right description must not exceed 20 characters in length.
    
    modify_user_right(user_id: uint128, access_right: String[20], has_right: bool) -> int8:
        Modifies the right of an existing user. Returns a status code indicating the success
        or failure of the operation:
            1 : Successfully changed the right.
            -1: The user doesn't exist.
            -2: The right doesn't exist for the user.
    
    check_user_right(user_id: uint128, access_right: String[20]) -> int8:
        Checks if a user has a specific right. Returns a status code:
            1 : User has the right.
            0 : User doesn't have the right.
            -1: The user doesn't exist.
    """

    def __init__(self, user_right_checker: ABIContract):
        self.user_right_checker = user_right_checker

    def create_user(self, user_id: uint128):
        assert user_id >=0
        assert user_id < 2**128

        return self.user_right_checker.create_user(user_id)

    def create_user_w_right(self, user_id: uint128, right: String[20]):
        assert user_id >=0
        assert user_id < 2**128
        assert len(right) <= 20, "right description has maximum length of 20"

        return (self.user_right_checker
                        .create_user_w_right(
                            user_id = user_id, 
                            right = right))

    def modify_user_right(self,
            user_id: uint128, 
            access_right: String[20], 
            has_right: bool) -> int8:
        """ 
        The contract return 3 code:
                1: successfully changed the right
                -1: the user doesn't exist
                -2: the right doesn't exist for the user
        """
        assert user_id >=0
        assert user_id < 2**128
        assert len(access_right) <= 20, "right description has maximum length of 20"
        assert isinstance(has_right, bool)

        return (self.user_right_checker
                        .create_user_w_right(
                            user_id = user_id, 
                            access_right = access_right))

    def check_user_right(self, 
                         user_id: uint128, 
                        access_right: String[20]) -> int8:
        """
        The contract return 4 code:
            1: user has the right
            0: user doesn't have the right
            -1: the user doesn't exist
        """
        assert user_id >=0
        assert user_id < 2**128
        assert len(access_right) <= 20, "right description has maximum length of 20"

        return (self.user_right_checker
                        .check_user_right(
                            user_id = user_id, 
                            access_right = access_right))