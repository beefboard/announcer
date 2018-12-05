import asyncio
import logging
from typing import List

from announcer.api.accounts import AccountsApi, AccountsApiError
from announcer.api.posts import Post, PostsApi, PostsApiError
from announcer.broadcasters.email import (
    BroadcastEmail,
    EmailBroadcaster,
    EmailBroadcasterError,
    SendError,
)


class AnnouncerService:
    EMAIL_POST_APPROVAL_TEMPLATE = """
Hi,

{post_author} has submitted a new post: {post_title}.

Please review post here: {post_link}
"""
    EMAIL_POST_SUBJECT = "New Beef submitted - Please review"

    def __init__(
        self,
        posts_addr: str,
        accounts_addr: str,
        email_username: str,
        email_password: str,
        email_host: str,
        email_port: int,
        view_posts_base_url: str = "https://beefboard.mooo.com/posts/",
    ):
        self._log = logging.getLogger(AnnouncerService.__name__)
        self._posts_api = PostsApi(posts_addr)
        self._accounts_api = AccountsApi(accounts_addr)
        self._email_broadcaster = EmailBroadcaster(
            email_host, email_port, email_username, email_password
        )

        self._posts_base_url = view_posts_base_url

    async def _get_new_posts(self) -> List[Post]:
        all_new_posts = await self._posts_api.get_posts(query={"approved": "false"})

        new_posts: List[Post] = []

        # Filter new posts for posts where we haven't already
        # sent out an email
        for new_post in all_new_posts:
            if not new_post.approval_requested:
                new_posts.append(new_post)
        return new_posts

    async def _get_admin_emails(self) -> List[str]:
        admin_users = await self._accounts_api.get_accounts({"type": "admin"})

        emails: List[str] = []
        for user in admin_users:
            emails.append(user.email)

        return emails

    def _generate_emails(
        self, recipients: List[str], new_posts: List[Post]
    ) -> List[BroadcastEmail]:
        emails = []
        for post in new_posts:
            emails.append(
                BroadcastEmail(
                    recipients,
                    AnnouncerService.EMAIL_POST_SUBJECT,
                    AnnouncerService.EMAIL_POST_APPROVAL_TEMPLATE.format(
                        post_author=post.author,
                        post_title=post.title,
                        post_link=f"{self._posts_base_url}{post.id}",
                    ),
                )
            )

        return emails

    async def _attempt_mark_post_requested(self, post: Post) -> None:
        try:
            await self._posts_api.set_approval_requested(post.id, True)
        except PostsApiError as e:
            self._log.error(f"Could not mark {post.id} as approval requested: {e}")

    async def _tick(self) -> None:
        self._log.debug("Collecting new posts")
        try:
            new_posts = await self._get_new_posts()
        except PostsApiError as e:
            self._log.error(f"Could not get new posts: {e}")
            return

        if not new_posts:
            self._log.debug("No new posts, finishing tick")
            return

        self._log.debug("Getting admin emails")
        try:
            admin_emails = await self._get_admin_emails()
        except AccountsApiError as e:
            self._log.error(f"Could not get admin emails: {e}")
            return

        if not admin_emails:
            return

        self._log.debug(f"Got {len(admin_emails)} admin email(s)")

        emails = self._generate_emails(admin_emails, new_posts)

        self._log.debug(f"Broadcasting {len(emails)} email(s) to admins")
        try:
            await self._email_broadcaster.send(emails)
        except SendError as e:
            self._log.warning(
                f"Could not send emails: ({e}). Marking emails as sent anyway"
            )
        except EmailBroadcasterError as e:
            self._log.error(f"Could not broadcast messages: {e}")
            return

        self._log.debug(f"Setting {len(new_posts)} as approval requested")
        tasks = []
        for post in new_posts:
            tasks.append(self._attempt_mark_post_requested(post))

        await asyncio.wait(tasks)

    async def _sleep(self, time: int) -> None:
        await asyncio.sleep(time)

    async def main_loop(self) -> None:
        self._log.info("Starting main loop")

        while True:
            await self._tick()
            await self._sleep(5)
