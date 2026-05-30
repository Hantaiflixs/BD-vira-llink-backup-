# api/routes.py
import datetime
import json
import random
import aiohttp
from fastapi import APIRouter, Depends, Body, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from bson import ObjectId
import copy

from config import (
    db, bot, OWNER_ID, BOT_USERNAME, DB_CHANNEL_ID,
    admin_cache, banned_cache, trending_cache, list_cache, category_cache,
    clear_app_cache, TOKEN
)
from helpers import validate_tg_data, verify_admin, format_views
from html_template import HTML_CODE

api_router = APIRouter()

# ==========================================
# 🛑 Pydantic Models for API Requests
# ==========================================
class UserManageModel(BaseModel):
    user_id: int
    action: str
    value: int = 0

class UserActionModel(BaseModel):
    uid: int
    initData: str

class ViewRequestModel(BaseModel):
    title: str

class SendRequestModel(BaseModel):
    userId: int
    movieId: str
    initData: str

class ReqModel(BaseModel):
    uid: int
    uname: str
    movie: str
    initData: str

class AdCreateModel(BaseModel):
    uid: int
    initData: str
    title: str
    subtitle: str = "দেরি না করে এখনো সবাই নিয়ে নিন"
    link: str
    image_url: str
    package: int

class AdminAdModel(BaseModel):
    title: str
    subtitle: str = "দেরি না করে এখনো সবাই নিয়ে নিন"
    link: str
    image_url: str

class WatchlistModel(BaseModel):
    uid: int
    title: str
    initData: str

class ReviewModel(BaseModel):
    uid: int
    uname: str
    title: str
    rating: int
    review: str
    initData: str

# ==========================================
# 🛑 System Settings API
# ==========================================
@api_router.get("/api/admin/sys_settings")
async def get_sys_settings(auth: bool = Depends(verify_admin)):
    cost_cfg = await db.settings.find_one({"id": "vip_cost"})
    days_cfg = await db.settings.find_one({"id": "vip_days"})
    unlock_cfg = await db.settings.find_one({"id": "unlock_hours"})
    social_cfg = await db.settings.find_one({"id": "social_links"})
    interval_cfg = await db.settings.find_one({"id": "ad_interval"}) 
    
    return {
        "vip_cost": cost_cfg["amount"] if cost_cfg else 30,
        "vip_days": days_cfg["days"] if days_cfg else 1,
        "unlock_hours": unlock_cfg["hours"] if unlock_cfg else 24,
        "ad_interval": interval_cfg["interval"] if interval_cfg else 3, 
        "social_links": social_cfg.get("links", {}) if social_cfg else {}
    }

@api_router.post("/api/admin/sys_settings")
async def save_sys_settings(data: dict = Body(...), auth: bool = Depends(verify_admin)):
    await db.settings.update_one({"id": "vip_cost"}, {"$set": {"amount": int(data.get("vip_cost", 30))}}, upsert=True)
    await db.settings.update_one({"id": "vip_days"}, {"$set": {"days": int(data.get("vip_days", 1))}}, upsert=True)
    await db.settings.update_one({"id": "unlock_hours"}, {"$set": {"hours": int(data.get("unlock_hours", 24))}}, upsert=True)
    await db.settings.update_one({"id": "ad_interval"}, {"$set": {"interval": int(data.get("ad_interval", 3))}}, upsert=True) 
    
    social_links = data.get("social_links", {})
    await db.settings.update_one({"id": "social_links"}, {"$set": {"links": social_links}}, upsert=True)
    
    clear_app_cache()
    return {"ok": True}

