import asyncio
import datetime
import random
import string
from typing import Any
from unittest.mock import MagicMock, Mock, call, patch

import asynctest

from announcer.api.accounts import AccountsApi, AccountsApiError, User
from announcer.api.posts import Post, PostsApi, PostsApiError
from announcer.broadcasters.email import (
    BroadcastEmail,
    EmailBroadcaster,
    EmailBroadcasterError,
    SendError,
)
from announcer.service import AnnouncerService


def async_return(result: Any) -> asyncio.Future:
    f: asyncio.Future = asyncio.Future()
    f.set_result(result)
    return f


def async_exception(exception: Exception) -> asyncio.Future:
    f: asyncio.Future = asyncio.Future()
    f.set_exception(exception)
    return f


POSTS_BASE_URL = "https://test.com/posts/"


class TestAnnouncerService(asynctest.TestCase):
    MOCK_POSTS_LIST = [
        Post(
            id="".join([random.choice(string.ascii_lowercase) for i in range(20)]),
            date=datetime.datetime.now(),
            title="test",
            author="me",
            content="test",
            approved=False,
            approval_requested=True,
            num_images=0,
            notified=False,
            pinned=False,
        ),
        Post(
            id="".join([random.choice(string.ascii_lowercase) for i in range(20)]),
            date=datetime.datetime.now(),
            title="test",
            author="me",
            content="test",
            approved=False,
            approval_requested=False,
            num_images=0,
            notified=False,
            pinned=False,
        ),
        Post(
            id="".join([random.choice(string.ascii_lowercase) for i in range(20)]),
            date=datetime.datetime.now(),
            title="test",
            author="me2",
            content="test",
            approved=False,
            approval_requested=False,
            num_images=0,
            notified=False,
            pinned=False,
        ),
    ]

    MOCK_USERS_LIST = [
        User(
            username="".join([random.choice(string.ascii_lowercase) for i in range(5)]),
            email="test@test.com",
            admin=True,
            firstName="test",
            lastName="test",
        ),
        User(
            username="".join([random.choice(string.ascii_lowercase) for i in range(5)]),
            email="test2@test.com",
            admin=True,
            firstName="test",
            lastName="test",
        ),
    ]

    def generate_service(self) -> Any:
        posts_addr = "http://localhost:3929"
        accounts_addr = "http://localhost:3923"
        email_username = "test@test.com"
        email_password = "test"
        email_host = "smtp.gmail.com"
        email_port = 23

        service: Any = AnnouncerService(
            posts_addr,
            accounts_addr,
            email_username,
            email_password,
            email_host,
            email_port,
        )

        service._posts_api = Mock(spec_set=service._posts_api)
        service._posts_api.get_posts.return_value = async_return([])
        service._posts_api.set_approval_requested.return_value = async_return(True)

        service._accounts_api = Mock(spec_set=service._accounts_api)
        service._accounts_api.get_accounts.return_value = async_return([])

        service._email_broadcaster = Mock(spec_set=service._email_broadcaster)
        service._email_broadcaster.send.return_value = async_return(None)

        return service

    @patch("announcer.service.PostsApi", autospec=True)
    @patch("announcer.service.EmailBroadcaster", autospec=True)
    @patch("announcer.service.AccountsApi", autospec=True)
    def test_init(
        self,
        MockAccountsApi: MagicMock,
        MockEmailBroadcaster: MagicMock,
        MockPostsApi: MagicMock,
    ) -> None:
        posts_addr = "http://localhost:3929"
        accounts_addr = "http://localhost:3923"
        email_username = "test@test.com"
        email_password = "test"
        email_host = "smtp.gmail.com"
        email_port = 23

        posts_base_url = "https://anaddress.com/posts/"

        service = AnnouncerService(
            posts_addr,
            accounts_addr,
            email_username,
            email_password,
            email_host,
            email_port,
            posts_base_url,
        )

        self.assertIs(service._posts_base_url, posts_base_url)

        MockPostsApi.assert_called_with(posts_addr)
        MockAccountsApi.assert_called_with(accounts_addr)
        MockEmailBroadcaster.assert_called_with(
            email_host, email_port, email_username, email_password
        )

    async def test_tick(self) -> None:
        service = self.generate_service()
        service._posts_api.get_posts.return_value = async_return(
            TestAnnouncerService.MOCK_POSTS_LIST
        )

        service._accounts_api.get_accounts.return_value = async_return(
            TestAnnouncerService.MOCK_USERS_LIST
        )

        await service._tick()

        admin_emails = []

        for user in TestAnnouncerService.MOCK_USERS_LIST:
            admin_emails.append(user.email)

        expected_emails = []
        for post in TestAnnouncerService.MOCK_POSTS_LIST:
            if not post.approval_requested:
                expected_emails.append(
                    BroadcastEmail(
                        admin_emails,
                        AnnouncerService.EMAIL_POST_SUBJECT,
                        AnnouncerService.EMAIL_POST_APPROVAL_TEMPLATE.format(
                            post_author=post.author,
                            post_title=post.title,
                            post_link=f"{service._posts_base_url}{post.id}",
                        ),
                    )
                )

        service._posts_api.get_posts.assert_called_with(query={"approved": "false"})
        service._accounts_api.get_accounts.assert_called_with({"type": "admin"})
        service._email_broadcaster.send.assert_called_with(expected_emails)

        expected_calls = []
        for post in TestAnnouncerService.MOCK_POSTS_LIST:
            if not post.approval_requested:
                expected_calls.append(call(post.id, True))

        service._posts_api.set_approval_requested.assert_has_calls(
            expected_calls, any_order=True
        )

    async def test_tick_no_new_posts(self) -> None:
        service = self.generate_service()

        service._posts_api.get_posts.return_value = async_return([])

        await service._tick()

        self.assertFalse(service._accounts_api.get_accounts.called)
        self.assertFalse(service._email_broadcaster.send.called)
        self.assertFalse(service._posts_api.set_approval_requested.called)

    async def test_tick_post_api_failure(self) -> None:
        service = self.generate_service()

        service._posts_api.get_posts.return_value = async_exception(
            PostsApiError("Some error")
        )
        await service._tick()

        self.assertFalse(service._accounts_api.get_accounts.called)
        self.assertFalse(service._email_broadcaster.send.called)
        self.assertFalse(service._posts_api.set_approval_requested.called)

    async def test_tick_accounts_api_error(self) -> None:
        service = self.generate_service()

        service._posts_api.get_posts.return_value = async_return(
            TestAnnouncerService.MOCK_POSTS_LIST
        )
        service._accounts_api.get_accounts.return_value = async_exception(
            AccountsApiError("Another error")
        )

        await service._tick()
        self.assertFalse(service._email_broadcaster.send.called)
        self.assertFalse(service._posts_api.set_approval_requested.called)

    async def test_tick_no_admins(self) -> None:
        service = self.generate_service()

        service._posts_api.get_posts.return_value = async_return(
            TestAnnouncerService.MOCK_POSTS_LIST
        )
        service._accounts_api.get_accounts.return_value = async_return([])

        await service._tick()
        self.assertFalse(service._email_broadcaster.send.called)
        self.assertFalse(service._posts_api.set_approval_requested.called)

    async def test_tick_email_broadcaster_send_error(self) -> None:
        service = self.generate_service()

        service._posts_api.get_posts.return_value = async_return(
            TestAnnouncerService.MOCK_POSTS_LIST
        )
        service._accounts_api.get_accounts.return_value = async_return(
            TestAnnouncerService.MOCK_USERS_LIST
        )

        service._email_broadcaster.send.return_value = async_exception(
            SendError("Could not send")
        )

        await service._tick()

        service._posts_api.set_approval_requested.assert_called()

    async def test_tick_email_broadcaster_other_error(self) -> None:
        service = self.generate_service()

        service._posts_api.get_posts.return_value = async_return(
            TestAnnouncerService.MOCK_POSTS_LIST
        )
        service._accounts_api.get_accounts.return_value = async_return(
            TestAnnouncerService.MOCK_USERS_LIST
        )

        service._email_broadcaster.send.return_value = async_exception(
            EmailBroadcasterError("Some error")
        )

        await service._tick()

        self.assertFalse(service._posts_api.set_approval_requested.called)

    async def test_tick_set_approval_requested_error(self) -> None:
        service = self.generate_service()

        service._posts_api.get_posts.return_value = async_return(
            TestAnnouncerService.MOCK_POSTS_LIST
        )
        service._accounts_api.get_accounts.return_value = async_return(
            TestAnnouncerService.MOCK_USERS_LIST
        )

        service._email_broadcaster.send.return_value = async_return(None)

        service._posts_api.set_approval_requested.return_value = async_exception(
            PostsApiError("Some error")
        )

        await service._tick()
