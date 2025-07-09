
from script.interface import RoleRightChecker
import sqlite3
from boa.contracts.abi.abi_contract import ABIContract
import boa
from flask import g
from eth_account import Account 
from pathlib import Path
from script import roles, rights
# config = get_config()
# active_network = config.get_active_network()
# Get the latest counter of the Counter contract
# user_right_checker = RoleRightChecker(
#                         active_network
#                         .get_latest_contract_checked("RoleRightChecker"))

def create_role_right_checker() -> RoleRightChecker:
    
    boa.set_network_env("http://127.0.0.1:8545")

    boa.env.add_account(Account.from_key("0x9db892b6ddbdc723db979a80e68a93d4649a3c416f5ce1c145f358b3b895880f"))
    
    if Path("cache/role_right_checker.address").exists():
        with open("cache/role_right_checker.address","r") as file:
            address = file.read()
        user_right_checker = RoleRightChecker(
                                boa
                                .load_partial("src/RoleRightChecker.vy")
                                .at(address))
    else:
        contract =  boa.load("src/RoleRightChecker.vy")
        with open("cache/role_right_checker.address","w") as file:
            address = file.write(contract.address)
        user_right_checker = RoleRightChecker(contract)
        user_right_checker.add_role_w_right(roles.ADMIN, rights.READ_PATIENT_BASIC_DATA)
        user_right_checker.add_role_w_right(roles.ADMIN, rights.READ_PATIENT_HEALTHCARE_RECORD_DATA)
        user_right_checker.add_role_w_right(roles.ADMIN, rights.WRITE_PATIENT_BASIC_DATA)
        user_right_checker.add_role_w_right(roles.ADMIN, rights.CHANGE_OWN_PASSWORD_RIGHT)
        user_right_checker.add_role_w_right(roles.ADMIN, rights.ADMIN_CHANGE_USER_PASSWORD_RIGHT)
        user_right_checker.add_role_w_right(roles.DOCTOR, rights.READ_PATIENT_BASIC_DATA)
        user_right_checker.add_role_w_right(roles.DOCTOR, rights.READ_PATIENT_HEALTHCARE_RECORD_DATA)
        user_right_checker.add_role_w_right(roles.DOCTOR, rights.CHANGE_OWN_PASSWORD_RIGHT)

        user_right_checker.add_role_w_right(roles.PATIENT, rights.READ_OWN_PATIENT_BASIC_DATA)
        user_right_checker.add_role_w_right(roles.PATIENT, rights.READ_OWN_HEALTHCARE_RECORD_RIGHT)
        user_right_checker.add_role_w_right(roles.PATIENT, rights.CHANGE_OWN_PASSWORD_RIGHT)
        # user_right_checker.modify_role_right(roles.PATIENT, READ_roles.PATIENT_BASIC_DATA, False)
        print(user_right_checker.check_right(roles.PATIENT, rights.READ_PATIENT_BASIC_DATA))
    return user_right_checker

def get_latest_contract_information(contract_name: str):
    with sqlite3.connect("deployment_information/ganache_deployments.db") as con:
        cur = con.cursor()
        query = f""" SELECT filename, contract_address 
                    FROM deployments
                    WHERE contract_name = '{contract_name}'
                    ORDER BY deployment_id DESC
        """
        res = cur.execute(query).fetchone()
    return res
    
