
from script.interface import RoleRightChecker
import sqlite3
from boa.contracts.abi.abi_contract import ABIContract
import boa
from flask import g
from eth_account import Account 

# config = get_config()
# active_network = config.get_active_network()
# Get the latest counter of the Counter contract
# user_right_checker = RoleRightChecker(
#                         active_network
#                         .get_latest_contract_checked("RoleRightChecker"))

def create_role_right_checker() -> RoleRightChecker:

    
    if "role_right_checker" in g:
        return g.role_right_checker
    
    boa.set_network_env("http://127.0.0.1:8545")
    contract_info = get_latest_contract_information("RoleRightChecker")

    boa.env.add_account(Account.from_key("0x9db892b6ddbdc723db979a80e68a93d4649a3c416f5ce1c145f358b3b895880f"))
    
    user_right_checker = RoleRightChecker(
                            boa
                            .load_partial(contract_info[0])
                            .at(contract_info[1]))

    g.role_right_checker = user_right_checker

    return g.role_right_checker

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
    
