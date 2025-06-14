import boa
from script.interface import RoleRightChecker as i_RoleRightChecker

def deploy():
    user_right_checker = boa.load("src/RoleRightChecker.vy")
    return i_RoleRightChecker(user_right_checker)

def moccasin_main():
    deploy()

