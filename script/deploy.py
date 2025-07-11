import boa
from script.interface import RoleRightChecker as i_RoleRightChecker
from eth_account import Account
from pathlib import Path


def deploy():
    user_right_checker = boa.load("src/RoleRightChecker.vy")
    return i_RoleRightChecker(user_right_checker)

def deploy_logger():
    boa.set_network_env("http://127.0.0.1:8545")
    boa.env.add_account(Account.from_key("0x9db892b6ddbdc723db979a80e68a93d4649a3c416f5ce1c145f358b3b895880f"))
    contract_logger = boa.load_partial("src/Logger.vy").deploy()
    
def moccasin_main():
    deploy_logger()

cache_folder = Path("cache")
cache_folder.mkdir(exist_ok=True)
cache_file = cache_folder/"contract_cache"

if not cache_file.exists():
    deploy()
