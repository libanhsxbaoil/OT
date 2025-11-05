import logging
import os  # Rất quan trọng để đọc biến môi trường
import redis # Thư viện mới để kết nối Redis
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Cấu hình ---

# Lấy thông tin từ Biến Môi trường (Environment Variables) của Render
TOKEN = os.environ.get("TELEGRAM_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")

if not TOKEN:
    raise ValueError("Chưa đặt biến TELEGRAM_TOKEN")
if not REDIS_URL:
    raise ValueError("Chưa đặt biến REDIS_URL")

# Tên của Hash trong Redis để lưu dữ liệu
REDIS_HASH_NAME = "overtime_data"

# Bật logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Kết nối Redis ---
try:
    # decode_responses=True giúp dữ liệu trả về từ Redis là string (thay vì bytes)
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    # Kiểm tra kết nối
    redis_client.ping()
    logger.info("Đã kết nối thành công đến Redis!")
except Exception as e:
    logger.error(f"Không thể kết nối đến Redis: {e}")
    # Nếu không kết nối được thì dừng bot
    exit()


# --- Các hàm xử lý lệnh (Command Handlers) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gửi tin nhắn chào mừng khi gõ /start."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Chào {user_name}!\n\n"
        "Tôi là Bot Tính Giờ Làm Thêm (phiên bản Render + Redis).\n\n"
        "• `/add <số giờ>` - Để cộng giờ (ví dụ: `/add 2.5`)\n"
        "• `/total` - Để xem tổng số giờ\n"
        "• `/reset` - Để xoá tổng giờ về 0"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cộng thêm giờ làm thêm cho người dùng (lưu vào Redis Hash)."""
    user_id = str(update.effective_user.id)
    
    try:
        hours_to_add = float(context.args[0])

        if hours_to_add <= 0:
            await update.message.reply_text("🚫 Vui lòng nhập số giờ lớn hơn 0.")
            return

        # Tự động cộng dồn giá trị float vào key (user_id) trong Hash
        # Nếu user_id chưa có, nó sẽ tự tạo và cộng
        new_total = redis_client.hincrbyfloat(REDIS_HASH_NAME, user_id, hours_to_add)

        await update.message.reply_text(
            f"✅ Đã thêm {hours_to_add} giờ.\n"
            f"Tổng giờ làm thêm của bạn hiện là: **{new_total:.2f} giờ**."
        )

    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Cú pháp sai! Vui lòng gõ: `/add <số giờ>`\nVí dụ: `/add 2.5`")
    except Exception as e:
        logger.error(f"Lỗi khi /add: {e}")
        await update.message.reply_text("Đã có lỗi xảy ra, vui lòng thử lại.")

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hiển thị tổng giờ làm thêm của người dùng từ Redis."""
    user_id = str(update.effective_user.id)
    
    # Lấy giá trị của key (user_id) từ trong Hash
    current_total_str = redis_client.hget(REDIS_HASH_NAME, user_id)
    
    # Nếu hget không tìm thấy (user chưa add lần nào), nó trả về None
    if current_total_str:
        current_total = float(current_total_str)
        await update.message.reply_text(f"📊 Tổng giờ làm thêm của bạn là: **{current_total:.2f} giờ**.")
    else:
        await update.message.reply_text("📊 Bạn chưa có giờ làm thêm nào (tổng là 0 giờ).")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset tổng giờ làm thêm của người dùng về 0 (Xoá key khỏi Hash)."""
    user_id = str(update.effective_user.id)
    
    # Xoá trường (field) user_id ra khỏi Hash
    # hdel trả về 1 nếu xoá thành công, 0 nếu không tìm thấy
    if redis_client.hdel(REDIS_HASH_NAME, user_id) > 0:
        await update.message.reply_text("♻️ Đã reset tổng giờ làm thêm của bạn về 0.")
    else:
        await update.message.reply_text("Bạn chưa có giờ làm thêm nào để reset.")

# --- Hàm Main để chạy Bot ---

def main():
    """Khởi động bot và lắng nghe các lệnh."""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("total", total))
    application.add_handler(CommandHandler("reset", reset))

    print("Bot đang chạy (kết nối với Redis)...")
    application.run_polling()

if __name__ == "__main__":
    main()
