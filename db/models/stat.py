import time
import umongo
from umongo import fields
from ..db import Instance
instance: umongo.Instance = Instance.get_current().instance


@instance.register
class Statistics(umongo.Document):
    today = fields.IntegerField(default=0)
    new_users_today = fields.IntegerField(default=0)
    open_bot_today = fields.ListField(fields.ReferenceField("User"), default=[])
    add_money_today = fields.IntegerField(default=0)
    all_likes = fields.IntegerField(default=0)

    class Meta:
        collection = instance.db.statistics

    @staticmethod
    async def delete_every_day(stat):

        stat.update({"new_users_today": 0})
        stat.update({"open_bot_today": []})
        stat.update({"add_money_today": 0})
        stat.update({"all_likes": 0})

        await stat.commit()

        return stat

    @staticmethod
    async def increase_param(param, stat, value):
        stat = await Statistics.get_current_stat()
        current = stat.dump()
        old_param = current[param]
        new_param = old_param + value
        stat.update({param: new_param})

        await stat.commit()

    @staticmethod
    async def decrease_param(param, stat, value):
        stat = await Statistics.get_current_stat()
        current = stat.dump()
        old_param = current[param]
        new_param = old_param - value
        stat.update({param: new_param})

        await stat.commit()

    @staticmethod
    async def update_param(param, stat, value):
        stat = await Statistics.get_current_stat()
        stat.update({param: value})

        await stat.commit()

    @staticmethod
    async def check_stat_for_exist():
        return Statistics.find({})

    @staticmethod
    async def create_stat():
        stat: Statistics = Statistics()
        await stat.commit()
        return stat

    @staticmethod
    async def update_today(stat):

        stat.update({"today": int(time.time())})
        await stat.commit()
        return stat

    @staticmethod
    async def get_current_stat():
        stat = await Statistics.check_stat_for_exist()

        current_stat = None
        check = ""
        async for s in stat:
            current_stat = s
            check += str(s)

        if not check:
            current_stat = await Statistics.create_stat()

        return current_stat