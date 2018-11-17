from typing import List
from announcer.api.posts import PostsApi, PostsApiError, Post
from announcer.api.accounts import AccountsApi, AccountsApiError
from announcer.broadcasters.email import (
    BroadcastEmail,
    EmailBroadcaster,
    EmailBroadcasterError,
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
    ) -> None:
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

    async def _get_admins(self) -> List[str]:
        admin_users = await self._accounts_api.get_accounts({"type": "admin"})

        emails: List[str] = []
        for user in admin_users:
            emails.append(user.email)

        return emails

    def _generate_emails(
        self, email_addresses: List[str], new_posts: List[Post]
    ) -> List[BroadcastEmail]:
        emails = []
        for post in new_posts:
            emails.append(
                BroadcastEmail(
                    ["test2@test.com", "test@gmail.com"],
                    AnnouncerService.EMAIL_POST_SUBJECT,
                    AnnouncerService.EMAIL_POST_APPROVAL_TEMPLATE.format(
                        post_author=post.author,
                        post_title=post.title,
                        post_link=f"{self._posts_base_url}{post.id}",
                    ),
                )
            )

        return emails

    async def _tick(self):
        new_posts = await self._get_new_posts()
        admin_emails = await self._get_admins()

        emails = self._generate_emails(admin_emails, new_posts)

        await self._email_broadcaster.send(emails)