# ==========================================
# 🛑 Render Web UI (Frontend Page)
# ==========================================
@api_router.get("/", response_class=HTMLResponse)
async def web_ui():
    tg_cfg = await db.settings.find_one({"id": "link_tg"})
    support_cfg = await db.settings.find_one({"id": "link_support"})
    b18_cfg = await db.settings.find_one({"id": "link_18"})
    dl_cfg = await db.settings.find_one({"id": "direct_links"})
    
    ad_time_cfg = await db.settings.find_one({"id": "ad_time"})
    ad_wait_seconds = ad_time_cfg['seconds'] if ad_time_cfg else 10
    
    interval_cfg = await db.settings.find_one({"id": "ad_interval"})
    ad_interval = interval_cfg["interval"] if interval_cfg else 3
    
    tg_url = tg_cfg['url'] if tg_cfg else "https://t.me/MovieeBD"
    support_link = support_cfg['url'] if support_cfg else "https://t.me/YourSupportUsername"
    link_18 = b18_cfg['url'] if b18_cfg else "https://t.me/MovieeBD"
    direct_links = dl_cfg.get('links', []) if dl_cfg else []
    dl_json = json.dumps(direct_links)
    
    social_cfg = await db.settings.find_one({"id": "social_links"})
    social_links_dict = social_cfg.get('links', {}) if social_cfg else {}
    social_json = json.dumps(social_links_dict)

    compiled_html = HTML_CODE.replace(
        "{{DIRECT_LINKS}}", dl_json
    ).replace(
        "{{TG_LINK}}", tg_url
    ).replace(
        "{{SUPPORT_LINK}}", support_link
    ).replace(
        "{{LINK_18}}", link_18
    ).replace(
        "{{BOT_USER}}", BOT_USERNAME
    ).replace(
        "{{AD_TIME}}", str(ad_wait_seconds)
    ).replace(
        "{{AD_INTERVAL}}", str(ad_interval)
    ).replace(
        "{{SOCIAL_LINKS}}", social_json
    )
    return compiled_html

# ==========================================
# 🛑 Gamification & Check-in APIs
# ==========================================
@api_router.get("/api/user/{uid}")
async def get_user_info(uid: int):
    now = datetime.datetime.utcnow()
    await db.users.update_one({"user_id": uid}, {"$set": {"last_active": now}})
    
    user = await db.users.find_one({"user_id": uid})
    is_admin = uid in admin_cache
    
    cost_cfg = await db.settings.find_one({"id": "vip_cost"})
    days_cfg = await db.settings.find_one({"id": "vip_days"})
    
    cost = cost_cfg["amount"] if cost_cfg else 30
    days = days_cfg["days"] if days_cfg else 1

    if not user: return {"vip": False, "admin": is_admin, "coins": 0, "vip_cost": cost, "vip_days": days}
    return {
        "vip": user.get("vip_until", now) > now, 
        "admin": is_admin,
        "coins": user.get("coins", 0),
        "vip_cost": cost,
        "vip_days": days
    }

@api_router.post("/api/add_coin")
async def add_coin_api(d: UserActionModel):
    if d.uid == 0 or not validate_tg_data(d.initData): return {"ok": False}
    await db.users.update_one({"user_id": d.uid}, {"$inc": {"coins": 5}})
    return {"ok": True}

@api_router.post("/api/buy_vip")
async def buy_vip_api(d: UserActionModel):
    if d.uid == 0 or not validate_tg_data(d.initData): return {"ok": False}
    user = await db.users.find_one({"user_id": d.uid})
    coins = user.get("coins", 0)
    
    cost_cfg = await db.settings.find_one({"id": "vip_cost"})
    days_cfg = await db.settings.find_one({"id": "vip_days"})
    cost = cost_cfg["amount"] if cost_cfg else 30
    days = days_cfg["days"] if days_cfg else 1
    
    if coins < cost: return {"ok": False, "msg": f"Not enough points! Need {cost} points."}
    
    now = datetime.datetime.utcnow()
    current_vip = user.get("vip_until", now) if user.get("vip_until") else now
    if current_vip < now: current_vip = now
    new_vip = current_vip + datetime.timedelta(days=days)
    
    await db.users.update_one({"user_id": d.uid}, {"$inc": {"coins": -cost}, "$set": {"vip_until": new_vip}})
    return {"ok": True}

