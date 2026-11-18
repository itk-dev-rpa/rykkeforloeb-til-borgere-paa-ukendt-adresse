"""This module contains the main process of the robot."""

from datetime import date, datetime, timedelta

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from itk_dev_shared_components.kmd_nova.authentication import NovaAccess
from itk_dev_shared_components.kmd_nova.nova_objects import NovaCase
from itk_dev_shared_components.smtp import smtp_util
from python_serviceplatformen.authentication import KombitAccess

from robot_framework import config
from robot_framework.sub_process import database, kmd_nova, letters, serviceplatformen


# The framework retries the process on errors, which starts it over from the top.
# These are kept on module level so an attempt picks up where the previous one
# stopped, instead of working through hundreds of already handled citizens again.
_handled_citizens: set[str] = set()
_citizens_without_cases: set[str] = set()
_citizens_outside_flow: set[str] = set()


def process(orchestrator_connection: OrchestratorConnection) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")

    if skip_date():
        orchestrator_connection.log_info("Today is a holiday. Skipping process.")
        return

    creds = orchestrator_connection.get_credential("Nova API")
    nova_access = NovaAccess(client_id=creds.username, client_secret=creds.password)

    kombit_access = serviceplatformen.get_kombit_access(orchestrator_connection)

    citizens_with_unknown_address = database.get_citizens_with_unknown_address()

    if _handled_citizens:
        orchestrator_connection.log_info(f"Resuming. {len(_handled_citizens)} citizens already handled.")

    for citizen in citizens_with_unknown_address:
        if citizen.cpr in _handled_citizens:
            continue

        result = handle_citizen(citizen, nova_access, kombit_access)
        orchestrator_connection.log_info(f"Result: {result} - CPR: {citizen.cpr}")

        if result == "No KLE case found":
            _citizens_without_cases.add(citizen.cpr)
        elif result == "No workable case found":
            _citizens_outside_flow.add(citizen.cpr)

        _handled_citizens.add(citizen.cpr)

    if _citizens_without_cases or _citizens_outside_flow:
        send_no_cases_notification(_citizens_without_cases, _citizens_outside_flow)


def handle_citizen(citizen: database.Citizen, nova_access: NovaAccess, kombit_access: KombitAccess) -> str:
    """Handle the process of a single citizen.
    Find the relevant Nova case, send reminders, and journalize relevant information.
    """
    found_case, kle_case_found = kmd_nova.get_relevant_case(citizen.cpr, nova_access)

    if not kle_case_found:
        return "No KLE case found"

    if not found_case:
        return "No workable case found"

    latest_step, latest_date = kmd_nova.get_case_reminder_information(found_case.uuid, nova_access)

    if latest_step >= config.MAX_REMINDER_COUNT:
        send_limit_reached_notification(citizen.cpr)
        return "Limit reached"

    # The first reminder is timed from the creation of the case, the following ones from the latest reminder.
    if latest_step == 0:
        reminder_due = datetime.today() - found_case.case_date > timedelta(days=config.FIRST_REMINDER_DELAY)
    else:
        reminder_due = datetime.today() - latest_date > timedelta(days=config.FOLLOWING_REMINDER_DELAY)

    if reminder_due:
        send_reminder(citizen, found_case, latest_step + 1, nova_access, kombit_access)
        return "Case handled"

    return "Reminder not due yet"


