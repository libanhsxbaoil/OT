from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import re, os

user_hours = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Xin chào! Gửi cho tôi số giờ làm thêm (VD: 2.5 hoặc 1h30m). Gõ /tong để xem tổng.")

async def add_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id

    match = re.match(r"(\d+(?:\.\d+)?)h?(\d*)m?", text)
    if not match:
        await update.message.reply_text("Vui lòng nhập đúng định dạng (VD: 2.5 hoặc 1h30m).")
        return

    hours = float(match.group(1))
    minutes = match.group(2)
    if minutes:
        hours += float(minutes) / 60

    user_hours[user_id] = user_hours.get(user_id, 0) + hours
    await update.message.reply_text(f"✅ Đã cộng {hours:.2f} giờ. Tổng hiện tại: {user_hours[user_id]:.2f} giờ.")

async def total_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    total = user_hours.get(user_id, 0)
    await update.message.reply_text(f"⏱ Tổng giờ làm thêm của bạn: {total:.2f} giờ.")

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tong", total_hours))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_hours))

    print("🤖 Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()