# ==========================================
# 🛑 Movies Data APIs
# ==========================================
@api_router.get("/api/trending")
async def trending_movies(uid: int = 0):
    unlocked_ids = []
    cfg_unlock = await db.settings.find_one({"id": "unlock_hours"})
    unlock_hrs = cfg_unlock['hours'] if cfg_unlock else 24
    if uid != 0:
        time_limit = datetime.datetime.utcnow() - datetime.timedelta(hours=unlock_hrs)
        async for u in db.user_unlocks.find({"user_id": uid, "unlocked_at": {"$gt": time_limit}}):
            unlocked_ids.append(u["movie_id"])

    if "trending_list" in trending_cache:
        movies = copy.deepcopy(trending_cache["trending_list"])
    else:
        seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        pipeline = [
            {"$group": {
                "_id": "$title", 
                "photo_id": {"$first": "$photo_id"}, 
                "db_photo_id": {"$first": "$db_photo_id"}, 
                "clicks": {"$sum": "$clicks"}, 
                "files": {"$push": {"id": {"$toString": "$_id"}, "quality": {"$ifNull": ["$quality", "HD"]}}}
            }},
            {"$lookup": {
                "from": "movie_views",
                "let": {"movie_title": "$_id"},
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$title", "$$movie_title"]},
                                {"$gte": ["$viewed_at", seven_days_ago]}
                            ]
                        }
                    }},
                    {"$count": "count"}
                ],
                "as": "weekly"
            }},
            {"$addFields": {
                "weekly_clicks": {"$ifNull": [{"$arrayElemAt": ["$weekly.count", 0]}, 0]}
            }},
            {"$sort": {"weekly_clicks": -1, "clicks": -1}},
            {"$limit": 10}
        ]
        movies = await db.movies.aggregate(pipeline).to_list(10)
        for m in movies:
            m["photo_id"] = m.get("photo_id") or (f"db_{m['db_photo_id']}" if m.get("db_photo_id") else None)
        trending_cache["trending_list"] = movies
        movies = copy.deepcopy(movies)

    for m in movies:
        for f in m["files"]: f["is_unlocked"] = f["id"] in unlocked_ids
    return movies

@api_router.get("/api/categories")
async def get_categories():
    if "all_cats" in category_cache:
        return category_cache["all_cats"]
    categories = await db.movies.distinct("categories")
    result = [c for c in categories if c]
    category_cache["all_cats"] = result
    return result

@api_router.get("/api/list")
async def list_movies(page: int = 1, q: str = "", uid: int = 0, cat: str = ""):
    unlocked_ids = []
    cfg_unlock = await db.settings.find_one({"id": "unlock_hours"})
    unlock_hrs = cfg_unlock['hours'] if cfg_unlock else 24
    if uid != 0:
        time_limit = datetime.datetime.utcnow() - datetime.timedelta(hours=unlock_hrs)
        async for u in db.user_unlocks.find({"user_id": uid, "unlocked_at": {"$gt": time_limit}}):
            unlocked_ids.append(u["movie_id"])

    cache_key = f"{page}_{q}_{cat}"
    if cache_key in list_cache:
        data = copy.deepcopy(list_cache[cache_key])
        movies = data["movies"]
        total_pages = data["total_pages"]
    else:
        limit = 100  
        skip = (page - 1) * limit
        match_stage = {}
        if q: match_stage["title"] = {"$regex": q, "$options": "i"}
        if cat: match_stage["categories"] = cat

        pipeline = [
            {"$match": match_stage},
            {"$group": {"_id": "$title", "photo_id": {"$first": "$photo_id"}, "db_photo_id": {"$first": "$db_photo_id"}, "clicks": {"$sum": "$clicks"}, "created_at": {"$max": "$created_at"}, "files": {"$push": {"id": {"$toString": "$_id"}, "quality": {"$ifNull": ["$quality", "HD"]}}}}},
            {"$sort": {"created_at": -1}}, {"$skip": skip}, {"$limit": limit}
        ]
        total_groups = (await db.movies.aggregate([{"$match": match_stage}, {"$group": {"_id": "$title"}}, {"$count": "total"}]).to_list(1))
        total_pages = (total_groups[0]["total"] + limit - 1) // limit if total_groups else 0
        movies = await db.movies.aggregate(pipeline).to_list(limit)
        for m in movies:
            m["photo_id"] = m.get("photo_id") or (f"db_{m['db_photo_id']}" if m.get("db_photo_id") else None)
        list_cache[cache_key] = {"movies": movies, "total_pages": total_pages}
        movies = copy.deepcopy(movies)

    for m in movies:
        for f in m["files"]: f["is_unlocked"] = f["id"] in unlocked_ids
    return {"movies": movies, "total_pages": total_pages}

