from src import RoleRightChecker, Logger


def deploy():
    user_right_checker = RoleRightChecker.deploy()
    logger = Logger.deploy()
    return user_right_checker

def moccasin_main():
    deploy()

