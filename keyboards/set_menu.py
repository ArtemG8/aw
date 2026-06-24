from aiogram.types import BotCommand


async def set_main_menu(bot) -> None:
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="materials", description="Полезные материалы"),
        BotCommand(command="contact", description="Написать в поддержку"),
    ]
    await bot.set_my_commands(commands)
