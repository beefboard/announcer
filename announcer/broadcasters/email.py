import aiosmtplib
from aiosmtplib.errors import (
    SMTPConnectError,
    SMTPAuthenticationError,
    SMTPRecipientsRefused,
    SMTPTimeoutError,
    SMTPResponseException,
)
from email.mime.text import MIMEText
from typing import List


class EmailBroadcasterError(Exception):
    pass


class BroadcasterTimeoutError(EmailBroadcasterError):
    pass


class ConnectError(EmailBroadcasterError):
    pass


class LoginError(EmailBroadcasterError):
    pass


class SendError(EmailBroadcasterError):
    pass


class BroadcastEmail:
    def __init__(self, recipients: List[str], subject: str, body: str):
        self.recipients = recipients
        self.subject = subject
        self.body = body

    def __eq__(self, other):
        return (
            self.recipients == other.recipients
            and self.subject == other.subject
            and self.body == other.body
        )


class EmailBroadcaster:
    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        self._client = aiosmtplib.SMTP(hostname=host, port=port)
        self._username = username
        self._password = password

    def _generate_message(self, recipient: str, subject: str, body: str) -> str:
        msg = MIMEText(body)
        msg["To"] = recipient
        msg["From"] = self._username
        msg["Subject"] = subject

        return msg.as_string()

    async def send(self, emails: List[BroadcastEmail]) -> None:
        try:
            await self._client.connect()
        except SMTPConnectError as e:
            raise ConnectError(e)
        except SMTPTimeoutError as e:
            raise BroadcasterTimeoutError(e)

        try:
            await self._client.login(self._username, self._password)
        except SMTPAuthenticationError as e:
            raise LoginError(e)
        except SMTPTimeoutError as e:
            raise BroadcasterTimeoutError(e)

        for email in emails:
            for recipient in email.recipients:
                try:
                    await self._client.sendmail(
                        self._username,
                        recipient,
                        self._generate_message(recipient, email.subject, email.body),
                    )
                except (SMTPRecipientsRefused, SMTPResponseException) as e:
                    raise SendError(e)
                except SMTPTimeoutError as e:
                    raise BroadcasterTimeoutError(e)

        try:
            await self._client.quit()
        except:
            pass
