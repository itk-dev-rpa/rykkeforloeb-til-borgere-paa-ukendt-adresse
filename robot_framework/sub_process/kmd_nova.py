"""This module handles interactions with KMD Nova."""

from datetime import datetime
from pathlib import Path
import re

from itk_dev_shared_components.kmd_nova.authentication import NovaAccess
from itk_dev_shared_components.kmd_nova import nova_cases, nova_notes, nova_documents
from itk_dev_shared_components.kmd_nova.nova_objects import NovaCase, Document

from robot_framework import config


def get_relevant_case(cpr: str, nova_access: NovaAccess) -> tuple[NovaCase, bool]:
    """Find the relevant case for the given cpr-number.

    Returns:
        The case to work on if any, and whether any case exists at all.
    """
    cases = nova_cases.get_cases(nova_access, cpr)

    kle_case_found = False
    found_case = None

    for case in cases:
        if case.kle_number == "23.05.00" and case.active_code == 'Active':
            kle_case_found = True
            if case.caseworker.ident == config.CASEWORKER.ident:
                found_case = case
                break

    return found_case, kle_case_found


def get_case_status(case_uuid: str, nova_access: NovaAccess) -> tuple[int, datetime | None]:
    """Get information about the latest reminder sent for a case.

    Parses journal notes to find the most recent reminder note created by the robot.
    Looks for notes with titles matching "Rykker X sendt". Notes dated before
    config.REMINDER_NOTE_CUTOFF are ignored (pre-go-live test/legacy notes).

    Args:
        case_uuid: The uuid of the case to check.
        nova_access: The NovaAccess object used to authenticate.

    Returns:
        A tuple of (step_number, last_reminder_date) where:
        - step_number is 0 if no reminders have been sent, otherwise the number from the latest reminder
        - last_reminder_date is None if no reminders sent
    """
    notes = nova_notes.get_notes(case_uuid, nova_access)

    latest_step = 0
    latest_date = None

    for note in notes:
        # Match both "Sendt: Rykker X" and "Ikke sendt: Rykker X"
        match = re.match(r"^(?:Ikke sendt:|Sendt:) Rykker (\d+)$", note.title)
        if not match:
            continue

        # Ignore reminder notes wrongly created before go-live.
        note_date = datetime.fromisoformat(note.journal_date)
        if note_date < config.REMINDER_NOTE_CUTOFF:
            continue

        # Find the largest step number
        step = int(match.group(1))
        if step > latest_step:
            latest_step = step
            latest_date = note_date

    return (latest_step, latest_date)


def upload_document(case_uuid: str, document_path: Path, nova_access: NovaAccess):
    """Upload a letter document to the Nova case.

    Args:
        case_uuid: UUID of the Nova case.
        document_path: The path to the document.
        nova_access: NovaAccess object used for auth.
    """
    with document_path.open("rb") as file:
        document_id = nova_documents.upload_document(file, document_path.name, nova_access)

    nova_doc = Document(
        uuid=document_id,
        title=document_path.name,
        sensitivity="Følsomme",
        document_type="Udgående",
        description="Rykker sendt til borger omkring ukendt adresse.",
        approved=True,
        caseworker=config.CASEWORKER
    )
    nova_documents.attach_document_to_case(case_uuid, nova_doc, nova_access)


def add_letter_note(case_uuid: str, sent: bool, reminder_number: int, nova_access: NovaAccess):
    """Add a note to the Nova case about the sending of a letter.

    Args:
        case_uuid: The uuid of the Nova case.
        sent: Whether the letter was actually sent or not.
        reminder_number: The count of the current reminder letter.
        nova_access:  NovaAccess object used for auth.
    """

    if sent:
        note_title = f"Sendt: Rykker {reminder_number}"
        note_text = f"Rykker {reminder_number} er blevet sendt til borgeren vedrørende ukendt adresse."
    else:
        note_title = f"Ikke sendt: Rykker {reminder_number}"
        note_text = (
            f"Rykker {reminder_number} blev IKKE sendt via digital post, da borgeren ikke er tilmeldt. "
            "Brevet er uploadet til sagen. Manuel opfølgning påkrævet."
        )

    nova_notes.add_text_note(case_uuid, note_title, note_text, config.CASEWORKER, approved=True, nova_access=nova_access)


def add_sms_note(case_uuid, reminder_number: int, nova_access: NovaAccess):
    """Add a note about a NemSMS being sent.

    Args:
        case_uuid: The uuid of the Nova case.
        reminder_number: The count of the current reminder letter.
        nova_access:  NovaAccess object used for auth.
    """
    nova_notes.add_text_note(
        case_uuid=case_uuid,
        note_title=f"NemSMS Sendt: Rykker {reminder_number}",
        note_text=f"NemSMS er blevet sendt til borgeren vedrørende rykkerbrev {reminder_number}",
        caseworker=config.CASEWORKER,
        approved=True,
        nova_access=nova_access
    )