@api_router.get("/api/image/{photo_id}")
async def get_image(photo_id: str):
    try:
        cache = await db.file_cache.find_one({"photo_id": photo_id})
        now = datetime.datetime.utcnow()
        file_path = None
        if cache and cache.get("expires_at", now) > now: 
            file_path = cache["file_path"]
        else:
            actual_file_id = photo_id
            db_msg_id = None
            if photo_id.startswith("db_"):
                parts = photo_id.split("_")
                if len(parts) > 1 and parts[1].isdigit():
                    db_msg_id = int(parts[1])
                movie = await db.movies.find_one({"db_photo_id": db_msg_id})
                if movie and movie.get("photo_id"): actual_file_id = movie["photo_id"]
            try:
                file_path = (await bot.get_file(actual_file_id)).file_path
            except Exception:
                if db_msg_id and DB_CHANNEL_ID:
                    try:
                        copied = await bot.copy_message(chat_id=DB_CHANNEL_ID, from_chat_id=DB_CHANNEL_ID, message_id=db_msg_id)
                        new_photo_id = copied.photo[-1].file_id
                        await bot.delete_message(chat_id=DB_CHANNEL_ID, message_id=copied.message_id)
                        await db.movies.update_many({"db_photo_id": db_msg_id}, {"$set": {"photo_id": new_photo_id}})
                        file_path = (await bot.get_file(new_photo_id)).file_path
                    except Exception: pass
            if file_path:
                await db.file_cache.update_one({"photo_id": photo_id}, {"$set": {"file_path": file_path, "expires_at": now + datetime.timedelta(minutes=50)}}, upsert=True)
        if not file_path: return {"error": "not found"}
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        async def stream_image():
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as resp:
                    async for chunk in resp.content.iter_chunked(1024): yield chunk
        return StreamingResponse(stream_image(), media_type="image/jpeg")
    except Exception: return {"error": "error"}

@api_router.post("/api/view_movie")
async def increment_movie_view(d: ViewRequestModel):
    try:
        await db.movies.update_many({"title": d.title}, {"$inc": {"clicks": 1}})
        await db.movie_views.insert_one({"title": d.title, "viewed_at": datetime.datetime.utcnow()})
    except Exception: pass
    return {"ok": True}

@api_router.post("/api/send")
async def send_file(d: SendRequestModel):
    if d.userId == 0 or not validate_tg_data(d.initData): return {"ok": False}
    try:
        m = await db.movies.find_one({"_id": ObjectId(d.movieId)})
        if m:
            now = datetime.datetime.utcnow()
            user = await db.users.find_one({"user_id": d.userId})
            is_vip = user and user.get("vip_until", now) > now
            time_cfg = await db.settings.find_one({"id": "del_time"})
            del_minutes = time_cfg['minutes'] if time_cfg else 60
            protect_cfg = await db.settings.find_one({"id": "protect_content"})
            is_protected = protect_cfg['status'] if protect_cfg else True
            caption = f"🎥 <b>{m['title']} [{m.get('quality', 'HD')}]</b>\n\n📥 Join: @TGLinkBase"
            if not is_vip: caption += f"\n\n⏳ <i>সতর্কতা: সিকিউরিটির জন্য এই ভিডিওটি <b>{del_minutes} মিনিট</b> পর অটোমেটিক ডিলিট হয়ে যাবে!</i>"
            db_file_id = m.get("db_file_id")
            sent_msg = None
            if db_file_id and DB_CHANNEL_ID:
                sent_msg = await bot.copy_message(chat_id=d.userId, from_chat_id=DB_CHANNEL_ID, message_id=db_file_id, caption=caption, parse_mode="HTML", protect_content=is_protected)
            else:
                if m.get("file_type") == "video": sent_msg = await bot.send_video(d.userId, m['file_id'], caption=caption, parse_mode="HTML", protect_content=is_protected)
                else: sent_msg = await bot.send_document(d.userId, m['file_id'], caption=caption, parse_mode="HTML", protect_content=is_protected)
            await db.user_unlocks.update_one({"user_id": d.userId, "movie_id": d.movieId}, {"$set": {"unlocked_at": now}}, upsert=True)
            if sent_msg and not is_vip: await db.auto_delete.insert_one({"chat_id": d.userId, "message_id": sent_msg.message_id, "delete_at": now + datetime.timedelta(minutes=del_minutes)})
    except Exception: pass
    return {"ok": True}

