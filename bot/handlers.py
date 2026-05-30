# bot/handlers.py
import datetime
import asyncio
import random
from bson import ObjectId
from aiogram import types, F
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramRetryAfter

from config import (
    dp, bot, db, pyro_app, OWNER_ID, CHANNEL_ID, ADMIN_PASS,
    BOT_USERNAME, DB_CHANNEL_ID, TUTORIAL_LINK, REQUEST_LINK, APP_URL,
    admin_cache, banned_cache, auto_reply_cache, keyword_replies_cache,
    video_queue, clear_app_cache, load_keyword_replies
)
from helpers import make_wide_thumbnail

# এআই অ্যাসিস্ট্যান্ট ইম্পোর্ট ও ব্যাকআপ লজিক
try:
    from assistant.ai_reply import get_smart_reply
except ImportError:
    async def get_smart_reply(text, name, db, user_id):
        return f"হ্যালো {name}! আপনার মেসেজটি পেয়েছি। আমাদের টিম আপনার সাথে শীঘ্রই যোগাযোগ করবে।"

# অ্যাডমিন এফএসএম স্টেট ক্লাস
class AdminStates(StatesGroup):
    waiting_for_bcast = State()
    waiting_for_reply = State()
    waiting_for_photo = State()
    waiting_for_title = State()
    waiting_for_quality = State() 
    waiting_for_category = State()
    waiting_for_series_search = State()
    waiting_for_episode_quality = State()
    
    waiting_for_bulk_series_search = State()
    waiting_for_bulk_start_num = State()
    waiting_for_bulk_quality = State()
    waiting_for_bulk_files = State()

