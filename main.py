import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
from database import init_db, add_user, get_points, update_points, get_channels, add_channel, remove_channel
import uuid

# ================= إعدادات البوت =================
BOT_TOKEN = "8618553459:AAHvI3KKWYfCkwKVlocJR5eOGdZvpj_sRTw"
ADMIN_ID = 6306620747
CONTACT_USER = "Ezzt00"
MAIN_CHANNEL = "@Ezzat_Hackk"  # قناتك الأساسية
# =================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def check_subscriptions(user_id):
    channels = [MAIN_CHANNEL] + get_channels()
    not_joined = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ['left', 'kicked']:
                not_joined.append(ch)
        except Exception:
            pass 
    return not_joined

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 طلب دعم لقناتي (تمويل)", callback_data="order_support")],
        [InlineKeyboardButton(text="👤 حسابي", callback_data="my_account"), InlineKeyboardButton(text="🔗 الإحالة", callback_data="referral")],
        [InlineKeyboardButton(text="⭐ شراء بالنجوم (تلقائي)", callback_data="buy_stars")],
        [InlineKeyboardButton(text="💳 شراء يدوي (تواصل)", url=f"https://t.me/{CONTACT_USER}")]
    ])

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    not_joined = await check_subscriptions(user_id)
    if not_joined:
        buttons = [[InlineKeyboardButton(text=f"اشترك في القناة 📢", url=f"https://t.me/{ch.replace('@', '')}")] for ch in not_joined]
        buttons.append([InlineKeyboardButton(text="✅ تحقق من الاشتراك", callback_data="check_join")])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("عذراً، يجب عليك الاشتراك في القنوات التالية لتتمكن من استخدام البوت:", reply_markup=markup)
        return

    if add_user(user_id, referrer_id) and referrer_id and referrer_id != user_id:
        update_points(referrer_id, 50)
        try:
            await bot.send_message(referrer_id, "🎉 عضو جديد دخل عبر رابطك! حصلت على 50 نقطة.")
        except:
            pass

    welcome_text = (
        "مرحباً بك في أضخم منصة لدعم وتمويل القنوات! 🚀\n"
        "اجمع النقاط، ضاعف أرقامك، وارفع قناتك الآن بعقلية القمة."
    )
    await message.answer(welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
    user_id = call.from_user.id
    
    not_joined = await check_subscriptions(user_id)
    if not_joined and call.data != "check_join":
        await call.answer("يجب البقاء في القنوات لاستخدام البوت!", show_alert=True)
        return

    if call.data == "check_join":
        await call.message.delete()
        await start_cmd(call.message)

    elif call.data == "my_account":
        points = get_points(user_id)
        await call.message.edit_text(f"👤 **معلومات حسابك:**\n\n- آي دي: `{user_id}`\n- الرصيد: **{points}** نقطة 🪙", reply_markup=main_menu(), parse_mode="Markdown")

    elif call.data == "referral":
        bot_info = await bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={user_id}"
        await call.message.edit_text(f"🔗 **رابط الإحالة:**\n{link}\n\nاحصل على 50 نقطة لكل شخص يشترك عبرك!", reply_markup=main_menu())

    elif call.data == "buy_stars":
        prices = [LabeledPrice(label="1000 نقطة", amount=50)] 
        await bot.send_invoice(user_id, "1000 نقطة 🪙", "شحن رصيد البوت", "buy_1000", "", "XTR", prices)

    elif call.data == "order_support":
        await call.answer("سيتم فتح قسم الطلبات قريباً! اجمع النقاط الآن.", show_alert=True)

@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    update_points(message.from_user.id, 1000)
    await message.answer("✅ تم الشراء بنجاح! أضيفت 1000 نقطة لرصيدك.")

# ================= لوحة الإدارة المخفية =================
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة قناة إجبارية للمعلنين", callback_data="admin_add_ch")],
        [InlineKeyboardButton(text="💰 شحن نقاط لمستخدم", callback_data="admin_add_pts")]
    ])
    await message.answer("👑 **لوحة تحكم الإدارة**:\n\n*ملاحظة:* قناتك الأساسية مضافة تلقائياً.", reply_markup=markup, parse_mode="Markdown")

@dp.message(Command("add_ch"))
async def add_ch_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        ch = message.text.split()[1] if len(message.text.split()) > 1 else None
        if ch:
            add_channel(ch)
            await message.answer(f"✅ تم إضافة {ch} للاشتراك الإجباري.")

@dp.message(Command("add_points"))
async def add_pts_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            _, uid, pts = message.text.split()
            update_points(int(uid), int(pts))
            await message.answer(f"✅ تم شحن {pts} نقطة للمستخدم {uid}.")
            await bot.send_message(int(uid), f"🎁 الإدارة أرسلت لك {pts} نقطة!")
        except:
            await message.answer("⚠️ الطريقة: /add_points ID POINTS")

async def main():
    init_db()
    print("🚀 البوت يعمل الآن...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
