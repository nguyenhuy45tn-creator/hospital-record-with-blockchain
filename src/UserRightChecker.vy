# @version ^0.4.0
# @license MIT

# -------------------------------------------------------------
# Role-Based Access Control (RBAC) Smart Contract in Vyper
# This contract allows adding roles and access rights, and mapping
# roles to rights in a permission management system.
# -------------------------------------------------------------

# State Variables

# Track the total number of roles and rights added.
current_num_role: uint8
current_num_right: uint8

# List of all added access rights (e.g., "READ", "WRITE")
right_list: public(DynArray[String[100], 2**8])

# Check if a right exists in the system
right_exists: public(HashMap[String[100], bool])

# Position of a right in the right_list array for quick access
right_position: public(HashMap[String[100], uint8])

# List of all added roles (e.g., "Admin", "User")
role_list: public(DynArray[String[100], 2**8])

# Check if a role exists in the system
role_exists: public(HashMap[String[100], bool])

# Position of a role in the role_list array for quick access
role_position: public(HashMap[String[100], uint8])

# Mapping between a role and its associated rights
# E.g., role_right_mapping["Admin"]["WRITE"] = True
role_right_mapping: public(HashMap[String[100], HashMap[String[100], bool]])

# Constructor - Initialize the contract state
@deploy
def __init__():
    self.current_num_role = 0
    self.current_num_right = 0
    self.role_list = []
    self.right_list = []

# Add a new role without any initial rights
@external
def add_role(role_name: String[100]):
    """
    Adds a new role to the system. This role does not have any rights by default.
    
    Parameters:
        role_name: Name of the role to add.
        
    Returns:
        1 on successful addition.
    """
    self.role_list.append(role_name)
    self.role_position[role_name] = self.current_num_role
    self.role_exists[role_name] = True
    self.current_num_role += 1

@internal
def add_role_int(role_name: String[100]):
    """
    Adds a new role to the system. This role does not have any rights by default.
    
    Parameters:
        role_name: Name of the role to add.
        
    Returns:
        1 on successful addition.
    """
    self.role_list.append(role_name)
    self.role_position[role_name] = self.current_num_role
    self.role_exists[role_name] = True
    self.current_num_role += 1


# Add a new access right to the system
@external
def add_right(right: String[100]):
    """
    Adds a new access right to the system.

    Parameters:
        right: Name of the access right to add.
    
    Returns:
        1 on successful addition.
    """
    self.right_list.append(right)
    self.right_position[right] = self.current_num_right
    self.right_exists[right] = True
    self.current_num_right += 1

# Add a new access right to the system
@internal
def add_right_int(right: String[100]):
    """
    Adds a new access right to the system.

    Parameters:
        right: Name of the access right to add.
    
    Returns:
        1 on successful addition.
    """
    self.right_list.append(right)
    self.right_position[right] = self.current_num_right
    self.right_exists[right] = True
    self.current_num_right += 1

# Modify whether a role has a certain right
@external
def modify_role_right(
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
    if not self.role_exists[role_name]:
        return -1
    
    self.role_right_mapping[role_name][right] = has_right
    return 1

@internal
def modify_role_right_int(
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
    if not self.role_exists[role_name]:
        return -1
    
    self.role_right_mapping[role_name][right] = has_right
    return 1

# Add a role and immediately assign it a right
@external
def add_role_w_right(
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
    if not self.role_exists[role_name]:
        self.add_role_int(role_name)

    if not self.right_exists[right]:
        self.add_right_int(right)

    return self.modify_role_right_int(role_name, right, True)

@external
@view
def check_right(role_name: String[100], right: String[100]) -> int8:
    """
    4 output: 
    -1: role doesn't exist
    -2: right doesn't exist
    0: role doesn't have right
    1: role has right
    """
    if not self.role_exists[role_name]:
        return -1
    
    if not self.right_exists[right]:
        return -2

    if not self.role_right_mapping[role_name][right]:
        return 0
    else: 
        return 1 
    

@external
def delete_role(role_name: String[100]) -> int8:

    role_idx: uint8 = self.role_position[role_name]
    role_idx_256: uint256 = convert(role_idx, uint256)

    if not(self.role_list[role_idx] == role_name):
        return -1
    
    for i: uint256 in range(len(self.role_list), bound=2**8):
        if i >= role_idx_256:
            self.role_list[i] = self.role_list[i+1] 

    self.role_exists[role_name] = False

    for right: String[100] in self.right_list:
        self.role_right_mapping[role_name][right] = False

    return 1

@external
def delete_right(right: String[100]) -> int8:

    right_idx: uint8 = self.right_position[right]
    right_idx_256: uint256 = convert(right_idx, uint256)

    if not(self.right_list[right_idx] == right):
        return -1
    
    for i: uint256 in range(len(self.right_list), bound=2**8):
        if i >= right_idx_256:
            self.right_list[i] = self.right_list[i+1] 

    self.right_exists[right] = False

    for role: String[100] in self.role_list:
        self.role_right_mapping[role][right] = False

    return 1