# ==========================================
# 🛑 PREMIUM START COMMAND WITH PROFILE CARD
# ==========================================
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    if uid in banned_cache: 
        return await message.answer("🚫 <b>আপনাকে ব্যান করা হয়েছে।</b>", parse_mode="HTML")
        
    await state.clear()
    now = datetime.datetime.utcnow()
    user = await db.users.find_one({"user_id": uid})
    
    # নতুন ইউজার রেজিস্ট্রেশন এবং রেফারেল হ্যান্ডলিং
    if not user:
        args = message.text.split(" ")
        if len(args) > 1 and args[1].startswith("ref_"):
            try:
                referrer_id = int(args[1].split("_")[1])
                if referrer_id != uid:
                    await db.users.update_one({"user_id": referrer_id}, {"$inc": {"refer_count": 1, "coins": 10}})
                    try: 
                        await bot.send_message(referrer_id, "🎉 <b>Congratulations!</b> You got <b>10 Points</b> for a new referral!", parse_mode="HTML")
                    except: pass
            except Exception: pass

        user_name = message.from_user.first_name or "User"
        user = {
            "user_id": uid, "first_name": user_name, "joined_at": now, "refer_count": 0, "coins": 0, "vip_until": now - datetime.timedelta(days=1), "last_active": now
        }
        await db.users.insert_one(user)
    else:
        await db.users.update_one({"user_id": uid}, {"$set": {"last_active": now}})
    
    # মেম্বারশিপ ও Gems এর ডাইনামিক স্ট্যাটাস
    is_vip = user.get("vip_until", now) > now
    coins = user.get("coins", 0)
    vip_status = "👑 Premium VIP" if is_vip else "⚡ Free User"
    
    # প্রিমিয়াম বাটন লেআউট
    kb = [
        [types.InlineKeyboardButton(text="🎬 Open Movie App (অ্যাপ খুলুন)", web_app=types.WebAppInfo(url=APP_URL))],
        [
            types.InlineKeyboardButton(text="কিভাবে ডাউনলোড করবেন ❓", url=TUTORIAL_LINK),
            types.InlineKeyboardButton(text="মুভি রিকোয়েস্ট ♻️", url=REQUEST_LINK)
        ],
        [types.InlineKeyboardButton(text="🎁 Refer & Earn (ফ্রি Gems)", callback_data="refer_info_start")]
    ]
    markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
    
    # ১৬:৯ রেশিওর ওয়েলকাম ইমেজের লিংক (আপনার ছবির লিংক বা ফাইল আইডি দিয়ে পরিবর্তন করতে পারেন)
    WELCOME_BANNER = "https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=1025&auto=format&fit=crop"

    if uid in admin_cache:
        # অ্যাডমিনদের জন্য মেসেজ
        text = (
            "👋 <b>হ্যালো অ্যাডমিন!</b>\n\n"
            "⚙️ <b>কমান্ড লিস্ট:</b>\n"
            "🔸 অটো আপলোড: <code>/autoupload on/off</code>\n"
            "🔸 অ্যাডমিন প্যানেল: <code>/addadmin ID</code> | <code>/deladmin ID</code> | <code>/adminlist</code>\n"
            "🔸 ডাইরেক্ট লিংক: <code>/addlink লিংক</code> | <code>/dellink লিংক</code> | <code>/seelinks</code>\n"
            "🔸 সাপোর্ট লিংক: <code>/setsupport লিংক</code>\n"
            "🔸 পেমেন্ট নাম্বার: <code>/setbkash নাম্বার</code> | <code>/setnagad নাম্বার</code>\n"
            "🔸 প্রোটেকশন: <code>/protect on/off</code> | অটো-ডিলিট: <code>/settime [মিনিট]</code>\n"
            "🔸 অ্যাড টাইম: <code>/setadtime [সেকেন্ড]</code>\n" 
            "🔸 স্ট্যাটাস: <code>/stats</code> | ব্রডকাস্ট: <code>/cast</code>\n"
            "🔸 মুভি ডিলিট: <code>/delmovie মুভির নাম</code> | <code>/delallmovies</code>\n"
            "🔸 ব্যান: <code>/ban ID</code> | আনব্যান: <code>/unban ID</code>\n"
            "🔸 VIP দিন: <code>/addvip ID দিন</code> | VIP বাতিল: <code>/removevip ID</code>\n"
            "🔸 পয়েন্ট দিন: <code>/addcoin ID পরিমাণ</code> | পয়েন্ট কাটুন: <code>/removecoin ID পরিমাণ</code>\n\n"
            f"🌐 <b>ওয়েব অ্যাডমিন প্যানেল:</b> <a href='{APP_URL}/admin'>এখানে ক্লিক করুন</a>\n"
            "<i>লগিন: admin / admin123</i>\n\n"
            "📥 <b>মুভি অ্যাড করতে প্রথমে ভিডিও বা ডকুমেন্ট ফাইল পাঠান।</b>"
        )
        try:
            await message.answer_photo(photo=WELCOME_BANNER, caption=text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            await message.answer(text, reply_markup=markup, parse_mode="HTML")
    else:
        # সাধারণ ইউজারদের জন্য প্রিমিয়াম ডাইনামিক প্রোফাইল মেসেজ
        user_name = message.from_user.first_name or "User"
        text = (
            f"👋 <b>Welcome, {user_name}!</b>\n"
            f"আমাদের মুভি ও ওয়েব সিরিজ মিনি-অ্যাপ বটে আপনাকে স্বাগতম।\n\n"
            f"📊 <b>আপনার প্রোফাইল তথ্য:</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>নাম:</b> {user_name}\n"
            f"🆔 <b>ইউজার আইডি:</b> <code>{uid}</code>\n"
            f"💎 <b>আপনার Gems:</b> <code>{coins} Gems</code>\n"
            f"👑 <b>মেম্বারশিপ:</b> <b>{vip_status}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"🍿 <i>নিচের বাটনে ক্লিক করে সরাসরি আমাদের মিনি-অ্যাপ থেকে ১ ক্লিকে হাই-স্পিডে মুভি এবং ওয়েব সিরিজ ডাউনলোড করুন বা সরাসরি বটেই প্লে করুন!</i>"
        )
        try:
            await message.answer_photo(photo=WELCOME_BANNER, caption=text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            await message.answer(text, reply_markup=markup, parse_mode="HTML")

# রেফারেল বাটন ইনফো হ্যান্ডলার
@dp.callback_query(F.data == "refer_info_start")
async def refer_info_start_cb(c: types.CallbackQuery):
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{c.from_user.id}"
    text = (
        "🎁 <b>Refer & Earn (ফ্রি Gems সংগ্রহ করুন):</b>\n\n"
        "আপনার বন্ধুদের সাথে নিচের লিংকটি শেয়ার করুন। আপনার লিংকে ক্লিক করে কেউ বটটি স্টার্ট করলেই আপনি পাবেন সম্পূর্ণ ফ্রিতে <b>১০ Gems</b>!\n\n"
        f"🔗 <b>আপনার ইনভাইট লিংক:</b>\n<code>{ref_link}</code>\n\n"
        "<i>পয়েন্ট জমিয়ে আপনি বিজ্ঞাপন ছাড়াই সরাসরি প্রিমিয়াম মেম্বারশিপ আনলক করতে পারবেন।</i>"
    )
    await c.message.answer(text, parse_mode="HTML")
    await c.answer()

# ==========================================
# 🛑 OTHER ADMIN COMMANDS
# ==========================================
@dp.message(Command("setadtime"))
async def set_ad_time(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        secs = int(m.text.split(" ")[1])
        await db.settings.update_one({"id": "ad_time"}, {"$set": {"seconds": secs}}, upsert=True)
        await m.answer(f"✅ অ্যাড ওয়েটিং টাইম <b>{secs} সেকেন্ড</b> সেট করা হয়েছে।", parse_mode="HTML")
    except Exception: 
        await m.answer("⚠️ সঠিক নিয়ম: <code>/setadtime ১৫</code>", parse_mode="HTML")

@dp.message(Command("autoupload"))
async def toggle_auto_upload(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        state = m.text.split(" ")[1].lower()
        await db.settings.update_one({"id": "auto_upload_mode"}, {"$set": {"status": state == "on"}}, upsert=True)
        await m.answer(f"✅ Auto Upload {'চালু' if state=='on' else 'বন্ধ'} করা হয়েছে।")
    except: pass

@dp.message(Command("addlink"))
async def add_direct_link(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        url = m.text.split(" ", 1)[1].strip()
        await db.settings.update_one({"id": "direct_links"}, {"$addToSet": {"links": url}}, upsert=True)
        await m.answer(f"✅ লিংক অ্যাড করা হয়েছে:\n<code>{url}</code>", parse_mode="HTML")
    except Exception: pass

@dp.message(Command("dellink"))
async def del_direct_link(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        url = m.text.split(" ", 1)[1].strip()
        await db.settings.update_one({"id": "direct_links"}, {"$pull": {"links": url}})
        await m.answer(f"❌ লিংকটি ডিলিট করা হয়েছে:\n<code>{url}</code>", parse_mode="HTML")
    except Exception: pass

@dp.message(Command("seelinks"))
async def see_direct_links(m: types.Message):
    if m.from_user.id not in admin_cache: return
    dl_cfg = await db.settings.find_one({"id": "direct_links"})
    links = dl_cfg.get("links", []) if dl_cfg else []
    if not links: return await m.answer("⚠️ কোনো ডাইরেক্ট লিংক নেই।")
    text = "🔗 <b>বর্তমান ডাইরেক্ট লিংক সমূহ:</b>\n\n"
    for i, link in enumerate(links, 1): text += f"{i}. <code>{link}</code>\n"
    await m.answer(text, parse_mode="HTML", disable_web_page_preview=True)

@dp.message(Command("setbkash"))
async def set_bkash(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        num = m.text.split(" ")[1]
        await db.settings.update_one({"id": "bkash_no"}, {"$set": {"number": num}}, upsert=True)
        await m.answer(f"✅ বিকাশ নাম্বার সেট করা হয়েছে: <b>{num}</b>", parse_mode="HTML")
    except Exception: pass

@dp.message(Command("setnagad"))
async def set_nagad(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        num = m.text.split(" ")[1]
        await db.settings.update_one({"id": "nagad_no"}, {"$set": {"number": num}}, upsert=True)
        await m.answer(f"✅ নগদ নাম্বার সেট করা হয়েছে: <b>{num}</b>", parse_mode="HTML")
    except Exception: pass

@dp.message(Command("settg"))
async def set_tg_link(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        link = m.text.split(" ")[1]
        await db.settings.update_one({"id": "link_tg"}, {"$set": {"url": link}}, upsert=True)
        await m.answer("✅ টেলিগ্রাম চ্যানেল লিংক আপডেট করা হয়েছে।")
    except Exception: pass

@dp.message(Command("setsupport"))
async def set_support_link(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        link = m.text.split(" ")[1]
        await db.settings.update_one({"id": "link_support"}, {"$set": {"url": link}}, upsert=True)
        await m.answer("✅ সাপোর্ট লিংক আপডেট করা হয়েছে।")
    except Exception: pass

@dp.message(Command("set18"))
async def set_18_link(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        link = m.text.split(" ")[1]
        await db.settings.update_one({"id": "link_18"}, {"$set": {"url": link}}, upsert=True)
        await m.answer("✅ 18+ লিংক আপডেট করা হয়েছে।")
    except Exception: pass

@dp.message(Command("protect"))
async def protect_cmd(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        state = m.text.split(" ")[1].lower()
        await db.settings.update_one({"id": "protect_content"}, {"$set": {"status": state == "on"}}, upsert=True)
        await m.answer(f"✅ ফরোয়ার্ড প্রোটেকশন {'চালু' if state=='on' else 'বন্ধ'} করা হয়েছে।")
    except Exception: pass

@dp.message(Command("settime"))
async def set_del_time(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        mins = int(m.text.split(" ")[1])
        await db.settings.update_one({"id": "del_time"}, {"$set": {"minutes": mins}}, upsert=True)
        await m.answer(f"✅ অটো-ডিলিট টাইম {mins} মিনিট সেট করা হয়েছে।")
    except Exception: pass

@dp.message(Command("delmovie"))
async def del_movie_cmd(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        title = m.text.split(" ", 1)[1].strip()
        result = await db.movies.delete_many({"title": title})
        if result.deleted_count > 0:
            clear_app_cache() 
            await m.answer(f"✅ '<b>{title}</b>' নামের {result.deleted_count} টি ফাইল ডিলিট হয়েছে!", parse_mode="HTML")
        else: await m.answer("⚠️ এই নামের কোনো মুভি পাওয়া যায়নি।")
    except Exception: await m.answer("⚠️ সঠিক নিয়ম: <code>/delmovie মুভির নাম</code>", parse_mode="HTML")

@dp.message(Command("delallmovies"))
async def del_all_movies_cmd(m: types.Message):
    if m.from_user.id not in admin_cache: return
    result = await db.movies.delete_many({})
    clear_app_cache()
    await m.answer(f"🗑 <b>সতর্কতা:</b> ডাটাবেস থেকে সর্বমোট <b>{result.deleted_count}</b> টি মুভি ডিলিট করা হয়েছে!", parse_mode="HTML")

@dp.message(Command("stats"))
async def stats_cmd(m: types.Message):
    if m.from_user.id not in admin_cache: return
    uc = await db.users.count_documents({})
    mc = await db.movies.count_documents({})
    now = datetime.datetime.utcnow()
    today_start = datetime.datetime(now.year, now.month, now.day)
    new_users_today = await db.users.count_documents({"joined_at": {"$gte": today_start}})
    
    text = (f"📊 <b>অ্যাডভান্সড স্ট্যাটাস:</b>\n\n👥 মোট ইউজার: <code>{uc}</code>\n🟢 আজকের নতুন ইউজার: <code>{new_users_today}</code>\n"
            f"🎬 মোট ফাইল আপলোড: <code>{mc}</code>")
    await m.answer(text, parse_mode="HTML")

@dp.message(Command("ban"))
async def ban_user_cmd(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        target_uid = int(m.text.split()[1])
        if target_uid in admin_cache: return await m.answer("⚠️ অ্যাডমিনকে ব্যান করা যাবে না!")
        await db.banned.update_one({"user_id": target_uid}, {"$set": {"user_id": target_uid}}, upsert=True)
        banned_cache.add(target_uid)
        await m.answer(f"🚫 ইউজার <code>{target_uid}</code> কে ব্যান করা হয়েছে!", parse_mode="HTML")
    except Exception: pass

@dp.message(Command("unban"))
async def unban_user_cmd(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        target_uid = int(m.text.split()[1])
        await db.banned.delete_one({"user_id": target_uid})
        banned_cache.discard(target_uid)
        await m.answer(f"✅ ইউজার <code>{target_uid}</code> আনব্যান হয়েছে!", parse_mode="HTML")
    except Exception: pass

@dp.message(Command("addadmin"))
async def add_admin_cmd(m: types.Message):
    if m.from_user.id != OWNER_ID: return await m.answer("⚠️ শুধুমাত্র মেইন Owner অ্যাডমিন অ্যাড করতে পারবে!")
    try:
        target_uid = int(m.text.split()[1])
        await db.admins.update_one({"user_id": target_uid}, {"$set": {"user_id": target_uid}}, upsert=True)
        admin_cache.add(target_uid)
        await m.answer(f"✅ ইউজার <code>{target_uid}</code> কে অ্যাডমিন বানানো হয়েছে!", parse_mode="HTML")
    except Exception: pass

@dp.message(Command("deladmin"))
async def del_admin_cmd(m: types.Message):
    if m.from_user.id != OWNER_ID: return await m.answer("⚠️ শুধুমাত্র Owner অ্যাডমিন রিমুভ করতে পারবে!")
    try:
        target_uid = int(m.text.split()[1])
        if target_uid == OWNER_ID: return await m.answer("⚠️ Main Owner কে ডিলিট করা সম্ভব নয়!")
        await db.admins.delete_one({"user_id": target_uid})
        admin_cache.discard(target_uid)
        await m.answer(f"❌ ইউজার <code>{target_uid}</code> রিমুভ করা হয়েছে!", parse_mode="HTML")
    except Exception: pass

@dp.message(Command("adminlist"))
async def list_admin_cmd(m: types.Message):
    if m.from_user.id not in admin_cache: return
    text = f"👑 <b>Owner:</b> <code>{OWNER_ID}</code>\n\n👮‍♂️ <b>Admins:</b>\n"
    async for a in db.admins.find(): text += f"▪️ <code>{a['user_id']}</code>\n"
    await m.answer(text, parse_mode="HTML")

@dp.message(Command("addvip"))
async def add_vip_cmd(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        args = m.text.split()
        target_uid = int(args[1])
        days = int(args[2]) if len(args) > 2 else 30 
        now = datetime.datetime.utcnow()
        user = await db.users.find_one({"user_id": target_uid})
        if not user: return await m.answer("⚠️ ইউজার ডাটাবেসে নেই।")
        current_vip = user.get("vip_until", now)
        if current_vip < now: current_vip = now
        await db.users.update_one({"user_id": target_uid}, {"$set": {"vip_until": current_vip + datetime.timedelta(days=days)}})
        await m.answer(f"✅ <code>{target_uid}</code> কে <b>{days} দিনের</b> VIP দেওয়া হয়েছে!", parse_mode="HTML")
    except Exception: pass

@dp.message(Command("removevip"))
async def remove_vip_cmd(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        target_uid = int(m.text.split()[1])
        now = datetime.datetime.utcnow()
        await db.users.update_one({"user_id": target_uid}, {"$set": {"vip_until": now - datetime.timedelta(days=1)}})
        await m.answer(f"❌ VIP বাতিল করা হয়েছে!", parse_mode="HTML")
    except Exception: pass

@dp.message(Command("addcoin"))
async def add_coin_cmd(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        args = m.text.split()
        target_uid = int(args[1])
        amount = int(args[2])
        
        user = await db.users.find_one({"user_id": target_uid})
        if not user: return await m.answer("⚠️ এই ইউজার ডাটাবেসে নেই।")
            
        await db.users.update_one({"user_id": target_uid}, {"$inc": {"coins": amount}})
        await m.answer(f"✅ ইউজার <code>{target_uid}</code> কে <b>{amount} পয়েন্ট</b> দেওয়া হয়েছে!", parse_mode="HTML")
        
        try:
            await bot.send_message(target_uid, f"🎉 <b>Congratulations!</b>\nআপনি অ্যাডমিনের কাছ থেকে <b>{amount} Points</b> পেয়েছেন! এখন আপনি Premium বা Ad Campaign শুরু করতে পারেন।", parse_mode="HTML")
        except: pass
    except Exception: 
        await m.answer("⚠️ সঠিক নিয়ম: <code>/addcoin UserID পরিমাণ</code>\n(যেমন: <code>/addcoin 123456789 500</code>)", parse_mode="HTML")

@dp.message(Command("removecoin"))
async def remove_coin_cmd(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        args = m.text.split()
        target_uid = int(args[1])
        amount = int(args[2])
        
        user = await db.users.find_one({"user_id": target_uid})
        if not user: return await m.answer("⚠️ এই ইউজার ডাটাবেসে নেই।")
            
        await db.users.update_one({"user_id": target_uid}, {"$inc": {"coins": -amount}})
        await m.answer(f"❌ ইউজার <code>{target_uid}</code> থেকে <b>{amount} পয়েন্ট</b> কেটে নেওয়া হয়েছে!", parse_mode="HTML")
    except Exception: 
        await m.answer("⚠️ সঠিক নিয়ম: <code>/removecoin UserID পরিমাণ</code>", parse_mode="HTML")

@dp.message(Command("cast"))
async def broadcast_prep(m: types.Message, state: FSMContext):
    if m.from_user.id not in admin_cache: return
    await state.set_state(AdminStates.waiting_for_bcast)
    await m.answer("📢 যে মেসেজটি ব্রডকাস্ট করতে চান সেটি পাঠান।\nবাতিল করতে /start দিন।")

@dp.message(AdminStates.waiting_for_bcast)
async def execute_broadcast(m: types.Message, state: FSMContext):
    await state.clear()
    await m.answer("⏳ ব্রডকাস্ট শুরু হয়েছে...")
    kb = [[types.InlineKeyboardButton(text="🎬 ওপেন মুভি অ্যাপ", web_app=types.WebAppInfo(url=APP_URL))]]
    markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
    success = 0
    async for u in db.users.find():
        try:
            await m.copy_to(chat_id=u['user_id'], reply_markup=markup)
            success += 1
            await asyncio.sleep(0.05)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await m.copy_to(chat_id=u['user_id'], reply_markup=markup)
                success += 1
            except Exception: pass
        except Exception: pass
    await m.answer(f"✅ সম্পন্ন! সর্বমোট <b>{success}</b> জনকে মেসেজ পাঠানো হয়েছে।", parse_mode="HTML")

@dp.message(Command("addreply"))
async def add_keyword_reply(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        args = m.text.split(" ", 1)[1]
        keyword, reply_msg = [x.strip() for x in args.split("|", 1)]
        keyword = keyword.lower()
        await db.keyword_replies.update_one({"keyword": keyword}, {"$set": {"keyword": keyword, "reply_message": reply_msg}}, upsert=True)
        await load_keyword_replies()
        await m.answer(f"✅ <b>{keyword}</b> এর জন্য ম্যানুয়াল রিপ্লাই সেট হয়েছে!", parse_mode="HTML")
    except Exception:
        await m.answer("⚠️ সঠিক নিয়ম: <code>/addreply কিওয়ার্ড | আপনার রিপ্লাই</code>\n(যেমন: <code>/addreply pushpa 2 | মুভিটি এখনো রিলিজ হয়নি।</code>)", parse_mode="HTML")

@dp.message(Command("delreply"))
async def del_keyword_reply(m: types.Message):
    if m.from_user.id not in admin_cache: return
    try:
        keyword = m.text.split(" ", 1)[1].strip().lower()
        res = await db.keyword_replies.delete_one({"keyword": keyword})
        if res.deleted_count > 0:
            await load_keyword_replies()
            await m.answer(f"✅ কিওয়ার্ড <b>{keyword}</b> ডিলিট করা হয়েছে!", parse_mode="HTML")
        else:
            await m.answer("⚠️ এই কিওয়ার্ড পাওয়া হয়নি।")
    except Exception:
        await m.answer("⚠️ সঠিক নিয়ম: <code>/delreply কিওয়ার্ড</code>", parse_mode="HTML")

# ==========================================
# 🛑 SMART AUTO-RESPONDER & ADMIN FORWARDING
# ==========================================
@dp.message(lambda m: m.chat.type == "private" and m.from_user.id not in admin_cache and (m.text is None or not m.text.startswith("/")))
async def forward_to_admin(m: types.Message):
    user_text = m.text.strip() if m.text else ""
    user_text_lower = user_text.lower()
    
    reply_text = ""
    is_manual_reply = False

    if user_text:
        for kw, rep_msg in keyword_replies_cache.items():
            if kw in user_text_lower:
                reply_text = rep_msg
                is_manual_reply = True
                break

    if not is_manual_reply:
        builder = InlineKeyboardBuilder()
        builder.button(text="✍️ রিপ্লাই দিন", callback_data=f"reply_{m.from_user.id}")
        markup = builder.as_markup()
        
        all_admins = set([OWNER_ID])
        async for a in db.admins.find(): all_admins.add(a["user_id"])
            
        for admin_id in all_admins:
            try:
                await bot.send_message(
                    admin_id, 
                    f"📩 <b>Message from <a href='tg://user?id={m.from_user.id}'>{m.from_user.first_name or 'User'}</b> (<code>{m.from_user.id}</code>):\n\n{m.text or '[Media/File]'}", 
                    parse_mode="HTML",
                    reply_markup=markup
                )
            except Exception: pass
        
        if m.from_user.id not in auto_reply_cache:
            auto_reply_cache[m.from_user.id] = True
            try:
                kb = [[types.InlineKeyboardButton(text="🎬 Watch Now (মুভি দেখুন)", web_app=types.WebAppInfo(url=APP_URL))]]
                user_markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
                
                if user_text:
                    try:
                        reply_text = await get_smart_reply(user_text, m.from_user.first_name or "User", db, user_id=m.from_user.id)
                    except Exception as ai_err:
                        reply_text = "হ্যালো! আপনার মেসেজটি আমরা পেয়েছি। আমাদের কোনো একজন অ্যাডমিন জলদি রিপ্লাই দেবেন।"
                else:
                    reply_text = "হ্যালো! আপনার মেসেজ/ফাইলটি অ্যাডমিনের কাছে পৌঁছে গেছে। প্রয়োজনে অ্যাডমিন আপনাকে রিপ্লাই দেবেন। ধন্যবাদ! ❤️"
                
                await m.reply(reply_text, reply_markup=user_markup, parse_mode="HTML")
            except Exception: pass
    else:
        if m.from_user.id not in auto_reply_cache:
            auto_reply_cache[m.from_user.id] = True
            try:
                kb = [[types.InlineKeyboardButton(text="🎬 Watch Now (মুভি দেখুন)", web_app=types.WebAppInfo(url=APP_URL))]]
                user_markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
                await m.reply(reply_text, reply_markup=user_markup, parse_mode="HTML")
                
                await db.messages.insert_one({
                    "user_id": str(m.from_user.id),
                    "text": user_text,
                    "reply": reply_text,
                    "timestamp": datetime.datetime.utcnow()
                })
            except Exception: pass

# ==========================================
# 🛑 MOVIE & EPISODE MANUAL UPLOAD LOGIC
# ==========================================
@dp.message(StateFilter(None), F.content_type.in_({'video', 'document'}), lambda m: m.from_user.id in admin_cache)
async def receive_movie_file(m: types.Message, state: FSMContext):
    config = await db.settings.find_one({"id": "auto_upload_mode"})
    is_auto = config["status"] if config else False
    
    if is_auto:
        aiogram_fid = m.video.file_id if m.video else m.document.file_id
        file_type = "video" if m.video else "document"
        await video_queue.put((m.chat.id, m.message_id, aiogram_fid, file_type))
        await m.answer(f"✅ ভিডিও অটো-প্রসেস কিউতে যুক্ত হয়েছে! সিরিয়াল: <b>{video_queue.qsize()}</b>", parse_mode="HTML")
    else:
        fid = m.video.file_id if m.video else m.document.file_id
        ftype = "video" if m.video else "document"
        
        db_file_id = None
        if DB_CHANNEL_ID:
            try:
                copied = await bot.copy_message(chat_id=DB_CHANNEL_ID, from_chat_id=m.chat.id, message_id=m.message_id)
                db_file_id = copied.message_id
            except Exception: pass
            
        await state.update_data(file_id=fid, file_type=ftype, db_file_id=db_file_id)
        
        kb = [
            [types.InlineKeyboardButton(text="🎬 নতুন মুভি/সিরিজ যুক্ত করুন", callback_data="upload_new")],
            [types.InlineKeyboardButton(text="➕ আগের সিরিজের নতুন এপিসোড", callback_data="upload_episode")]
        ]
        markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
        await m.answer("✅ ফাইল পেয়েছি! এটি কি নতুন কোনো মুভি নাকি আগের কোনো সিরিজের নতুন এপিসোড?", reply_markup=markup)

@dp.callback_query(F.data == "upload_new")
async def upload_new_cb(c: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_photo)
    await c.message.edit_text("✅ <b>নতুন মুভি/সিরিজ!</b>\nএবার মুভির <b>পোস্টার (Photo)</b> সেন্ড করুন।", parse_mode="HTML")

@dp.callback_query(F.data == "upload_episode")
async def upload_episode_cb(c: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_series_search)
    await c.message.edit_text("✅ <b>নতুন এপিসোড!</b>\n\nযে সিরিজে এড করতে চান, সেই <b>সিরিজের নামের কয়েক অক্ষর</b> লিখে রিপ্লাই দিন (যেমন: Farzi)।", parse_mode="HTML")

@dp.message(AdminStates.waiting_for_series_search, F.text)
async def search_series_for_episode(m: types.Message, state: FSMContext):
    query = m.text.strip()
    pipeline = [
        {"$match": {"title": {"$regex": query, "$options": "i"}}},
        {"$group": {"_id": "$title", "photo_id": {"$first": "$photo_id"}, "db_photo_id": {"$first": "$db_photo_id"}, "categories": {"$first": "$categories"}}},
        {"$limit": 10}
    ]
    results = await db.movies.aggregate(pipeline).to_list(10)

    if not results: return await m.answer("⚠️ এই নামে কোনো সিরিজ পাওয়া যায়নি! আবার সঠিক নাম লিখে পাঠান।")

    await state.update_data(search_results=results)
    
    builder = InlineKeyboardBuilder()
    for idx, res in enumerate(results): builder.button(text=f"📺 {res['_id']}", callback_data=f"sel_series_{idx}")
    builder.adjust(1)
    
    await m.answer("👇 নিচে থেকে আপনার কাঙ্ক্ষিত সিরিজটি সিলেক্ট করুন:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("sel_series_"))
async def selected_series_cb(c: types.CallbackQuery, state: FSMContext):
    idx = int(c.data.split("_")[2])
    data = await state.get_data()
    selected = data["search_results"][idx]

    await state.update_data(title=selected["_id"], photo_id=selected["photo_id"], db_photo_id=selected.get("db_photo_id"), categories=selected.get("categories", []))
    
    await state.set_state(AdminStates.waiting_for_episode_quality)
    await c.message.edit_text(f"✅ <b>{selected['_id']}</b> সিলেক্ট হয়েছে!\n\nএবার এই নতুন ফাইলের <b>এপিসোড নাম্বার বা কোয়ালিটি</b> লিখে পাঠান।", parse_mode="HTML")

@dp.message(AdminStates.waiting_for_episode_quality, F.text)
async def finalize_new_episode(m: types.Message, state: FSMContext):
    quality = m.text.strip()
    data = await state.get_data()
    title = data["title"]
    photo_id = data["photo_id"]
    categories = data.get("categories", [])
    
    await db.movies.insert_one({
        "title": title, "quality": quality, "photo_id": photo_id, 
        "file_id": data["file_id"], "file_type": data["file_type"],
        "db_file_id": data.get("db_file_id"), "db_photo_id": data.get("db_photo_id"),
        "categories": categories, "clicks": 0, "created_at": datetime.datetime.utcnow()
    })
    clear_app_cache() 
    
    await state.clear()
    await m.answer(f"🎉 <b>{title} [{quality}]</b> সফলভাবে সিরিজে এড করা সম্পূর্ণ হয়েছে!", parse_mode="HTML")

    if CHANNEL_ID:
        try:
            bot_info = await bot.get_me()
            kb = [
                [types.InlineKeyboardButton(text="📥 Download & Watch 🎬", url=f"https://t.me/{bot_info.username}?start=new")],
                [types.InlineKeyboardButton(text="কিভাবে ডাউনলোড করবেন ❓", url=TUTORIAL_LINK)],
                [types.InlineKeyboardButton(text="♻️ MOVIE REQUEST ♻️", url=REQUEST_LINK)]
            ]
            markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
            cat_display = ", ".join(categories) if categories else "N/A"
            caption = (f"🔥 <b>নতুন এপিসোড যুক্ত হয়েছে!</b>\n\n📌 <b>টাইটেল:</b> {title}\n🏷 <b>এপিসোড/কোয়ালিটি:</b> {quality}\n🎭 <b>ক্যাটাগরি:</b> {cat_display}\n\n👇 <i>বট থেকে ভিডিওটি পেতে নিচের বাটনে ক্লিক করুন।</i>")
            await bot.send_photo(chat_id=CHANNEL_ID, photo=photo_id, caption=caption, parse_mode="HTML", reply_markup=markup)
        except Exception: pass

# ==========================================
# 🛑 BULK UPLOAD MODULE FOR WEB SERIES
# ==========================================
@dp.message(Command("bulk"), lambda m: m.from_user.id in admin_cache)
async def init_bulk_upload_cmd(m: types.Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_bulk_series_search)
    await m.answer("📦 <b>Bulk এপিসোড আপলোড!</b>\n\nযে ওয়েব সিরিজে এপিসোডগুলো যোগ করতে চান, সেই সিরিজের নামের কয়েকটি অক্ষর লিখে সার্চ করুন (যেমন: Farzi)।", parse_mode="HTML")

@dp.message(AdminStates.waiting_for_bulk_series_search, F.text)
async def search_series_for_bulk(m: types.Message, state: FSMContext):
    query = m.text.strip()
    pipeline = [
        {"$match": {"title": {"$regex": query, "$options": "i"}}},
        {"$group": {"_id": "$title", "photo_id": {"$first": "$photo_id"}, "db_photo_id": {"$first": "$db_photo_id"}, "categories": {"$first": "$categories"}}},
        {"$limit": 10}
    ]
    results = await db.movies.aggregate(pipeline).to_list(10)

    if not results: 
        return await m.answer("⚠️ এই নামে কোনো সিরিজ পাওয়া যায়নি! আবার সঠিক নাম লিখে পাঠান।")

    await state.update_data(search_results=results)
    
    builder = InlineKeyboardBuilder()
    for idx, res in enumerate(results): 
        builder.button(text=f"📺 {res['_id']}", callback_data=f"sel_bulk_series_{idx}")
    builder.adjust(1)
    
    await m.answer("👇 নিচে থেকে আপনার কাঙ্ক্ষিত সিরিজটি সিলেক্ট করুন:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("sel_bulk_series_"))
async def selected_bulk_series_cb(c: types.CallbackQuery, state: FSMContext):
    idx = int(c.data.split("_")[3])
    data = await state.get_data()
    selected = data["search_results"][idx]

    await state.update_data(
        title=selected["_id"], 
        photo_id=selected["photo_id"], 
        db_photo_id=selected.get("db_photo_id"), 
        categories=selected.get("categories", []),
        bulk_files=[] 
    )
    
    await state.set_state(AdminStates.waiting_for_bulk_start_num)
    await c.message.edit_text(f"✅ <b>{selected['_id']}</b> সিলেক্ট হয়েছে!\n\nএবার শুরুর এপিসোড নাম্বারটি দিন (যেমন: 1 বা 5):", parse_mode="HTML")

@dp.message(AdminStates.waiting_for_bulk_start_num, F.text)
async def receive_bulk_start_num(m: types.Message, state: FSMContext):
    val = m.text.strip()
    if not val.isdigit():
        return await m.answer("⚠️ অনুগ্রহ করে শুধুমাত্র একটি সংখ্যা দিন (যেমন: 1 বা 5):")
    
    await state.update_data(start_num=int(val))
    await state.set_state(AdminStates.waiting_for_bulk_quality)
    await m.answer("✅ এবার এপিসোডগুলোর কমন কোয়ালিটি লিখে পাঠান (যেমন: 720p HD বা WebRip):")

@dp.message(AdminStates.waiting_for_bulk_quality, F.text)
async def receive_bulk_quality(m: types.Message, state: FSMContext):
    quality = m.text.strip()
    await state.update_data(quality=quality)
    await state.set_state(AdminStates.waiting_for_bulk_files)
    
    kb = [[types.InlineKeyboardButton(text="🚀 আপলোড সম্পন্ন করুন (Done)", callback_data="bulk_upload_done")]]
    markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
    
    await m.answer(
        f"✅ কোয়ালিটি সেভ হয়েছে!\n\n"
        f"এবার আপনার **১ম ফাইলসহ সবগুলো এপিসোড ফাইল একসাথে সিলেক্ট করে ফরওয়ার্ড বা সেন্ড করুন**।\n"
        f"সব ফাইল পাঠানো শেষ হলে নিচের <b>'Done'</b> বাটনে ক্লিক করুন।", 
        parse_mode="HTML", 
        reply_markup=markup
    )

@dp.message(AdminStates.waiting_for_bulk_files, F.content_type.in_({'video', 'document'}))
async def collect_bulk_files(m: types.Message, state: FSMContext):
    fid = m.video.file_id if m.video else m.document.file_id
    ftype = "video" if m.video else "document"
    
    db_file_id = None
    if DB_CHANNEL_ID:
        try:
            copied = await bot.copy_message(chat_id=DB_CHANNEL_ID, from_chat_id=m.chat.id, message_id=m.message_id)
            db_file_id = copied.message_id
        except Exception: pass
    
    data = await state.get_data()
    bulk_files = data.get("bulk_files", [])
    
    bulk_files.append({
        "file_id": fid,
        "file_type": ftype,
        "db_file_id": db_file_id
    })
    
    await state.update_data(bulk_files=bulk_files)
    
    kb = [[types.InlineKeyboardButton(text="🚀 আপলোড সম্পন্ন করুন (Done)", callback_data="bulk_upload_done")]]
    markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
    
    await m.answer(
        f"📥 ফাইলটি কিউতে যুক্ত হয়েছে! মোট ফাইল সংখ্যা: <b>{len(bulk_files)}</b>\n"
        f"আরো ফাইল থাকলে সেন্ড করুন, অথবা শেষ করতে নিচের বাটনে চাপুন।", 
        parse_mode="HTML", 
        reply_markup=markup
    )

@dp.callback_query(F.data == "bulk_upload_done")
async def finalize_bulk_upload(c: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    
    title = data.get("title")
    photo_id = data.get("photo_id")
    categories = data.get("categories", [])
    start_num = data.get("start_num", 1)
    quality = data.get("quality", "HD")
    bulk_files = data.get("bulk_files", [])
    
    if not bulk_files:
        return await c.message.answer("⚠️ কোনো ফাইল পাওয়া যায়নি! প্রসেস বাতিল করা হলো।")
    
    status_msg = await c.message.answer(f"⏳ <b>ডাটাবেজে {len(bulk_files)} টি এপিসোড আপলোড হচ্ছে... অনুগ্রহ করে অপেক্ষা করুন।</b>", parse_mode="HTML")
    
    success_count = 0
    episodes_added = []
    
    for idx, file_data in enumerate(bulk_files):
        current_ep = start_num + idx
        ep_quality_str = f"S01E{current_ep:02d} [{quality}]"
        
        await db.movies.insert_one({
            "title": title, 
            "quality": ep_quality_str, 
            "photo_id": photo_id, 
            "file_id": file_data["file_id"], 
            "file_type": file_data["file_type"],
            "db_file_id": file_data.get("db_file_id"), 
            "db_photo_id": data.get("db_photo_id"),
            "categories": categories, 
            "clicks": 0, 
            "created_at": datetime.datetime.utcnow()
        })
        episodes_added.append(f"Episode {current_ep:02d}")
        success_count += 1
        
    clear_app_cache() 
    await bot.delete_message(c.message.chat.id, status_msg.message_id)
    
    await c.message.answer(
        f"🎉 <b>Bulk Upload সফল হয়েছে!</b>\n\n"
        f"📌 সিরিজ: <b>{title}</b>\n"
        f"📦 মোট যুক্ত হয়েছে: <b>{success_count} টি এপিসোড</b>\n"
        f"🏷 কোয়ালিটি: <b>{quality}</b>\n"
        f"🔢 এপিসোড রেঞ্জ: {episodes_added[0]} থেকে {episodes_added[-1]}", 
        parse_mode="HTML"
    )
    
    if CHANNEL_ID:
        try:
            bot_info = await bot.get_me()
            kb = [
                [types.InlineKeyboardButton(text="📥 Download & Watch 🎬", url=f"https://t.me/{bot_info.username}?start=new")],
                [types.InlineKeyboardButton(text="কিভাবে ডাউনলোড করবেন ❓", url=TUTORIAL_LINK)],
                [types.InlineKeyboardButton(text="♻️ MOVIE REQUEST ♻️", url=REQUEST_LINK)]
            ]
            markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
            cat_display = ", ".join(categories) if categories else "N/A"
            caption = (
                f"🔥 <b>একাধিক নতুন এপিসোড যুক্ত হয়েছে!</b>\n\n"
                f"📌 <b>টাইটেল:</b> {title}\n"
                f"🔢 <b>এপিসোড সমূহ:</b> {episodes_added[0]} - {episodes_added[-1]}\n"
                f"🏷 <b>কোয়ালিটি:</b> {quality}\n"
                f"🎭 <b>ক্যাটাগরি:</b> {cat_display}\n\n"
                f"👇 <i>বট থেকে ভিডিওগুলো পেতে নিচের বাটনে ক্লিক করুন।</i>"
            )
            await bot.send_photo(chat_id=CHANNEL_ID, photo=photo_id, caption=caption, parse_mode="HTML", reply_markup=markup)
        except Exception: pass

# ==========================================
# 🛑 IMAGE PROCESSING STATE HANDLER
# ==========================================
@dp.message(AdminStates.waiting_for_photo, F.photo)
async def receive_movie_photo(m: types.Message, state: FSMContext):
    status_msg = await m.answer("⏳ <b>ছবিটি চ্যাপ্টা (16:9) করা হচ্ছে...</b>", parse_mode="HTML")
    photo_id = m.photo[-1].file_id
    file_info = await bot.get_file(photo_id)
    
    temp_in = f"temp_in_{photo_id}.jpg"
    temp_out = f"temp_out_{photo_id}.jpg"
    await bot.download_file(file_info.file_path, temp_in)
    
    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(None, make_wide_thumbnail, temp_in, temp_out)
    
    db_photo_id = None
    target_file = temp_out if success else temp_in
    
    if DB_CHANNEL_ID:
        try:
            copied_photo = await bot.send_photo(DB_CHANNEL_ID, FSInputFile(target_file))
            db_photo_id = copied_photo.message_id
            photo_id = copied_photo.photo[-1].file_id
        except Exception: pass
    
    if success:
        sent_photo = await m.answer_photo(FSInputFile(temp_out), caption="✅ <b>পোস্টার রেডি!</b>\nএবার <b>টাইটেল (নাম)</b> লিখে পাঠান।", parse_mode="HTML")
        if not DB_CHANNEL_ID: photo_id = sent_photo.photo[-1].file_id
    else:
        await m.answer("✅ পোস্টার পেয়েছি! এবার <b>টাইটেল (নাম)</b> লিখে পাঠান Regel।", parse_mode="HTML")
        
    await state.update_data(photo_id=photo_id, db_photo_id=db_photo_id)
    await state.set_state(AdminStates.waiting_for_title)
    await bot.delete_message(m.chat.id, status_msg.message_id)
    
    if os.path.exists(temp_in): os.remove(temp_in)
    if os.path.exists(temp_out): os.remove(temp_out)

@dp.message(AdminStates.waiting_for_title, F.text)
async def receive_movie_title(m: types.Message, state: FSMContext):
    await state.update_data(title=m.text.strip())
    await state.set_state(AdminStates.waiting_for_quality)
    await m.answer("✅ নাম সেভ হয়েছে! এবার ফাইলের <b>কোয়ালিটি বা এপিসোড নাম্বার</b> দিন।", parse_mode="HTML")

@dp.message(AdminStates.waiting_for_quality, F.text)
async def receive_movie_quality(m: types.Message, state: FSMContext):
    await state.update_data(quality=m.text.strip())
    await state.set_state(AdminStates.waiting_for_category)
    await m.answer("✅ কোয়ালিটি সেভ হয়েছে!\n\nএবার মুভির <b>ক্যাটাগরি</b> লিখে পাঠান।\n<i>(একাধিক হলে কমা দিয়ে লিখুন। যেমন: Bangla Dub, Action, 18+)</i>\n\n<i>(ক্যাটাগরি না দিতে চাইলে 'Skip' লিখুন)</i>", parse_mode="HTML")

@dp.message(AdminStates.waiting_for_category, F.text)
async def receive_movie_category(m: types.Message, state: FSMContext):
    cat_text = m.text.strip()
    if cat_text.lower() in ['skip', 'none', 'no']: categories = []
    else: categories = [cat.strip() for cat in cat_text.split(",") if cat.strip()]
    
    data = await state.get_data()
    await state.clear()
    
    title = data["title"]
    photo_id = data["photo_id"]
    quality = data["quality"]
    
    await db.movies.insert_one({
        "title": title, "quality": quality, "photo_id": photo_id, 
        "file_id": data["file_id"], "file_type": data["file_type"],
        "db_file_id": data.get("db_file_id"), "db_photo_id": data.get("db_photo_id"),
        "categories": categories,
        "clicks": 0, "created_at": datetime.datetime.utcnow()
    })
    clear_app_cache() 
    
    cat_display = ", ".join(categories) if categories else "N/A"
    await m.answer(f"🎉 <b>{title} [{quality}]</b> অ্যাপে সফলভাবে যুক্ত করা হয়েছে!\n🏷 ক্যাটাগরি: <b>{cat_display}</b>", parse_mode="HTML")

    if CHANNEL_ID:
        try:
            bot_info = await bot.get_me()
            kb = [
                [types.InlineKeyboardButton(text="📥 Download & Watch 🎬", url=f"https://t.me/{bot_info.username}?start=new")],
                [types.InlineKeyboardButton(text="কিভাবে ডাউনলোড করবেন ❓", url=TUTORIAL_LINK)],
                [types.InlineKeyboardButton(text="♻️ MOVIE REQUEST ♻️", url=REQUEST_LINK)]
            ]
            markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
            caption = (f"🔥 <b>নতুন ফাইল যুক্ত হয়েছে!</b>\n\n📌 <b>টাইটেল:</b> {title}\n🏷 <b>কোয়ালিটি:</b> {quality}\n🎭 <b>ক্যাটাগরি:</b> {cat_display}\n\n👇 <i>বট থেকে ভিডিওটি পেতে নিচের বাটনে ক্লিক করুন।</i>")
            await bot.send_photo(chat_id=CHANNEL_ID, photo=photo_id, caption=caption, parse_mode="HTML", reply_markup=markup)
        except Exception: pass

# ==========================================
# 🛑 CALLBACK QUERY HANDLERS (TRX & REPLY)
# ==========================================
@dp.callback_query(F.data.startswith("trx_"))
async def handle_trx_approval(c: types.CallbackQuery):
    if c.from_user.id not in admin_cache: return
    action, _, pay_id = c.data.split("_")
    
    payment = await db.payments.find_one({"_id": ObjectId(pay_id)})
    if not payment or payment["status"] != "pending": return await c.answer("ইতিমধ্যে প্রসেস করা হয়েছে!", show_alert=True)
        
    user_id = payment["user_id"]
    days = payment["days"]
    
    if action == "approve":
        now = datetime.datetime.utcnow()
        user = await db.users.find_one({"user_id": user_id})
        current_vip = user.get("vip_until", now) if user else now
        if current_vip < now: current_vip = now
        await db.users.update_one({"user_id": user_id}, {"$set": {"vip_until": current_vip + datetime.timedelta(days=days)}})
        await db.payments.update_one({"_id": ObjectId(pay_id)}, {"$set": {"status": "approved"}})
        await c.message.edit_text(c.message.text + f"\n\n✅ <b>Approve করা হয়েছে!</b>", parse_mode="HTML")
        try: await bot.send_message(user_id, f"🎉 <b>পেমেন্ট সফল!</b> আপনার পেমেন্ট অ্যাপ্রুভ হয়েছে এবং VIP চালু হয়েছে!", parse_mode="HTML")
        except: pass
    else:
        await db.payments.update_one({"_id": ObjectId(pay_id)}, {"$set": {"status": "rejected"}})
        await c.message.edit_text(c.message.text + "\n\n❌ <b>Reject করা হয়েছে!</b>", parse_mode="HTML")

@dp.callback_query(F.data.startswith("reply_"))
async def process_reply_cb(c: types.CallbackQuery, state: FSMContext):
    if c.from_user.id not in admin_cache: return
    user_id = int(c.data.split("_")[1])
    await state.set_state(AdminStates.waiting_for_reply)
    await state.update_data(target_uid=user_id)
    await c.message.reply("✍️ <b>ইউজারকে কী রিপ্লাই দিতে চান তা লিখে পাঠান:</b>", parse_mode="HTML")

@dp.message(AdminStates.waiting_for_reply)
async def send_reply(m: types.Message, state: FSMContext):
    data = await state.get_data()
    target_uid = data.get("target_uid")
    await state.clear()
    try:
        if m.text: await bot.send_message(target_uid, f"📩 <b>অ্যাডমিন রিপ্লাই:</b>\n\n{m.text}", parse_mode="HTML")
        else: await m.copy_to(target_uid, caption=f"📩 <b>অ্যাডমিন রিপ্লাই:</b>\n\n{m.caption or ''}", parse_mode="HTML")
        await m.answer("✅ ইউজারকে রিপ্লাই পাঠানো হয়েছে!")
    except Exception: await m.answer("⚠️ রিপ্লাই পাঠানো যায়নি!")
