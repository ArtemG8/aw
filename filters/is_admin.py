from aiogram.filters import BaseFilter
from aiogram.types import Message

from config import conf


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user is not None and message.from_user.id in conf.ADMIN_IDS
