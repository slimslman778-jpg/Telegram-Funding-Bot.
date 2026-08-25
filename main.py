import asyncio
import uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (init_db, add_user, get_points, update_points, 
                      get_channels, add_channel, create_gift_db, redeem_gift_db, 
                      add_order, get_active_order, get_order_link_db, complete_task, skip_order_db)

# ================= إعدادات البوت =================
BOT_TOKEN = "8618553459:AAHvI3KKWYfCkwKVlocJR5eOGdZvpj_sRTw"
ADMIN_ID = 6306620747
CONTACT_USER = "Ezzt00"
MAIN_CHANNEL = "@Ezzat_Hackk"
# =================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class OrderState(StatesGroup):
    waiting_for_link = State()
    waiting_for_count = State()

class GiftState(StatesGroup):
    waiting_for_points = State()
    waiting_for_uses = State()

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
        [InlineKeyboardButton(text="➕ تجميع النقاط (انضم واربح)", callback_data="earn_points")],
        [InlineKeyboardButton(text="🛒 طلب تمويل لقناتي (تلقائي)", callback_data="order_support")],
        [InlineKeyboardButton(text="👤 حسابي", callback_data="my_account"), InlineKeyboardButton(text="🔗 الإحالة", callback_data="referral")],
        [InlineKeyboardButton(text="⭐ شراء بالنجوم (تلقائي)", callback_data="buy_stars")],
        [InlineKeyboardButton(text="💡 تعليمات البوت", callback_data="help_info"), InlineKeyboardButton(text="📞 التواصل مع الإدارة", url=f"https://t.me/{CONTACT_USER}")]
    ])

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    payload = args[1] if len(args) > 1 else None
    
    referrer_id = None
    gift_code = None
    if payload:
        if payload.startswith("gift_"):
            gift_code = payload
        elif payload.isdigit():
            referrer_id = int(payload)

    not_joined = await check_subscriptions(user_id)
    if not_joined:
        buttons = [[InlineKeyboardButton(text=f"اشترك في القناة 📢", url=f"https://t.me/{ch.replace('@', '')}")] for ch in not_joined]
        buttons.append([InlineKeyboardButton(text="✅ تحقق من الاشتراك", callback_data="check_join")])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("عذراً، يجب عليك الاشتراك في القنوات التالية أولاً:\n*(إذا استخدمت رابط هدية، اضغط عليه مجدداً بعد الاشتراك)*", reply_markup=markup, parse_mode="Markdown")
        return

    # الإحالة أصبحت 1500 نقطة
    if add_user(user_id, referrer_id) and referrer_id and referrer_id != user_id:
        update_points(referrer_id, 1500)
        try:
            await bot.send_message(referrer_id, "🎉 عضو جديد دخل عبر رابطك! حصلت على 1500 نقطة.")
        except: pass

    if gift_code:
        res = redeem_gift_db(user_id, gift_code)
        if type(res) == int:
            await message.answer(f"🎁 مبروك! حصلت على {res} نقطة من رابط الهدية.")
        else:
            await message.answer("⚠️ الرابط مستخدم أو منتهي الصلاحية.")

    welcome_text = "مرحباً بك في أضخم منصة لدعم وتمويل القنوات! 🚀\nاجمع النقاط، ضاعف أرقامك، وارفع قناتك الآن بعقلية القمة."
    await message.answer(welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query()
async def callbacks(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    not_joined = await check_subscriptions(user_id)
    
    if not_joined and not call.data.startswith("verify_order") and call.data != "check_join":
        await call.answer("يجب البقاء في القنوات الإجبارية لاستخدام البوت!", show_alert=True)
        return

    if call.data == "check_join":
        await call.message.delete()
        await bot.send_message(user_id, "مرحباً بك مجدداً! 🚀", reply_markup=main_menu())

    elif call.data == "my_account":
        points = get_points(user_id)
        await call.message.edit_text(f"👤 **معلومات حسابك:**\n\n- آي دي: `{user_id}`\n- الرصيد: **{points}** نقطة 🪙", reply_markup=main_menu(), parse_mode="Markdown")

    elif call.data == "referral":
        bot_info = await bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={user_id}"
        await call.message.edit_text(f"🔗 **رابط الإحالة:**\n{link}\n\nاحصل على **1500 نقطة** لكل شخص يشترك عبرك!", reply_markup=main_menu(), parse_mode="Markdown")

    elif call.data == "help_info":
        help_text = (
            "💡 **تعليمات استخدام البوت:**\n\n"
            "1️⃣ **كيف أجمع النقاط؟**\n"
            "اضغط على زر 'تجميع النقاط'، اشترك في القنوات المعروضة واضغط تحقق لتربح النقاط. أو شارك رابط الإحالة لتربح 1500 نقطة.\n\n"
            "2️⃣ **كيف أمول قناتي؟**\n"
            "اضغط 'طلب تمويل لقناتي'، أدخل معرف قناتك العام (يجب أن يبدأ بـ @)، وحدد العدد المطلوب (تكلفة العضو 30 نقطة). البوت سيضيف قناتك في قسم التجميع وسيدخل الأعضاء تلقائياً!\n\n"
            "3️⃣ **هل الأعضاء حقيقيون؟**\n"
            "نعم 100%! الأعضاء هم مستخدمون آخرون للبوت يبحثون عن النقاط مثلما تفعل أنت."
        )
        await call.message.edit_text(help_text, reply_markup=main_menu(), parse_mode="Markdown")

    # ========= نظام التبادل التلقائي =========
    elif call.data == "earn_points":
        order = get_active_order(user_id)
        if not order:
            await call.message.edit_text("لا توجد قنوات متاحة حالياً للتمويل. عد لاحقاً أو قم بدعوة أصدقائك!", reply_markup=main_menu())
            return
        
        order_id, link = order
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 انضم للقناة الآن", url=link)],
            [InlineKeyboardButton(text="✅ تحقق من الانضمام (15+ نقطة)", callback_data=f"verify_order_{order_id}")],
            [InlineKeyboardButton(text="⏭️ تخطي هذه القناة", callback_data=f"skip_order_{order_id}")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="cancel")]
        ])
        await call.message.edit_text(f"➕ **تجميع النقاط:**\n\nاشترك في هذه القناة للحصول على 15 نقطة:\n{link}", reply_markup=markup)

    elif call.data.startswith("verify_order_"):
        order_id = int(call.data.split("_")[2])
        order_link = get_order_link_db(order_id)
        
        username = None
        if "t.me/" in order_link:
            username = "@" + order_link.split("t.me/")[1].split("/")[0].split("?")[0]
        elif order_link.startswith("@"):
            username = order_link
            
        if not username:
            skip_order_db(user_id, order_id)
            await call.answer("تم تخطي الرابط بسبب خطأ في صيغته.", show_alert=True)
            await callbacks(types.CallbackQuery(id=call.id, from_user=call.from_user, data="earn_points", message=call.message), state)
            return
            
        try:
            member = await bot.get_chat_member(username, user_id)
            if member.status in ['member', 'administrator', 'creator']:
                if complete_task(user_id, order_id):
                    await call.answer("✅ تم التحقق! حصلت على 15 نقطة.", show_alert=True)
                await callbacks(types.CallbackQuery(id=call.id, from_user=call.from_user, data="earn_points", message=call.message), state)
            else:
                await call.answer("⚠️ لم تشترك في القناة بعد! اشترك ثم اضغط تحقق.", show_alert=True)
        except Exception:
            await call.answer("عذراً، البوت لا يمكنه التحقق. تم تخطي القناة.", show_alert=True)
            skip_order_db(user_id, order_id)
            await callbacks(types.CallbackQuery(id=call.id, from_user=call.from_user, data="earn_points", message=call.message), state)

    elif call.data.startswith("skip_order_"):
        order_id = int(call.data.split("_")[2])
        skip_order_db(user_id, order_id)
        await call.answer("تم تخطي القناة.")
        await callbacks(types.CallbackQuery(id=call.id, from_user=call.from_user, data="earn_points", message=call.message), state)
    # =========================================

    elif call.data == "buy_stars":
        prices = [LabeledPrice(label="1000 نقطة", amount=50)] 
        await bot.send_invoice(user_id, "1000 نقطة 🪙", "شحن رصيد البوت", "buy_1000", "", "XTR", prices)

    elif call.data == "order_support":
        await call.message.answer("🔗 أرسل الآن معرف قناتك (يجب أن تكون عامة وتبدأ بـ @)\nمثال: `@Ezzat_Hackk`", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel")]]))
        await state.set_state(OrderState.waiting_for_link)
        await call.answer()

    elif call.data == "admin_gift":
        if user_id != ADMIN_ID: return
        await call.message.answer("🎁 النقاط لكل شخص؟ (رقم)", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel")]]))
        await state.set_state(GiftState.waiting_for_points)
        await call.answer()

    elif call.data == "admin_add_ch":
        if user_id != ADMIN_ID: return
        await call.message.answer("لإضافة قناة أرسل:\n`/add_ch @Username`", parse_mode="Markdown")
        await call.answer()

    elif call.data == "admin_add_pts":
        if user_id != ADMIN_ID: return
        await call.message.answer("لشحن نقاط أرسل:\n`/add_points ID POINTS`", parse_mode="Markdown")
        await call.answer()

    elif call.data == "cancel":
        await state.clear()
        await call.message.edit_text("🔙 عدنا للقائمة الرئيسية.", reply_markup=main_menu())

@dp.message(OrderState.waiting_for_link)
async def order_get_link(message: types.Message, state: FSMContext):
    link = message.text
    if not link.startswith("@") and "t.me/" not in link:
        await message.answer("⚠️ يرجى إرسال معرف صحيح يبدأ بـ @")
        return
    await state.update_data(link=link)
    await message.answer("🔢 كم عدد الأعضاء المطلوب؟ (كل 1 عضو = 30 نقطة)\nأرسل رقماً فقط:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel")]]))
    await state.set_state(OrderState.waiting_for_count)

