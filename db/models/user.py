import time
import typing
import string
import random
import umongo
from umongo import fields

from db.models.stat import Statistics
from db.models.instagram_account import InstagramAccount
from ..db import Instance
from bson.objectid import ObjectId

instance: umongo.Instance = Instance.get_current().instance


@instance.register
class User(umongo.Document):
    uid = fields.IntegerField(required=True, unique=True)
    ref_code = fields.StringField(required=True, unique=True)
    username = fields.StringField(required=True)
    balance = fields.FloatField(default=0)
    balance_from_friends = fields.FloatField(default=0)
    created_time = fields.IntegerField(default=int(time.time()))
    referrals = fields.ListField(fields.ReferenceField("User"), default=[])
    accounts = fields.ListField(fields.ReferenceField("InstagramAccount"), default=[])
    inviter = fields.IntegerField(required=False, unique=False)
    notes = fields.StringField(default="")
    ban_time = fields.IntegerField(default=0)

    class Meta:
        collection = instance.db.users

    @staticmethod
    async def create_user(
            uid: int, inviter, referrals: list, username: int
    ) -> typing.Union["User", typing.NoReturn]:

        ref_code = "".join(
            (
                random.choice(string.ascii_letters + string.digits + str(i))
                for i in range(6)
            )
        )

        while await User.get_user_by_ref_link(ref_code=ref_code) is not None:
            ref_code = "".join(
                (
                    random.choice(string.ascii_letters + string.digits + str(i))
                    for i in range(6)
                )
            )

        if inviter is not None:
            user: User = User(
                uid=uid, ref_code=ref_code, inviter=inviter, referrals=referrals, username=username
            )
        else:
            user: User = User(uid=uid, ref_code=ref_code, referrals=referrals, username=username)
        await user.commit()
        return user

    @staticmethod
    async def get_user(uid: int) -> typing.Union["User", typing.NoReturn]:

        user = await User.find_one({"uid": uid})
        return user

    @staticmethod
    async def get_user_by_ref_link(
            ref_code: str,
    ) -> typing.Union["User", typing.NoReturn]:

        try:
            user = await User.find_one({"ref_code": ref_code})
            return user
        except:
            return None

    @staticmethod
    async def get_user_by_str_pk(uid) -> typing.Union["User", typing.NoReturn]:

        return await User.find_one({'_id': ObjectId(str(uid))})

    @staticmethod
    async def get_user_by_pk(uid) -> typing.Union["User", typing.NoReturn]:

        user = await User.find_one({"id": uid})
        return user


    @staticmethod
    async def update_balance_friends(user: "User", value: float) -> typing.Union["User", typing.NoReturn]:
        current: dict = user.dump()
        current_balance: float = current['balance_from_friends']

        user.update({"balance_from_friends": current_balance + value})

        await user.commit()
        return user

    @staticmethod
    async def add_referral(
            user: "User", referral
    ) -> typing.Union["User", typing.NoReturn]:

        current: dict = user.dump()
        referrals: list = current["referrals"]
        referrals.append(referral)
        user.update({"referrals": referrals})

        await user.commit()
        return user

    @staticmethod
    async def add_account(user: "User", account: InstagramAccount) -> typing.Union["User", typing.NoReturn]:

        current: dict = user.dump()
        accounts: list = current["accounts"]
        new_accounts = []

        for acc_pk in accounts:
            acc_: InstagramAccount = await InstagramAccount.find_by_pk(pk=acc_pk)
            if acc_ is not None:
                new_accounts.append(acc_)
        new_accounts.append(account)
        user.update({"accounts": new_accounts})

        await user.commit()
        return user

    @staticmethod
    async def delete_account(user: "User", account: InstagramAccount) -> typing.Union["User", typing.NoReturn]:

        current: dict = user.dump()
        accounts: list = current["accounts"]
        accounts_ = []
        for acc in accounts:
            if str(acc) != str(account.pk):
                accounts_.append(acc)

        user.update({"accounts": accounts_})

        await user.commit()
        return user

    @staticmethod
    async def pay(user: "User", price) -> typing.Union["User", typing.NoReturn]:

        current: dict = user.dump()
        user_voices = float(current["voices"]) - price

        user.update({"voices": user_voices})

        await user.commit()
        return user

    @staticmethod
    async def give_money(user: "User", value) -> typing.Union["User", typing.NoReturn]:

        current: dict = user.dump()
        user_balance = float(current["balance"]) + value

        user.update({"balance": user_balance})

        await user.commit()
        return user

    @staticmethod
    async def minus_money(user: "User", value) -> typing.Union[
        "User", typing.NoReturn]:
        current: dict = user.dump()
        user_balance = float(current["balance"]) - value
        user.update({"balance": user_balance})
        await user.commit()
        return user

    @staticmethod
    async def get_all_users() -> typing.Union["User", typing.NoReturn]:
        return User.find({})


    @staticmethod
    async def update_open_bot_today(user_new: "User"):
        stat = await Statistics.get_current_stat()
        current = stat.dump()

        open_bot_today = current["open_bot_today"]

        new_open_bot_today = []
        for user in open_bot_today:
            user_: User = await User.get_user_by_str_pk(uid=user)
            if user_ not in new_open_bot_today:
                new_open_bot_today.append(user_)

        if user_new not in new_open_bot_today:
            new_open_bot_today.append(user_new)

        stat.update({"open_bot_today": new_open_bot_today})
        await stat.commit()
        return stat

    @staticmethod
    async def remove(user):
        await user.remove()
