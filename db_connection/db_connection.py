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
    Table,
    UniqueConstraint,
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

# --- Association Tables for Many-to-Many relationships ---

# Association table for Roles <-> Permissions
role_permissions_table = Table('role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.role_id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.permission_id', ondelete='CASCADE'), primary_key=True)
)

# Association table for Users <-> Roles
user_roles_table = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.role_id', ondelete='CASCADE'), primary_key=True)
)

class Role(Base):
    __tablename__ = 'roles'

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    permissions = relationship("Permission", secondary=role_permissions_table, back_populates="roles")
    users = relationship("User", secondary=user_roles_table, back_populates="roles")

    def __repr__(self):
        return f"<Role(role_name='{self.role_name}')>"

class Permission(Base):
    __tablename__ = 'permissions'

    permission_id = Column(Integer, primary_key=True)
    permission_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    roles = relationship("Role", secondary=role_permissions_table, back_populates="permissions")

    def __repr__(self):
        return f"<Permission(permission_name='{self.permission_name}')>"

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    # Use client-side default for UUID, ensure postgres pgcrypto extension is enabled if using server default
    system_wide_identifier = Column(PG_UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    # Use LargeBinary to store byte output from bcrypt
    salt = Column(LargeBinary, nullable=False, default=gensalt())
    hashed_password = Column(LargeBinary, nullable=False)
    full_name = Column(String(255), nullable=False)
    address = Column(Text)
    hospital_designation = Column(String(100))
    # Use timezone=True for TIMESTAMPTZ, server_default for database-level default
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationship to Roles (many-to-many)
    roles = relationship("Role", secondary=user_roles_table, back_populates="users")
    # Relationship to HealthcareRecord (one-to-one, patient perspective)
    healthcare_record = relationship("HealthcareRecord", back_populates="patient", uselist=False, foreign_keys='HealthcareRecord.patient_user_id', cascade="all, delete-orphan")
    # Relationships for tracking updates (one-to-many)
    updated_records = relationship("HealthcareRecord", back_populates="last_updated_by", foreign_keys='HealthcareRecord.last_updated_by_user_id')


    def __repr__(self):
        return f"<User(username='{self.username}', system_id='{self.system_wide_identifier}')>"

class HealthcareRecord(Base):
    __versioned__ = {}
    __tablename__ = 'healthcare_records'

    record_id = Column(Integer, primary_key=True)
    patient_user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    record_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_updated_by_user_id = Column(Integer, ForeignKey('users.user_id'))

    # Relationship back to the User (patient)
    patient = relationship("User", back_populates="healthcare_record", foreign_keys=[patient_user_id])
    # Relationship back to the User who last updated
    last_updated_by = relationship("User", back_populates="updated_records", foreign_keys=[last_updated_by_user_id])
    

    # Unique constraint to ensure one current record per patient
    __table_args__ = (UniqueConstraint('patient_user_id', name='uq_patient_current_record'),)


    def __repr__(self):
        return f"<HealthcareRecord(record_id={self.record_id}, patient_user_id={self.patient_user_id}, version={self.current_version})>"



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

def get_health_records(user_system_wide_identifier:uuid.UUID):
    """
    Retrieves the healthcare record associated with a specific user.

    Only call after access control is performed

    First finds the user by their system-wide identifier, then finds the
    healthcare record linked to that user's primary key ID.

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine instance to use for the session.
        user_system_wide_identifier (uuid.UUID): The unique UUID identifier of the user whose record is needed.

    Returns:
        HealthcareRecord | None: The HealthcareRecord object if found, otherwise None.
    """
    with Session(engine) as session:
        query = select(User).where(User.system_wide_identifier == user_system_wide_identifier)
        user = session.execute(query).scalar_one()
        if user:
            query = select(HealthcareRecord).where(HealthcareRecord.patient_user_id == user.user_id)
            record = session.execute(query).scalar()
            return record
        return None            

def add_user(engine, username:str, password:str, full_name:str, address:str, hospital_designation:str):
    """
    Adds a new user to the database.

    Only call after access control is performed

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine instance to use for the session.
        username (str): The desired username (must be unique).
        password (str): The hashed password for the user.
        full_name (str): The user's full name.
        address (str): The user's address.
        hospital_designation (str): The user's hospital designation.
    """
    with Session(engine) as session:
        new_user = User(username=username, 
                        hashed_password=password, 
                        full_name=full_name, 
                        address=address, 
                        hospital_designation=hospital_designation)
        session.add(new_user)
        session.commit()
        return
        

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
                user.roles.append(roles[user_data["role"]])
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