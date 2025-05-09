# @version ^0.4.0
# @license MIT

# -------------------------------------------------------------
# Role-Based Access Control (RBAC) Smart Contract in Vyper
# This contract allows adding roles and access rights, and mapping
# roles to rights in a permission management system.
# -------------------------------------------------------------

# State Variables

# Track the total number of roles and rights added.
current_num_role: uint16
current_num_right: uint16

# List of all added access rights (e.g., "READ", "WRITE")
right_list: public(DynArray[String[100], 20])

# Check if a right exists in the system
right_exists: public(HashMap[String[100], bool])

# Position of a right in the right_list array for quick access
right_position: public(HashMap[String[100], uint16])

# List of all added roles (e.g., "Admin", "User")
role_list: public(DynArray[String[100], 20])

# Check if a role exists in the system
role_exists: public(HashMap[String[100], bool])

# Position of a role in the role_list array for quick access
role_position: public(HashMap[String[100], uint16])

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
    return 1

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
    return 1

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

# Add a role and immediately assign it a right
@external
def add_role_w_right(
        role_name: String[100], 
        right: String[100]
):
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
        self.add_role(role_name)

    if not self.right_exists[right]:
        self.add_right(right)

    return self.modify_role_right(role_name, right, True)