def send_reminder(citizen: database.Citizen, case: NovaCase, reminder_number: int, nova_access: NovaAccess, kombit_access: KombitAccess) -> None:
    """Send the given reminder to the citizen as digital post and journalize it on the case.

    A NemSMS notification is sent as well, if the letter reached the citizen.
    """
    match reminder_number:
        case 1:
            template_number = 1
            letter_label = f"{citizen.first_name}, din adresse er ukendt."
        case 2:
            template_number = 2
            letter_label = f"{citizen.first_name}, din adresse er ikke gyldig!"
        case _:
            template_number = 3
            letter_label = f"{citizen.first_name}, din handling er påkrævet."

    deadline_date = datetime.now() + timedelta(days=config.LETTER_DEADLINE_DAYS)
    pdf_path = letters.fill_template(template_number, citizen.first_name, deadline_date, case.case_number, letter_label)
    letter_sent = serviceplatformen.send_reminder_letter(citizen.cpr, pdf_path, letter_label, kombit_access)

    kmd_nova.upload_document(case.uuid, pdf_path, nova_access)
    kmd_nova.add_letter_note(case.uuid, letter_sent, reminder_number, nova_access)

    if letter_sent:
        sms_sent = serviceplatformen.send_nemsms(citizen.cpr, kombit_access)
        if sms_sent:
            kmd_nova.add_sms_note(case.uuid, reminder_number, nova_access)


def send_no_cases_notification(cprs_without_cases: set[str], cprs_outside_flow: set[str]):
    """Send a notification about citizens on an unknown address who have no case at all."""

    body = "\n".join((
        "Hejsa\n",
        "Følgende borgere er på ukendt adresse, men har ingen aktiv sag i Nova med KLE 23.05.00:\n",
        "\n".join(cprs_without_cases),
        "\nFølgende borgere har en sag i Nova, men er ikke sat til automatisk rykkerforløb:\n",
        "\n".join(cprs_outside_flow),
        "\nVenlig hilsen",
        "Rykkerforløb-robotten",
    ))

    smtp_util.send_email(
        receiver=config.NOTIFICATION_RECEIVER,
        sender="itk-rpa@ba.aarhus.dk",
        subject="Borgere på ukendt adresse mangler sager i Nova",
        body=body,
        smtp_port=config.SMTP_PORT,
        smtp_server=config.SMTP_SERVER
    )


def send_limit_reached_notification(cpr: str):
    """Send a notification about a citizen on an unknown address who has
    received the maximum number of reminders.
    """

    body = "\n".join((
        "Hejsa\n",
        "Følgende borger er på ukendt adresse og har modtaget maks antal automatiske rykkere:",
        f"{cpr}",
        "\nVenlig hilsen",
        "Rykkerforløb-robotten",
    ))

    smtp_util.send_email(
        receiver=config.NOTIFICATION_RECEIVER,
        sender="itk-rpa@ba.aarhus.dk",
        subject="Borger på ukendt adresse har modtaget maks antal rykkere",
        body=body,
        smtp_port=config.SMTP_PORT,
        smtp_server=config.SMTP_SERVER
    )


def skip_date() -> bool:
    """Check if today's date is in the Christmas period (20/12 - 3/1) or a Danish holiday.

    Returns:
        True if the date should be skipped.
    """
    check_date = date.today()

    # Christmas period 20/12 - 3/1. This also covers Nytårsdag, Juledag and 2. juledag.
    if (check_date.month == 12 and check_date.day >= 20) or (check_date.month == 1 and check_date.day <= 3):
        return True

    easter = _easter_sunday(check_date.year)
    holidays = {
        easter - timedelta(days=3),  # Skærtorsdag
        easter - timedelta(days=2),  # Langfredag
        easter,  # Påskedag
        easter + timedelta(days=1),  # 2. påskedag
        easter + timedelta(days=39),  # Kristi himmelfartsdag
        easter + timedelta(days=49),  # Pinsedag
        easter + timedelta(days=50),  # 2. pinsedag
        date(check_date.year, 6, 5),  # Grundlovsdag
    }

    return check_date in holidays


def _easter_sunday(year: int) -> date:
    """Calculate the date of Easter Sunday using the anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)



if __name__ == '__main__':
    import os
    import uuid
    conn_string = os.getenv("OpenOrchestratorConnString")
    crypto_key = os.getenv("OpenOrchestratorKey")
    oc = OrchestratorConnection("Rykkerforløb test", conn_string, crypto_key, '', "trigger_id", uuid.uuid4())
    process(oc)
