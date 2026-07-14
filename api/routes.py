# api/routes.py
import datetime
import json
import random
import aiohttp
import html
from fastapi import APIRouter, Depends, Body, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from bson import ObjectId
import copy

from config import (
    db, bot, OWNER_ID, BOT_USERNAME, DB_CHANNEL_ID,
    admin_cache, banned_cache, trending_cache, list_cache,
    clear_app_cache, TOKEN, logger
)
from helpers import validate_tg_data, verify_admin, format_views

try:
    from html_template import HTML_CODE
except ImportError:
    pass

api_router = APIRouter()

# ==========================================
# ⚡ Global System Settings (LIVE MODE)
# ==========================================
settings_cache = {}

async def fetch_setting(setting_id: str):
    # Cache system off kora holo jate bot er command sathe sathe web e kaj kore
    cfg = await db.settings.find_one({"id": setting_id})
    return cfg

def invalidate_settings_cache():
    settings_cache.clear()

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

class InteractRequestModel(BaseModel):
    video_id: str
    telegram_id: int
    action: str
    comment_text: str = None

# ==========================================
# 🛑 System Settings API
# ==========================================
@api_router.get("/api/admin/sys_settings")
async def get_sys_settings(auth: bool = Depends(verify_admin)):
    cost_cfg = await fetch_setting("vip_cost")
    days_cfg = await fetch_setting("vip_days")
    unlock_cfg = await fetch_setting("unlock_hours")
    social_cfg = await fetch_setting("social_links")
    interval_cfg = await fetch_setting("ad_interval") 
    
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
    
    invalidate_settings_cache()
    clear_app_cache()
    return {"ok": True}

