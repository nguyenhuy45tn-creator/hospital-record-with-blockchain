from moccasin.config import get_config
from boa.contracts.abi.abi_contract import ABIContract
import boa
from eth_account import Account
from script.interface import RoleRightChecker
import inspect
import uuid
from functools import wraps
from datetime import datetime
import json
from script.interface import Logger, Log
from script.deploy import deploy
import boa

# Get the latest counter of the Counter contract
boa.set_network_env("http://127.0.0.1:8545")
boa.env.add_account(Account.from_key("0x9db892b6ddbdc723db979a80e68a93d4649a3c416f5ce1c145f358b3b895880f"))
contract_logger = boa.load_partial("src/Logger.vy").at("0xb99df60f7b61F8643eE8B465869d43196C318AaA")


_logger = Logger(contract_logger)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)

def logged(logger: Logger= _logger):
    def _inner_logged(func):
        @wraps(func)
        def with_logging(*args, **kwargs):
            # Filter out 'engine' and 'role_right_checker' from kwargs
            kwargs_to_log = {k: v for k, v in kwargs.items() if k not in ['engine', 'role_right_checker']}

            # Filter out 'engine' and 'role_right_checker' from args based on function signature
            try:
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
            except ValueError: # Happens for some built-in functions/methods
                param_names = [] # Cannot inspect, so log args as is or make a choice to empty them

            args_to_log_list = []
            for i, arg_val in enumerate(args):
                if i < len(param_names):
                    param_name = param_names[i]
                    if param_name not in ['engine', 'role_right_checker']:
                        args_to_log_list.append(arg_val)
                else:
                    # This argument is part of *args in the wrapped function's definition
                    args_to_log_list.append(arg_val)
            args_to_log = tuple(args_to_log_list)

            try:
                value = func(*args, **kwargs)
                log = Log(func, 
                          result = "Success",
                          args=args_to_log, 
                          kwargs=kwargs_to_log)
                logger.add_log(
                        json.dumps(
                            log.__dict__,
                            indent=4,
                            default=json_serial # Use the custom serializer
                            )
                    )
                return value
            except Exception as e:
                log = Log(func, 
                          result = "Error", 
                        #   in failure case, we log the error message
                        #   but not in sucess case since not all output
                        #   are json serializable. 
                          output = repr(e), 
                          args=args_to_log, 
                          kwargs=kwargs_to_log)
                logger.add_log(
                        json.dumps(
                            log.__dict__,
                            indent=4,
                            default=json_serial # Use the custom serializer
                            )
                    )
                raise e
            print("----------",log.output)
           
            
        return with_logging
    return _inner_logged
