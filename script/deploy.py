import boa
from script.interface import RoleRightChecker as i_RoleRightChecker
from src import Logger


def deploy():
    user_right_checker = boa.load("src/RoleRightChecker.vy")
    return i_RoleRightChecker(user_right_checker)

def deploy_logger():
    Logger.deploy()
    
def moccasin_main():
    deploy_logger()
    

