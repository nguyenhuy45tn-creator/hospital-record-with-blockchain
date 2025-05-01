# pragma version ^0.4.0
# @license MIT

struct State_of_Right:
    user_exist: bool
    right_exist: bool
    has_right: bool

user_right_mapping: public(HashMap[uint128, HashMap[String[20], State_of_Right]])

@external
def create_user(
        user_id: uint128, 
        right: String[20]):

    self.user_right_mapping[user_id][right] = State_of_Right(
                                                user_exist = True,
                                                right_exist = True,
                                                has_right = True)



@external
def modify_user_right(
        user_id: uint128, 
        access_right: String[20], 
        has_right: bool) -> int8:
    #The contract return 3 code:
    #   1: successfully changed the right
    #  -1: the user doesn't exist
    #  -2: the right doesn't exist for the user
    

    state_of_right: State_of_Right = self.user_right_mapping[user_id][access_right]

    if not state_of_right.user_exist:
        return -1
    
    if not state_of_right.right_exist:
        return -2

    state_of_right.has_right = has_right
    return 1

@external
@view
def check_user_right(user_id: uint128, 
        access_right: String[20]) -> int8:
    #The contract return 4 code:
    #   1: user has the right
    #   0: user doesn't have the right
    #  -1: the user doesn't exist
    #  -2: the right doesn't exist for the user

        state_of_right: State_of_Right = self.user_right_mapping[user_id][access_right]

        if not state_of_right.user_exist:
            return -1
        
        if not state_of_right.right_exist:
            return -2

        if state_of_right.has_right:
            return 1
        else:
            return 0
    

    
    
