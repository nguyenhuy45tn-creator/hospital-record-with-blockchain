import boa
from pytest import fixture
from script.interface import Logger as interface_Logger
from script.interface import Log
from script.contract_logger import logged
import json

@fixture
def logger():
    contract_logger = boa.load("src/Logger.vy")
    return contract_logger

def test_logged_simple_arg():
    """
        test case where the arguments are of simple type
    """
    numbers = [0, 1 ,2, 3]
    exponents = [0, 1, 2, 3]
    @logged(contract_logger)
    def some_func(num: int, exponent: dict):
        return num**exponent
    
    [some_func(num, exponent=exp) for num, exp in zip(numbers, exponents)]

    assert logger.get_length() == len(numbers), logger.get_length()
    logs: list[str] = contract_logger.get_newest()
    for enum, log in enumerate(logs):
        obj = json.loads(log)
        assert obj["func"] == "some_func", log
        assert obj["args"] == [enum], log
        assert obj["kwargs"] == {"exponent": enum}, log
        assert obj["result"] == "Success", logs

def test_logged_complex_input():
    """
        test case where the arguments are of complex type
    """

    numbers = [[0], [1] ,[2], [3]]
    exponents = [{"arg": 0}, 
                {"arg": 1}, 
                {"arg": 2}, 
                {"arg": 3}]
    @logged(contract_logger)
    def some_func(num: int, exponent: dict):
        return num[0]**exponent["arg"]
    
    [some_func(num, exponent=exp) for num, exp in zip(numbers, exponents)]

    assert logger.get_length() == len(numbers), logger.get_length()
    logs: list[str] = contract_logger.get_newest()
    for enum, log in enumerate(logs):
        obj = json.loads(log)
        assert obj["func"] == "some_func", log
        assert obj["args"] == [[enum,],], log
        assert obj["kwargs"] == {"exponent": {"arg": enum}}, log
        assert obj["result"] == "Success", logs

def test_failure():
    """
        test in case an exception is raised in the inner function
    """
    test_input = {"key":"23"}

    @logged(contract_logger)
    def some_func(test_input: dict):
        result = test_input["non_exist_key"]
    
    try:
        some_func(test_input=test_input)
    except Exception as e:
        print(e)

    logs: list[str] = contract_logger.get_newest()
    newest_res = json.loads(logs[-1])
    assert newest_res["result"] == "Error", logs[-1]
    assert newest_res["output"] == "KeyError('non_exist_key')", logs[-1]



