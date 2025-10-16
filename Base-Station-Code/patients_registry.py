import uuid
from typing import List, Any


class Patient:
    """
    Represents a single patient in the triage system.
    """
    def __init__(self, name : str, background: str, prex_conditions: List[str]):
        self.name = name
        self.background = background
        self._prex_conditions = prex_conditions # protected data
        self.ID = 0


    def summary(self) -> str:
        """
        Return a summary of the patient's information without being exposed publicly.
        :return:
        """
        return (f"Patient ID: {self.ID}\n"
                f"Name: {self.name}\n"
                f"Reason for visit: {self.background}"
        )

    def get_prex_conditions(self, authorized = False) -> list[str] | str:
        """
        Return a patients preexisting conditions only if authorized.

        :param authorized: Checker to ensure patients past is protected
        :return: List or string
        """
        if authorized:
            return self._prex_conditions
        return "Access Denied: Protected Information"


class PatientsRegistry:
    """
    This class contains information about multiple patients.
    """
    def __init__(self):
        self.patients = {}
        self._next_patient_id = 1 # start IDs at 1

    def add_patient(self, patient: Patient):
        """
        Adds a patient to the registry.
        :param patient: Individual to add
        :return:
        """
        patient.ID = self._next_patient_id
        self.patients[patient.ID] = patient
        self._next_patient_id += 1

    def get_patients(self, patient_id: int) -> Patient | None:
        """
        Returns a list of patients.
        :return:
        """
        return self.patients.get(patient_id)

    def list_patients(self) -> list[tuple[Any, Any]]:
        """
        Returns a list of patient IDs and names for display.
        :return:
        """
        return [(p.ID, p.name) for p in self.patients.values()]