@api_router.post("/api/request")
async def handle_request(data: ReqModel):
    if not validate_tg_data(data.initData): return {"ok": False}
    user = await db.users.find_one({"user_id": data.uid})
    is_vip = False
    if user and user.get("vip_until", datetime.datetime.utcnow()) > datetime.datetime.utcnow(): is_vip = True
    vip_tag = "🔥 <b>[VIP PRIORITY]</b>\n" if is_vip else ""
    now = datetime.datetime.utcnow()
    await db.requests.insert_one({"user_id": data.uid, "uname": data.uname, "movie": data.movie, "status": "pending", "created_at": now, "is_vip": is_vip})
    all_admins = set([OWNER_ID])
    async for a in db.admins.find(): all_admins.add(a["user_id"])
    for admin_id in all_admins:
        try: await bot.send_message(admin_id, f"{vip_tag}🔔 <b>নতুন মুভি রিকোয়েস্ট!</b>\n👤 ইউজার: {data.uname} (<code>{data.uid}</code>)\n🎬 মুভি: <b>{data.movie}</b>", parse_mode="HTML")
        except Exception: pass
    return {"ok": True}

# ==========================================
# 🛑 Advertising Campaign APIs
# ==========================================
@api_router.post("/api/ads/create")
async def create_sponsored_ad(d: AdCreateModel):
    if not validate_tg_data(d.initData): return {"ok": False, "msg": "Invalid Request"}
    costs = {1: 500, 3: 1200, 7: 2500}
    cost = costs.get(d.package, 500)
    days = d.package if d.package in costs else 1
    user = await db.users.find_one({"user_id": d.uid})
    if not user or user.get("coins", 0) < cost: return {"ok": False, "msg": f"Not enough points! Need {cost} points."}
    now = datetime.datetime.utcnow()
    await db.users.update_one({"user_id": d.uid}, {"$inc": {"coins": -cost}})
    await db.ads.insert_one({"user_id": d.uid, "title": d.title, "subtitle": d.subtitle, "link": d.link, "image_url": d.image_url, "created_at": now, "expires_at": now + datetime.timedelta(days=days)})
    try: await bot.send_message(OWNER_ID, f"📢 <b>New Ad Campaign Started!</b>\n👤 User ID: <code>{d.uid}</code>\n📝 Title: {d.title}\n🔗 Link: {d.link}\n⏳ Duration: {days} Days\n💰 Paid: {cost} Coins", parse_mode="HTML")
    except: pass
    return {"ok": True, "msg": "Ad campaign started successfully!"}

@api_router.get("/api/ads/active")
async def get_active_ads():
    now = datetime.datetime.utcnow()
    ads = await db.ads.find({"expires_at": {"$gte": now}}).sort("created_at", -1).to_list(20)
    for ad in ads: ad['_id'] = str(ad['_id'])
    return ads

# ==========================================
# 🛑 Watchlist & Review System APIs
# ==========================================
@api_router.post("/api/watchlist/add")
async def add_to_watchlist(d: WatchlistModel):
    if not validate_tg_data(d.initData): return {"ok": False}
    await db.users.update_one({"user_id": d.uid}, {"$addToSet": {"watchlist": d.title}})
    return {"ok": True}

@api_router.post("/api/watchlist/remove")
async def remove_from_watchlist(d: WatchlistModel):
    if not validate_tg_data(d.initData): return {"ok": False}
    await db.users.update_one({"user_id": d.uid}, {"$pull": {"watchlist": d.title}})
    return {"ok": True}

@api_router.get("/api/watchlist/list/{uid}")
async def get_watchlist(uid: int):
    user = await db.users.find_one({"user_id": uid})
    if not user: return {"watchlist": []}
    watchlist = user.get("watchlist", [])
    if not watchlist: return {"watchlist": []}
    pipeline = [{"$match": {"title": {"$in": watchlist}}}, {"$group": {"_id": "$title", "photo_id": {"$first": "$photo_id"}, "db_photo_id": {"$first": "$db_photo_id"}, "clicks": {"$sum": "$clicks"}, "created_at": {"$max": "$created_at"}, "files": {"$push": {"id": {"$toString": "$_id"}, "quality": {"$ifNull": ["$quality", "HD"]}}}}}, {"$sort": {"created_at": -1}}]
    movies = await db.movies.aggregate(pipeline).to_list(len(watchlist))
    formatted_movies = []
    for m in movies:
        p_id = m.get("photo_id") or (f"db_{m['db_photo_id']}" if m.get("db_photo_id") else None)
        formatted_movies.append({"title": m["_id"], "photo_id": p_id, "files": m["files"], "clicks": m.get("clicks", 0)})
    return {"watchlist": formatted_movies}

