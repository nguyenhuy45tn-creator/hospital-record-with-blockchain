from src import Logger
from pytest import fixture
from script.interface import Logger as interface_Logger
from script.contract_logger import logged, _logger

def test_logged():
    num = 2
    
    @logged()
    def some_func(num: int):
        return num**2
    
    some_func(2)
    return _logger.get_newest()

[print(x) for x in test_logged()]