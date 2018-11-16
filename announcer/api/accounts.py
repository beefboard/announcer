import json
from typing import Any, Dict, List

import aiohttp
from aiohttp.client_exceptions import ClientConnectionError

from dataclasses import dataclass


class AccountsApiError(Exception):
    pass


class InvalidResponse(AccountsApiError):
    pass


@dataclass
class User:
    username: str
    email: str
    admin: bool
    firstName: str
    lastName: str


class AccountsApi:
    TIMEOUT = 3

    def __init__(self, address: str) -> None:
        self._address = address

    def _decode_user(self, user_data: Dict[str, Any]):
        return User(
            username=user_data["username"],
            email=user_data["email"],
            admin=user_data["admin"],
            firstName=user_data["firstName"],
            lastName=user_data["lastName"],
        )

    async def _get_response(self, request) -> dict:
        try:
            async with request as response:
                if response.status == 500:
                    raise AccountsApiError("Internal server error")
                return await response.json()
        except (TimeoutError, ClientConnectionError) as e:
            raise AccountsApiError(e)
        except json.JSONDecodeError as e:
            raise InvalidResponse("Could not decode response json")

    async def get_accounts(self, query) -> List[User]:
        async with aiohttp.ClientSession() as session:
            data = await self._get_response(
                session.get(self._address + "/v1/accounts", params=query)
            )

            if "accounts" not in data:
                raise InvalidResponse("Bad response")

            users = []
            for user_data in data["accounts"]:
                users.append(self._decode_user(user_data))

            return users