@api_router.post("/api/reviews/add")
async def add_review(d: ReviewModel):
    if not validate_tg_data(d.initData): return {"ok": False}
    now = datetime.datetime.utcnow()
    await db.reviews.update_one({"user_id": d.uid, "movie_title": d.title}, {"$set": {"user_id": d.uid, "uname": d.uname, "movie_title": d.title, "rating": d.rating, "review": d.review, "created_at": now}}, upsert=True)
    return {"ok": True}

@api_router.get("/api/reviews/get/{title}")
async def get_reviews(title: str):
    reviews = await db.reviews.find({"movie_title": title}).sort("created_at", -1).to_list(50)
    avg_r = sum(r["rating"] for r in reviews) / len(reviews) if reviews else 0
    for r in reviews:
        r["_id"] = str(r["_id"])
        r["created_at"] = r["created_at"].isoformat()
    return {"reviews": reviews, "avg_rating": round(avg_r, 1)}

# ==========================================
# 🛑 Gamification Daily Activity & Wheel
# ==========================================
@api_router.post("/api/gamification/daily_checkin")
async def daily_checkin(d: UserActionModel):
    if not validate_tg_data(d.initData): return {"ok": False}
    user = await db.users.find_one({"user_id": d.uid})
    if not user: return {"ok": False, "msg": "User not found"}
    now = datetime.datetime.utcnow()
    last_c = user.get("last_check_in")
    if last_c and last_c.date() == now.date(): return {"ok": False, "msg": "Already checked in today!"}
    await db.users.update_one({"user_id": d.uid}, {"$set": {"last_check_in": now}, "$inc": {"coins": 5}})
    return {"ok": True, "coins": user.get("coins", 0) + 5}

@api_router.post("/api/gamification/spin")
async def spin_wheel(d: UserActionModel):
    if not validate_tg_data(d.initData): return {"ok": False}
    user = await db.users.find_one({"user_id": d.uid})
    if not user or user.get("coins", 0) < 5: return {"ok": False, "msg": "Not enough points! Need 5 points to spin."}
    rewards = [{"type": "points", "amount": 0, "weight": 35}, {"type": "points", "amount": 2, "weight": 25}, {"type": "points", "amount": 5, "weight": 20}, {"type": "points", "amount": 10, "weight": 12}, {"type": "points", "amount": 20, "weight": 5}, {"type": "points", "amount": 50, "weight": 2}, {"type": "vip", "days": 1, "weight": 1}]
    choices = []
    for r in rewards: choices.extend([r] * r["weight"])
    reward = random.choice(choices)
    await db.users.update_one({"user_id": d.uid}, {"$inc": {"coins": -5}})
    msg = ""
    if reward["type"] == "points":
        if reward["amount"] > 0:
            await db.users.update_one({"user_id": d.uid}, {"$inc": {"coins": reward["amount"]}})
            msg = f"You won {reward['amount']} Points!"
        else: msg = "Better luck next time!"
    elif reward["type"] == "vip":
        now = datetime.datetime.utcnow()
        cv = user.get("vip_until", now) if user.get("vip_until") else now
        if cv < now: cv = now
        await db.users.update_one({"user_id": d.uid}, {"$set": {"vip_until": cv + datetime.timedelta(days=1)}})
        msg = "Congratulations! You won 1 Day VIP Pass!"
    return {"ok": True, "reward": reward, "msg": msg}

@api_router.get("/api/gamification/leaderboard")
async def get_leaderboard():
    tops = await db.users.find().sort("refer_count", -1).limit(10).to_list(10)
    lead = []
    for u in tops: 
        lead.append({"name": u.get("first_name", "User"), "refer_count": u.get("refer_count", 0), "coins": u.get("coins", 0)})
    return {"leaderboard": lead}

@api_router.get("/api/requests/user_list/{uid}")
async def user_requests(uid: int):
    reqs = await db.requests.find({"user_id": uid}).sort("created_at", -1).to_list(50)
    for r in reqs:
        r["_id"] = str(r["_id"])
        r["created_at"] = r["created_at"].isoformat()
    return {"requests": reqs}

