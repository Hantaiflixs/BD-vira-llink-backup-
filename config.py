# config.py
import os
import asyncio
import logging
from cachetools import TTLCache
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client as PyroClient
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from fastapi import FastAPI
from fastapi.security import HTTPBasic

# ইভেন্ট লুপ ফিক্স
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# কনফিগারেশন ভ্যারিয়েবলসমূহ
TOKEN = os.environ.get("TOKEN")                  
API_ID = "37875259"                              
API_HASH = "d7c626c8cd1f358b04178ca0fd803ded"                
SESSION_STRING = ""                            
MONGO_URL = "mongodb+srv://kentkouhnae1f:rCKrDhIdpLEkF0Qc@cluster0.lsxeyl3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"              
OWNER_ID = 8698935150                    
CHANNEL_ID = "-1004487224429"                   
ADMIN_PASS = "admin123"                        
BOT_USERNAME = "bdvirallink_1bot"                

APP_URL = os.getenv("APP_URL", "http://localhost:8000")

TUTORIAL_LINK = "https://t.me/howtodowloadvideo/2"
REQUEST_LINK = "https://t.me/+4bfJX8PLBLc2MjI9"

_db_ch = "-1004328471246"                       
DB_CHANNEL_ID = int(_db_ch) if _db_ch.lstrip('-').isdigit() else None

PORT_NUMBER = 8000                             

# বটের মূল অবজেক্ট (HTML পার্স মোড সহ)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()
security = HTTPBasic()

# পাইরোগ্রাম ক্লায়েন্ট সেটআপ
if SESSION_STRING:
    pyro_app = PyroClient("user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING, in_memory=True, no_updates=True)
else:
    pyro_app = PyroClient("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN, in_memory=True, no_updates=True)

# ডাটাবেস ক্লায়েন্ট সেটআপ
client = AsyncIOMotorClient(MONGO_URL)
db = client['movie_database']

# ক্যাশ মেমোরি সেটআপ
admin_cache = set([OWNER_ID]) 
banned_cache = set() 

trending_cache = TTLCache(maxsize=10, ttl=3600)
list_cache = TTLCache(maxsize=100, ttl=3600)
category_cache = TTLCache(maxsize=5, ttl=43200)
auto_reply_cache = TTLCache(maxsize=1000, ttl=10) 

keyword_replies_cache = {}

# অটো-আপলোড কিউ (Queue)
video_queue = asyncio.Queue()

# ডাটাবেস থেকে কনফিগারেশন ও ক্যাশ লোড করার ফাংশনসমূহ
async def load_keyword_replies():
    keyword_replies_cache.clear()
    async for kw in db.keyword_replies.find():
        keyword_replies_cache[kw["keyword"]] = kw["reply_message"]

async def load_admins():
    admin_cache.clear()
    admin_cache.add(OWNER_ID)
    async for admin in db.admins.find(): 
        admin_cache.add(admin["user_id"])

async def load_banned_users():
    banned_cache.clear()
    async for b_user in db.banned.find(): 
        banned_cache.add(b_user["user_id"])

def clear_app_cache():
    trending_cache.clear()
    list_cache.clear()
    category_cache.clear()
