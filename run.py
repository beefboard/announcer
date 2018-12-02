import os
import logging
import asyncio
from announcer.service import AnnouncerService


def start():
    asyncio.get_event_loop().run_until_complete(service.main_loop())


posts_api = os.environ.get("POSTS_API", "http://localhost:2833")
accounts_api = os.environ.get("ACCOUNTS_API", "http://localhost:2832")

email_username = os.environ.get("EMAIL_USERNAME", None)
email_password = os.environ.get("EMAIL_PASSWORD", None)
email_host = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
email_port = int(os.environ.get("EMAIL_PORT", 25))
posts_base_url = os.environ.get("EMAIL_BASE_URL", "https://beefboard.mooo.com/posts/")

log_level = os.environ.get("LOG_LEVEL", logging.INFO)

if not email_username or not email_username:
    raise ValueError("EMAIL_USERNAME and EMAIL_PASSWORD environment not set")

assert email_username is not None
assert email_password is not None

logging.basicConfig(level=log_level)

service = AnnouncerService(
    posts_api,
    accounts_api,
    email_username,
    email_password,
    email_host,
    email_port,
    posts_base_url,
)

start()
