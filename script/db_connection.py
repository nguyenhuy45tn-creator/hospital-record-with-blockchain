import uuid
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    LargeBinary,
    select
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base, Session
from sqlalchemy.sql import func 
from sqlalchemy_continuum import make_versioned
from bcrypt import hashpw, checkpw, gensalt

# Define the base class for declarative models
Base = declarative_base()

class Role(Base):
    __tablename__ = 'roles'

    role_name = Column(String(50), primary_key=True)
    description = Column(Text)

    users = relationship("User", back_populates="role") # A role can have multiple users

    def __repr__(self):
        return f"<Role(role_name='{self.role_name}')>"
    
class Login(Base):
    __tablename__ = 'logins'

    user_name = Column(String(100), primary_key=True, index=True)
    # Use LargeBinary to store byte output from bcrypt
    hashed_password = Column(LargeBinary, nullable=False)
    salt = Column(LargeBinary, nullable=False)

    user = relationship("User", back_populates="login_details", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Login(user_name='{self.user_name}')>"

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
    user_role_name = Column(String(50), ForeignKey('roles.role_name'))

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
        return f"<User(user_name='{self.user_name}', system_id='{self.system_wide_identifier}', version={getattr(self, 'sa_version', None)})>"

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
        return f"<HealthcareRecord(record_id={self.record_id}, patient_user_id={self.patient_user_id}, version={getattr(self, 'sa_version', None)})>"

def initialize_database():
    """
    Initializes the database connection and creates tables if they don't exist.
    Only call once at start.

    This function defines the database connection URL, creates the SQLAlchemy
    engine, and then creates all tables defined in the Base metadata.

    Returns:
        sqlalchemy.engine.Engine: The created SQLAlchemy engine instance.
    """
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/sampledb"
    make_versioned(user_cls=None) 
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)

    return engine

def get_single_user(engine, user_system_wide_identifier:uuid.UUID):
    """
    Only call after access control is performed
    
    Retrieves a single user from the database based on their system-wide identifier.

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine instance to use for the session.
        user_system_wide_identifier (uuid.UUID): The unique UUID identifier of the user to retrieve.

    Returns:
        User: The User object corresponding to the provided identifier.

    Raises:
        sqlalchemy.orm.exc.NoResultFound: If no user with the given identifier is found.
        sqlalchemy.orm.exc.MultipleResultsFound: If multiple users somehow have the same identifier (shouldn't happen due to unique constraint).
    """
    with Session(engine) as session:
        query =  select(User).where(User.system_wide_identifier == user_system_wide_identifier)
        output = session.execute(query).scalar_one()

    return output

def get_all_users(engine):
    """
    Retrieves all users from the database.

    Only call after access control is performed

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine instance to use for the session.

    Returns:
        list[User]: A list containing all User objects in the database.
    """
    with Session(engine) as session:
        query =  select(User)
        output = session.execute(query).scalars().all()
    return output

def get_health_records(engine, user_system_wide_identifier:uuid.UUID):
    """
    Retrieves the healthcare records associated with a specific user.

    Only call after access control is performed

    First finds the user by their system-wide identifier, then finds the
    healthcare records linked to that user's primary key ID. A user can
    have multiple healthcare records.

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine instance to use for the session.
        user_system_wide_identifier (uuid.UUID): The unique UUID identifier of the user whose record is needed.

    Returns:
        list[HealthcareRecord]: A list of HealthcareRecord objects associated with the user.
                                Returns an empty list if the user is not found or has no records.
    """
    with Session(engine) as session:
        query = select(User).where(User.system_wide_identifier == user_system_wide_identifier)
        user = session.execute(query).scalar_one_or_none() # Use scalar_one_or_none to handle user not found
        if user:
            query = select(HealthcareRecord).where(HealthcareRecord.patient_user_id == user.user_id)
            records = session.execute(query).scalars().all()
            return records
        return [] # Return an empty list if user not found

def add_user(engine, username: str, password_plain: str, full_name: str, address: str, hospital_designation: str):
    """
    Adds a new user and their login credentials to the database.

    Only call after access control is performed

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine instance to use for the session.
        username (str): The desired username (must be unique for logins).
        password_plain (str): The user's plain text password
        full_name (str): The user's full name.
        address (str): The user's address.
        hospital_designation (str): The user's hospital designation.

    Raises:
        ValueError: If the username already exists.
    """
    with Session(engine) as session:
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
            hospital_designation=hospital_designation
        )

        # Associate the User with the Login entry via the relationship
        # This will also ensure User.user_name is set to new_login_entry.user_name
        new_user.login_details = new_login_entry

        # Add the new_user to the session.
        # SQLAlchemy will also add new_login_entry due to the relationship and FK.
        session.add(new_user)
        session.commit()
        

def add_health_record(engine, user_id:int, record_data:dict, creator_user_id:int):
    """
    Adds a new healthcare record for a specific user.

    Only call after access control is performed

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine instance to use for the session.
        user_id (int): The primary key ID of the user (patient) this record belongs to.
        record_data (dict): A dictionary containing the healthcare data to be stored (will be saved as JSONB).
        creator_user_id (int): The primary key ID of the user who created this record.
    """
    with Session(engine) as session:
        new_record = HealthcareRecord(patient_user_id=user_id, record_data=record_data, last_updated_by_user_id=creator_user_id)
        session.add(new_record)
        session.commit()
        return

