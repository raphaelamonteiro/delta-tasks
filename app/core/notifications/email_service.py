from app.core.logger import get_logger
logger = get_logger("app.notifications.email")

class EmailService:
    """
    Serviço responsável apenas por enviar emails.
    Aqui depois entra o Resend.
    """

    def __init__(self, resend_client=None):
        self.resend_client = resend_client

    async def send_email(self, to: str, subject: str, content: str) -> None:
        await self.resend_client.emails.send({
            "from": "noreply@delta-tasks.com",
            "to": to,
            "subject": subject,
            "html": content,
        })