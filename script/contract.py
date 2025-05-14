from moccasin.config import get_config
from boa.contracts.abi.abi_contract import ABIContract
import boa
from eth_account import Account
from script.interface import RoleRightChecker

# from deploy import UserRightChecker
# from boa.deployments import Deployment

config = get_config()
active_network = config.get_active_network()
# Get the latest counter of the Counter contract
user_right_checker = RoleRightChecker(
                        active_network
                        .get_latest_contract_checked("RoleRightChecker"))



