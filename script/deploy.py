from src import UserRightChecker
from script.interface import UserRightChecker as i_UserRightChecker

def deploy() -> i_UserRightChecker:
    user_right_checker: i_UserRightChecker = UserRightChecker.deploy()
    return user_right_checker

def moccasin_main() -> i_UserRightChecker:
    user_right_checker = deploy()

