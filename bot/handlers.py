# bot/handlers.py
import datetime
import asyncio
import random
import html
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
    video_queue, clear_app_cache, load_keyword_replies, logger
)
from helpers import make_wide_thumbnail

# এআই অ্যাসিস্ট্যান্ট ইম্পোর্ট ও ব্যাকআপ লজিক
try:
    from assistant.ai_reply import get_smart_reply, smart_search
except ImportError:
    async def get_smart_reply(text, name, db, user_id, save_history=True):
        return f"হ্যালো {name}! আপনার মেসেজটি পেয়েছি। আমাদের টিম আপনার সাথে শীঘ্রই যোগাযোগ করবে।"
    async def smart_search(db, text):
        return None

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

# বটের স্প্যাম ওয়ার্নিং মেসেজ ব্যাকগ্রাউন্ডে স্বয়ংক্রিয়ভাবে ক্লিন করার হেল্পার ফাংশন
async def delete_after_delay(chat_id, message_id, delay=20):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except: pass

# ==========================================
# 🛑 PREMIUM START COMMAND WITH PROFILE CARD
# ==========================================
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    if uid in banned_cache: 
        return await message.answer("🚫 <b>You are banned from using this bot.</b>", parse_mode="HTML")
        
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
    
    # প্রিমিয়াম বাটন লেআউট (সম্পূর্ণ নিচে নিচে এবং স্ট্যান্ডার্ড ইংরেজিতে)
    kb = [
        [types.InlineKeyboardButton(text="🎬 WATCH NOW 🎬", web_app=types.WebAppInfo(url=APP_URL))],
        [types.InlineKeyboardButton(text="📖 HOW TO DOWNLOAD", url=TUTORIAL_LINK)],
        [types.InlineKeyboardButton(text="♻️ REQUEST MOVIE", url=REQUEST_LINK)],
        [types.InlineKeyboardButton(text="🎁 REFER & EARN", callback_data="refer_info_start")]
    ]
    markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
    
    # ১৬:৯ রেশিওর ওয়েলকাম ব্যানার ইমেজ
    WELCOME_BANNER = "https://files.catbox.moe/abd55m.jpg"

    if uid in admin_cache:
        # অ্যাডমিনদের জন্য মেসেজ
        text = (
            "👋 <b>Hello Admin!</b>\n\n"
            "⚙️ <b>Admin Command Menu:</b>\n"
            "🔸 Auto Upload: <code>/autoupload on/off</code>\n"
            "🔸 Manage Admin: <code>/addadmin ID</code> | <code>/deladmin ID</code> | <code>/adminlist</code>\n"
            "🔸 Direct Links: <code>/addlink URL</code> | <code>/dellink URL</code> | <code>/seelinks</code>\n"
            "🔸 Support Link: <code>/setsupport URL</code>\n"
            "🔸 Payment: <code>/setbkash Number</code> | <code>/setnagad Number</code>\n"
            "🔸 Protection: <code>/protect on/off</code> | <code>/settime [minutes]</code>\n"
            "🔸 Ad Settings: <code>/setadtime [seconds]</code>\n" 
            "🔸 Stats & Broadcast: <code>/stats</code> | <code>/cast</code>\n"
            "🔸 Delete Movie: <code>/delmovie title</code> | <code>/delallmovies</code>\n"
            "🔸 User Controls: <code>/ban ID</code> | <code>/unban ID</code>\n"
            "🔸 Points & VIP: <code>/addcoin ID amount</code> | <code>/addvip ID days</code>\n\n"
            f"🌐 <b>Web Admin Panel:</b> <a href='{APP_URL}/admin'>Open Dashboard</a>\n\n"
            "📥 <i>To upload a movie, simply send/forward any video or document here.</i>"
        )
        try:
            await message.answer_photo(photo=WELCOME_BANNER, caption=text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            await message.answer(text, reply_markup=markup, parse_mode="HTML")
    else:
        # সাধারণ ইউজারদের জন্য প্রিমিয়াম কার্ড মেসেজ
        user_name = message.from_user.first_name or "User"
        text = (
            f"👋 <b>Welcome, {user_name}!</b>\n"
            f"Welcome to MovieZone BD - Cinema in your pocket.\n\n"
            f"📊 <b>YOUR PROFILE STATS:</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Account:</b> {user_name}\n"
            f"🆔 <b>User ID:</b> <code>{uid}</code>\n"
            f"💎 <b>My Gems:</b> <code>{coins} Gems</code>\n"
            f"👑 <b>Membership:</b> <b>{vip_status}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"🍿 <i>Click the <b>'WATCH NOW'</b> button below to open the mini-app and download or stream movies instantly!</i>"
        )
        try:
            await message.answer_photo(photo=WELCOME_BANNER, caption=text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            await message.answer(text, reply_markup=markup, parse_mode="HTML")

# রেফারেল ইনফো বাটন হ্যান্ডলার (Callback)
@dp.callback_query(F.data == "refer_info_start")
async def refer_info_start_cb(c: types.CallbackQuery):
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{c.from_user.id}"
    text = (
        "🎁 <b>Refer & Earn Gems:</b>\n\n"
        "Share your unique invitation link with friends. Whenever someone starts the bot using your link, you will receive <b>10 Gems</b> instantly!\n\n"
        f"🔗 <b>Your Invitation Link:</b>\n<code>{ref_link}</code>\n\n"
        "<i>Use points to unlock Premium VIP membership for an ad-free experience!</i>"
    )
    await c.message.answer(text, parse_mode="HTML")
    await c.answer()

# ==========================================
# 🛑 MAYA AI ASSISTANT FOR ADMINS (CO-PILOT COMMANDS)
# ==========================================
@dp.message(Command("maya"), lambda m: m.from_user.id in admin_cache)
async def admin_maya_chat(m: types.Message):
    prompt = m.text.split(" ", 1)
    if len(prompt) < 2:
        return await m.answer("⚠️ <b>Please specify a question!</b>\nUsage: <code>/maya write a marketing idea</code>", parse_mode="HTML")
    
    status_msg = await m.answer("⏳ <i>Maya is thinking...</i>", parse_mode="HTML")
    try:
        reply = await get_smart_reply(prompt[1], m.from_user.first_name, db, user_id=m.from_user.id, save_history=True)
        await bot.delete_message(m.chat.id, status_msg.message_id)
        await m.reply(reply, parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Error:</b> {str(e)}", parse_mode="HTML")

@dp.message(Command("caption"), lambda m: m.from_user.id in admin_cache)
async def admin_caption_gen(m: types.Message):
    prompt = m.text.split(" ", 1)
    if len(prompt) < 2:
        return await m.answer("⚠️ <b>Please specify a movie name!</b>\nUsage: <code>/caption Puspa 2</code>", parse_mode="HTML")
    
    status_msg = await m.answer("⏳ <i>Generating poster caption...</i>", parse_mode="HTML")
    try:
        ai_prompt = f"Write an extremely attractive, professional, and dramatic Telegram channel post caption in Bangladeshi Bengali with lots of emojis for the movie: '{prompt[1]}'. Emphasize that it's now available on our Mini-App."
        reply = await get_smart_reply(ai_prompt, m.from_user.first_name, db, user_id=m.from_user.id, save_history=False)
        await bot.delete_message(m.chat.id, status_msg.message_id)
        await m.reply(reply, parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Error:</b> {str(e)}", parse_mode="HTML")

@dp.message(Command("movienews"), lambda m: m.from_user.id in admin_cache)
async def admin_movienews_gen(m: types.Message):
    status_msg = await m.answer("⏳ <i>Fetching hot movie news & gossip...</i>", parse_mode="HTML")
    try:
        ai_prompt = "Write an extremely interesting, trending movie news or gossip in Bangladeshi Bengali with emojis for a Telegram channel. Make it read like a hot gossip magazine post!"
        reply = await get_smart_reply(ai_prompt, m.from_user.first_name, db, user_id=m.from_user.id, save_history=False)
        await bot.delete_message(m.chat.id, status_msg.message_id)
        await m.reply(reply, parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Error:</b> {str(e)}", parse_mode="HTML")

@dp.message(Command("greeting"), lambda m: m.from_user.id in admin_cache)
async def admin_greeting_gen(m: types.Message):
    prompt = m.text.split(" ", 1)
    event = prompt[1] if len(prompt) > 1 else "general"
    status_msg = await m.answer(f"⏳ <i>Generating customized welcome greeting for '{event}'...</i>", parse_mode="HTML")
    try:
        ai_prompt = f"Write a beautiful, warm, and highly engaging welcome greeting in Bangladeshi Bengali with stylish emojis for our Telegram bot start menu. The theme/event is: '{event}'. Make it sound very welcoming!"
        reply = await get_smart_reply(ai_prompt, m.from_user.first_name, db, user_id=m.from_user.id, save_history=False)
        await bot.delete_message(m.chat.id, status_msg.message_id)
        await m.reply(reply, parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Error:</b> {str(e)}", parse_mode="HTML")

# ==========================================
# 🛑 NEW ADVANCED AI COMMANDS FOR ADMINS
# ==========================================
@dp.message(Command("broadcast_copy"), lambda m: m.from_user.id in admin_cache)
async def admin_broadcast_copy_gen(m: types.Message):
    latest_cursor = db.movies.find({}, {"title": 1}).sort("created_at", -1).limit(3)
    latest_movies = await latest_cursor.to_list(length=3)
    movie_list_str = ", ".join([mv["title"] for mv in latest_movies]) if latest_movies else "No recent movies"
    
    status_msg = await m.answer("⏳ <i>Drafting high-converting broadcast notification...</i>", parse_mode="HTML")
    try:
        ai_prompt = (
            f"Draft an extremely engaging, emotional, and persuasive Telegram broadcast message/newsletter in Bangladeshi Bengali with stylish emojis. "
            f"The goal is to invite users to watch our latest blockbuster releases. The latest movies added are: '{movie_list_str}'. "
            f"Tell them they can watch/download these in 1-click in our Mini-App by clicking the button below."
        )
        reply = await get_smart_reply(ai_prompt, m.from_user.first_name, db, user_id=m.from_user.id, save_history=False)
        await bot.delete_message(m.chat.id, status_msg.message_id)
        await m.reply(reply, parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Error:</b> {str(e)}", parse_mode="HTML")

@dp.message(Command("dmca"), lambda m: m.from_user.id in admin_cache)
async def admin_dmca_analyzer(m: types.Message):
    prompt = m.text.split(" ", 1)
    if len(prompt) < 2:
        return await m.answer("⚠️ <b>Please specify the DMCA text!</b>\nUsage: <code>/dmca [paste claim text here]</code>", parse_mode="HTML")
    
    status_msg = await m.answer("⏳ <i>Analyzing copyright claim safety...</i>", parse_mode="HTML")
    try:
        ai_prompt = (
            f"Analyze this raw copyright/DMCA claim/complaint text. "
            f"Extract the movie/series name being reported. Then, write a warning report in Bangladeshi Bengali to the admin advising them. "
            f"If a movie is found, write the exact command they can run to delete it, like: `/delmovie [Movie Name]`. "
            f"Here is the DMCA text:\n\n{prompt[1]}"
        )
        reply = await get_smart_reply(ai_prompt, m.from_user.first_name, db, user_id=m.from_user.id, save_history=False)
        await bot.delete_message(m.chat.id, status_msg.message_id)
        await m.reply(reply, parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Error:</b> {str(e)}", parse_mode="HTML")

@dp.message(Command("retarget"), lambda m: m.from_user.id in admin_cache)
async def admin_retarget_copy_gen(m: types.Message):
    prompt = m.text.split(" ", 1)
    target = prompt[1] if len(prompt) > 1 else "Action blockbusters"
    status_msg = await m.answer(f"⏳ <i>Drafting personalized retargeting campaign for '{target}'...</i>", parse_mode="HTML")
    try:
        ai_prompt = (
            f"Write a highly personalized, psychological re-engagement/retargeting message in Bangladeshi Bengali with emojis. "
            f"The target audience is users who previously watched or searched for '{target}'. "
            f"Address them warmly (use placeholders like '{{Name}}'), and write in a way that feels like Netflix's personalized recommendations: "
            f"'Because you watched/searched for X, we recommend checking out Y on our Mini-App...'. Make it highly clickable."
        )
        reply = await get_smart_reply(ai_prompt, m.from_user.first_name, db, user_id=m.from_user.id, save_history=False)
        await bot.delete_message(m.chat.id, status_msg.message_id)
        await m.reply(reply, parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Error:</b> {str(e)}", parse_mode="HTML")

# চ্যাট মেমোরি ইনস্ট্যান্ট ক্লিয়ার করার কমান্ড (রিসেট করার জন্য)
@dp.message(Command("clear"), lambda m: m.from_user.id in admin_cache)
async def admin_clear_chat_memory(m: types.Message):
    identifier = str(m.from_user.id)
    await db.messages.delete_many({"user_id": identifier})
    await m.reply("🧹 <b>Your AI chat memory has been cleared and reset successfully!</b>\nমায়া এখন সম্পূর্ণ সুস্থ এবং নতুন ইনপুট নিতে প্রস্তুত। 😊", parse_mode="HTML")

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

# ==========================================
# 🛑 OPTIMIZED LIVE-PROGRESS BROADCAST CONTROLLER
# ==========================================
@dp.message(AdminStates.waiting_for_bcast)
async def execute_broadcast(m: types.Message, state: FSMContext):
    await state.clear()
    
    # ডাটাবেসের মোট ইউজার সংখ্যা কাউন্ট করা হচ্ছে
    total_users = await db.users.count_documents({})
    
    # অ্যাডমিনের কাছে প্রাথমিক স্ট্যাটাস মেসেজ পাঠানো হলো
    status_msg = await m.answer("⏳ <b>Broadcasting initialized... Preparing to send.</b>", parse_mode="HTML")
    
    kb = [[types.InlineKeyboardButton(text="🎬 ওপেন মুভি অ্যাপ", web_app=types.WebAppInfo(url=APP_URL))]]
    markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
    
    success = 0
    failed = 0
    total_checked = 0
    
    async for u in db.users.find():
        user_id = u['user_id']
        total_checked += 1
        
        try:
            # মেসেজটি ইউজারের কাছে কপি করা হচ্ছে
            await m.copy_to(chat_id=user_id, reply_markup=markup)
            success += 1
        except TelegramRetryAfter as e:
            # যদি টেলিগ্রাম থেকে রেট-লিমিট দেয়, তবে ডাইনামিকালি ওয়েট করে পুনরায় ট্রাই করবে
            await asyncio.sleep(e.retry_after)
            try:
                await m.copy_to(chat_id=user_id, reply_markup=markup)
                success += 1
            except Exception:
                failed += 1
        except Exception:
            # যদি ইউজার বটটি ব্লক করে থাকে বা অ্যাকাউন্ট নিষ্ক্রিয় থাকে
            failed += 1
        
        # টেলিগ্রামের এডিট লিমিট (Edit Rate Limit) ঠিক রাখতে প্রতি ৫০ জন ইউজার পর পর অগ্রগতি আপডেট করবে
        if total_checked % 50 == 0 or total_checked == total_users:
            percentage = int((total_checked / total_users) * 100)
            progress_text = (
                f"📢 <b>Broadcasting in Progress...</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🟢 <b>Success:</b> <code>{success}</code>\n"
                f"🔴 <b>Failed/Blocked:</b> <code>{failed}</code>\n"
                f"👥 <b>Total processed:</b> <code>{total_checked}</code> / <code>{total_users}</code>\n"
                f"📊 <b>Progress:</b> <code>{percentage}%</code>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⏳ <i>Please do not send other commands while broadcasting...</i>"
            )
            try:
                await bot.edit_message_text(
                    chat_id=m.chat.id, 
                    message_id=status_msg.message_id, 
                    text=progress_text, 
                    parse_mode="HTML"
                )
            except Exception:
                pass
            
        # টেলিগ্রাম ফ্লাডিং এড়াতে সামান্য বিরতি
        await asyncio.sleep(0.04)
        
    # ব্রডকাস্ট সম্পন্ন হওয়ার চূড়ান্ত মেসেজ
    final_text = (
        f"✅ <b>Broadcasting Completed!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>Successfully Sent:</b> <code>{success}</code>\n"
        f"🔴 <b>Failed (Blocked/Inactive):</b> <code>{failed}</code>\n"
        f"👥 <b>Total Users in Database:</b> <code>{total_users}</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📢 <i>All active users have received your broadcast!</i>"
    )
    await bot.send_message(m.chat.id, final_text, parse_mode="HTML")

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
# 🛑 SMART AUTO-RESPONDER & ADMIN FORWARDING (SECURED WITH HTML ESCAPING & ONE-CLICK BAN)
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
        # প্রমোショナル বা স্প্যাম লিংক স্ক্যান করা হচ্ছে (অটো-মডারেশন)
        is_spam = False
        if "http" in user_text_lower or "t.me" in user_text_lower or "joinchat" in user_text_lower or "bit.ly" in user_text_lower:
            is_spam = True
            
        spam_tag = "⚠️ <b>[SUSPECTED SPAM/PROMOTION]</b>\n" if is_spam else ""
        
        builder = InlineKeyboardBuilder()
        builder.button(text="✍️ রিপ্লাই দিন", callback_data=f"reply_{m.from_user.id}")
        
        # স্প্যামার হলে সরাসরি ১-ক্লিক ব্যান বাটন যুক্ত হবে
        if is_spam:
            builder.button(text="🚫 BAN USER", callback_data=f"admin_ban_{m.from_user.id}")
            
        markup = builder.as_markup()
        
        all_admins = set([OWNER_ID])
        async for a in db.admins.find(): all_admins.add(a["user_id"])
            
        # HTML Entity Parsing ক্র্যাশ এড়াতে নাম এবং মেসেজ এস্কেপ করা হলো
        escaped_name = html.escape(m.from_user.first_name or "User")
        escaped_text = html.escape(m.text) if m.text else "[Media/File]"
            
        for admin_id in all_admins:
            try:
                await bot.send_message(
                    admin_id, 
                    f"{spam_tag}📩 <b>Message from <a href='tg://user?id={m.from_user.id}'>{escaped_name}</a></b> (<code>{m.from_user.id}</code>):\n\n{escaped_text}", 
                    parse_mode="HTML",
                    reply_markup=markup
                )
            except Exception as err:
                logger.error(f"HTML Forward crash bypassed: {err}")
        
        if m.from_user.id not in auto_reply_cache:
            auto_reply_cache[m.from_user.id] = True
            try:
                kb = [[types.InlineKeyboardButton(text="🎬 Watch Now (মুভি দেখুন)", web_app=types.WebAppInfo(url=APP_URL))]]
                user_markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
                
                if user_text:
                    try:
                        reply_text = await get_smart_reply(user_text, m.from_user.first_name or "User", db, user_id=m.from_user.id, save_history=True)
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

# ১-ক্লিক ব্যান বাটন প্রসেস (Callback)
@dp.callback_query(F.data.startswith("admin_ban_"))
async def admin_one_click_ban_cb(c: types.CallbackQuery):
    if c.from_user.id not in admin_cache: return
    target_uid = int(c.data.split("_")[2])
    
    await db.banned.update_one({"user_id": target_uid}, {"$set": {"user_id": target_uid}}, upsert=True)
    banned_cache.add(target_uid)
    
    await c.message.edit_text(c.message.text + f"\n\n🚫 <b>User {target_uid} has been BANNED successfully!</b>", parse_mode="HTML")
    await c.answer("User Banned successfully!", show_alert=True)

# ==========================================
# 🛑 SMART AUTOMATIC MOVIE REQUEST AUTO-RESPONDER FOR GROUPS (SAVAGE ROASTING & AUTO-CLEAN)
# ==========================================
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_request_responder(m: types.Message):
    user_text = m.text.strip() if m.text else ""
    if not user_text: return
    
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    # ⚠️ ১. ডাইনামিক কড়াকড়ি স্প্যাম-লিংক প্রোটেকশন (নন-অ্যাডমিন লিংক ডিটেক্টর ও র্যান্ডম রোস্টিং)
    if m.from_user.id not in admin_cache:
        user_text_lower = user_text.lower()
        is_unauthorized_link = False
        
        # মেসেজে কোনো লিংক টাইপ টেক্সট বা এনটিটি আছে কি না চেক করা হচ্ছে
        if any(x in user_text_lower for x in ["http://", "https://", "t.me/", "joinchat", "bit.ly"]):
            is_unauthorized_link = True
        elif m.entities:
            for entity in m.entities:
                if entity.type in ["url", "text_link"]:
                    is_unauthorized_link = True
                    break
                    
        if is_unauthorized_link:
            try:
                # ক. গ্রুপ থেকে ফালতু লিংকটি সাথে সাথে ডিলিট করে দেওয়া হলো
                await bot.delete_message(chat_id=m.chat.id, message_id=m.message_id)
                
                # খ. কড়া ভাষায় স্প্যামারকে খাঁটি বাংলা রোস্টিং করা হচ্ছে (m.answer এর পরিবর্তে সরাসরি bot.send_message ব্যবহার করা হলো)
                escaped_name = html.escape(m.from_user.first_name or "User")
                roast_replies = [
                    f"🚨 <b>ওই বলদ {escaped_name}!</b> এটা কি তোর বাপের জায়গা পাইছিস যে এখানে লিংক শেয়ার করতেছিস? যা ভাগ এখান থেকে! 😡",
                    f"🚨 <b>শোন রে বলদ {escaped_name}!</b> আমাদের পারমিশন ছাড়া গ্রুপে ফালতু লিংক শেয়ার করবি না। পরেরবার করলে এক ক্লিকে গ্রুপ থেকে লাথি দিয়ে বের করে দেব! 😤",
                    f"🚨 <b>এই আবাল {escaped_name}!</b> এখানে ফালতু লিংক আর বটের প্রচারণা চালানো নিষেধ। নিজের চরকায় তেল দে, এখানে বাপের জায়গা মনে করিস না! 🤬",
                    f"🚨 <b>তোর বাপের রাজত্ব পাইছিস {escaped_name}?</b> গ্রুপে পারমিশন ছাড়া লিংক শেয়ার করা একদম নিষেধ! বেশি পন্ডিতি করলে ডিরেক্ট ব্যান করে দেব! 😡🔥"
                ]
                roast_text = random.choice(roast_replies)
                
                # original message ডিলিট হওয়ার পরও যেন মেসেজ ১০০% শো করে সেজন্য bot.send_message ব্যবহার করা হয়েছে
                sent_warn = await bot.send_message(chat_id=m.chat.id, text=roast_text, parse_mode="HTML")
                
                # গ. গ্রুপের সৌন্দর্য রক্ষার্থে বটের কড়া ওয়ার্নিং মেসেজটি ২০ সেকেন্ড পর স্বয়ংক্রিয়ভাবে মুছে যাবে (নন-ব্লকিং)
                asyncio.create_task(delete_after_delay(m.chat.id, sent_warn.message_id, 20))
                return
            except Exception as e:
                logger.error(f"Savage link moderator error: {e}")

    # ২. ডেটাবেসে ফাস্ট স্মার্ট সার্চ করা হচ্ছে (সম্পূর্ণ এপিআই বিল বা খরচ-মুক্ত)
    found_movie = await smart_search(db, user_text)
    
    if found_movie:
        # মুভিটি পাওয়া গেছে! ১-ক্লিক ওয়াচ লিঙ্কসহ গ্রুপে রিপ্লাই দেওয়া হচ্ছে
        bot_link = f"https://t.me/{bot_username}?start=new"
        kb = [[types.InlineKeyboardButton(text="🎬 WATCH / DOWNLOAD NOW", url=bot_link)]]
        markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
        
        escaped_name = html.escape(m.from_user.first_name or "User")
        text = (
            f"🍿 <b>Hey {escaped_name}!</b>\n\n"
            f"আপনি যে মুভিটি খুঁজছেন—'<b>{found_movie['title']}</b>' "
            f"সেটি আমাদের মিনি-অ্যাপে অলরেডি আপলোড করা আছে! 😍\n\n"
            f"👇 নিচের বাটনে ক্লিক করে সরাসরি আমাদের বটে গিয়ে দেখে নিন বা ডাউনলোড করুন।"
        )
        return await m.reply(text, reply_markup=markup, parse_mode="HTML")
        
    # ৩. মুভি পাওয়া যায়নি। মায়াকে মেনশন বা মায়া ডাকলে এআই চালু হবে (খরচ নিয়ন্ত্রণে রাখতে)
    is_mentioned = (
        f"@{bot_username}" in user_text 
        or "maya" in user_text.lower() 
        or "মায়া" in user_text
    )
    
    if is_mentioned:
        status_msg = await m.reply("⏳ <i>Maya is checking...</i>", parse_mode="HTML")
        try:
            ai_prompt = (
                f"The user '{m.from_user.first_name}' is asking for a movie in our request group. "
                f"We searched our database, and the movie is NOT available. "
                f"Write a very polite, sweet, and comforting reply in Bangladeshi Bengali. "
                f"Explain that we don't have this movie yet (or it might not be released yet), "
                f"and tell them they can request it in our bot or wait, and we will upload it soon! "
                f"Keep the reply short, friendly, and helpful. User's query: '{user_text}'"
            )
            # গ্রুপে চ্যাট মেমোরি জমে করাপশন এড়াতে save_history=False রাখা হয়েছে
            reply = await get_smart_reply(ai_prompt, m.from_user.first_name, db, user_id=m.from_user.id, save_history=False)
            await bot.delete_message(m.chat.id, status_msg.message_id)
            await m.reply(reply, parse_mode="HTML")
        except Exception as e:
            try: await bot.delete_message(m.chat.id, status_msg.message_id)
            except: pass

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
            caption = (f"🔥 <b>নতুন এপিসোড যুক্ত হয়েছে!</b>\n\n📌 <b>টাইটেল:</b> {title}\n🏷 <b>এপিসোড/কোয়ালিটি:</b> {quality}\n🎭 <b>ক্যাটাগরি:</b> {cat_display}\n\n👇 <i>বট থেকে...</i>")
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
            caption = (f"🔥 <b>নতুন ফাইল যুক্ত হয়েছে!</b>\n\n📌 <b>টাইটেল:</b> {title}\n🏷 <b>কোয়ালিটি:</b> {quality}\n🎭 <b>ক্যাটাগরি:</b> {cat_display}\n\n👇 <i>বট থেকে...</i>")
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
