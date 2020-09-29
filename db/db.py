import asyncio

import umongo
from motor.motor_asyncio import AsyncIOMotorClient
from db.mixin import ContextInstanceMixin
from db.bd_config import *


class DB(ContextInstanceMixin):
    def __init__(self):
        uri = f'mongodb://{DB_USERNAME}:{DB_PASS}@{DB_HOST}:27017/{DB_NAME}'
        self.loop = asyncio.get_event_loop()
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[DB_NAME]

        self.set_current(self)


class Instance(ContextInstanceMixin):

    def __init__(self, db_: DB = None):
        if not db_:
            self.db = DB.get_current().db
        else:
            self.db = db_

        self.instance = umongo.Instance(self.db)

        self.set_current(self)


db = DB()
instance = Instance()