from script.contract import create_role_right_checker
from script.rights import READ_OWN_PATIENT_BASIC_DATA, READ_PATIENT_BASIC_DATA, WRITE_PATIENT_BASIC_DATA, READ_PATIENT_HEALTHCARE_RECORD_DATA, WRITE_PATIENT_HEALTHCARE_RECORD_DATA,READ_OWN_HEALTHCARE_RECORD_RIGHT, ADD_USER_ROLE, CHANGE_OWN_PASSWORD_RIGHT, ADMIN_CHANGE_USER_PASSWORD_RIGHT
from script.roles import PATIENT, DOCTOR, NURSE, ADMIN
from script import roles, rights
import boa
from eth_account import Account
from boa.deployments import DeploymentsDB, set_deployments_db
import sqlite3
set_deployments_db(DeploymentsDB("deployment_information/deployments.db"))

boa.set_network_env("http://127.0.0.1:8545")

boa.env.add_account(Account.from_key("0x9db892b6ddbdc723db979a80e68a93d4649a3c416f5ce1c145f358b3b895880f"))

user_right_checker = create_role_right_checker()
user_right_checker.add_role_w_right(role_name=PATIENT, right= READ_OWN_HEALTHCARE_RECORD_RIGHT)
user_right_checker.add_role_w_right(role_name=PATIENT, right= READ_OWN_PATIENT_BASIC_DATA)
user_right_checker.add_role_w_right(role_name=PATIENT, right= CHANGE_OWN_PASSWORD_RIGHT)
user_right_checker.add_role_w_right(role_name=DOCTOR, right= READ_PATIENT_BASIC_DATA)
user_right_checker.add_role_w_right(role_name=DOCTOR, right= WRITE_PATIENT_BASIC_DATA)
user_right_checker.add_role_w_right(role_name=DOCTOR, right= READ_OWN_HEALTHCARE_RECORD_RIGHT)
user_right_checker.add_role_w_right(role_name=DOCTOR, right= READ_OWN_PATIENT_BASIC_DATA)
user_right_checker.add_role_w_right(role_name=DOCTOR, right= READ_PATIENT_HEALTHCARE_RECORD_DATA)
user_right_checker.add_role_w_right(role_name=DOCTOR, right= WRITE_PATIENT_HEALTHCARE_RECORD_DATA)
user_right_checker.add_role_w_right(role_name=DOCTOR, right= CHANGE_OWN_PASSWORD_RIGHT)
user_right_checker.add_role_w_right(role_name=NURSE, right= READ_PATIENT_BASIC_DATA)
user_right_checker.add_role_w_right(role_name=NURSE, right= WRITE_PATIENT_BASIC_DATA)
user_right_checker.add_role_w_right(role_name=NURSE, right= READ_OWN_HEALTHCARE_RECORD_RIGHT)
user_right_checker.add_role_w_right(role_name=NURSE, right= READ_OWN_PATIENT_BASIC_DATA)
user_right_checker.add_role_w_right(role_name=NURSE, right= READ_PATIENT_HEALTHCARE_RECORD_DATA)
user_right_checker.add_role_w_right(role_name=NURSE, right= WRITE_PATIENT_HEALTHCARE_RECORD_DATA)
user_right_checker.add_role_w_right(role_name=NURSE, right= CHANGE_OWN_PASSWORD_RIGHT)
user_right_checker.add_role_w_right(role_name=ADMIN, right= ADD_USER_ROLE)
user_right_checker.add_role_w_right(role_name=ADMIN, right= WRITE_PATIENT_BASIC_DATA)
user_right_checker.add_role_w_right(role_name=ADMIN, right= ADMIN_CHANGE_USER_PASSWORD_RIGHT)
user_right_checker.add_role_w_right(role_name=ADMIN, right= CHANGE_OWN_PASSWORD_RIGHT)
print(user_right_checker.check_right(PATIENT, READ_PATIENT_BASIC_DATA))

# with sqlite3.connect("deployment_information/deployments.db") as conn:
#     conn.execute("""
        
#         CREATE TABLE IF NOT EXISTS deployments(
#             deployment_id integer primary key autoincrement,
#             session_id text,
#             contract_address text,
#             contract_name text,
#             filename text,
#             rpc text,
#             deployer text,
#             tx_hash text,
#             broadcast_ts real,
#             tx_dict text,
#             receipt_dict text,
#             source_code text,
#             abi text
#         );""")
# with set_deployments_db(DeploymentsDB("deployment_information/deployments.db")):
#     contract_logger = boa.load("src/Logger.vy")

# print(contract_logger.address)