from src import RoleRightChecker, Logger
from script.interface import RoleRightChecker as i_RoleRightChecker

def deploy():
    user_right_checker = RoleRightChecker.deploy()
    logger = Logger.deploy()
    return i_RoleRightChecker(user_right_checker)

def moccasin_main():
    deploy()

