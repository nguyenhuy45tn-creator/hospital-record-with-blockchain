import boa.interpret
from eth_account import Account
from script.interface import RoleRightChecker
import inspect
import uuid
from functools import wraps
from datetime import datetime
import json
from script.interface import Logger, Log
from script.deploy import deploy
import sqlite3
import boa
from pathlib import Path

# Get the latest counter of the Counter contract
boa.set_network_env("http://127.0.0.1:8545")
boa.env.add_account(Account.from_key("0x9db892b6ddbdc723db979a80e68a93d4649a3c416f5ce1c145f358b3b895880f"))

if not Path("cache/contract_logger.address").exists():
    contract_logger = boa.load("src/Logger.vy")
    with open("cache/contract_logger.address","w") as file:
        address = file.write(contract_logger.address)
else:
    with open("cache/contract_logger.address","r") as file:
            address = file.read()
    contract_logger = boa.load_partial("src/Logger.vy").at(address)

_logger = Logger(contract_logger)

cached_log = Path("cache")/"cached_log.db"

conn = None
if sqlite3.threadsafety == 3:
    conn = sqlite3.connect(
        str(cached_log.absolute()), 
        check_same_thread=False)


#initialize cache
if conn is not None:
    conn.execute("""
        DROP TABLE IF EXISTS cached_logs;
    """)
    conn.execute("""
            CREATE TABLE IF NOT EXISTS cached_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_mss VARCHAR(1000)
            );""")
    for i in range(contract_logger.get_length()):
            log_mss = contract_logger.log_db(i)
            conn.execute("""
                INSERT INTO cached_logs(log_mss) VALUES (?)
                """, (log_mss,)
                )
    conn.commit()




def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)

def logged(logger=_logger):
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
                log_mss = json.dumps(
                            log.__dict__,
                            indent=4,
                            default=json_serial # Use the custom serializer
                            )
                logger.add_log(
                        log_mss
                    )
                conn.execute("""
                INSERT INTO cached_logs(log_mss) VALUES (?)
                """, (log_mss,)
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
                log_mss = json.dumps(
                            log.__dict__,
                            indent=4,
                            default=json_serial # Use the custom serializer
                            )
                logger.add_log(
                    log_mss
                    )
                
                conn.execute("""
                INSERT INTO cached_logs(log_mss) VALUES (?)
                """, (log_mss,)
                )
                raise e
            print("----------",log.output)
           
            
        return with_logging
    return _inner_logged
