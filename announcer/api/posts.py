from typing import List
import datetime
from dateutil.parser import parse

import aiohttp

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


class PostsApi:
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

    async def get_posts(self) -> List[Post]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self._address + "/v1/posts") as response:
                posts = []
                data = await response.json()

                for post_data in data["posts"]:
                    posts.append(self._decode_post(post_data))

                return posts
