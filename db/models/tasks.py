import umongo
import time
from umongo import fields
from ..db import Instance
from bson.objectid import ObjectId

instance: umongo.Instance = Instance.get_current().instance


@instance.register
class Tasks(umongo.Document):
    hashtag = fields.StringField(required=True)
    create_time = fields.IntegerField(required=True)
    owner_inst = fields.StringField(required=True)
    start_time = fields.IntegerField(required=True)