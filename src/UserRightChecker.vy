# pragma version ^0.4.0
# @license MIT

#role: string[100]
#right: string[100]
current_num_role: uint16
current_num_right: uint16

right_list: public(DynArray[String[100], 20])
right_exists: public(HashMap[String[100], bool])
right_position: public(HashMap[String[100], uint16]) # check if role exist fast

role_list: public(DynArray[String[100], 20])
role_exists: public(HashMap[String[100], bool])
role_position: public(HashMap[String[100], uint16]) # store where the role is in the array

role_right_mapping: public(HashMap[String[100], HashMap[String[100], bool]])

@deploy
def __init__():
    self.current_num_role = 0
    self.current_num_right = 0
    self.role_list = []
    self.right_list = []

@external
def add_role(role_name: String[100]):
    # this add a role with no right
    # useful if you just want to initiate a role

    self.role_list.append(role_name)
    self.role_position[role_name] = self.current_num_role
    self.current_num_role = self.current_num_role + 1

    return 1

@external
def add_right(right: String[100]):
    # this add a role with no right
    # useful if you just want to initiate a role

    self.right_list.append(right)
    self.right_position[right] = self.current_num_role
    self.current_num_right = self.current_num_right + 1

    return 1

@external
def modify_role_right(
        role_name: String[100], 
        right: String[100], 
        has_right: bool) -> int8:
    #The contract return 3 code:
    #   1: successfully changed the right
    #  -1: the role doesn't exist

    if not (self.role_position[role_name] >= 0):
        return -1
    
    self.role_right_mapping[role_name][access_right] = has_right
    return 1

@external
def add_role_w_right(
        role_name: String[100], 
        right: String[100]):

    if not self.role_exists[role_name]:
        self.add_role(role_name)

    if not self.right_exists[right]:
        self.add_right(right)

    return self.modify_role_right(role_name, right, True)



@external
@view
def check_right(role: String[100], 
        access_right: String[100]) -> int8:
    #The contract return 4 code:
    #   1: role has the right
    #   0: role doesn't have the right
    #  -1: the role doesn't exist

    if not self.role_exist[role_name]:
        return -1

    if self.role_right_mapping[role_name][access_right] == True:
        return 1
    else:
        return 0
    
