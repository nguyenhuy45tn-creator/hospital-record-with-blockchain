from moccasin.config import get_config
from boa.contracts.abi.abi_contract import ABIContract
import boa
from eth_account import Account
from script.interface import RoleRightChecker
from functools import wraps
from datetime import datetime
import json
from script.interface import Logger, Log



config = get_config()
active_network = config.get_active_network()
# Get the latest counter of the Counter contract
contract_logger = active_network \
                        .get_latest_contract_checked("Logger")

_logger = Logger(contract_logger)

def logged(logger: Logger= _logger):
    def _inner_logged(func):
        @wraps(func)
        def with_logging(*args, **kwargs):
            try:
                value = func(*args, **kwargs)
                log = Log(func, 
                          result = "Success", 
                          output = value, 
                          args=args, 
                          kwargs=kwargs)
            except Exception as e:
                result = f"Failed - {e}"
                log = Log(func, 
                          result = "Error", 
                          output = str(e), 
                          args=args, 
                          kwargs=kwargs)
            logger.add_log(
                        json.dumps(
                            log.__dict__,
                            indent=4
                            )
                    )
            return value
        return with_logging
    return _inner_logged

