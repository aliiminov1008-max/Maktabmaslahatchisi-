import os
import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_CHAT_ID = 5060424574  # Maslahatchining shaxsiy Telegram ID'si

# O'quvchidan kelgan anonim xabarlarni saqlab turadi:
# {maslahatchiga_yuborilgan_xabar_id: o'quvchi_chat_id}
# Diqqat: bu vaqtinchalik xotira, bot qayta ishga tushsa tozalanadi.
pending_replies = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 Assalomu alaykum!\n\n"
        "Maktab Maslahatchi botiga xush kelibsiz!\n\n"
        "📚 Bu bot orqali:\n"
        "• Kasbga yo'naltirish\n"
        "• Metodik materiallar\n"
        "• Testlar\n"
        "• Psixologik tavsiyalar\n"
        "• Me'yoriy hujjatlar\n\n"
        "bo'yicha ma'lumot olishingiz mumkin."
    )


async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """WebApp ichidagi forma orqali kelgan ma'lumotlarni qabul qiladi."""
    raw = update.effective_message.web_app_data.data
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return

    if data.get("type") == "anon_message":
        text = data.get("text", "").strip()
        if not text:
            return

        user_chat_id = update.effective_chat.id

        sent = await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                "📩 Yangi anonim murojaat:\n\n"
                f"{text}\n\n"
                "— Javob berish uchun shu xabarga *reply* qiling."
            ),
            parse_mode="Markdown",
        )
        # Shu xabar ID'sini o'quvchi ID'siga bog'lab qo'yamiz
        pending_replies[sent.message_id] = user_chat_id

        await update.effective_message.reply_text(
            "✅ Xabaringiz maslahatchiga yetkazildi. Javob kelsa, shu yerga yoziladi."
        )


async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maslahatchi anonim xabarga reply qilganda, javobni o'quvchiga yetkazadi."""
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    if not update.message.reply_to_message:
        return

    original_id = update.message.reply_to_message.message_id
    student_chat_id = pending_replies.get(original_id)
    if not student_chat_id:
        return

    await context.bot.send_message(
        chat_id=student_chat_id,
        text=f"💬 Maslahatchidan javob:\n\n{update.message.text}",
    )
    await update.message.reply_text("✅ Javobingiz o'quvchiga yuborildi.")


app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
app.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.Chat(ADMIN_CHAT_ID), handle_admin_reply))

app.run_polling()
