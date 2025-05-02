def test_query_user_exist_full_right(user_right_checker):

    result = user_right_checker.check_user_right(1, "read_patient_data")

    assert result == 1

def test_query_user_doesnt_exist(user_right_checker):

    result = user_right_checker.check_user_right(3, "read_patient_data")

    assert result == -1

def test_query_user_exists_no_right(user_right_checker):

    result = user_right_checker.check_user_right(2, "read_patient_data")

    assert result == 0, f"the funciton gives {result}"