def update_health_record(engine, user_id:int, record_id:int, record_data:dict):
    """
    Updates an existing healthcare record.

    Only call after access control is performed

    Finds the record by its primary key ID and updates its data,
    the last updated timestamp, and the ID of the user performing the update.

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine instance to use for the session.
        user_id (int): The primary key ID of the user performing the update.
        record_id (int): The primary key ID of the healthcare record to update.
        record_data (dict): The new dictionary data for the record.
    """
    with Session(engine) as session:
        query = select(HealthcareRecord).where(HealthcareRecord.record_id == record_id)
        record = session.execute(query).scalar_one()
        if record:
            record.record_data = record_data
            record.last_updated_at = datetime.now()
            record.last_updated_by_user_id = user_id
            session.commit()
            return
        return

def populate_example_data(engine):
    """
    Populates the database with example roles, permissions, users, and records
    if they don't already exist. This function is idempotent.

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine instance.
    """
    with Session(engine) as session:
        # --- 1. Define and Create Roles ---
        roles_data = {
            "Patient": "A patient user, can read own records.",
            "Doctor": "A medical doctor, can read/edit patient records.",
            "Nurse": "A nurse, can read/edit patient records.",
            "Admin": "An administrator, can manage users and roles."
        }
        roles = {}
        for name, desc in roles_data.items():
            role = session.query(Role).filter_by(role_name=name).first()
            if not role:
                role = Role(role_name=name, description=desc)
                session.add(role)
            roles[name] = role

        # --- 2. Define and Create Permissions ---
        permissions_data = {
            "read_own_record": "Allows reading own health records.",
            "read_patient_record": "Allows reading any patient's health records.",
            "edit_patient_record": "Allows editing any patient's health records.",
            "manage_users": "Allows creating, updating, and deleting users.",
            "manage_roles": "Allows managing roles and permissions."
        }
        permissions = {}
        for name, desc in permissions_data.items():
            perm = session.query(Permission).filter_by(permission_name=name).first()
            if not perm:
                perm = Permission(permission_name=name, description=desc)
                session.add(perm)
            permissions[name] = perm

        # Commit roles and permissions before assigning them
        session.commit()
        # Refresh roles/permissions objects to ensure they have IDs after commit
        for name in roles: roles[name] = session.merge(roles[name])
        for name in permissions: permissions[name] = session.merge(permissions[name])


        # --- 3. Assign Permissions to Roles (Idempotent) ---
        role_permission_map = {
            "Patient": ["read_own_record"],
            "Doctor": ["read_patient_record", "edit_patient_record"],
            "Nurse": ["read_patient_record", "edit_patient_record"],
            "Admin": ["manage_users", "manage_roles", "read_patient_record"] # Admins might need to read records too
        }

        for role_name, perm_names in role_permission_map.items():
            role = roles[role_name]
            current_perm_names = {p.permission_name for p in role.permissions}
            for perm_name in perm_names:
                if perm_name not in current_perm_names:
                    role.permissions.append(permissions[perm_name])

        # --- 4. Create Example Users (Idempotent) ---
        # NOTE: Using plain text passwords here, which will be hashed and salted below.
        users_data = [
            {"username": "patient_alice", "password": "password123", "full_name": "Alice Wonderland", "address": "123 Rabbit Hole", "hospital_designation": "Patient", "role": "Patient"},
            {"username": "doctor_bob", "password": "password123", "full_name": "Dr. Bob Smith", "address": "456 Health St", "hospital_designation": "General Practitioner", "role": "Doctor"},
            {"username": "nurse_carol", "password": "password123", "full_name": "Carol Danvers", "address": "789 Care Ave", "hospital_designation": "Registered Nurse", "role": "Nurse"},
            {"username": "admin_dave", "password": "password123", "full_name": "Dave Administrator", "address": "1 Admin Plaza", "hospital_designation": "System Admin", "role": "Admin"},
        ]

        created_users = {}
        for user_data in users_data:
            user = session.query(User).filter_by(username=user_data["username"]).first()
            if not user:
                salt = gensalt()
                hashed_pw = hashpw(user_data["password"].encode('utf-8'), salt) # Encode password to bytes
                user = User(
                    username=user_data["username"],
                    salt=salt, # Store the generated salt
                    hashed_password=hashed_pw, # Store the hashed password
                    full_name=user_data["full_name"],
                    address=user_data["address"],
                    hospital_designation=user_data["hospital_designation"]
                )
                user.role = roles[user_data["role"]] # Assign single role object
                session.add(user)
            created_users[user_data["username"]] = user

        # Commit users to get their IDs
        session.commit()
        # Refresh user objects
        for username in created_users: created_users[username] = session.merge(created_users[username])

        # --- 5. Create Example Health Record for Patient (Idempotent) ---
        patient_user = created_users["patient_alice"]
        doctor_user = created_users["doctor_bob"]
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


if __name__ == '__main__':
    try:
        engine = initialize_database()
        print("Database initialized.")
        populate_example_data(engine) # Call the population function

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure the database server is running, the database exists,")
        print("and the connection string (user, password, host, port, dbname) is correct.")
        print("For PostgreSQL, you might need to install 'psycopg2-binary': pip install psycopg2-binary")