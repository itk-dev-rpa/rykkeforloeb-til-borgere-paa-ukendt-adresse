"""This module contains configuration constants used across the framework"""


from datetime import datetime

from itk_dev_shared_components.kmd_nova.nova_objects import Caseworker

# The number of times the robot retries on an error before terminating.
MAX_RETRY_COUNT = 3

# Whether the robot should be marked as failed if MAX_RETRY_COUNT is reached.
FAIL_ROBOT_ON_TOO_MANY_ERRORS = True

# Error screenshot config
SMTP_SERVER = "smtp.adm.aarhuskommune.dk"
SMTP_PORT = 25
SCREENSHOT_SENDER = "robot@friend.dk"

# Constant/Credential names
ERROR_EMAIL = "Error Email"

KEYVAULT_CREDENTIALS = "Keyvault"
KEYVAULT_URI = "Keyvault URI"
KEYVAULT_PATH = "Digital_Post_Ukendt_Adresse"

# Constants
CVR = "55133018"
REMINDER_NOTE_CUTOFF = datetime(2026, 8, 1)  # Used to avoid wrong journal notes created earlier
LIBREOFFICE_TIMEOUT_SECONDS = 60
PATH_TO_LIBREOFFICE = "C:/Program Files/LibreOffice/program/soffice.exe"

FIRST_REMINDER_DELAY = 1  # TODO
FOLLOWING_REMINDER_DELAY = 0  # TODO
MAX_REMINDER_COUNT = 24
LETTER_DEADLINE_DAYS = 30

CASEWORKER = Caseworker(
    name='AZRPA78 - Rpabruger Rpa78 - MÅ IKKE SLETTES RITM0283472',
    ident='AZRPA78',
    uuid='a577c0a2-a131-43a5-b4e6-b4f5bb75028f',
    type='user'
)

NOTIFICATION_RECEIVER = "ghbm@aarhus.dk"  # TODO