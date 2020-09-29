import time
import umongo
from umongo import fields
import typing
from ..db import Instance
from bson.objectid import ObjectId

instance: umongo.Instance = Instance.get_current().instance


@instance.register
class InstagramAccount(umongo.Document):
    user = fields.ReferenceField('User', required=True)
    ig_login = fields.StringField(required=True)
    ig_password = fields.StringField(required=True)
    proxy = fields.StringField(default="")
    created_time = fields.IntegerField(default=time.time)
    paid_before = fields.IntegerField(default=0)
    count_likes = fields.FloatField(default=0)
    count_saves = fields.FloatField(default=0)

    class Meta:
        collection = instance.db.insta_accounts

    @staticmethod
    async def create_account(user, ig_login, ig_password, proxy):
        account = InstagramAccount(user=user, ig_login=ig_login, ig_password=ig_password, proxy=proxy)
        await account.commit()
        return account

    @staticmethod
    async def get_user_accs(user):
        user_pk = user.dump().get('id')

        user_tasks = InstagramAccount.find({
            'user': ObjectId(user_pk),
        })

        return user_tasks

    @staticmethod
    async def find_by_pk(pk):

        return await InstagramAccount.find_one({'_id': ObjectId(str(pk))})

    @staticmethod
    async def find_by_username(ig_login):
        return await InstagramAccount.find_one({'ig_login': ig_login})


    @staticmethod
    async def delete_acc(account) -> typing.Union[typing.NoReturn]:
        await account.remove()

