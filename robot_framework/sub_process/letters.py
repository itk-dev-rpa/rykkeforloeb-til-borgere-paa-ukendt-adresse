"""This module handles merging and converting letter templates."""

from datetime import datetime
from pathlib import Path
import re
import subprocess
import uuid

from docxtpl import DocxTemplate

from robot_framework import config


def fill_template(template_number: int, first_name: str, deadline: datetime, case_number: str, letter_label: str) -> Path:
    """Fill a template with the given context and convert it to PDF.

    Args:
        template_number: The number of the template to use. 1-3.
        first_name: The first name of the receiver.
        deadline: The response deadline. Only used for template 2.
        case_number: The relevant Nova case number.
        letter_label: The label of the letter. Used as the file name.

    Returns:
        The path to the generated PDF.
    """

    template_path = Path("templates") / f"Rykker {template_number} - Ukendt adresse.docx"
    tmp_dir = config.TMP_DIR / Path(str(uuid.uuid4()))
    docx_path = tmp_dir / f"{_to_file_name(letter_label)}.docx"
    pdf_path = docx_path.with_suffix(".pdf")

    # Merge docx template
    context = {
        "Fornavn": first_name,
        "dato": deadline.strftime(format="%d/%m/%Y"),
        "Sagsnummer": case_number
    }

    tmp_dir.mkdir(parents=True)
    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(filename=docx_path)

    # Convert to pdf
    subprocess.run(
        args=[config.PATH_TO_LIBREOFFICE, "--headless", "--convert-to", "pdf", "--outdir", str(tmp_dir), str(docx_path)],
        check=True,
        timeout=config.LIBREOFFICE_TIMEOUT_SECONDS,
    )

    return pdf_path


def _to_file_name(letter_label: str) -> str:
    """Turn a letter label into a file name Windows accepts.

    Removes the characters that aren't allowed in file names and trims
    trailing dots and spaces, which Windows strips silently.
    """
    file_name = re.sub(r'[<>:"/\\|?*]', "", letter_label)
    return file_name.rstrip(". ")


def kill_libreoffice() -> None:
    """Forcefully terminate any lingering LibreOffice process."""
    subprocess.run(args=["taskkill", "/F", "/T", "/IM", "soffice.exe"], check=False)
