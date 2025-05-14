from src import Logger
from pytest import fixture
from script.interface import Logger as interface_Logger
from script.contract_logger import logged


logger = Logger.deploy()
contract_logger = interface_Logger(logger)

def test_logged():
    num = 2
    
    @logged(contract_logger)
    def some_func(num: int):
        return num**2
    
    some_func(2)
    return contract_logger.get_newest()

print(test_logged()[0])