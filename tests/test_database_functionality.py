from script.db_connection import get_single_user, Role, Login, User
from sqlalchemy.orm import Session
from bcrypt import gensalt, hashpw

def test_get_single_user(db_engine):
    with Session(db_engine) as session:
        role_name="testrole"
    
        role =session.query(Role).filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name = role_name, description="Test Role")
            session.add(role)
            session.commit()
            role = session.merge(role)

        login_user_name="testusername"
        salt=gensalt()
        password="873eh"
        hashed_password = hashpw(password,salt)
        login =session.query(Login).filter_by(user_name=login_user_name).first()
        if not login:
            login = Login(user_name=login_user_name,hashed_password=hashed_password,salt=salt)
            session.add(login_user_name)
            session.commit()
            login = session.merge(login)


        test_user = User(full_name="Test User", address="test street", hospital_designation="Test_des")
        test_user.login_details = login
        test_user.role = role
        session.add(test_user)
        session.commit()
        user_sswi = test_user.system_wide_identifier
    
    retrieved_user = get_single_user(db_engine, user_sswi)
    assert retrieved_user is not None
    assert retrieved_user.system_wide_identifier == user_sswi
    assert retrieved_user.full_name == "Test User"
    assert retrieved_user.address == "test street"
    

        
    

        
