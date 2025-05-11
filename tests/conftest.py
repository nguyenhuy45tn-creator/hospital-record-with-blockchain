import pytest
from script.deploy import deploy
from script.rights import READ_PATIENT_BASIC_DATA, WRITE_PATIENT_BASIC_DATA, READ_PATIENT_HEALTHCARE_RECORD_DATA, WRITE_PATIENT_HEALTHCARE_RECORD_DATA
from script.roles import PATIENT, DOCTOR