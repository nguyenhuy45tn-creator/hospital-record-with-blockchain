import uuid
import string
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    LargeBinary,
    select,
    text,
    cast,
    and_,
    or_
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base, Session, configure_mappers
from sqlalchemy.sql import func 
from sqlalchemy_continuum import make_versioned, utils as continuum_utils
from bcrypt import hashpw, checkpw, gensalt
from random import choices
from script.interface import RoleRightChecker 
from script.roles import ADMIN
from script.contract import create_role_right_checker
from script.contract_logger import logged

from script.rights import READ_OWN_PATIENT_BASIC_DATA, READ_PATIENT_BASIC_DATA, WRITE_PATIENT_BASIC_DATA, READ_PATIENT_HEALTHCARE_RECORD_DATA, WRITE_PATIENT_HEALTHCARE_RECORD_DATA,READ_OWN_HEALTHCARE_RECORD_RIGHT, ADD_USER_ROLE, CHANGE_OWN_PASSWORD_RIGHT, ADMIN_CHANGE_USER_PASSWORD_RIGHT

from os import environ

# Global variables for engine and role_right_checker



# Define the base class for declarative models
Base = declarative_base()
# Initialize sqlalchemy-continuum right after Base definition
# and before any models are defined.
make_versioned(user_cls=None)

class Role(Base):
    __tablename__ = 'roles'

    role_name = Column(String(50), primary_key=True)
    description = Column(Text)

    users = relationship("User", back_populates="role") # A role can have multiple users

    def __repr__(self):
        return f"{self.role_name}"
    
    
