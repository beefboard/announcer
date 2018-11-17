import os
from announcer.service import AnnouncerService

posts_api = os.environ.get("POSTS_API", "http://localhost:2392")
accounts_api = os.environ.get("ACCOUNTS_API", "http://localhost:2393")

AnnouncerService(posts_api, accounts_api)
