from typing import List
import datetime
from dateutil.parser import parse

import aiohttp
from aiohttp.client_exceptions import ClientConnectionError
import json

from dataclasses import dataclass


@dataclass
class Post:
    id: str
    author: str
    title: str
    content: str
    num_images: int
    date: datetime.datetime
    approved: bool = False
    pinned: bool = False
    notified: bool = False
    approval_requested: bool = False


class PostsApiError(Exception):
    pass


class InvalidResponse(PostsApiError):
    pass


class PostsApi:
    TIMEOUT = 3
    POSTS_KEY = "posts"
    SUCCESS_KEY = "success"

    def __init__(self, address: str) -> None:
        self._address = address

    def _decode_post(self, post_data):
        return Post(
            id=post_data["id"],
            author=post_data["author"],
            title=post_data["title"],
            content=post_data["content"],
            num_images=post_data["numImages"],
            date=parse(post_data["date"]),
            approved=post_data["approved"],
            pinned=post_data["pinned"],
            notified=post_data["notified"],
            approval_requested=post_data["approvalRequested"],
        )

    async def _get_response(self, request) -> dict:
        try:
            async with request as response:
                if response.status == 500:
                    raise PostsApiError("Internal server error")
                return await response.json()
        except (TimeoutError, ClientConnectionError) as e:
            raise PostsApiError(e)
        except json.JSONDecodeError as e:
            raise InvalidResponse("Could not decode response json")

    async def get_posts(self) -> List[Post]:
        async with aiohttp.ClientSession() as session:
            data = await self._get_response(
                session.get(self._address + "/v1/posts", timeout=PostsApi.TIMEOUT)
            )

            if PostsApi.POSTS_KEY not in data:
                raise InvalidResponse("posts missing from response")

            posts = []

            for post_data in data[PostsApi.POSTS_KEY]:
                posts.append(self._decode_post(post_data))

            return posts

    async def set_approval_requested(self, post_id: str, requested: bool) -> bool:
        async with aiohttp.ClientSession() as session:
            data = await self._get_response(
                session.put(
                    self._address + "/v1/posts/" + post_id,
                    data={"approvalRequested": requested},
                    timeout=PostsApi.TIMEOUT,
                )
            )

            if PostsApi.SUCCESS_KEY not in data:
                raise InvalidResponse("SUCCESS_KEY missing from response")

            return data[PostsApi.SUCCESS_KEY]