# ==========================================
# 🛑 Render Admin Web Panel Dashboard (HTML)
# ==========================================
@api_router.get("/admin", response_class=HTMLResponse)
async def web_admin_panel(auth: bool = Depends(verify_admin)):
    html_content = """
    <!DOCTYPE html>
    <html lang="bn">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Panel - MovieZone BD</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            .neon-card {
                background: rgba(30, 41, 59, 0.7);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.05);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            }
            .pulse-dot {
                animation: blink 1.5s infinite;
            }
            @keyframes blink {
                0%, 100% { opacity: 0.2; transform: scale(0.9); }
                50% { opacity: 1; transform: scale(1.1); }
            }
        </style>
    </head>
    <body class="bg-gray-950 text-white p-5 font-sans">
        <div class="max-w-6xl mx-auto">
            <h1 class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-amber-500 mb-6 border-b border-gray-800 pb-3 flex items-center gap-2">
                <i class="fa-solid fa-gauge-high"></i> Ultimate Admin Dashboard
            </h1>
            
            <div class="flex flex-wrap gap-2 mb-6 border-b border-gray-800 pb-3">
                <button onclick="switchAdminTab('dashboard')" id="tabBtn-dashboard" class="px-4 py-2 bg-blue-600 rounded text-white font-bold transition">Dashboard & Analytics</button>
                <button onclick="switchAdminTab('users')" id="tabBtn-users" class="px-4 py-2 bg-gray-800 hover:bg-gray-750 rounded text-gray-300 font-bold transition">User Manager</button>
                <button onclick="switchAdminTab('settings')" id="tabBtn-settings" class="px-4 py-2 bg-gray-800 hover:bg-gray-750 rounded text-gray-300 font-bold transition">System Settings</button>
                <button onclick="switchAdminTab('social')" id="tabBtn-social" class="px-4 py-2 bg-gray-800 hover:bg-gray-750 rounded text-gray-300 font-bold transition">Social Links</button>
                <button onclick="switchAdminTab('movies')" id="tabBtn-movies" class="px-4 py-2 bg-gray-800 hover:bg-gray-750 rounded text-gray-300 font-bold transition">Manage Videos</button>
                <button onclick="switchAdminTab('ads')" id="tabBtn-ads" class="px-4 py-2 bg-gray-800 hover:bg-gray-750 rounded text-gray-300 font-bold transition">Ads Manager</button>
                <button onclick="switchAdminTab('keywords')" id="tabBtn-keywords" class="px-4 py-2 bg-gray-800 hover:bg-gray-750 rounded text-gray-300 font-bold transition">Keyword Replies</button>
                <button onclick="switchAdminTab('requests')" id="tabBtn-requests" class="px-4 py-2 bg-gray-800 hover:bg-gray-750 rounded text-gray-300 font-bold transition">User Requests</button>
            </div>

            <div id="adminTab-dashboard" class="admin-tab-content">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8" id="statsBoard">
                    <div class="neon-card p-5 rounded-2xl border-l-4 border-green-500 flex items-center justify-between shadow-lg">
                        <div class="flex items-center gap-3">
                            <div class="bg-green-500/10 p-4 rounded-xl text-green-400 text-2xl relative">
                                <i class="fa-solid fa-wave-square"></i>
                                <span class="absolute top-1 right-1 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-gray-950 pulse-dot"></span>
                            </div>
                            <div>
                                <p class="text-gray-400 text-xs font-bold uppercase tracking-wider">Live Online</p>
                                <h3 class="text-2xl font-black text-green-400" id="stLiveOnline">0</h3>
                            </div>
                        </div>
                        <span class="text-xs text-green-500/80 font-semibold bg-green-500/10 px-2 py-0.5 rounded-full">App Activity</span>
                    </div>
                    
                    <div class="neon-card p-5 rounded-2xl border-l-4 border-blue-500 flex items-center gap-3 shadow-lg">
                        <div class="bg-blue-600/10 p-4 rounded-xl text-blue-400 text-2xl"><i class="fa-solid fa-users"></i></div>
                        <div><p class="text-gray-400 text-xs font-bold uppercase tracking-wider">Total Users</p><h3 class="text-2xl font-black text-blue-400" id="stUsers">...</h3></div>
                    </div>
                    <div class="neon-card p-5 rounded-2xl border-l-4 border-orange-500 flex items-center gap-3 shadow-lg">
                        <div class="bg-orange-600/10 p-4 rounded-xl text-orange-400 text-2xl"><i class="fa-solid fa-video"></i></div>
                        <div><p class="text-gray-400 text-xs font-bold uppercase tracking-wider">Total Videos</p><h3 class="text-2xl font-black text-orange-400" id="stMovies">...</h3></div>
                    </div>
                    <div class="neon-card p-5 rounded-2xl border-l-4 border-purple-500 flex items-center gap-3 shadow-lg">
                        <div class="bg-purple-600/10 p-4 rounded-xl text-purple-400 text-2xl"><i class="fa-solid fa-eye"></i></div>
                        <div><p class="text-gray-400 text-xs font-bold uppercase tracking-wider">Total Views</p><h3 class="text-2xl font-black text-purple-400" id="stViews">...</h3></div>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div class="neon-card rounded-2xl p-6 shadow-xl col-span-1">
                        <h2 class="text-lg font-bold text-gray-200 mb-4 flex items-center gap-2"><i class="fa-solid fa-chart-line text-blue-500"></i> Active Statistics</h2>
                        <div class="grid grid-cols-1 gap-4">
                            <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-850">
                                <p class="text-xs text-gray-400 font-bold uppercase">Active Today (DAU)</p>
                                <h3 id="analyticsDau" class="text-2xl font-bold text-green-400">0</h3>
                            </div>
                            <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-850">
                                <p class="text-xs text-gray-400 font-bold uppercase">Active Weekly (WAU)</p>
                                <h3 id="analyticsWau" class="text-2xl font-bold text-blue-400">0</h3>
                            </div>
                            <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-850">
                                <p class="text-xs text-gray-400 font-bold uppercase">Total User Reviews</p>
                                <h3 id="analyticsReviews" class="text-2xl font-bold text-yellow-400">0</h3>
                            </div>
                        </div>
                    </div>

                    <div class="neon-card rounded-2xl p-6 shadow-xl col-span-2">
                        <h2 class="text-lg font-bold text-gray-200 mb-4 flex items-center gap-2"><i class="fa-solid fa-chart-bar text-purple-500"></i> Top Videos by Views</h2>
                        <div class="h-64 relative">
                            <canvas id="categoryChart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="neon-card rounded-2xl p-6 shadow-xl mb-8">
                    <h2 class="text-lg font-bold text-gray-200 mb-4"><i class="fa-solid fa-star text-yellow-400"></i> Top Rated Videos (By User Reviews)</h2>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-sm whitespace-nowrap">
                            <thead class="bg-gray-900/80 text-gray-300">
                                <tr>
                                    <th class="p-4 rounded-l-lg">Video Title</th>
                                    <th class="p-4">Average Rating</th>
                                    <th class="p-4 rounded-r-lg">Total Reviews</th>
                                </tr>
                            </thead>
                            <tbody id="analyticsTopRatedList">
                                <tr><td colspan="3" class="p-4 text-center text-gray-500">Loading top rated videos...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div id="adminTab-users" class="admin-tab-content hidden">
                <div class="neon-card rounded-2xl shadow-xl p-6 mb-8">
                    <div class="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
                        <h2 class="text-xl font-bold text-blue-400 flex items-center gap-2"><i class="fa-solid fa-users-gear"></i> User Manager Panel</h2>
                        <div class="relative w-full md:w-1/3">
                            <input type="text" id="userSearchInput" placeholder="🔍 Search UID or Name..." oninput="searchUsers()" class="w-full bg-gray-900 text-white px-4 py-2 rounded-xl border border-gray-800 focus:outline-none focus:border-blue-500">
                        </div>
                    </div>
                    
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-sm whitespace-nowrap">
                            <thead class="bg-gray-900/80 text-gray-300">
                                <tr>
                                    <th class="p-4 rounded-l-lg">User Info</th>
                                    <th class="p-4">Points</th>
                                    <th class="p-4">VIP Status</th>
                                    <th class="p-4">Invites</th>
                                    <th class="p-4 rounded-r-lg text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody id="userTableBody">
                                <tr><td colspan="5" class="text-center p-8 text-gray-400">Search for a user by name or UID to begin managing...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div id="adminTab-settings" class="admin-tab-content hidden">
                <div class="neon-card rounded-2xl shadow-xl p-6 mb-8">
                    <h2 class="text-xl font-bold text-gray-200 mb-4"><i class="fa-solid fa-cogs"></i> System Settings</h2>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div>
                            <label class="text-gray-400 text-sm font-bold block mb-1">VIP Cost (Points)</label>
                            <input type="number" id="cfgVipCost" class="w-full bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none">
                        </div>
                        <div>
                            <label class="text-gray-400 text-sm font-bold block mb-1">VIP Duration (Days)</label>
                            <input type="number" id="cfgVipDays" class="w-full bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none">
                        </div>
                        <div>
                            <label class="text-gray-400 text-sm font-bold block mb-1">Video Unlock (Hours)</label>
                            <input type="number" id="cfgUnlockHrs" class="w-full bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none">
                        </div>
                        <div>
                            <label class="text-gray-400 text-sm font-bold block mb-1">Ad Interval (Videos Limit)</label>
                            <input type="number" id="cfgAdInterval" placeholder="e.g. 3 or 4" class="w-full bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none">
                        </div>
                    </div>
                    <button onclick="saveSysSettings()" class="mt-4 bg-green-600 hover:bg-green-500 text-white px-6 py-2 rounded font-bold transition">Save Settings</button>
                </div>
            </div>

            <div id="adminTab-social" class="admin-tab-content hidden">
                <div class="neon-card rounded-2xl shadow-xl p-6 mb-8">
                    <h2 class="text-xl font-bold text-blue-400 mb-4"><i class="fa-solid fa-share-nodes"></i> Social Media Links</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="text-gray-400 text-sm font-bold block mb-1">Facebook Group</label>
                            <input type="url" id="cfgFbGroup" placeholder="https://facebook.com/groups/..." class="w-full bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none">
                        </div>
                        <div>
                            <label class="text-gray-400 text-sm font-bold block mb-1">Facebook Page</label>
                            <input type="url" id="cfgFbPage" placeholder="https://facebook.com/..." class="w-full bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none">
                        </div>
                        <div>
                            <label class="text-gray-400 text-sm font-bold block mb-1">YouTube Channel</label>
                            <input type="url" id="cfgYoutube" placeholder="https://youtube.com/..." class="w-full bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none">
                        </div>
                        <div>
                            <label class="text-gray-400 text-sm font-bold block mb-1">Video Review Channel</label>
                            <input type="url" id="cfgReview" placeholder="https://t.me/..." class="w-full bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none">
                        </div>
                    </div>
                    <button onclick="saveSysSettings()" class="mt-4 bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded font-bold transition">Save Social Links</button>
                </div>
            </div>

            <div id="adminTab-movies" class="admin-tab-content hidden">
                <div class="neon-card rounded-2xl shadow-xl p-6 mb-8">
                    <div class="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
                        <h2 class="text-xl font-bold text-gray-200"><i class="fa-solid fa-list-ul"></i> Manage Videos</h2>
                        <input type="text" id="adminSearch" placeholder="🔍 Search Videos..." class="bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:outline-none w-full md:w-1/3">
                    </div>

                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-sm whitespace-nowrap">
                            <thead class="bg-gray-700 text-gray-300">
                                <tr><th class="p-4">Title</th><th class="p-4">Views</th><th class="p-4">Parts</th><th class="p-4">Action</th></tr>
                            </thead>
                            <tbody id="movieTableBody"><tr><td colspan="4" class="text-center p-8 text-gray-400">Loading...</td></tr></tbody>
                        </table>
                    </div>
                    <div class="flex justify-center items-center gap-3 mt-6" id="adminPagination"></div>
                </div>
            </div>

            <div id="adminTab-ads" class="admin-tab-content hidden">
                <div class="neon-card rounded-2xl shadow-xl p-6">
                    <div class="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
                        <h2 class="text-xl font-bold text-yellow-400"><i class="fa-solid fa-bullhorn"></i> Ads Manager (Sponsored)</h2>
                    </div>
                    
                    <div class="bg-gray-900 p-4 rounded-lg border border-gray-700 mb-6">
                        <h3 class="text-gray-300 font-bold mb-3">Create Free Ad (Admin Only)</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                            <input type="text" id="adTitle" placeholder="Ad Title (e.g. Free Cashout)" class="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:outline-none">
                            <input type="text" id="adSubtitle" placeholder="Ad Subtitle / Short Description" class="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:outline-none">
                            <input type="text" id="adLink" placeholder="URL / Link" class="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:outline-none">
                            <input type="text" id="adImage" placeholder="Image URL (Optional)" class="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:outline-none">
                        </div>
                        <button onclick="createAdminAd()" class="bg-yellow-600 hover:bg-yellow-500 text-white px-6 py-2 rounded font-bold whitespace-nowrap">Create Ad</button>
                    </div>

                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-sm whitespace-nowrap">
                            <thead class="bg-gray-700 text-gray-300">
                                <tr><th class="p-4">Title</th><th class="p-4">Subtitle</th><th class="p-4">Link</th><th class="p-4">Expires</th><th class="p-4">Action</th></tr>
                            </thead>
                            <tbody id="adsTableBody"><tr><td colspan="5" class="text-center p-8 text-gray-400">Loading Ads...</td></tr></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div id="adminTab-keywords" class="admin-tab-content hidden">
                <div class="neon-card rounded-2xl border border-gray-700 p-6 shadow mb-8">
                    <h2 class="text-xl font-bold text-gray-200 mb-4"><i class="fa-solid fa-reply text-green-500"></i> Auto-Reply Keyword Manager</h2>
                    
                    <div class="bg-gray-900 p-4 rounded-lg border border-gray-700 mb-6">
                        <h3 class="text-gray-300 font-bold mb-3">Add Custom Keyword Reply</h3>
                        <div class="flex flex-col md:flex-row gap-3">
                            <input type="text" id="kwInput" placeholder="Keyword (e.g. pushpa 2)" class="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:outline-none md:w-1/3">
                            <input type="text" id="kwReplyInput" placeholder="Reply Message" class="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:outline-none flex-grow">
                            <button onclick="addKeywordReply()" class="bg-green-600 hover:bg-green-500 text-white px-6 py-2 rounded font-bold whitespace-nowrap">Add Rule</button>
                        </div>
                    </div>

                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-sm whitespace-nowrap">
                            <thead class="bg-gray-700 text-gray-300">
                                <tr><th class="p-4">Keyword</th><th class="p-4">Reply Message</th><th class="p-4">Action</th></tr>
                            </thead>
                            <tbody id="keywordsTableBody">
                                <tr><td colspan="3" class="p-4 text-center text-gray-500">Loading custom keyword rules...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div id="adminTab-requests" class="admin-tab-content hidden">
                <div class="neon-card rounded-2xl border border-gray-700 p-6 shadow mb-8">
                    <h2 class="text-xl font-bold text-gray-200 mb-4"><i class="fa-solid fa-code-pull-request text-red-500"></i> User Video Requests Management</h2>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-sm whitespace-nowrap">
                            <thead class="bg-gray-700 text-gray-300">
                                <tr>
                                    <th class="p-4">User Name (UID)</th>
                                    <th class="p-4">Requested Video</th>
                                    <th class="p-4">Priority Status</th>
                                    <th class="p-4">Actions</th>
                                </tr>
                            </thead>
                            <tbody id="requestsTableBody">
                                <tr><td colspan="4" class="text-center p-8 text-gray-400">Loading requests...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

        </div>
        <script>
            let currentPage = 1;
            let searchQuery = "";
            let searchTimeout = null;
            let categoryChart = null;

            async function switchAdminTab(tabId) {
                document.querySelectorAll('.admin-tab-content').forEach(content => content.classList.add('hidden'));
                document.getElementById('adminTab-' + tabId).classList.remove('hidden');
                
                document.querySelectorAll('[id^="tabBtn-"]').forEach(btn => {
                    btn.className = "px-4 py-2 bg-gray-800 hover:bg-gray-750 rounded text-gray-300 font-bold transition";
                });
                document.getElementById('tabBtn-' + tabId).className = "px-4 py-2 bg-blue-600 rounded text-white font-bold transition";

                if (tabId === 'dashboard') { loadStats(); loadAnalytics(); }
                else if (tabId === 'users') { searchUsers(); }
                else if (tabId === 'settings') { loadSysSettings(); }
                else if (tabId === 'movies') { loadAdminData(1); }
                else if (tabId === 'ads') { loadAds(); }
                else if (tabId === 'keywords') { loadKeywordList(); }
                else if (tabId === 'requests') { loadAdminRequests(); }
            }

            async function loadSysSettings() {
                try {
                    const res = await fetch('/api/admin/sys_settings');
                    const data = await res.json();
                    document.getElementById('cfgVipCost').value = data.vip_cost;
                    document.getElementById('cfgVipDays').value = data.vip_days;
                    document.getElementById('cfgUnlockHrs').value = data.unlock_hours;
                    document.getElementById('cfgAdInterval').value = data.ad_interval || 3;
                    
                    if(data.social_links) {
                        document.getElementById('cfgFbGroup').value = data.social_links.fb_group || '';
                        document.getElementById('cfgFbPage').value = data.social_links.fb_page || '';
                        document.getElementById('cfgYoutube').value = data.social_links.youtube || '';
                        document.getElementById('cfgReview').value = data.social_links.review_channel || '';
                    }
                } catch(e) {}
            }

            async function saveSysSettings() {
                const payload = {
                    vip_cost: document.getElementById('cfgVipCost').value,
                    vip_days: document.getElementById('cfgVipDays').value,
                    unlock_hours: document.getElementById('cfgUnlockHrs').value,
                    ad_interval: document.getElementById('cfgAdInterval').value,
                    social_links: {
                        fb_group: document.getElementById('cfgFbGroup').value,
                        fb_page: document.getElementById('cfgFbPage').value,
                        youtube: document.getElementById('cfgYoutube').value,
                        review_channel: document.getElementById('cfgReview').value
                    }
                };
                try {
                    await fetch('/api/admin/sys_settings', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(payload)
                    });
                    alert('Settings saved successfully!');
                } catch(e) {
                    alert('Failed to save settings.');
                }
            }

            async function loadStats() {
                try {
                    const res = await fetch('/api/admin/stats');
                    const data = await res.json();
                    document.getElementById('stUsers').innerText = data.users;
                    document.getElementById('stMovies').innerText = data.movies;
                    document.getElementById('stViews').innerText = data.views;
                } catch(e) {}
            }

            async function loadAnalytics() {
                try {
                    const res = await fetch('/api/admin/analytics');
                    const data = await res.json();
                    
                    document.getElementById('stLiveOnline').innerText = data.live_online;
                    document.getElementById('analyticsDau').innerText = data.active_today;
                    document.getElementById('analyticsWau').innerText = data.active_week;
                    document.getElementById('analyticsReviews').innerText = data.total_reviews;

                    const labels = data.top_videos.map(v => v._id);
                    const counts = data.top_videos.map(v => v.total_views);

                    if (categoryChart) categoryChart.destroy();
                    const ctx = document.getElementById('categoryChart').getContext('2d');
                    categoryChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Views',
                                data: counts,
                                backgroundColor: 'rgba(139, 92, 246, 0.5)',
                                borderColor: 'rgba(139, 92, 246, 1)',
                                borderWidth: 1,
                                borderRadius: 8
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
                                x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                            }
                        }
                    });

                    let ratedHtml = '';
                    data.top_rated.forEach(m => {
                        ratedHtml += `
                        <tr class="border-b border-gray-800 hover:bg-gray-900/40">
                            <td class="p-4 font-bold text-yellow-400">${m._id}</td>
                            <td class="p-4 font-semibold"><i class="fa-solid fa-star text-yellow-400 mr-1"></i> ${m.avg_rating.toFixed(1)} / 5</td>
                            <td class="p-4 text-gray-400">${m.total_reviews} Reviews</td>
                        </tr>`;
                    });
                    document.getElementById('analyticsTopRatedList').innerHTML = ratedHtml || '<tr><td colspan="3" class="p-4 text-center text-gray-500">No video reviews logged yet.</td></tr>';

                } catch(e) { console.log(e); }
            }

            async function searchUsers() {
                const query = document.getElementById('userSearchInput').value.trim();
                const res = await fetch(`/api/admin/users/search?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                let html = '';
                
                if (data.users.length === 0) {
                    html = '<tr><td colspan="5" class="text-center p-8 text-gray-500">No matching users found...</td></tr>';
                } else {
                    data.users.forEach(u => {
                        const vipBadge = u.is_vip ? '<span class="px-2 py-0.5 text-xs bg-yellow-500/10 text-yellow-400 font-bold border border-yellow-500/20 rounded-full">👑 VIP</span>' : '<span class="px-2 py-0.5 text-xs bg-gray-500/10 text-gray-400 rounded-full">Free</span>';
                        const banBtn = u.is_banned ? 
                            `<button onclick="userAction(${u.user_id}, 'unban')" class="bg-emerald-600/10 hover:bg-emerald-600/20 border border-emerald-500/20 text-emerald-400 px-3 py-1 rounded-xl transition font-semibold text-xs">Unban</button>` :
                            `<button onclick="userAction(${u.user_id}, 'ban')" class="bg-red-600/10 hover:bg-red-600/20 border border-red-500/20 text-red-400 px-3 py-1 rounded-xl transition font-semibold text-xs">Ban User</button>`;

                        html += `
                        <tr class="border-b border-gray-800 hover:bg-gray-900/40">
                            <td class="p-4">
                                <span class="font-bold block">${u.first_name}</span>
                                <span class="text-xs text-gray-500 block">${u.user_id}</span>
                            </td>
                            <td class="p-4 text-blue-400 font-semibold">${u.coins} Gems</td>
                            <td class="p-4">${vipBadge}</td>
                            <td class="p-4 text-gray-400">${u.refer_count} referrals</td>
                            <td class="p-4 text-right flex gap-2 justify-end">
                                <button onclick="promptCoins(${u.user_id})" class="bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 border border-blue-500/20 px-2 py-1 rounded-xl text-xs transition">Gems</button>
                                <button onclick="promptVip(${u.user_id})" class="bg-yellow-600/10 hover:bg-yellow-600/20 text-yellow-400 border border-yellow-500/20 px-2 py-1 rounded-xl text-xs transition">VIP</button>
                                ${banBtn}
                            </td>
                        </tr>`;
                    });
                }
                document.getElementById('userTableBody').innerHTML = html;
            }

            async function userAction(userId, action, value = 0) {
                const res = await fetch('/api/admin/users/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ user_id: userId, action: action, value: value })
                });
                const d = await res.json();
                if (d.ok) searchUsers();
            }

            function promptCoins(userId) {
                const amount = prompt("Enter amount of points to ADD (positive number) or REMOVE (negative number):", "100");
                if (amount && !isNaN(amount)) {
                    const val = parseInt(amount);
                    if (val >= 0) userAction(userId, 'add_coins', val);
                    else userAction(userId, 'remove_coins', Math.abs(val));
                }
            }

            function promptVip(userId) {
                const days = prompt("Enter days of VIP membership to ADD (Type 0 to remove VIP):", "30");
                if (days !== null && !isNaN(days)) {
                    const val = parseInt(days);
                    if (val === 0) userAction(userId, 'remove_vip');
                    else userAction(userId, 'add_vip', val);
                }
            }

            document.getElementById('adminSearch').addEventListener('input', function(e) {
                clearTimeout(searchTimeout);
                searchQuery = e.target.value.trim();
                searchTimeout = setTimeout(() => loadAdminData(1), 500);
            });

            async function loadAdminData(page = 1) {
                currentPage = page;
                document.getElementById('movieTableBody').innerHTML = '<tr><td colspan="4" class="text-center p-8 text-gray-400">Loading...</td></tr>';
                const res = await fetch(`/api/admin/data?page=${currentPage}&q=${encodeURIComponent(searchQuery)}`); 
                const data = await res.json();
                
                let html = '';
                if(data.movies.length === 0) {
                    html = '<tr><td colspan="4" class="text-center p-8 text-gray-400">No videos found.</td></tr>';
                } else {
                    data.movies.forEach(m => {
                        html += `<tr class="border-b border-gray-700 hover:bg-gray-750">
                            <td class="p-4 font-medium">${m._id}</td>
                            <td class="p-4 text-gray-400">${m.clicks} Views</td>
                            <td class="p-4 text-green-400 font-bold">${m.file_count} Parts</td>
                            <td class="p-4 flex gap-2">
                                <button onclick="addViews('${encodeURIComponent(m._id)}')" class="text-yellow-400 bg-yellow-900 px-3 py-1 rounded transition hover:bg-yellow-800">Boost</button>
                                <button onclick="deleteMovie('${encodeURIComponent(m._id)}')" class="text-red-400 bg-red-900 px-3 py-1 rounded transition hover:bg-red-800">Delete</button>
                            </td>
                        </tr>`;
                    });
                }
                document.getElementById('movieTableBody').innerHTML = html;

                let pageHtml = "";
                if(data.total_pages > 1) {
                    pageHtml += `<button ${currentPage === 1 ? 'disabled class="px-4 py-2 bg-gray-700 text-gray-500 rounded"' : 'class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-white" onclick="loadAdminData(' + (currentPage - 1) + ')"'}>Prev</button>`;
                    pageHtml += `<span class="px-4 py-2 font-bold">Page ${currentPage} of ${data.total_pages}</span>`;
                    pageHtml += `<button ${currentPage === data.total_pages ? 'disabled class="px-4 py-2 bg-gray-700 text-gray-500 rounded"' : 'class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-white" onclick="loadAdminData(' + (currentPage + 1) + ')"'}>Next</button>`;
                }
                document.getElementById('adminPagination').innerHTML = pageHtml;
            }

            async function deleteMovie(title) {
                if(!confirm('Are you sure you want to delete ALL files for this video?')) return;
                await fetch('/api/admin/movie/' + title, {method: 'DELETE'}); 
                loadAdminData(currentPage); loadStats();
            }

            async function addViews(title) {
                let amount = prompt("How many views to add?", "1000");
                if(amount && !isNaN(amount)) {
                    await fetch('/api/admin/movie/' + title, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({add_clicks: parseInt(amount)}) });
                    loadAdminData(currentPage); loadStats();
                }
            }

            async function loadAds() {
                const res = await fetch('/api/admin/ads_list');
                const data = await res.json();
                let html = '';
                data.ads.forEach(ad => {
                    let exp = new Date(ad.expires_at).toLocaleString();
                    let subText = ad.subtitle || "N/A";
                    html += `<tr class="border-b border-gray-700 hover:bg-gray-750">
                        <td class="p-4 font-bold text-yellow-400">${ad.title}</td>
                        <td class="p-4 text-gray-300">${subText}</td>
                        <td class="p-4"><a href="${ad.link}" target="_blank" class="text-blue-400 underline">Link</a></td>
                        <td class="p-4">${exp}</td>
                        <td class="p-4"><button onclick="deleteAd('${ad._id}')" class="bg-red-600 text-white px-3 py-1 rounded">Delete</button></td>
                    </tr>`;
                });
                document.getElementById('adsTableBody').innerHTML = html || '<tr><td colspan="5" class="text-center p-8 text-gray-400">No active ads.</td></tr>';
            }

            async function createAdminAd() {
                const payload = {
                    title: document.getElementById('adTitle').value,
                    subtitle: document.getElementById('adSubtitle').value || "দেরি না করে এখনো সবাই নিয়ে নিন",
                    link: document.getElementById('adLink').value,
                    image_url: document.getElementById('adImage').value
                };
                await fetch('/api/admin/ads/create', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
                alert('Ad created successfully!');
                loadAds();
            }

            async function deleteAd(id) {
                if(confirm('Delete this ad?')) {
                    await fetch('/api/admin/ads/' + id, {method: 'DELETE'});
                    loadAds();
                }
            }

            async function loadKeywordList() {
                try {
                    const res = await fetch('/api/admin/keywords');
                    const data = await res.json();
                    let html = '';
                    data.keywords.forEach(kw => {
                        html += `
                        <tr class="border-b border-gray-700 hover:bg-gray-750">
                            <td class="p-4 font-bold text-green-400">${kw.keyword}</td>
                            <td class="p-4 text-gray-300 whitespace-pre-wrap">${kw.reply_message}</td>
                            <td class="p-4"><button onclick="deleteKeyword('${kw.keyword}')" class="bg-red-600 hover:bg-red-500 text-white px-3 py-1 rounded">Delete</button></td>
                        </tr>`;
                    });
                    document.getElementById('keywordsTableBody').innerHTML = html || '<tr><td colspan="3" class="p-4 text-center text-gray-500">No keyword responses.</td></tr>';
                } catch(e) {}
            }

            async function addKeywordReply() {
                const keyword = document.getElementById('kwInput').value.trim();
                const reply = document.getElementById('kwReplyInput').value.trim();
                if(!keyword || !reply) { alert('Enter Keyword and reply!'); return; }
                
                await fetch('/api/admin/keywords', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ keyword: keyword, reply_message: reply })
                });
                document.getElementById('kwInput').value = '';
                document.getElementById('kwReplyInput').value = '';
                loadKeywordList();
            }

            async function deleteKeyword(keyword) {
                if(confirm(`Delete response rule for keyword "${keyword}"?`)) {
                    await fetch(`/api/admin/keywords/${encodeURIComponent(keyword)}`, { method: 'DELETE' });
                    loadKeywordList();
                }
            }

            async function loadAdminRequests() {
                try {
                    const res = await fetch('/api/admin/requests');
                    const data = await res.json();
                    let html = '';
                    data.requests.forEach(req => {
                        let priorityClass = req.is_vip ? "bg-yellow-900 text-yellow-300 border-yellow-700" : "bg-gray-800 text-gray-400 border-gray-700";
                        let selectPending = req.status === 'pending' ? 'selected' : '';
                        let selectProcessing = req.status === 'processing' ? 'selected' : '';
                        let selectUploaded = req.status === 'uploaded' ? 'selected' : '';
                        
                        html += `
                        <tr class="border-b border-gray-700 hover:bg-gray-750">
                            <td class="p-4">
                                <span class="font-bold text-white block">${req.uname}</span>
                                <span class="text-xs text-gray-500 block">${req.user_id}</span>
                            </td>
                            <td class="p-4 font-bold text-blue-400">${req.movie}</td>
                            <td class="p-4"><span class="px-2 py-1 text-xs font-bold border rounded ${priorityClass}">${req.is_vip ? "⭐ VIP Priority" : "Free"}</span></td>
                            <td class="p-4 flex gap-2 items-center">
                                <select onchange="updateRequestStatus('${req._id}', this.value)" class="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white">
                                    <option value="pending" ${selectPending}>⏳ Pending</option>
                                    <option value="processing" ${selectProcessing}>⚙️ Processing</option>
                                    <option value="uploaded" ${selectUploaded}>✅ Uploaded</option>
                                </select>
                                <button onclick="deleteRequest('${req._id}')" class="bg-red-600 hover:bg-red-500 text-white px-2 py-1 rounded"><i class="fa-solid fa-trash"></i></button>
                            </td>
                        </tr>`;
                    });
                    document.getElementById('requestsTableBody').innerHTML = html || '<tr><td colspan="4" class="text-center p-8 text-gray-400">No requests log.</td></tr>';
                } catch(e) {}
            }

            async function updateRequestStatus(id, newStatus) {
                await fetch(`/api/requests/${id}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({status: newStatus})
                });
                loadAdminRequests();
            }

            async function deleteRequest(id) {
                if(confirm('Delete this request entry?')) {
                    await fetch(`/api/admin/requests/${id}`, { method: 'DELETE' });
                    loadAdminRequests();
                }
            }
            
            loadSysSettings(); loadStats(); loadAnalytics();
            
            setInterval(() => {
                const activeTab = document.querySelector('.admin-tab-content:not(.hidden)');
                if (activeTab && activeTab.id === 'adminTab-dashboard') {
                    loadStats();
                    loadAnalytics();
                }
            }, 10000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ==========================================
# 🛑 Render Web UI (Frontend Page)
# ==========================================
@api_router.get("/", response_class=HTMLResponse)
async def web_ui():
    tg_cfg = await fetch_setting("link_tg")
    support_cfg = await fetch_setting("link_support")
    b18_cfg = await fetch_setting("link_18")
    dl_cfg = await fetch_setting("direct_links")
    ad_time_cfg = await fetch_setting("ad_time")
    interval_cfg = await fetch_setting("ad_interval")
    social_cfg = await fetch_setting("social_links")
    
    ad_wait_seconds = ad_time_cfg['seconds'] if ad_time_cfg else 10
    ad_interval = interval_cfg["interval"] if interval_cfg else 3
    
    tg_url = tg_cfg['url'] if tg_cfg else "https://t.me/+Sr1C42A4v2M5NmI9"
    support_link = support_cfg['url'] if support_cfg else "https://t.me/contentremoval_1bot"
    link_18 = b18_cfg['url'] if b18_cfg else "https://t.me/+MEVxls-VFSZhZjQ1"
    direct_links = dl_cfg.get('links', []) if dl_cfg else []
    dl_json = json.dumps(direct_links)
    
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
    
    cost_cfg = await fetch_setting("vip_cost")
    days_cfg = await fetch_setting("vip_days")
    
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
    
    cost_cfg = await fetch_setting("vip_cost")
    days_cfg = await fetch_setting("vip_days")
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
# 🛑 Videos Data APIs
# ==========================================
@api_router.get("/api/trending")
async def trending_movies(uid: int = 0):
    unlocked_ids = []
    cfg_unlock = await fetch_setting("unlock_hours")
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
            {"$sort": {"created_at": 1}},
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

@api_router.get("/api/list")
async def list_movies(page: int = 1, q: str = "", uid: int = 0):
    unlocked_ids = []
    cfg_unlock = await fetch_setting("unlock_hours")
    unlock_hrs = cfg_unlock['hours'] if cfg_unlock else 24
    if uid != 0:
        time_limit = datetime.datetime.utcnow() - datetime.timedelta(hours=unlock_hrs)
        async for u in db.user_unlocks.find({"user_id": uid, "unlocked_at": {"$gt": time_limit}}):
            unlocked_ids.append(u["movie_id"])

    cache_key = f"{page}_{q}"
    if cache_key in list_cache:
        data = copy.deepcopy(list_cache[cache_key])
        movies = data["movies"]
        total_pages = data["total_pages"]
    else:
        limit = 15  
        skip = (page - 1) * limit
        match_stage = {}
        if q: match_stage["title"] = {"$regex": q, "$options": "i"}

        pipeline = [
            {"$match": match_stage},
            {"$sort": {"created_at": 1}}, 
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
                if movie and movie.get("photo_id"): 
                    actual_file_id = movie["photo_id"]
            else:
                movie = await db.movies.find_one({"photo_id": photo_id})
                if movie and movie.get("db_photo_id"):
                    db_msg_id = movie["db_photo_id"]
            
            try:
                file_path = (await bot.get_file(actual_file_id)).file_path
            except Exception:
                if db_msg_id and DB_CHANNEL_ID:
                    try:
                        forwarded = await bot.forward_message(
                            chat_id=DB_CHANNEL_ID,
                            from_chat_id=DB_CHANNEL_ID,
                            message_id=db_msg_id
                        )
                        
                        if forwarded.photo:
                            new_photo_id = forwarded.photo[-1].file_id
                            await bot.delete_message(chat_id=DB_CHANNEL_ID, message_id=forwarded.message_id)
                            await db.movies.update_many(
                                {"db_photo_id": db_msg_id}, 
                                {"$set": {"photo_id": new_photo_id}}
                            )
                            file_path = (await bot.get_file(new_photo_id)).file_path
                    except Exception as err:
                        logger.error(f"Image auto-repair failed: {err}")
                    
        if file_path:
            await db.file_cache.update_one(
                {"photo_id": photo_id}, 
                {"$set": {"file_path": file_path, "expires_at": now + datetime.timedelta(minutes=50)}}, 
                upsert=True
            )
            
        if not file_path: return {"error": "not found"}
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        
        async def stream_image():
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as resp:
                    if resp.status != 200:
                        await db.file_cache.delete_one({"photo_id": photo_id})
                        yield b""
                        return
                    async for chunk in resp.content.iter_chunked(1024): yield chunk

        headers = {"Cache-Control": "public, max-age=31536000, immutable", "Access-Control-Allow-Origin": "*"}
        return StreamingResponse(stream_image(), media_type="image/jpeg", headers=headers)
    except Exception as e: 
        logger.error(f"get_image error: {e}")
        return {"error": "error"}

async def db_increment_view(title: str):
    try:
        await db.movies.update_many({"title": title}, {"$inc": {"clicks": 1}})
        await db.movie_views.insert_one({"title": title, "viewed_at": datetime.datetime.utcnow()})
    except Exception: pass

@api_router.post("/api/view_movie")
async def increment_movie_view(d: ViewRequestModel, background_tasks: BackgroundTasks):
    background_tasks.add_task(db_increment_view, d.title)
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
            
            time_cfg = await fetch_setting("del_time")
            del_minutes = time_cfg['minutes'] if time_cfg else 60
            protect_cfg = await fetch_setting("protect_content")
            is_protected = protect_cfg['status'] if protect_cfg else True
            
            escaped_name = html.escape(user.get("first_name", "User") if user else "User")
            m_title = html.escape(m['title'])
            ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{d.userId}"
            
            delivery_wishes = [
                f"🍿 <b>Hey {escaped_name}!</b> Here is your video '<b>{m_title}</b>' 🎬\n\nভিডিওটি দেখার সময় বন্ধুদের ভুলো না কিন্তু! নিচে তোমার স্পেশাল শেয়ার লিংকটি দিলাম, বন্ধুদের সাথে শেয়ার করলেই পেয়ে যাবে ফ্রি Gems। একসাথে দেখার মজাই আলাদা! 😍\n\n🔗 <b>Your Invite Link:</b> <code>{ref_link}</code>"
            ]
            maya_wish = random.choice(delivery_wishes)
            caption = f"{maya_wish}\n\n📥 Join: @getnewlink11"
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
    return {"ok": True}

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
    return {"ok": True, "msg": "Ad campaign started successfully!"}

@api_router.get("/api/ads/active")
async def get_active_ads():
    now = datetime.datetime.utcnow()
    ads = await db.ads.find({"expires_at": {"$gte": now}}).sort("created_at", -1).to_list(20)
    for ad in ads: ad['_id'] = str(ad['_id'])
    return ads

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
    pipeline = [
        {"$match": {"title": {"$in": watchlist}}}, 
        {"$sort": {"created_at": 1}},
        {"$group": {"_id": "$title", "photo_id": {"$first": "$photo_id"}, "db_photo_id": {"$first": "$db_photo_id"}, "clicks": {"$sum": "$clicks"}, "created_at": {"$max": "$created_at"}, "files": {"$push": {"id": {"$toString": "$_id"}, "quality": {"$ifNull": ["$quality", "HD"]}}}}}, 
        {"$sort": {"created_at": -1}}
    ]
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
    
    if not user or user.get("coins", 0) < 5: 
        user_name = user.get("first_name", "User") if user else "User"
        return {"ok": False, "msg": f"আরে {user_name}! 🥺 স্পিন করতে ৫ Gems প্রয়োজন। তোমার ব্যালেন্স কম আছে। বন্ধুদের ইনভাইট লিংক শেয়ার করে Gems বাড়িয়ে নাও, জলদি যাও! 😉✨"}
        
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
        {"$group": {"_id": "$title", "clicks": {"$sum": "$clicks"}, "file_count": {"$sum": 1}, "created_at": {"$max": "$created_at"}}}, 
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
    return {"ok": True}

@api_router.delete("/api/admin/keywords/{keyword}")
async def delete_keyword_api(keyword: str, auth: bool = Depends(verify_admin)):
    await db.keyword_replies.delete_one({"keyword": keyword.lower()})
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
    
    top_v = await db.movies.aggregate([
        {"$group": {"_id": "$title", "total_views": {"$sum": "$clicks"}}},
        {"$sort": {"total_views": -1}},
        {"$limit": 5}
    ]).to_list(5)
    
    t_r = await db.reviews.aggregate([
        {"$group": {"_id": "$movie_title", "avg_rating": {"$avg": "$rating"}, "total_reviews": {"$sum": 1}}},
        {"$sort": {"avg_rating": -1, "total_reviews": -1}},
        {"$limit": 5}
    ]).to_list(5)
    
    return {
        "live_online": live, 
        "active_today": len(a_t), 
        "active_week": len(a_w), 
        "total_reviews": await db.reviews.count_documents({}), 
        "total_requests": await db.requests.count_documents({}), 
        "pending_requests": await db.requests.count_documents({"status": "pending"}), 
        "top_videos": top_v, 
        "top_rated": t_r
    }

# ==========================================
# 🛑 API for Like & Comment System (Details Page)
# ==========================================
@api_router.post("/api/interact")
async def handle_interaction(d: InteractRequestModel):
    if not d.telegram_id: return {"status": "error", "message": "Telegram ID missing"}
        
    now = datetime.datetime.utcnow()
    
    if d.action == 'like':
        existing_like = await db.likes.find_one({"video_id": d.video_id, "user_id": d.telegram_id})
        if not existing_like:
            await db.likes.insert_one({"video_id": d.video_id, "user_id": d.telegram_id, "created_at": now})
            await db.movies.update_many({"title": d.video_id}, {"$inc": {"likes": 1}})
            
        m = await db.movies.find_one({"title": d.video_id})
        new_likes = m.get("likes", 0) if m else 0
        return {"status": "success", "new_likes": new_likes}
        
    elif d.action == 'comment':
        if d.comment_text:
            user = await db.users.find_one({"user_id": d.telegram_id})
            uname = user.get("first_name", "User") if user else "User"
            
            await db.video_comments.insert_one({
                "video_id": d.video_id, 
                "user_id": d.telegram_id, 
                "uname": uname,
                "comment": d.comment_text, 
                "created_at": now
            })
        return {"status": "success"}

@api_router.get("/api/video_details/{title}")
async def get_video_details_api(title: str):
    m = await db.movies.find_one({"title": title})
    likes = m.get("likes", 0) if m else 0
    clicks = m.get("clicks", 0) if m else 0
    
    # Fetch comments for this video
    comments = await db.video_comments.find({"video_id": title}).sort("created_at", -1).to_list(50)
    formatted_comments = []
    for c in comments:
        try:
            date_str = c.get("created_at").strftime("%d %b, %H:%M") if c.get("created_at") else ""
        except:
            date_str = ""
            
        formatted_comments.append({
            "uname": c.get("uname", "User"),
            "comment": c.get("comment", ""),
            "date": date_str
        })
        
    return {
        "ok": True,
        "likes": likes,
        "downloads": clicks, 
        "comment_count": len(formatted_comments),
        "comments": formatted_comments
    }

