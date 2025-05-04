# pragma version ^0.4.0
# @license MIT

user_exist: public(HashMap[uint128, bool])
user_right_mapping: public(HashMap[uint128, HashMap[String[20], bool]])

@external
def create_user_w_right(
        user_id: uint128, 
        right: String[20]):

    self.user_exist[user_id] = True
    self.user_right_mapping[user_id][right] = True


@external
def  create_user(user_id: uint128):
    self.user_exist[user_id] = True
    

@external
def modify_user_right(
        user_id: uint128, 
        access_right: String[20], 
        has_right: bool) -> int8:
    #The contract return 3 code:
    #   1: successfully changed the right
    #  -1: the user doesn't exist

    if not self.user_exist[user_id]:
        return -1
    
    self.user_right_mapping[user_id][access_right] = has_right
    return 1

@external
@view
def check_user_right(user_id: uint128, 
        access_right: String[20]) -> int8:
    #The contract return 4 code:
    #   1: user has the right
    #   0: user doesn't have the right
    #  -1: the user doesn't exist

    if not self.user_exist[user_id]:
        return -1

    if self.user_right_mapping[user_id][access_right] == True:
        return 1
    else:
        return 0
    
    

    
