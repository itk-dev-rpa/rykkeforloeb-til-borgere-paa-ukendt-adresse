import base64
from pathlib import Path

from hvac import Client
from python_serviceplatformen.authentication import KombitAccess
from python_serviceplatformen import digital_post
from python_serviceplatformen.models import message
from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework import config


def get_kombit_access(orchestrator_connection: OrchestratorConnection):
    """Get Kombit access credentials."""
    # Access Keyvault
    certificate_path = "certificate.pem"
    vault_auth = orchestrator_connection.get_credential(config.KEYVAULT_CREDENTIALS)
    vault_uri = orchestrator_connection.get_constant(config.KEYVAULT_URI).value
    vault_client = Client(vault_uri)
    token = vault_client.auth.approle.login(role_id=vault_auth.username, secret_id=vault_auth.password)
    vault_client.token = token['auth']['client_token']

    # Get certificate
    read_response = vault_client.secrets.kv.v2.read_secret_version(mount_point='rpa', path=config.KEYVAULT_PATH, raise_on_deleted_version=True)
    certificate = read_response['data']['data']['cert']

    with open(certificate_path, 'w', encoding='utf-8') as cert_file:
        cert_file.write(certificate)

    # Prepare access to the service platform
    return KombitAccess(config.CVR, certificate_path)


def send_reminder_letter(recipient_cpr: str, letter_path: Path, letter_label: str, kombit_access: KombitAccess) -> bool:
    if not digital_post.is_registered(recipient_cpr, "digitalpost", kombit_access):
        return False

    sender = message.Sender(
        senderID=config.CVR,
        idType="CVR",
        label="Aarhus Kommune"
    )

    recipient = message.Recipient(
        recipientID=recipient_cpr,
        idType="CPR"
    )

    file_content = base64.b64encode(letter_path.read_bytes()).decode("utf-8")
    file = message.File(encodingFormat="application/pdf", filename=str(letter_path.name), language="da", content=file_content)

    msg = message.create_digital_post_with_main_document(
        label=letter_label,
        recipient=recipient,
        sender=sender,
        files=[file]
    )

    digital_post.send_message("Digital Post", msg, kombit_access)

    return True


def send_nemsms(recipient_cpr: str, kombit_access: KombitAccess) -> bool:
    if not digital_post.is_registered(recipient_cpr, "nemsms", kombit_access):
        return False

    recipient = message.Recipient(
        recipientID=recipient_cpr, idType="CPR"
    )
    sender = message.Sender(
        senderID=config.CVR, idType="CVR", label="Aarhus Kommune"
    )

    for language in ("da", "en"):
        sms_path = Path("templates") / f"sms_text_{language}.txt"
        sms_text = sms_path.read_text(encoding="utf8")

        msg = message.create_nemsms("NemSMS", sms_text, sender, recipient)
        digital_post.send_message("NemSMS", msg, kombit_access)

    return True