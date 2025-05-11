from script.contract import user_right_checker

print()
print("----------------")
print("checking import")
print(user_right_checker.view_roles())
print(user_right_checker.view_rights())
print(user_right_checker.check_right("doctor", "write_patient_data"))