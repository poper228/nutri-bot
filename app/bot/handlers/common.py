from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я помогаю разбирать лабораторные анализы.\n\n"
        "Отправь PDF с анализами — получишь подробный нутрициологический разбор."
    )
