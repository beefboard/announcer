import asynctest
import aiosmtplib
from aiosmtplib.errors import (
    SMTPResponseException,
    SMTPConnectError,
    SMTPAuthenticationError,
    SMTPRecipientsRefused,
    SMTPTimeoutError,
)
from email.mime.text import MIMEText
from unittest.mock import patch, MagicMock, create_autospec, call
from announcer.broadcasters.email import (
    EmailBroadcaster,
    EmailBroadcasterError,
    LoginError,
    ConnectError,
    BroadcastEmail,
    SendError,
    BroadcasterTimeoutError,
)
import asyncio


class TestEmailBroadcaster(asynctest.TestCase):
    TEST_EMAIL = "test@email.com"

    def setup_smtp_mocks(self):
        self._mock_smtp.quit.reset_mock()
        self._mock_smtp.connect.reset_mock()
        self._mock_smtp.login.reset_mock()
        self._mock_smtp.sendmail.reset_mock()

        mock_future: asyncio.Future = asyncio.Future()
        mock_future.set_result(None)

        self._mock_smtp.connect.return_value = mock_future
        self._mock_smtp.login.return_value = mock_future
        self._mock_smtp.sendmail.return_value = mock_future
        self._mock_smtp.quit.return_value = mock_future

    def setUp(self):
        self._client = EmailBroadcaster(
            "localhost", 25, TestEmailBroadcaster.TEST_EMAIL, "test"
        )
        # Override the smtp client with a mock version which we can test
        self._mock_smtp = create_autospec(aiosmtplib.SMTP)
        self._client._client = self._mock_smtp

    @patch("aiosmtplib.SMTP")
    def test_init(self, MockSMTP: MagicMock) -> None:
        """
        Test that email broadcaster initialises the smtp library
        correctly
        """
        client = EmailBroadcaster("localhost", 25, "test", "testpass")

        MockSMTP.assert_called_with(hostname="localhost", port=25)
        self.assertIs(client._username, "test")
        self.assertIs(client._password, "testpass")

    def generate_message(self, recipient: str, subject, body) -> str:
        msg = MIMEText(body)
        msg["To"] = recipient
        msg["From"] = TestEmailBroadcaster.TEST_EMAIL
        msg["Subject"] = subject

        return msg.as_string()

    async def test_send(self) -> None:
        recipients = ["test@test.com", "test2@gmail.com"]
        subject = "A subject"
        body = "A body"

        email = BroadcastEmail(recipients, subject, body)

        self.setup_smtp_mocks()

        await self._client.send([email])

        self._mock_smtp.connect.assert_called()
        self._mock_smtp.login.assert_called_with(
            self._client._username, self._client._password
        )
        expected_send_calls = []
        for recipient in recipients:
            expected_send_calls.append(
                call(
                    TestEmailBroadcaster.TEST_EMAIL,
                    recipient,
                    self.generate_message(recipient, subject, body),
                )
            )

        self._mock_smtp.sendmail.assert_has_calls(expected_send_calls)
        self._mock_smtp.quit.assert_called()

    async def test_send_login_failure(self) -> None:
        recipients = ["test@test.com", "test2@gmail.com"]
        subject = "A subject"
        body = "A body"

        email = BroadcastEmail(recipients, subject, body)

        self.setup_smtp_mocks()

        mock_future: asyncio.Future = asyncio.Future()
        mock_future.set_exception(SMTPAuthenticationError(0, "Bad error"))
        self._mock_smtp.login.return_value = mock_future

        error = None
        try:
            await self._client.send([email])
        except EmailBroadcasterError as e:
            error = e

        self.assertIs(type(error), LoginError)

        mock_future2: asyncio.Future = asyncio.Future()
        mock_future2.set_exception(SMTPTimeoutError("Timeout"))
        self._mock_smtp.login.return_value = mock_future2

        error2 = None
        try:
            await self._client.send([email])
        except EmailBroadcasterError as e:
            error2 = e

        self.assertIs(type(error2), BroadcasterTimeoutError)

    async def test_send_sendmail_failure(self) -> None:
        recipients = ["test@test.com", "test2@gmail.com"]
        subject = "A subject"
        body = "A body"

        email = BroadcastEmail(recipients, subject, body)

        self.setup_smtp_mocks()

        mock_future: asyncio.Future = asyncio.Future()
        mock_future.set_exception(SMTPResponseException(0, "An error"))
        self._mock_smtp.sendmail.return_value = mock_future

        error = None
        try:
            await self._client.send([email])
        except EmailBroadcasterError as e:
            error = e

        self.assertIs(type(error), SendError)

        mock_future2: asyncio.Future = asyncio.Future()
        mock_future2.set_exception(SMTPTimeoutError("Timeout"))
        self._mock_smtp.sendmail.return_value = mock_future2

        error2 = None
        try:
            await self._client.send([email])
        except EmailBroadcasterError as e:
            error2 = e

        self.assertIs(type(error2), BroadcasterTimeoutError)

        mock_future3: asyncio.Future = asyncio.Future()
        mock_future3.set_exception(SMTPRecipientsRefused("test@gmail.com"))
        self._mock_smtp.sendmail.return_value = mock_future3

        error3 = None
        try:
            await self._client.send([email])
        except EmailBroadcasterError as e:
            error3 = e

        self.assertIs(type(error3), SendError)

    async def test_send_connect_failure(self) -> None:
        recipients = ["test@test.com", "test2@gmail.com"]
        subject = "A subject"
        body = "A body"

        email = BroadcastEmail(recipients, subject, body)

        self.setup_smtp_mocks()

        mock_future: asyncio.Future = asyncio.Future()
        mock_future.set_exception(SMTPConnectError("An error"))
        self._mock_smtp.connect.return_value = mock_future

        error = None
        try:
            await self._client.send([email])
        except EmailBroadcasterError as e:
            error = e

        self.assertIs(type(error), ConnectError)

        mock_future2: asyncio.Future = asyncio.Future()
        mock_future2.set_exception(SMTPTimeoutError("Timeout"))
        self._mock_smtp.connect.return_value = mock_future2

        error2 = None
        try:
            await self._client.send([email])
        except EmailBroadcasterError as e:
            error2 = e

        self.assertIs(type(error2), BroadcasterTimeoutError)

    async def test_quit_failure(self) -> None:
        recipients = ["test@test.com", "test2@gmail.com"]
        subject = "A subject"
        body = "A body"

        email = BroadcastEmail(recipients, subject, body)

        self.setup_smtp_mocks()

        mock_future: asyncio.Future = asyncio.Future()
        mock_future.set_exception(SMTPResponseException(0, "An error"))
        self._mock_smtp.quit.return_value = mock_future

        await self._client.send([email])
        self._mock_smtp.quit.assert_called()

        mock_future2: asyncio.Future = asyncio.Future()
        mock_future2.set_exception(SMTPTimeoutError("Timeout"))
        self._mock_smtp.quit.return_value = mock_future2

        await self._client.send([email])
        self._mock_smtp.quit.assert_called()
