import datetime
import unittest

import asynctest
from aioresponses import aioresponses

from announcer.api.accounts import AccountsApi, AccountsApiError, InvalidResponse, User


class TestAccountsApi(asynctest.TestCase):
    ADDRESS = "http://localhost:3924"

    def setUp(self):
        self.client = AccountsApi(TestAccountsApi.ADDRESS)

    def test_initialisation(self) -> None:
        test_client = AccountsApi("http://google.com")
        self.assertIsNot(test_client, None)
        self.assertIs(test_client._address, "http://google.com")

    @aioresponses()
    async def test_get_accounts(self, m: aioresponses):
        mock_account = {
            "username": "test",
            "email": "test@test.com",
            "admin": False,
            "firstName": "test",
            "lastName": "test",
        }
        m.get(
            TestAccountsApi.ADDRESS + "/v1/accounts?type=admin",
            payload={"accounts": [mock_account]},
        )

        users = await self.client.get_accounts({"type": "admin"})
        assert len(users) == 1
        for user in users:
            assert type(user) == User
            assert user.username == mock_account["username"]

    async def test_get_accounts_error(self) -> None:
        error = None
        try:
            await self.client.get_accounts({"something": "somethingelse"})
        except AccountsApiError as e:
            error = e
        assert type(error) == AccountsApiError

    @aioresponses()
    async def test_get_accounts_server_error(self, m) -> None:
        m.get(TestAccountsApi.ADDRESS + "/v1/accounts?type=admin", status=500)

        error = None
        try:
            await self.client.get_accounts({"type": "admin"})
        except AccountsApiError as e:
            error = e
        assert type(error) == AccountsApiError

    @aioresponses()
    async def test_get_accounts_non_json_response(self, m: aioresponses) -> None:
        m.get(TestAccountsApi.ADDRESS + "/v1/accounts?type=admin", body="test")
        error = None
        try:
            await self.client.get_accounts({"type": "admin"})
        except AccountsApiError as e:
            error = e
        assert type(error) == InvalidResponse

    @aioresponses()
    async def test_get_accounts_bad_json_response(self, m: aioresponses) -> None:
        m.get(
            TestAccountsApi.ADDRESS + "/v1/accounts?type=admin", payload={"weird": True}
        )
        try:
            await self.client.get_accounts({"type": "admin"})
        except InvalidResponse as e:
            error = e

        assert type(error) == InvalidResponse
