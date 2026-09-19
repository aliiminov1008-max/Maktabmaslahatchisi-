import os
import time
import hmac
import hashlib
from datetime import datetime
from urllib.parse import parse_qsl
from zoneinfo import ZoneInfo
from aiohttp import web
import json
import logging
from telegram import Update, MenuButtonWebApp, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_CHAT_ID = 5060424574  # Maslahatchining shaxsiy Telegram ID'si

# Web App (GitHub Pages) manzili — reponi qayta nomlaganda shu yerni yangilang
# "?v=" — bot har gal qayta ishga tushganda manzil o'zgaradi, shuning uchun
# Telegram eski (kesh) sahifani ko'rsatmaydi.
WEBAPP_URL = "https://aliiminov1008-max.github.io/jismoniytarbiya1/?v=" + str(int(time.time()))

# O'quvchidan kelgan anonim xabarlarni saqlab turadi:
# {maslahatchiga_yuborilgan_xabar_id: o'quvchi_chat_id}
# Diqqat: bu vaqtinchalik xotira, bot qayta ishga tushsa tozalanadi.
pending_replies = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # "🏆 Testni boshlash" tugmasini to'g'ri (yangi) WebApp manziliga ishora
    # qilib qayta yuboramiz — bu eski, boshqa manzilga ishora qiluvchi tugmani
    # avtomatik almashtiradi (Telegram klaviaturani yangilaydi).
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("🏆 Testni boshlash", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True,
    )
    await update.message.reply_text(
        "🎓 Assalomu alaykum!\n\n"
        "Maktab Maslahatchi botiga xush kelibsiz!\n\n"
        "📚 Bu bot orqali:\n"
        "• Kasbga yo'naltirish\n"
        "• Metodik materiallar\n"
        "• Testlar\n"
        "• Psixologik tavsiyalar\n"
        "• Me'yoriy hujjatlar\n\n"
        "bo'yicha ma'lumot olishingiz mumkin.",
        reply_markup=keyboard,
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


# ---------- Web App ochilganda maslahatchiga xabar (token faqat serverda) ----------
ALLOWED_ORIGIN = "https://aliiminov1008-max.github.io"
CORS = {
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def check_init_data(init_data: str):
    """Telegram initData imzosini tekshiradi va user ma'lumotini qaytaradi."""
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received = pairs.pop("hash", None)
    if not received:
        return None
    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, received):
        return None
    try:
        return json.loads(pairs.get("user", "{}"))
    except json.JSONDecodeError:
        return None


async def handle_options(request):
    return web.Response(status=204, headers=CORS)


async def handle_notify(request):
    bot = request.app["bot"]
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False}, status=400, headers=CORS)
    user = check_init_data(body.get("initData", ""))
    if not user:
        return web.json_response({"ok": False}, status=403, headers=CORS)

    now = datetime.now(ZoneInfo("Asia/Tashkent")).strftime("%d/%m/%Y, %H:%M:%S")
    text = f"🔔 Web App ochildi!\n📅 {now}\n\n👤 Foydalanuvchi:\n🆔 ID: {user.get('id')}\n"
    name = (user.get("first_name") or "") + (" " + user["last_name"] if user.get("last_name") else "")
    if name.strip():
        text += f"📛 Ism: {name.strip()}\n"
    if user.get("username"):
        text += f"🔗 Username: @{user['username']}\n"
    if user.get("language_code"):
        text += f"🌐 Til: {user['language_code']}\n"
    text += "\n"
    if body.get("access"):
        text += "✅ Ruxsat: BOR (to'liq kirish)"
    else:
        text += f"🔒 Ruxsat: YO'Q\n💡 ID ni Sheetsga qo'shish: {user.get('id')}"
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    return web.json_response({"ok": True}, headers=CORS)


async def start_web_server(application: Application):
    web_app = web.Application()
    web_app["bot"] = application.bot
    web_app.router.add_post("/notify", handle_notify)
    web_app.router.add_options("/notify", handle_options)
    web_app.router.add_get("/", lambda r: web.Response(text="ok"))
    runner = web.AppRunner(web_app)
    await runner.setup()
    port = int(os.environ.get("PORT", "8080"))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    logging.info("Notify server ishga tushdi: port %s", port)


async def set_menu_button(application: Application):
    """Bot ishga tushganda Menu Button (Web App) manzilini avtomatik o'rnatadi —
    endi BotFather'da qo'lda o'zgartirish shart emas."""
    try:
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Ochish", web_app=WebAppInfo(url=WEBAPP_URL))
        )
        logging.info("Menu button o'rnatildi: %s", WEBAPP_URL)
    except Exception as e:
        logging.warning("Menu button o'rnatilmadi: %s", e)
    try:
        await start_web_server(application)
    except Exception as e:
        logging.warning("Notify server ishga tushmadi: %s", e)


app = Application.builder().token(TOKEN).post_init(set_menu_button).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
app.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.Chat(ADMIN_CHAT_ID), handle_admin_reply))

app.run_polling()
