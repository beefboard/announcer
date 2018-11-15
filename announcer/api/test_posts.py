import unittest
import asynctest
import datetime

from announcer.api.posts import PostsApi, Post
from aioresponses import aioresponses

TEST_POSTS_ADDRESS = "http://localhost:3922"
posts_client = PostsApi(TEST_POSTS_ADDRESS)


class TestPostsApi(asynctest.TestCase):
    def test_initialisation(self):
        test_client = PostsApi("http://google.com")
        assert test_client is not None
        assert test_client._address is "http://google.com"

    @aioresponses()
    async def test_get_posts(self, m):
        mock_post = {
            "id": "asdasd",
            "date": datetime.datetime.now().isoformat(),
            "title": "test",
            "author": "me",
            "content": "test",
            "approved": True,
            "approvalRequested": True,
            "numImages": 0,
            "notified": False,
            "pinned": False,
        }
        m.get(TEST_POSTS_ADDRESS + "/v1/posts", payload={"posts": [mock_post]})

        posts_response = await posts_client.get_posts()
        assert len(posts_response) is 1
        for post in posts_response:
            assert type(post) == Post
