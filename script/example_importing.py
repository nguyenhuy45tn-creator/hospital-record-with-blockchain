from script.contract import user_right_checker

print("creating user with id: 2")
user_right_checker.add_role('patient')

print("add right")
user_right_checker.add_right("read_patient_data")

print("check user right to read_patient_information. Should be true(code 1).")
result = user_right_checker.check_right("nurse", "read_patient_data")
print(f"Code: {result}.")


user_right_checker.add_role_w_right("doctor", "write_patient_data")
print("check user right to read_patient_information. Should be false (code 0).")
result = user_right_checker.check_right("patient","read_patient_data")
print(f"Code: {result}.")
print()
user_right_checker.add_role_w_right("nurse", "read_patient_data")
print("check user right to read_patient_information. Should be true(code 1).")
result = user_right_checker.check_right("nurse", "read_patient_data")
print(f"Code: {result}.")

print("role list")