class Login(Base):
    __tablename__ = 'logins'

    user_name = Column(String(100), primary_key=True, index=True)
    # Use LargeBinary to store byte output from bcrypt
    hashed_password = Column(LargeBinary, nullable=False)
    salt = Column(LargeBinary, nullable=False)

    user = relationship("User", back_populates="login_details", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"{self.user_name}"

class User(Base):
    __versioned__ = {}
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    system_wide_identifier = Column(PG_UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    user_name = Column(String(100), ForeignKey('logins.user_name'), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    address = Column(Text)
    hospital_designation = Column(String(100))
    last_updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    updated_by_user_id = Column(Integer, ForeignKey('users.user_id'))
    user_role_name = Column(String(50), ForeignKey('roles.role_name'), nullable=False)

    # Relationship to Login (one-to-one)
    login_details = relationship("Login", back_populates="user", uselist=False, foreign_keys=[user_name])

    # Relationship to Role (many-to-one)
    role = relationship("Role", back_populates="users", foreign_keys=[user_role_name])

    # Self-referential relationships for user updates
    # The user who updated this user record:
    updated_by_user = relationship(
        "User",
        remote_side=[user_id],  # The 'user_id' of the User who performed the update
        foreign_keys=[updated_by_user_id],
        back_populates="users_they_updated"
    )
    # List of users that this user instance has updated:
    users_they_updated = relationship(
        "User",
        foreign_keys=[updated_by_user_id], # Looks for User records where updated_by_user_id is this user's ID
        back_populates="updated_by_user"
    )

    # Relationships to HealthcareRecord
    # Healthcare records where this user is the patient:
    patient_records = relationship(
        "HealthcareRecord",
        foreign_keys="[HealthcareRecord.patient_user_id]",
        back_populates="patient"
    )
    # Healthcare records that this user last updated:
    updated_records = relationship(
        "HealthcareRecord",
        foreign_keys="[HealthcareRecord.last_updated_by_user_id]",
        back_populates="last_updated_by"
    )

    def __repr__(self):
        version_display = None
        # Check if the instance is persistent (has an ID) before calling count_versions
        if continuum_utils.is_versioned(self) and self.user_id is not None:
            try:
                num_versions = continuum_utils.count_versions(self)
                version_display = num_versions - 1 if num_versions > 0 else None
            except Exception: # pragma: no cover (should not happen if persisted and versioned)
                pass # Keep version_display as None
        return f"<User(user_name='{self.user_name}', system_id='{self.system_wide_identifier}', version={version_display})>"
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'system_wide_identifier': str(self.system_wide_identifier) if self.system_wide_identifier else None,
            'user_name': self.user_name,
            'full_name': self.full_name,
            'address': self.address,
            'hospital_designation': self.hospital_designation,
            'last_updated_at': self.last_updated_at.isoformat() if self.last_updated_at else None,
            'updated_by_user_id': self.updated_by_user_id,
            'user_role_name': self.user_role_name
        }
        

class HealthcareRecord(Base):
    __versioned__ = {}
    __tablename__ = 'healthcare_records'

    record_id = Column(Integer, primary_key=True)
    patient_user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    record_data = Column(JSONB, nullable=False)
    last_updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_updated_by_user_id = Column(Integer, ForeignKey('users.user_id'))

    # Relationship to User (patient)
    patient = relationship(
        "User",
        foreign_keys=[patient_user_id],
        back_populates="patient_records"
    )
    # Relationship to User (who last updated this record)
    last_updated_by = relationship(
        "User",
        foreign_keys=[last_updated_by_user_id],
        back_populates="updated_records"
    )

    def __repr__(self):
        version_display = None
        # Check if the instance is persistent (has an ID) before calling count_versions
        if continuum_utils.is_versioned(self) and self.record_id is not None:
            try:
                num_versions = continuum_utils.count_versions(self)
                version_display = num_versions - 1 if num_versions > 0 else None
            except Exception: # pragma: no cover (should not happen if persisted and versioned)
                pass # Keep version_display as None
        return f"<HealthcareRecord(record_id={self.record_id}, patient_user_id={self.patient_user_id}, version={version_display})>"



def initialize_database():
    """
    Initializes the database connection and creates tables if they don't exist.
    This function is idempotent for engine creation and table creation.

    Returns:
        sqlalchemy.engine.Engine: The created SQLAlchemy engine instance as a global variable.
    """
    global engine
    if engine is None:
        DATABASE_URL = environ.get('DATABASE_URL', "postgresql://postgres:postgres@localhost:5432/sampledb")
        configure_mappers() # Ensure all mappers are configured before creating tables
        current_engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(current_engine)
        engine = current_engine
        print("Database engine initialized and tables created.")
    return engine

DATABASE_URL = environ.get('DATABASE_URL', "postgresql://postgres:postgres@localhost:5432/sampledb")
engine = create_engine(DATABASE_URL) # Initialize engine as None at module level

def _get_requestee_user_and_role(session, requestee_username: str):
    """Helper to fetch the requestee user and their role name."""
    requestee_user = session.query(User).join(Login).filter(Login.user_name == requestee_username).one_or_none()
    if not requestee_user:
        # This case should ideally be caught by a higher-level authentication layer
        raise ValueError(f"Requestee user '{requestee_username}' not found.")
    if not requestee_user.role:
        raise PermissionError(f"Requestee user '{requestee_username}' does not have an assigned role. Access denied.")
    return requestee_user, requestee_user.role.role_name

def _check_access(role_right_checker: RoleRightChecker, role_name: str, right_name: str, operation_description: str):
    """Helper to perform the access check and raise PermissionError if denied."""
    access_result = role_right_checker.check_right(role_name, right_name)
    if access_result == 1:
        return  # Access granted
    elif access_result == 0:
        raise PermissionError(f"User role '{role_name}' lacks right '{right_name}' to {operation_description}. Access denied.")
    elif access_result == -1:
        raise PermissionError(f"Role '{role_name}' not found in access control system. Cannot {operation_description}. Access denied.")
    elif access_result == -2:
        raise PermissionError(f"Right '{right_name}' not found in access control system. Cannot {operation_description}. Access denied.")
    else:
        raise PermissionError(f"Unknown access control result ({access_result}) for role '{role_name}' and right '{right_name}'. Cannot {operation_description}. Access denied.")

def get_single_user(requestee_username: str, user_system_wide_identifier:uuid.UUID):
    """
    Retrieves a single user from the database based on their system-wide identifier.
    Access control is performed before retrieving the user.
    This function uses global 'engine' for database sessions and global 'role_right_checker' for access control.

    Args:
        requestee_username (str): The username of the user making the request.
        user_system_wide_identifier (uuid.UUID): The unique UUID identifier of the user to retrieve.

    Returns:
        User: The User object corresponding to the provided identifier.

    Raises:
        PermissionError: If the requestee does not have permission to view the user.
        sqlalchemy.orm.exc.NoResultFound: If no user with the given identifier is found.
        sqlalchemy.orm.exc.MultipleResultsFound: If multiple users somehow have the same identifier (shouldn't happen due to unique constraint).
    """
    print("[241] requestee",requestee_username)
    print("[241] user_system_wide_identifier",user_system_wide_identifier)
    with Session(engine) as session:
        requestee_user, requestee_role_name = _get_requestee_user_and_role(session, requestee_username)

        # Determine the appropriate right based on whether it's a self-read or other-read
        target_user_for_swid_check = session.query(User).filter(User.system_wide_identifier == user_system_wide_identifier).one_or_none()
        if not target_user_for_swid_check:
            raise ValueError(f"User with SWID '{user_system_wide_identifier}' not found.")

        role_right_checker = create_role_right_checker()
        print(requestee_user.system_wide_identifier)
        
        if requestee_user.system_wide_identifier == target_user_for_swid_check.system_wide_identifier:
            print("[251] triggered")
            _check_access(role_right_checker, requestee_role_name, READ_OWN_PATIENT_BASIC_DATA, f"view own profile (SWID: {user_system_wide_identifier})")
        else:
            print("[254] triggered")
            _check_access(role_right_checker, requestee_role_name, READ_PATIENT_BASIC_DATA, f"view profile for user SWID: {user_system_wide_identifier}")

        query =  select(User).where(User.system_wide_identifier == user_system_wide_identifier)
        output = session.execute(query).scalar_one()

    return output

def get_all_users(requestee_username: str):
    """
    Retrieves all users from the database.
    Access control is performed to ensure the requestee has permission.
    This function uses global 'engine' for database sessions and global 'role_right_checker' for access control.

    Args:
        requestee_username (str): The username of the user making the request.

    Returns:
        list[User]: A list containing all User objects in the database.

    Raises:
        PermissionError: If the requestee does not have permission to list all users.
    """
    with Session(engine) as session:
        requestee_user, requestee_role_name = _get_requestee_user_and_role(session, requestee_username)
        role_right_checker = create_role_right_checker()
        _check_access(role_right_checker, requestee_role_name, READ_PATIENT_BASIC_DATA, "list all users")

        query =  select(User)
        representation = []
        output = session.execute(query).fetchall()
        for row in output:
            for user in row:
                # print(user)
                representation.append(user.to_dict())
    return representation

def get_all_roles(): #no validate, not public endpoint
    with Session(engine) as session:
        query = select(Role)
        output = session.execute(query).scalars().all()
    return output


def get_health_records(requestee_username: str, patient_swid:uuid.UUID):
    """
    Retrieves the healthcare records associated with a specific user.
    Access control is performed based on whether the requestee is viewing their own
    records or another patient's records.

    First finds the user by their system-wide identifier, then finds the
    healthcare records linked to that user's primary key ID. A user can
    have multiple healthcare records.
    This function uses global 'engine' for database sessions and global 'role_right_checker' for access control.

    Args:
        requestee_username (str): The username of the user making the request.
        patient_swid (uuid.UUID): The unique UUID identifier of the patient whose records are needed.

    Returns:
        list[HealthcareRecord]: A list of HealthcareRecord objects associated with the user.
                                Returns an empty list if the user is not found or has no records.

    Raises:
        PermissionError: If the requestee does not have permission to view these health records.
    """
    with Session(engine) as session:
        requestee_user, requestee_role_name = _get_requestee_user_and_role(session, requestee_username)
        if requestee_user.system_wide_identifier == patient_swid:
            _check_access(role_right_checker, requestee_role_name, READ_OWN_HEALTHCARE_RECORD_RIGHT, f"view own health records (Patient SWID: {patient_swid})")
        else:
            _check_access(role_right_checker, requestee_role_name, READ_PATIENT_HEALTHCARE_RECORD_DATA, f"view health records for patient SWID: {patient_swid}")

        patient_user = session.query(User).filter(User.system_wide_identifier == patient_swid).one_or_none()
        if not patient_user:
            raise ValueError(f"Patient with SWID '{patient_swid}' not found.")



        query = select(HealthcareRecord).where(HealthcareRecord.patient_user_id == patient_user.user_id)
        records = session.execute(query).scalars().all()
    return records

@logged()
def add_user(requestee_username: str, full_name: str, address: str, hospital_designation: str, role_for_new_user: str):
    """
    Adds a new user and their login credentials to the database.
    Access control is performed to ensure the requestee has permission.
    Username and password for the new user are generated automatically.
    This function uses global 'engine' for database sessions and global 'role_right_checker' for access control.

    Args:
        requestee_username (str): The username of the user making the request.
        full_name (str): The user's full name.
        address (str): The user's address.
        hospital_designation (str): The user's hospital designation.
        role_for_new_user (str): The name of the role to assign to the new user.

    Returns:
        tuple[str, str]: The generated username and plain text password for the new user.

    Raises:
        PermissionError: If the requestee does not have permission to add a user.
        ValueError: If the username already exists.
    """
    with Session(engine) as session:
        requestee_user, requestee_role_name = _get_requestee_user_and_role(session, requestee_username)

        role_right_checker = create_role_right_checker()
        _check_access(role_right_checker, requestee_role_name, WRITE_PATIENT_BASIC_DATA, "add a new user")

        # Generate a random username and password
        username = ''.join(choices(string.ascii_uppercase + string.digits, k=6))
        password_plain = ''.join(choices(string.ascii_uppercase + string.digits, k=12))

        # Check if username (for login) already exists
        existing_login = session.query(Login).filter_by(user_name=username).first()
        if existing_login:
            raise ValueError(f"Login username '{username}' already exists.")

        # Generate salt and hash the password
        salt = gensalt()
        hashed_password = hashpw(password_plain.encode('utf-8'), salt)

        # Create the Login instance
        new_login_entry = Login(
            user_name=username,
            hashed_password=hashed_password,
            salt=salt
        )

        # Create the User instance
        new_user = User(
            full_name=full_name,
            address=address,
            hospital_designation=hospital_designation,
            user_role_name=role_for_new_user
        )

        # Associate the User with the Login entry via the relationship
        # This will also ensure User.user_name is set to new_login_entry.user_name
        new_user.login_details = new_login_entry

        # Add the new_user to the session.
        # SQLAlchemy will also add new_login_entry due to the relationship and FK.
        session.add(new_user)
        session.commit()
    return username, password_plain

        
@logged()
def add_health_record(requestee_username: str, patient_user_id:int, record_data:dict):
    """
    Adds a new healthcare record for a specific user.
    Access control is performed. The requestee becomes the creator of the record.
    This function uses global 'engine' for database sessions and global 'role_right_checker' for access control.

    Args:
        requestee_username (str): The username of the user making the request (and creating the record).
        patient_user_id (int): The primary key ID of the user (patient) this record belongs to.
        record_data (dict): A dictionary containing the healthcare data to be stored (will be saved as JSONB).

    Raises:
        PermissionError: If the requestee does not have permission to add a health record.
        ValueError: If the patient_user_id or requestee_username is invalid.
    """
    with Session(engine) as session:
        requestee_user, requestee_role_name = _get_requestee_user_and_role(session, requestee_username)
        role_right_checker = create_role_right_checker()
        _check_access(role_right_checker, requestee_role_name, WRITE_PATIENT_HEALTHCARE_RECORD_DATA, f"add health record for patient ID {patient_user_id}")

        # Ensure patient exists
        patient_exists = session.query(User).filter_by(user_id=patient_user_id).count() > 0
        if not patient_exists:
            raise ValueError(f"Patient with user_id '{patient_user_id}' not found.")

        new_record = HealthcareRecord(patient_user_id=patient_user_id, record_data=record_data, last_updated_by_user_id=requestee_user.user_id)
        session.add(new_record)
        session.commit()
        return

def update_health_record(requestee_username: str, record_id:int, record_data:dict):
    """
    Updates an existing healthcare record.
    Access control is performed. The requestee becomes the updater of the record.

    Finds the record by its primary key ID and updates its data,
    the last updated timestamp, and the ID of the user performing the update.

    This function uses global 'engine' for database sessions and global 'role_right_checker' for access control.

    Args:
        requestee_username (str): The username of the user making the request (and updating the record).
        record_id (int): The primary key ID of the healthcare record to update.
        record_data (dict): The new dictionary data for the record.

    Raises:
        PermissionError: If the requestee does not have permission to update the health record.
        sqlalchemy.orm.exc.NoResultFound: If the record_id does not exist.
        ValueError: If requestee_username is invalid.
    """
    with Session(engine) as session:
        requestee_user, requestee_role_name = _get_requestee_user_and_role(session, requestee_username)
        _check_access(role_right_checker, requestee_role_name, WRITE_PATIENT_HEALTHCARE_RECORD_DATA, f"update health record ID {record_id}")

        query = select(HealthcareRecord).where(HealthcareRecord.record_id == record_id)
        record = session.execute(query).scalar_one()
        if record:
            record.record_data = record_data
            record.last_updated_at = datetime.now(timezone.utc)
            record.last_updated_by_user_id = requestee_user.user_id
            session.commit()
            return
        else:
            raise ValueError(f"Record with ID '{record_id}' not found.")

@logged()
def update_patient_basic_data(requestee_username: str, sys_wide_id:int, record_data:dict):
    """
    Updates an existing healthcare record.
    Access control is performed. The requestee becomes the updater of the record.

    Finds the record by its primary key ID and updates its data,
    the last updated timestamp, and the ID of the user performing the update.

    This function uses global 'engine' for database sessions and global 'role_right_checker' for access control.

    Args:
        requestee_username (str): The username of the user making the request (and updating the record).
        record_id (int): The primary key ID of the healthcare record to update.
        record_data (dict): The new dictionary data for the record.

    Raises:
        PermissionError: If the requestee does not have permission to update the health record.
        sqlalchemy.orm.exc.NoResultFound: If the record_id does not exist.
        ValueError: If requestee_username is invalid.
    """
    role_right_checker = create_role_right_checker()
    with Session(engine) as session:
        requestee_user, requestee_role_name = _get_requestee_user_and_role(session, requestee_username)
        _check_access(role_right_checker, requestee_role_name, WRITE_PATIENT_BASIC_DATA, f"fail to update patient basic info")

        query = select(User).where(User.system_wide_identifier == sys_wide_id)
        record = session.execute(query).scalar_one()
        if record:
            record.full_name = record_data["full_name"]
            record.address = record_data["address"]
            record.last_updated_at = datetime.now(timezone.utc)
            record.last_updated_by_user_id = requestee_user.user_id
            session.commit()
            return
        else:
            raise ValueError(f"Cannot find user")

@logged()
def add_role(requestee_username: str, role_name_to_add:str, description:str):
    """
    Adds a new role to the database.
    Access control is performed.
    This function uses global 'engine' for database sessions and global 'role_right_checker' for access control.

    Args:
        requestee_username (str): The username of the user making the request.
        role_name_to_add (str): The unique name for the new role.
        description (str): A description of the role's purpose or permissions.

    Raises:
        ValueError: If a role with the given role_name already exists.
    """
    with Session(engine) as session:
        requestee_user, requestee_role_name = _get_requestee_user_and_role(session, requestee_username)
        _check_access(role_right_checker, requestee_role_name, ADD_USER_ROLE, f"add new role '{role_name_to_add}'")

        # Check if a role with this name already exists
        existing_role = session.query(Role).filter_by(role_name=role_name_to_add).first()
        if existing_role:
            raise ValueError(f"Role '{role_name_to_add}' already exists.")

        # Create the new Role instance
        new_role = Role(role_name=role_name_to_add, description=description)
        session.add(new_role)
        session.commit()
    
def change_password(requestee_username: str, target_sys_id:str, new_password:str):
    """
    Changes the password for a given user.
    Access control is performed. Users can change their own password, or an admin
    can change other users' passwords, depending on rights.
    This function uses global 'engine' for database sessions and global 'role_right_checker' for access control.

    Args:
        requestee_username (str): The username of the user making the request.
        target_username (str): The username of the user whose password is to be changed.
        new_password (str): The new plain text password.

    Raises:
        PermissionError: If the requestee does not have permission.
        ValueError: If the username does not exist.
    """
    role_right_checker = create_role_right_checker()
    with Session(engine) as session:

        _requestee_user, requestee_role_name = _get_requestee_user_and_role(session, requestee_username)

        target_user_for_swid_check = session.query(User).filter(User.system_wide_identifier == target_sys_id).one_or_none()

        if _requestee_user.system_wide_identifier == target_user_for_swid_check.system_wide_identifier:
            _check_access(role_right_checker, requestee_role_name, CHANGE_OWN_PASSWORD_RIGHT, "change own password")
        else:
            _check_access(role_right_checker, requestee_role_name, ADMIN_CHANGE_USER_PASSWORD_RIGHT, f"change password for user '{target_sys_id}'")

        login_entry = session.query(Login).filter_by(user_name=target_user_for_swid_check.user_name).first()

        if not login_entry:
            raise ValueError(f"User '{target_user_for_swid_check.user_name}' not found.")

        # Generate new salt and hash the new password
        new_salt = gensalt()
        new_hashed_password = hashpw(new_password.encode('utf-8'), new_salt)

        # Update the login entry
        login_entry.salt = new_salt
        login_entry.hashed_password = new_hashed_password

        session.commit()
        print(f"Password for user '{target_sys_id}' changed successfully by '{requestee_username}'.")


def check_password(username: str, password_to_check: str) -> bool:
    """
    Checks if the provided password for a given username is correct.

    This function uses the global 'engine' for database sessions.

    Args:
        username (str): The username of the user to check.
        password_to_check (str): The plain text password to verify.

    Returns:
        bool: True if the password is correct, False otherwise (including if the user is not found).
    """
    with Session(engine) as session:
        login_entry = session.query(Login).filter_by(user_name=username).one_or_none()

        if not login_entry:
            return False  # User not found

        return checkpw(password_to_check.encode('utf-8'), login_entry.hashed_password)

def check_search_access(requestee_username):

    with Session(engine) as session:
        role_right_checker = create_role_right_checker()
        requestee_user, requestee_role_name = _get_requestee_user_and_role(session, requestee_username)
    print("role name----------", requestee_role_name)
    _check_access(role_right_checker, requestee_role_name, READ_PATIENT_BASIC_DATA, "list all users")

def search_users(requestee_username, search_phrase:str):
    with Session(engine) as session:
        requestee_user, requestee_role_name = _get_requestee_user_and_role(session, requestee_username)
        role_right_checker = create_role_right_checker()
        _check_access(role_right_checker, requestee_role_name, READ_PATIENT_BASIC_DATA, "list all users")

        # Use parameterized query to prevent SQL injection
        query = select(User).where(
            and_(
                or_(
                    func.left(cast(User.system_wide_identifier, String(36)), len(search_phrase)) == search_phrase,
                    func.lower(func.left(cast(User.full_name, String(36)), len(search_phrase))) == search_phrase.lower()
                ),
                User.user_role_name != "admin"
            )
        )
        result = session.execute(query).all()
        # query = f""" 
        #     SELECT * 
        #     FROM users
        #     WHERE 
        #         (
        #             LEFT(
        #                 CAST(
        #                     system_wide_identifier AS VARCHAR(20)), 
        #                     {len(search_phrase)}
        #                 ) = :search_phrase
        #             OR LEFT(
        #                 CAST(
        #                     full_name AS VARCHAR(20)), 
        #                     {len(search_phrase)}
        #                 ) = :search_phrase
        #         )
        #         AND user_role_name <> '{ADMIN}'       
        # """
        # #now it is safe against injection
        # result = session.execute(
        #     text(query), 
        #     {"search_phrase": search_phrase}).fetchall()

    # results = []
    # for row in result:
    #     for user in row.tuple():
    #         results.append(user.to_dict())
    return result # send the result directly



def get_system_wide_id(requestee_username: str) -> tuple[str, str]:
    """
    Purposefully left no security check since the informaiton returned is 
    highly low impact. This is to classify user_information page.
    """
    with Session(engine) as session:
        requestee, role = _get_requestee_user_and_role(session, requestee_username)
    return requestee.system_wide_identifier, role


def populate_example_data():
    """
    Populates the database with example roles, permissions, users, and records
    if they don't already exist. This function is idempotent.
    This function uses the global 'engine' for database sessions.
    """
    # engine and role_right_checker are expected to be global
    with Session(engine) as session:
        # --- 1. Define and Create Roles ---
        roles_data = {
            "patient": "A patient user, can read own records.",
            "doctor": "A medical doctor, can read/edit patient records.",
            "nurse": "A nurse, can read/edit patient records.",
            "admin": "An administrator, can manage users and roles."
        }
        roles = {}
        for name, desc in roles_data.items():
            role = session.query(Role).filter_by(role_name=name).first()
            if not role:
                role = Role(role_name=name, description=desc)
                session.add(role)
            roles[name] = role

        # Commit roles
        session.commit()
        # Refresh roles objects to ensure they have IDs after commit
        for name in roles: roles[name] = session.merge(roles[name])

        # --- 2. Create Example Users (Idempotent) ---
        users_data = [
            {"username": "patient_alice", "password": "password123", "full_name": "Alice Wonderland", "address": "123 Rabbit Hole", "hospital_designation": "Patient", "role": "patient"},
            {"username": "doctor_bob", "password": "password123", "full_name": "Dr. Bob Smith", "address": "456 Health St", "hospital_designation": "General Practitioner", "role": "doctor"},
            {"username": "nurse_carol", "password": "password123", "full_name": "Carol Danvers", "address": "789 Care Ave", "hospital_designation": "Registered Nurse", "role": "nurse"},
            {"username": "admin_dave", "password": "password123", "full_name": "Dave Administrator", "address": "1 Admin Plaza", "hospital_designation": "System Admin", "role": "admin"},
        ]

        created_users = {}
        for user_data in users_data:
            # Check if login (and thus user) already exists
            login_entry = session.query(Login).filter_by(user_name=user_data["username"]).first()
            if not login_entry:
                salt = gensalt()
                hashed_pw = hashpw(user_data["password"].encode('utf-8'), salt)
                
                new_login = Login(
                    user_name=user_data["username"],
                    salt=salt,
                    hashed_password=hashed_pw
                )

                user = User(
                    # user_name will be set via the login_details relationship
                    full_name=user_data["full_name"],
                    address=user_data["address"],
                    hospital_designation=user_data["hospital_designation"]
                )
                user.login_details = new_login # Associate user with login
                user.role = roles[user_data["role"]] # Assign single role object
                session.add(user) # Adding user will also add new_login due to relationship
                created_users[user_data["username"]] = user
            else:
                # User already exists, fetch them via the login entry's user relationship
                # and ensure it's part of the current session.
                if login_entry.user:
                    created_users[user_data["username"]] = session.merge(login_entry.user)
                else:
                    # Fallback: if login_entry.user is None (should not happen with correct setup)
                    # try to find User by user_name. This is less ideal.
                    _user = session.query(User).filter_by(user_name=login_entry.user_name).first()
                    if _user:
                        created_users[user_data["username"]] = _user
                    else:
                        print(f"Warning: Login {login_entry.user_name} exists but no associated User found. Skipping.")

        # Commit users to get their IDs
        session.commit()
        # Refresh user objects
        for username_key in list(created_users.keys()): # Iterate over a copy of keys
            if created_users[username_key]:
                 created_users[username_key] = session.merge(created_users[username_key])
            else: # Should not happen if logic above is correct
                del created_users[username_key]

        # --- 3. Create Example Health Record for Patient (Idempotent) ---
        patient_user = created_users.get("patient_alice")
        doctor_user = created_users.get("doctor_bob")

        if patient_user and doctor_user: # Ensure users were found/created
            existing_record = session.query(HealthcareRecord).filter_by(patient_user_id=patient_user.user_id).first()
            if not existing_record:
                record_data = {
                    "allergies": ["Penicillin"],
                    "conditions": ["Hypertension"],
                    "medications": [{"name": "Lisinopril", "dosage": "10mg", "frequency": "daily"}],
                    "notes": "Patient presented with high blood pressure."
                }
                new_record = HealthcareRecord(
                    patient_user_id=patient_user.user_id,
                    record_data=record_data,
                    last_updated_by_user_id=doctor_user.user_id # Track who created/updated
                )
                session.add(new_record)

        # Final commit for any remaining changes (role assignments, records)
        session.commit()
        print("Example data population complete (or data already existed).")

def moccasin_main():
    try:
        engine = initialize_database()
        print("Database initialized.")
        populate_example_data()

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure the database server is running, the database exists,")
        print("and the connection string (user, password, host, port, dbname) is correct.")
        print("For PostgreSQL, you might need to install 'psycopg2-binary': pip install psycopg2-binary")

if __name__ == '__main__':
    try:
        engine = initialize_database()
        print("Database initialized.")
        populate_example_data()

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure the database server is running, the database exists,")
        print("and the connection string (user, password, host, port, dbname) is correct.")
        print("For PostgreSQL, you might need to install 'psycopg2-binary': pip install psycopg2-binary")