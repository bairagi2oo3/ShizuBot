from os import getenv

from pyrogram import filters
from dotenv import load_dotenv

load_dotenv()

API_ID = "25742938"
# -------------------------------------------------------------
API_HASH = "b35b715fe8dc0a58e8048988286fc5b6"
# --------------------------------------------------------------
BOT_TOKEN = getenv("BOT_TOKEN", None)
STRING1 = getenv("STRING_SESSION", None)
DB_NAME = "shizuDB"
MONGO_URL = getenv("MONGO_URL", None)
OWNER_ID = int(getenv("OWNER_ID", "8150875959"))
BOT_ID = int(getenv("BOT_ID", "7946219352"))
SUPPORT_GRP = "KING_BOT_UPDATE"
UPDATE_CHNL = "LINKPR0MOTION"
OWNER_USERNAME = "AboutBotMakerl"
TIME_ZONE = "Asia/Kolkata"
LOG_GROUP_ID = int(getenv("LOG_GROUP_ID", "-1002524224601"))
# --------------------------------------------------------------
SUDOERS = list(map(int, getenv("SUDOERS", "8150875959").split()))
# --------------------------------------------------------------

### DONT TOUCH or EDIT codes after this line
BANNED_USERS = filters.user()

# For customized or modified Repository
UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "https://github.com/bairagi2oo3/ShizuBot",
)
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
