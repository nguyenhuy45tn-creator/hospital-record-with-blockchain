from moccasin.config import get_config
from boa.contracts.abi.abi_contract import ABIContract
import boa
from eth_account import Account


# from deploy import UserRightChecker
# from boa.deployments import Deployment



def moccasin_main():
    config = get_config()
    active_network = config.get_active_network()
    # Get the latest counter of the Counter contract
    user_right_checker: ABIContract= active_network.get_latest_contract_checked("UserRightChecker")
    
    # if user_right_checker is None:
    #     boa.set_network_env("http://127.0.0.1:8545")
    #     boa.env.add_account(Account.from_key("0x646f1ce2fdad0e6deeeb5c7e8e5543bdde65e86029e2fd9fc169899c440a7913"))
    #     user_right_checker: UserRightChecker = boa.load_partial("src/UserRightChecker_deployer.vy").at("0x0290FB167208Af455bB137780163b7B7a9a10C16")

    user_right_checker.create_user(2)