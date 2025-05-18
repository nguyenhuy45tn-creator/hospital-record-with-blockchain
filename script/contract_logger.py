from moccasin.config import get_config
from boa.contracts.abi.abi_contract import ABIContract
import boa
from eth_account import Account
from script.interface import RoleRightChecker
from functools import wraps
from datetime import datetime
import json
from script.interface import Logger, Log
from deploy import deploy

config = get_config()
active_network = config.get_active_network()
# Get the latest counter of the Counter contract
contract_logger = active_network \
                        .get_latest_contract_checked("Logger")

if contract_logger is None:
    deploy()
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
                          args=args, 
                          kwargs=kwargs)
                logger.add_log(
                        json.dumps(
                            log.__dict__,
                            indent=4
                            )
                    )
                return value
            except Exception as e:

                log = Log(func, 
                          result = "Error", 
                        #   in dailure case, we log the error message
                        #   but not in sucess case since not all output
                        #   are json serializable. 
                          output = repr(e), 
                          args=args, 
                          kwargs=kwargs)
                logger.add_log(
                        json.dumps(
                            log.__dict__,
                            indent=4
                            )
                    )
                raise e
            print("----------",log.output)
           
            
        return with_logging
    return _inner_logged

