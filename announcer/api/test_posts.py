import unittest
import asynctest
import datetime

from announcer.api.posts import PostsApi, Post, PostsApiError, InvalidResponse
from aioresponses import aioresponses

TEST_POSTS_ADDRESS = "http://localhost:3922"
posts_client = PostsApi(TEST_POSTS_ADDRESS)


class TestPostsApi(asynctest.TestCase):
    def test_initialisation(self) -> None:
        test_client = PostsApi("http://google.com")
        assert test_client is not None
        assert test_client._address is "http://google.com"

    @aioresponses()
    async def test_get_posts(self, m: aioresponses) -> None:
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
            assert post.id == mock_post["id"]
            assert post.title == mock_post["title"]

    @aioresponses()
    async def test_get_posts_query(self, m: aioresponses) -> None:
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
        m.get(
            TEST_POSTS_ADDRESS + "/v1/posts?approved=false",
            payload={"posts": [mock_post]},
        )

        posts_response = await posts_client.get_posts(query={"approved": "false"})
        assert len(posts_response) is 1

    async def test_get_posts_error(self) -> None:
        error = None
        try:
            await posts_client.get_posts()
        except PostsApiError as e:
            error = e
        assert type(error) == PostsApiError

    @aioresponses()
    async def test_get_posts_server_error(self, m: aioresponses) -> None:
        m.get(TEST_POSTS_ADDRESS + "/v1/posts", status=500)
        try:
            await posts_client.get_posts()
        except PostsApiError as e:
            error = e

        assert type(error) == PostsApiError

    @aioresponses()
    async def test_get_posts_non_json_response(self, m: aioresponses) -> None:
        m.get(TEST_POSTS_ADDRESS + "/v1/posts", body="test")
        try:
            await posts_client.get_posts()
        except InvalidResponse as e:
            error = e

        assert type(error) == InvalidResponse

    @aioresponses()
    async def test_get_posts_bad_json_response(self, m: aioresponses) -> None:
        m.get(TEST_POSTS_ADDRESS + "/v1/posts", payload={"something": []})
        try:
            await posts_client.get_posts()
        except InvalidResponse as e:
            error = e

        assert type(error) == InvalidResponse

    @aioresponses()
    async def test_set_approval_requested(self, m: aioresponses) -> None:
        mock_post_id = "sadfnasdf"
        m.put(
            TEST_POSTS_ADDRESS + "/v1/posts/" + mock_post_id, payload={"success": True}
        )

        success = await posts_client.set_approval_requested(mock_post_id, True)

        assert success == True, "Response should be success value"

    async def test_set_approval_requested_error(self) -> None:
        error = None
        try:
            await posts_client.set_approval_requested("sdfasdf", True)
        except PostsApiError as e:
            error = e
        assert type(error) == PostsApiError

    @aioresponses()
    async def test_set_approval_requested_server_error(self, m) -> None:
        mock_post_id = "sadfnasdf"
        m.put(TEST_POSTS_ADDRESS + "/v1/posts/" + mock_post_id, status=500)

        error = None
        try:
            await posts_client.set_approval_requested(mock_post_id, True)
        except PostsApiError as e:
            error = e
        assert type(error) == PostsApiError

    @aioresponses()
    async def test_set_approval_requested_non_json_response(
        self, m: aioresponses
    ) -> None:
        mock_post_id = "sadfnasdf"
        m.put(TEST_POSTS_ADDRESS + "/v1/posts/" + mock_post_id, body="test")
        try:
            await posts_client.set_approval_requested(mock_post_id, True)
        except InvalidResponse as e:
            error = e

        assert type(error) == InvalidResponse

    @aioresponses()
    async def test_set_approval_requested_bad_json_response(
        self, m: aioresponses
    ) -> None:
        mock_post_id = "sadfnasdf"
        m.put(TEST_POSTS_ADDRESS + "/v1/posts/" + mock_post_id, payload={"weird": True})
        try:
            await posts_client.set_approval_requested(mock_post_id, True)
        except InvalidResponse as e:
            error = e

        assert type(error) == InvalidResponse
