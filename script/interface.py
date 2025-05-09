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

class RoleRightChecker:
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

    def add_role(self, role_name: String[100]):

        assert len(role_name) <= 100

        return self.user_right_checker.create_user(user_id)

    def add_right(self, right: String[100]):
        assert len(right) <= 100

        return self.user_right_checker.add_right(right)

    def modify_role_right(
        self, 
        role_name: String[100], 
        right: String[100], 
        has_right: bool
    ) -> int8:
        """
        Assigns or revokes a specific right for a given role.

        Parameters:
            role_name: The name of the role to modify.
            right: The name of the right to assign or revoke.
            has_right: If True, assigns the right. If False, revokes it.

        Returns:
            1 if the right was successfully modified.
        -1 if the role does not exist.
        """
        return (self.user_right_checker
                    .create_user_w_right(
                            role_name = role_name, 
                            right = right))

    def add_role_w_right(
        self,
        role_name: String[100], 
        right: String[100]
    ) -> int8:
        """
        Adds a new role and a right if they don't exist,
        and assigns the right to the role.

        Parameters:
            role_name: The name of the role to add or update.
            right: The name of the right to assign.

        Returns:
            Result of the modify_role_right function.
        """

        return self.user_right_checker.add_role_w_right(role_name, right)
    
    def check_right(self, role_name: String[100], right: String[100]) -> int8:

        """
    4 output: 
    -1: role doesn't exist
    -2: right doesn't exist
    0: role doesn't have right
    1: role has right
    """
        assert len(role_name) <= 100
        assert len(right) <= 100
        
        return (self.user_right_checker
                        .check_user_right(
                            role_name,
                            right
                        ))
    
    def delete_role(self,role_name: String[100]) -> int8:
        assert len(role_name) <= 100
        return self.user_right_checker.delete_role(role_name)