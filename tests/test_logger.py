import boa
from pytest import fixture
from script.interface import Logger
from script.interface import Log
from script.contract_logger import logged
import json

@fixture
def logger():
    boa.reset_env()
    contract_logger = boa.load("src/Logger.vy")
    return contract_logger

def test_logged_simple_arg(logger):
    """
        test case where the arguments are of simple type
    """
    numbers = [0, 1 ,2, 3]
    exponents = [0, 1, 2, 3]
    @logged(logger)
    def some_func(num: int, exponent: dict):
        return num**exponent
    
    [some_func(num, exponent=exp) for num, exp in zip(numbers, exponents)]

    assert logger.get_length() == len(numbers), logger.get_length()
    logs: list[dict] = Logger(logger).get_newest(1)
    logs.reverse()
    for enum, log in enumerate(logs):
        obj = log
        assert obj["func"] == "some_func", log
        assert obj["args"] == [numbers[-(enum+1)]], log
        assert obj["kwargs"] == {"exponent": exponents[-(enum+1)]}, log
        assert obj["result"] == "Success", logs

def test_logged_complex_input(logger):
    """
        test case where the arguments are of complex type
    """

    numbers = [[0], [1] ,[2], [3]]
    exponents = [{"arg": 0}, 
                {"arg": 1}, 
                {"arg": 2}, 
                {"arg": 3}]
    @logged(logger)
    def some_func(num: int, exponent: dict):
        return num[0]**exponent["arg"]
    
    [some_func(num, exponent=exp) for num, exp in zip(numbers, exponents)]

    assert logger.get_length() == len(numbers), logger.get_length()
    logs: list[str] = Logger(logger).get_newest(10)
    for enum, log in enumerate(logs):
        obj = log
        assert obj["func"] == "some_func", log
        assert obj["args"] == [[enum,],], log
        assert obj["kwargs"] == {"exponent": {"arg": enum}}, log
        assert obj["result"] == "Success", logs

def test_failure(logger):
    """
        test in case an exception is raised in the inner function
    """
    test_input = {"key":"23"}

    @logged(logger)
    def some_func(test_input: dict):
        result = test_input["non_exist_key"]
    
    try:
        some_func(test_input=test_input)
    except Exception as e:
        print(e)

    logs: list[str] = Logger(logger).get_newest(1)
    newest_res = logs[0]
    assert newest_res["result"] == "Error", logs[-1]
    assert newest_res["output"] == "KeyError('non_exist_key')", logs[-1]



