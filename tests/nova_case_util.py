"""This module helps creating new test cases in Nova since the UI doesn't allow it anymore."""

import os
from datetime import datetime
import time
import uuid

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from itk_dev_shared_components.kmd_nova.authentication import NovaAccess
from itk_dev_shared_components.kmd_nova.nova_objects import NovaCase, CaseParty, Caseworker, Department
from itk_dev_shared_components.kmd_nova import nova_cases


NOVA_PARTY = CaseParty(
    role="Primær",
    identification_type="CprNummer",
    identification="6101009805",
    name="Test Test"
)
NOVA_DEPARTMENT = Department(
    id=818485,
    name="Borgerservice",
    user_key="4BBORGER"
)
NOVA_USER = Caseworker(
    name="svcitkopeno svcitkopeno",
    ident="AZX0080",
    uuid="0bacdddd-5c61-4676-9a61-b01a18cec1d5"
)


def _get_case(case_uuid: str, nova_access: NovaAccess) -> NovaCase | None:
    """Get a case by the given uuid. Retry for up to 10 seconds until the case appears.

    Args:
        case_uuid: The uuid of the case to get.
        nova_access: The NovaAccess object used to authenticate.

    Returns:
        The case with the given uuid if it exists.
    """
    for _ in range(10):
        time.sleep(1)
        try:
            return nova_cases.get_case(case_uuid, nova_access)
        except ValueError:
            pass
    return None


def add_test_case(nova_access):
    """Add a new test case to Nova and print the case number."""
    case = NovaCase(
        uuid=str(uuid.uuid4()),
        title="Rykkerforløb ukendt adresse",
        case_date=datetime.now(),
        progress_state="Opstaaet",
        case_parties=[NOVA_PARTY],
        kle_number="23.05.00",
        proceeding_facet="G01",
        sensitivity="Fortrolige",
        caseworker=NOVA_USER,
        responsible_department=NOVA_DEPARTMENT,
        security_unit=NOVA_DEPARTMENT
    )

    nova_cases.add_case(case, nova_access)
    nova_case = _get_case(case.uuid, nova_access)
    print(nova_case.case_number)


if __name__ == '__main__':
    conn_string = os.getenv("OpenOrchestratorConnString")
    crypto_key = os.getenv("OpenOrchestratorKey")
    oc = OrchestratorConnection("Nova case util", conn_string, crypto_key, '', "trigger_id", uuid.uuid4())

    creds = oc.get_credential("Nova API")
    nc = NovaAccess(client_id=creds.username, client_secret=creds.password)

    add_test_case(nc)
