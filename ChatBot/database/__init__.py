from motor.motor_asyncio import AsyncIOMotorClient
import config

ChatBot = AsyncIOMotorClient(config.MONGO_URL)

db = ChatBot["ChattBot"]
usersdb = db["users"]
chatsdb = db["chats"]
sudodb = db["sudo"]
authdb = db["authusers"]

from .chats import *
from .admin import *
from .fsub import *
from .sudo import *
from .auth import *