# ==========================================
# 🛑 Backend Web Admin Dashboard & API Logs
# ==========================================
@api_router.get("/api/admin/stats")
async def admin_stats_api(auth: bool = Depends(verify_admin)):
    user_count = await db.users.count_documents({})
    movie_count = await db.movies.count_documents({})
    total_views = 0
    views_agg = await db.movies.aggregate([{"$group": {"_id": None, "total": {"$sum": "$clicks"}}}]).to_list(1)
    if views_agg: total_views = views_agg[0]["total"]
    return {"users": user_count, "movies": movie_count, "views": total_views}

@api_router.get("/api/admin/data")
async def get_admin_data(page: int = 1, q: str = "", auth: bool = Depends(verify_admin)):
    limit = 20
    skip = (page - 1) * limit
    match_stage = {"title": {"$regex": q, "$options": "i"}} if q else {}
    
    pipeline = [
        {"$match": match_stage},
        {"$group": {"_id": "$title", "clicks": {"$sum": "$clicks"}, "file_count": {"$sum": 1}, "created_at": {"$max": "$created_at"}, "categories": {"$first": "$categories"}}}, 
        {"$sort": {"created_at": -1}}, 
        {"$skip": skip}, 
        {"$limit": limit}
    ]
    movies = await db.movies.aggregate(pipeline).to_list(limit)
    
    total_groups = await db.movies.aggregate([{"$match": match_stage}, {"$group": {"_id": "$title"}}, {"$count": "total"}]).to_list(1)
    total_pages = (total_groups[0]["total"] + limit - 1) // limit if total_groups else 0
    
    return {"movies": movies, "total_pages": total_pages}

@api_router.delete("/api/admin/movie/{title}")
async def delete_movie_api(title: str, auth: bool = Depends(verify_admin)):
    await db.movies.delete_many({"title": title})
    clear_app_cache() 
    return {"ok": True}

@api_router.put("/api/admin/movie/{title}")
async def edit_movie_api(title: str, data: dict = Body(...), auth: bool = Depends(verify_admin)):
    if add_clicks := data.get("add_clicks"):
        await db.movies.update_many({"title": title}, {"$inc": {"clicks": int(add_clicks)}})
    if "new_categories" in data:
        await db.movies.update_many({"title": title}, {"$set": {"categories": data["new_categories"]}})
    clear_app_cache() 
    return {"ok": True}

@api_router.post("/api/admin/ads/create")
async def create_admin_ad(d: AdminAdModel, auth: bool = Depends(verify_admin)):
    await db.ads.insert_one({"user_id": 0, "title": d.title, "subtitle": d.subtitle, "link": d.link, "image_url": d.image_url, "created_at": datetime.datetime.utcnow(), "expires_at": datetime.datetime.utcnow() + datetime.timedelta(days=365)})
    return {"ok": True}

@api_router.get("/api/admin/ads_list")
async def get_all_ads(auth: bool = Depends(verify_admin)):
    ads = await db.ads.find().sort("created_at", -1).to_list(50)
    for ad in ads: ad['_id'] = str(ad['_id'])
    return {"ads": ads}

@api_router.delete("/api/admin/ads/{ad_id}")
async def delete_ad(ad_id: str, auth: bool = Depends(verify_admin)):
    await db.ads.delete_one({"_id": ObjectId(ad_id)})
    return {"ok": True}

@api_router.get("/api/admin/requests")
async def admin_get_requests(auth: bool = Depends(verify_admin)):
    reqs = await db.requests.find().sort("created_at", -1).to_list(100)
    for r in reqs:
        r["_id"] = str(r["_id"])
        r["created_at"] = r["created_at"].isoformat()
    return {"requests": reqs}

@api_router.put("/api/admin/requests/{req_id}")
async def admin_update_request(req_id: str, data: dict = Body(...), auth: bool = Depends(verify_admin)):
    await db.requests.update_one({"_id": ObjectId(req_id)}, {"$set": {"status": data.get("status")}})
    return {"ok": True}

@api_router.delete("/api/admin/requests/{req_id}")
async def admin_delete_request(req_id: str, auth: bool = Depends(verify_admin)):
    await db.requests.delete_one({"_id": ObjectId(req_id)})
    return {"ok": True}

@api_router.get("/api/admin/keywords")
async def get_keywords_api(auth: bool = Depends(verify_admin)):
    kws = await db.keyword_replies.find().to_list(100)
    for kw in kws: kw["_id"] = str(kw["_id"])
    return {"keywords": kws}

