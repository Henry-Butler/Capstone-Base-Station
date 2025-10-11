from patients_registry import Patient, PatientsRegistry

def main():
    # create some test patients
    P1 = Patient("John Smith", "Chest Pain", ["Hypertension", "Inflammation on left abdomen"])
    P2 = Patient("Maria Chamberton", "Excessive Blood Loss", ["Diabetes", "hemophilia"])
    P3 = Patient("Charlie", "Broken Leg", [])

    # create registry
    registry = PatientsRegistry()

    # add patients
    registry.add_patient(P1)
    registry.add_patient(P2)
    registry.add_patient(P3)

    # print same info
    print("=====Patient Directory=====")
    for pid, name in registry.list_patients():
        print(f"ID {pid}: {name}")

    print()
    print("Individual Patients")
    print(P1.summary())
    print(P2.summary())
    print(P3.summary())

    # test to access protected data
    print()
    print("Unauthorized personel:", P1.get_prex_conditions())
    print("Authorized:", P1.get_prex_conditions(authorized=True))

if __name__ == "__main__":
    main()