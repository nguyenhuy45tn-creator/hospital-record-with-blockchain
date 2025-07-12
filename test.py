import boa
from eth_account import Account
from script.interface import RoleRightChecker
import inspect
import uuid
from functools import wraps
from datetime import datetime
import json
from script.interface import Logger, Log
from script.deploy import deploy
import boa

boa.set_network_env("http://127.0.0.1:8545")
boa.env.add_account(Account.from_key("0x9db892b6ddbdc723db979a80e68a93d4649a3c416f5ce1c145f358b3b895880f"))
contract_logger = boa.load_partial("src/Logger.vy").at("0xBbc121f934aCD16c503305858bccaEB928aCF067")
print(contract_logger.get_length())
for i in range(0, contract_logger.get_length()): 
    print(contract_logger.get_value(i))
