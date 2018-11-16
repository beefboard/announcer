import unittest
import asynctest
import datetime

from announcer.api.accounts import AccountsApi, User, AccountsApiError, InvalidResponse
from aioresponses import aioresponses

TEST_ACCOUNTS_ADDRESS = "http://localhost:3924"
accounts_client = AccountsApi(TEST_ACCOUNTS_ADDRESS)


class TestAccountsApi(asynctest.TestCase):
    def test_initialisation(self) -> None:
        test_client = AccountsApi("http://google.com")
        assert test_client is not None
        assert test_client._address is "http://google.com"

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
            TEST_ACCOUNTS_ADDRESS + "/v1/accounts?type=admin",
            payload={"accounts": [mock_account]},
        )

        users = await accounts_client.get_accounts({"type": "admin"})
        assert len(users) == 1
        for user in users:
            assert type(user) == User
            assert user.username == mock_account["username"]

    async def test_get_accounts_error(self) -> None:
        error = None
        try:
            await accounts_client.get_accounts({"something": "somethingelse"})
        except AccountsApiError as e:
            error = e
        assert type(error) == AccountsApiError

    @aioresponses()
    async def test_get_accounts_server_error(self, m) -> None:
        m.get(TEST_ACCOUNTS_ADDRESS + "/v1/accounts?type=admin", status=500)

        error = None
        try:
            await accounts_client.get_accounts({"type": "admin"})
        except AccountsApiError as e:
            error = e
        assert type(error) == AccountsApiError

    @aioresponses()
    async def test_get_accounts_non_json_response(self, m: aioresponses) -> None:
        m.get(TEST_ACCOUNTS_ADDRESS + "/v1/accounts?type=admin", body="test")
        error = None
        try:
            await accounts_client.get_accounts({"type": "admin"})
        except AccountsApiError as e:
            error = e
        assert type(error) == InvalidResponse

    @aioresponses()
    async def test_get_accounts_bad_json_response(self, m: aioresponses) -> None:
        mock_post_id = "sadfnasdf"
        m.get(
            TEST_ACCOUNTS_ADDRESS + "/v1/accounts?type=admin", payload={"weird": True}
        )
        try:
            await accounts_client.get_accounts({"type": "admin"})
        except InvalidResponse as e:
            error = e

        assert type(error) == InvalidResponse
