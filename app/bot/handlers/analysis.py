import io

from aiogram import Bot, F, Router
from aiogram.types import Message

from app.services.breakdown.builder import BreakdownBuilder

router = Router()

_MAX_MSG_LEN = 4000  # Telegram limit is 4096


def _split_text(text: str) -> list[str]:
    """Split long text into chunks that fit Telegram's message limit."""
    if len(text) <= _MAX_MSG_LEN:
        return [text]
    parts = []
    while text:
        parts.append(text[:_MAX_MSG_LEN])
        text = text[_MAX_MSG_LEN:]
    return parts


@router.message(F.document)
async def handle_document(message: Message, bot: Bot, builder: BreakdownBuilder) -> None:
    doc = message.document
    if doc.mime_type != "application/pdf":
        await message.answer("Поддерживаются только PDF файлы с анализами.")
        return

    status_msg = await message.answer("⏳ Анализирую, подождите...")

    try:
        file = await bot.get_file(doc.file_id)
        buf = io.BytesIO()
        await bot.download_file(file.file_path, destination=buf)
        file_bytes = buf.getvalue()

        result = await builder.build_from_bytes(file_bytes, "application/pdf")
        abnormal_count = sum(1 for i in result.analysis.indicators if i.status in ("low", "high"))

        header = (
            f"📋 Показателей: {len(result.analysis.indicators)}, "
            f"отклонений: {abnormal_count}\n\n"
        )
        full_text = header + result.text

        await status_msg.delete()
        for part in _split_text(full_text):
            await message.answer(part)

    except ValueError as e:
        await status_msg.edit_text(f"❌ Ошибка: {e}")
    except Exception:
        await status_msg.edit_text("❌ Не удалось обработать файл. Попробуй ещё раз.")
        raise


@router.message(F.photo)
async def handle_photo(message: Message) -> None:
    await message.answer(
        "Пожалуйста, отправь анализы в виде PDF файла.\n"
        "Фотографии пока не поддерживаются."
    )
