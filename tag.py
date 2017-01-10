import re
import traceback

import discord
import motor.motor_asyncio

from utils_text import parse_bool, regex_test



mongo_client = motor.motor_asyncio.AsyncIOMotorClient()

overwatch_db = mongo_client.overwatch

trigger_str_collection = overwatch_db.trigger_str

class Tagger:
    def __init__(self, client):
        self.client = client




