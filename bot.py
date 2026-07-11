from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8004306854:AAEJ1zKdXNgiDxNpVVIgWcG0xD4UccV4rJQ"

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

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

app.run_polling()
