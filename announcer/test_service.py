import asynctest
import asyncio
from announcer.service import AnnouncerService
from announcer.api.posts import PostsApi, Post
from announcer.api.accounts import AccountsApi, User
from announcer.broadcasters.email import EmailBroadcaster, BroadcastEmail
from unittest.mock import patch, MagicMock, Mock, call
from typing import Any
import datetime


def async_return(result):
    f = asyncio.Future()
    f.set_result(result)
    return f


POSTS_BASE_URL = "https://test.com/posts/"


class TestAnnouncerService(asynctest.TestCase):
    def generate_service(self) -> AnnouncerService:
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

    async def test_tick(self):
        service = self.generate_service()
        service._posts_api.get_posts.return_value = async_return(
            [
                Post(
                    **{
                        "id": "asdasd",
                        "date": datetime.datetime.now().isoformat(),
                        "title": "test",
                        "author": "me",
                        "content": "test",
                        "approved": False,
                        "approval_requested": True,
                        "num_images": 0,
                        "notified": False,
                        "pinned": False,
                    }
                ),
                Post(
                    **{
                        "id": "dflksdf",
                        "date": datetime.datetime.now().isoformat(),
                        "title": "Another title",
                        "author": "me2",
                        "content": "test",
                        "approved": False,
                        "approval_requested": False,
                        "num_images": 0,
                        "notified": False,
                        "pinned": False,
                    }
                ),
                Post(
                    **{
                        "id": "sadfasdf",
                        "date": datetime.datetime.now().isoformat(),
                        "title": "test",
                        "author": "me",
                        "content": "test",
                        "approved": False,
                        "approval_requested": False,
                        "num_images": 0,
                        "notified": False,
                        "pinned": False,
                    }
                ),
            ]
        )

        service._accounts_api.get_accounts.return_value = async_return(
            [
                User(
                    **{
                        "username": "test",
                        "email": "test@test.com",
                        "admin": True,
                        "firstName": "test",
                        "lastName": "test",
                    }
                ),
                User(
                    **{
                        "username": "test",
                        "email": "test2@test.com",
                        "admin": True,
                        "firstName": "test",
                        "lastName": "test",
                    }
                ),
            ]
        )

        await service._tick()

        expected_emails = [
            BroadcastEmail(
                ["test2@test.com", "test@gmail.com"],
                AnnouncerService.EMAIL_POST_SUBJECT,
                AnnouncerService.EMAIL_POST_APPROVAL_TEMPLATE.format(
                    post_author="me2",
                    post_title="Another title",
                    post_link=f"{service._posts_base_url}dflksdf",
                ),
            ),
            BroadcastEmail(
                ["test2@test.com", "test@gmail.com"],
                AnnouncerService.EMAIL_POST_SUBJECT,
                AnnouncerService.EMAIL_POST_APPROVAL_TEMPLATE.format(
                    post_author="me",
                    post_title="test",
                    post_link=f"{service._posts_base_url}sadfasdf",
                ),
            ),
        ]

        service._posts_api.get_posts.assert_called_with(query={"approved": "false"})
        service._accounts_api.get_accounts.assert_called_with({"type": "admin"})
        service._email_broadcaster.send.assert_called_with(expected_emails)

        service._posts_api.set_approval_requested.assert_has_calls(
            [call("dflksdf", True), call("sadfasdf", True)]
        )

    async def test_tick_no_new_posts(self):
        service = self.generate_service()

        service._posts_api.get_posts.return_value = async_return([])

        await service._tick()