@dp.message(OrderState.waiting_for_count)
async def order_get_count(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    count = int(message.text)
    cost = count * 30  # التكلفة الجديدة 30 نقطة للعضو
    
    user_id = message.from_user.id
    pts = get_points(user_id)
    if pts < cost:
        await message.answer(f"❌ رصيدك غير كافٍ.\nرصيدك: {pts}\nالتكلفة: {cost} نقطة", reply_markup=main_menu())
        await state.clear()
        return
        
    data = await state.get_data()
    link = data['link']
    
    update_points(user_id, -cost)
    add_order(user_id, link, count, cost)
    
    await message.answer(f"✅ تم استلام طلبك بنجاح!\n🔗 القناة: {link}\n👥 العدد: {count}\n💰 التكلفة: {cost} نقطة.\n\nسيبدأ البوت بإضافة الأعضاء تلقائياً عبر قسم التجميع.", reply_markup=main_menu())
    await state.clear()

@dp.message(GiftState.waiting_for_points)
async def admin_gift_pts(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    await state.update_data(points=int(message.text))
    await message.answer("👥 أقصى عدد لاستخدام الرابط؟ (رقم فقط)")
    await state.set_state(GiftState.waiting_for_uses)
    
@dp.message(GiftState.waiting_for_uses)
async def admin_gift_uses(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    uses = int(message.text)
    data = await state.get_data()
    points = data['points']
    
    code = "gift_" + str(uuid.uuid4().hex)[:8]
    create_gift_db(code, points, uses)
    
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={code}"
    
    await message.answer(f"✅ تم إنشاء رابط الهدية!\n`{link}`\n💰 النقاط: {points} | 👥 العدد: {uses}", parse_mode="Markdown")
    await state.clear()

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 إنشاء رابط هدية", callback_data="admin_gift")],
        [InlineKeyboardButton(text="➕ قناة إجبارية", callback_data="admin_add_ch"), InlineKeyboardButton(text="💰 شحن نقاط", callback_data="admin_add_pts")]
    ])
    await message.answer("👑 **لوحة الإدارة**:", reply_markup=markup, parse_mode="Markdown")

@dp.message(Command("add_ch"))
async def add_ch_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        ch = message.text.split()[1] if len(message.text.split()) > 1 else None
        if ch:
            add_channel(ch)
            await message.answer(f"✅ تم إضافة {ch}")

@dp.message(Command("add_points"))
async def add_pts_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            _, uid, pts = message.text.split()
            update_points(int(uid), int(pts))
            await message.answer(f"✅ تم شحن {pts} نقطة.")
            await bot.send_message(int(uid), f"🎁 الإدارة أرسلت لك {pts} نقطة!")
        except: pass

@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    update_points(message.from_user.id, 1000)
    await message.answer("✅ تم الشراء بنجاح! أضيفت 1000 نقطة.")

async def main():
    init_db()
    print("🚀 البوت يعمل الآن بكامل الميزات...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