@api_router.post("/api/admin/keywords")
async def add_keyword_api(data: dict = Body(...), auth: bool = Depends(verify_admin)):
    kw = data.get("keyword", "").lower().strip()
    rep = data.get("reply_message", "").strip()
    if not kw or not rep: raise HTTPException(status_code=400, detail="Missing data")
    await db.keyword_replies.update_one({"keyword": kw}, {"$set": {"keyword": kw, "reply_message": rep}}, upsert=True)
    await load_keyword_replies()
    return {"ok": True}

@api_router.delete("/api/admin/keywords/{keyword}")
async def delete_keyword_api(keyword: str, auth: bool = Depends(verify_admin)):
    await db.keyword_replies.delete_one({"keyword": keyword.lower()})
    await load_keyword_replies()
    return {"ok": True}

@api_router.get("/api/admin/users/search")
async def search_users(q: str = "", auth: bool = Depends(verify_admin)):
    ms = {}
    if q:
        if q.isdigit(): ms["user_id"] = int(q)
        else: ms["first_name"] = {"$regex": q, "$options": "i"}
    users = await db.users.find(ms).limit(20).to_list(20)
    form = []
    now = datetime.datetime.utcnow()
    for u in users:
        uid = u["user_id"]
        is_b = uid in banned_cache or (await db.banned.find_one({"user_id": uid}) is not None)
        form.append({
            "user_id": uid, 
            "first_name": u.get("first_name", "User"), 
            "coins": u.get("coins", 0), 
            "refer_count": u.get("refer_count", 0), 
            "is_vip": u.get("vip_until", now) > now, 
            "is_banned": is_b
        })
    return {"users": form}

@api_router.post("/api/admin/users/action")
async def manage_user_action(d: UserManageModel, auth: bool = Depends(verify_admin)):
    uid = d.user_id
    now = datetime.datetime.utcnow()
    if d.action == "ban":
        await db.banned.update_one({"user_id": uid}, {"$set": {"user_id": uid}}, upsert=True)
        banned_cache.add(uid)
    elif d.action == "unban":
        await db.banned.delete_one({"user_id": uid})
        banned_cache.discard(uid)
    elif d.action == "add_coins": await db.users.update_one({"user_id": uid}, {"$inc": {"coins": d.value}})
    elif d.action == "remove_coins": await db.users.update_one({"user_id": uid}, {"$inc": {"coins": -d.value}})
    elif d.action == "add_vip":
        user = await db.users.find_one({"user_id": uid})
        cv = user.get("vip_until", now) if user else now
        if cv < now: cv = now
        await db.users.update_one({"user_id": uid}, {"$set": {"vip_until": cv + datetime.timedelta(days=d.value)}})
    elif d.action == "remove_vip": await db.users.update_one({"user_id": uid}, {"$set": {"vip_until": now - datetime.timedelta(days=1)}})
    return {"ok": True}

@api_router.get("/api/admin/analytics")
async def get_analytics(auth: bool = Depends(verify_admin)):
    now = datetime.datetime.utcnow()
    t_start = datetime.datetime(now.year, now.month, now.day)
    seven_d = t_start - datetime.timedelta(days=7)
    live = await db.users.count_documents({"last_active": {"$gte": now - datetime.timedelta(minutes=5)}})
    a_t = await db.user_unlocks.distinct("user_id", {"unlocked_at": {"$gte": t_start}})
    a_w = await db.user_unlocks.distinct("user_id", {"unlocked_at": {"$gte": seven_d}})
    c_s = await db.movies.aggregate([{"$unwind": "$categories"}, {"$group": {"_id": "$categories", "total_views": {"$sum": "$clicks"}}}, {"$sort": {"total_views": -1}}, {"$limit": 5}]).to_list(5)
    t_r = await db.reviews.aggregate([{"$group": {"_id": "$movie_title", "avg_rating": {"$avg": "$rating"}, "total_reviews": {"$sum": 1}}}, {"$sort": {"avg_rating": -1, "total_reviews": -1}}, {"$limit": 5}]).to_list(5)
    return {"live_online": live, "active_today": len(a_t), "active_week": len(a_w), "total_reviews": await db.reviews.count_documents({}), "total_requests": await db.requests.count_documents({}), "pending_requests": await db.requests.count_documents({"status": "pending"}), "category_stats": c_s, "top_rated": t_r}
