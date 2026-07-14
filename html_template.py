# html_template.py

HTML_CODE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>BD Viral Link</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
        body { background: #0f172a; font-family: sans-serif; color: #fff; overflow-x: hidden; width: 100%; -webkit-overflow-scrolling: touch; padding-bottom: 80px; } 
        
        header { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 12px 10px; border-bottom: 1px solid #1e293b; position: sticky; top: 0; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(10px); z-index: 1000; width: 100%; transform: translateZ(0); will-change: transform; gap: 8px; }
        .logo { font-size: 22px; font-weight: 900; white-space: nowrap; letter-spacing: 1px; }
        .logo span { background: #ef4444; color: #fff; padding: 2px 6px; border-radius: 4px; margin-left: 3px; font-size: 14px; }
        
        .home-btn { background: rgba(59, 130, 246, 0.1); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.5); padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 11px; cursor: pointer; display: flex; align-items: center; gap: 4px; transition: 0.2s; white-space: nowrap; }
        .home-btn:active { transform: scale(0.95); background: rgba(59, 130, 246, 0.2); }

        .bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(15, 23, 42, 0.98); backdrop-filter: blur(15px); border-top: 1px solid #334155; display: flex; justify-content: space-around; align-items: center; padding: 10px 0; z-index: 2000; padding-bottom: calc(10px + env(safe-area-inset-bottom)); }
        .nav-item { display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; font-size: 11px; font-weight: bold; cursor: pointer; transition: 0.2s; width: 25%; gap: 4px; }
        .nav-item i { font-size: 20px; transition: transform 0.2s; }
        .nav-item.active { color: #38bdf8; }
        .nav-item.active i { transform: scale(1.15); }
        .nav-item:active { transform: scale(0.9); }
        
        .dropdown-menu { display: none; position: fixed; bottom: 85px; right: 15px; background: rgba(15, 23, 42, 0.98); backdrop-filter: blur(10px); border: 1px solid #334155; border-radius: 12px; overflow: hidden; box-shadow: 0 -5px 25px rgba(0,0,0,0.5); z-index: 2000; width: 250px; animation: slideUp 0.2s ease-out forwards; }
        @keyframes slideUp { 0% { opacity: 0; transform: translateY(15px); } 100% { opacity: 1; transform: translateY(0); } }
        
        .dropdown-menu a { display: flex; align-items: center; gap: 10px; padding: 12px 15px; color: white; text-decoration: none; font-weight: 600; font-size: 14px; cursor: pointer; transition: background 0.2s ease; border-bottom: 1px solid #334155; }
        .dropdown-menu a:hover, .dropdown-menu a:active { background: rgba(51, 65, 85, 0.5); }
        .dropdown-menu a i { font-size: 16px; width: 20px; text-align: center; }
        
        .coin-tag { background: #3b82f6; color: white; font-weight: 900; padding: 2px 8px; border-radius: 10px; margin-left: 2px; font-size: 12px; }
        .vip-tag { background: linear-gradient(45deg, #fbbf24, #f59e0b); color: #000; font-size: 12px; padding: 3px 8px; border-radius: 12px; font-weight: bold; display: none; margin-left:5px; }

        .search-box { padding: 15px; }
        .search-input { width: 100%; padding: 16px; border-radius: 25px; border: none; outline: none; text-align: center; background: #1e293b; color: #fff; font-size: 18px; font-weight: bold; }

        .section-title { padding: 5px 15px 15px; font-size: 20px; font-weight: 900; display: flex; align-items: center; gap: 8px; color:#ff416c; }
        
        .trending-container { display: flex; overflow-x: auto; gap: 15px; padding: 0 15px 20px; scroll-behavior: smooth; scroll-snap-type: x mandatory; }
        .trending-container::-webkit-scrollbar { display: none; }
        .trending-card { min-width: 280px; max-width: 280px; background: transparent; overflow: hidden; cursor: pointer; flex-shrink: 0; position: relative; transition: transform 0.2s; transform: translateZ(0); will-change: transform; scroll-snap-align: start; }
        .trending-card:active { transform: scale(0.98); }

        .ad-carousel-container {
            width: 100%;
            margin: 5px 0 15px 0;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .ad-carousel-track {
            display: flex;
            overflow-x: auto;
            scroll-snap-type: x mandatory;
            gap: 12px;
            width: 100%;
            padding: 10px 0;
            scrollbar-width: none; 
        }
        .ad-carousel-track::-webkit-scrollbar {
            display: none; 
        }
        .ad-carousel-card {
            min-width: 250px;
            max-width: 250px;
            background: #ffffff;
            color: #1e293b;
            border-radius: 20px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            scroll-snap-align: start;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            flex-shrink: 0;
            text-decoration: none;
            transition: transform 0.2s;
        }
        .ad-carousel-card:active {
            transform: scale(0.97);
        }
        .ad-carousel-img-wrap {
            width: 100%;
            aspect-ratio: 16/10;
            background: #e2e8f0;
            overflow: hidden;
        }
        .ad-carousel-img-wrap img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .ad-carousel-body {
            padding: 12px 15px 15px 15px;
            text-align: left; 
            display: flex;
            flex-direction: column;
            align-items: flex-start; 
            gap: 4px;
            background: #ffffff;
        }
        .ad-carousel-title {
            font-size: 16px;
            font-weight: 800;
            color: #0f172a;
            white-space: nowrap;
            text-overflow: ellipsis;
            overflow: hidden;
            width: 100%;
            line-height: 1.2;
        }
        .ad-carousel-subtitle {
            font-size: 12px;
            color: #64748b;
            white-space: nowrap;
            text-overflow: ellipsis;
            overflow: hidden;
            width: 100%;
            line-height: 1.4;
            margin-bottom: 8px;
        }
        .ad-carousel-btn {
            background: linear-gradient(135deg, #ff4e2a, #ff7300);
            color: #ffffff;
            font-size: 13px;
            font-weight: 800;
            padding: 6px 20px;
            border-radius: 20px;
            border: none;
            outline: none;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(255, 78, 42, 0.3);
            display: inline-block;
        }
        .ad-carousel-dots {
            display: flex;
            gap: 5px;
            margin-top: 5px;
            justify-content: center;
        }
        .ad-carousel-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #475569;
            transition: background 0.2s, transform 0.2s;
        }
        .ad-carousel-dot.active {
            background: #ff4e2a;
            transform: scale(1.25);
        }

        .grid { padding: 0 15px 20px; display: flex; flex-direction: column; gap: 20px; }
        .card { background: transparent; overflow: hidden; cursor: pointer; transition: transform 0.2s; border-radius: 0; transform: translateZ(0); will-change: transform; }
        .card:active { transform: scale(0.98); }
        
        /* ⚡ শিমার লোডিং অ্যানিমেশন ডিজাইন (Layout Shift বন্ধ করতে) */
        .shimmer-placeholder {
            background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%);
            background-size: 200% 100%;
            animation: loading-shimmer 1.5s infinite;
        }
        @keyframes loading-shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        .post-content { position: relative; padding: 3px; border-radius: 12px; background: linear-gradient(45deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 200%; }
        .post-content img { width: 100%; aspect-ratio: 16/9; height: auto; object-fit: cover; display: block; border-radius: 10px; }
        
        .card-footer { padding: 12px 5px 0; display: flex; align-items: flex-start; gap: 12px; text-align: left; }
        .channel-logo { width: 40px; height: 40px; border-radius: 50%; background: white; color: #ef4444; border: 1px solid #e5e7eb; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 16px; flex-shrink: 0; }
        .title-text { color: #f8fafc; font-size: 16px; font-weight: bold; line-height: 1.4; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-top: 2px; }

        .top-badge, .ep-badge, .view-badge { position: absolute; font-weight: bold; padding: 4px 8px; border-radius: 6px; font-size: 11px; z-index: 10; color: white;}
        .top-badge { top: 10px; left: 10px; background: linear-gradient(45deg, #ff0000, #cc0000); }
        .view-badge { bottom: 10px; left: 10px; background: rgba(0,0,0,0.75); }
        .ep-badge { top: 10px; right: 10px; background: #10b981; }

        /* ⚡ লোডার আইকন ডিজাইন */
        .infinite-scroll-loader {
            display: none;
            justify-content: center;
            align-items: center;
            padding: 15px 0 30px 0;
            width: 100%;
        }

        .community-section { margin: 10px 15px 30px; padding: 15px; background: rgba(30, 41, 59, 0.5); border: 1px solid #334155; border-radius: 16px; backdrop-filter: blur(10px); }
        .social-grid { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
        .social-btn { display: flex; align-items: center; gap: 8px; padding: 10px 15px; border-radius: 12px; font-weight: bold; font-size: 13px; text-decoration: none; transition: transform 0.2s, box-shadow 0.2s; flex-grow: 1; justify-content: center; min-width: 140px; }
        .social-btn:active { transform: scale(0.95); }
        .fb-btn { background: rgba(24, 119, 242, 0.1); color: #1877f2; border: 1px solid rgba(24, 119, 242, 0.3); }
        .yt-btn { background: rgba(255, 0, 0, 0.1); color: #ff0000; border: 1px solid rgba(255, 0, 0, 0.3); }
        .tg-btn { background: rgba(36, 161, 222, 0.1); color: #24A1DE; border: 1px solid rgba(36, 161, 222, 0.3); }

        .developer-credit { margin: 10px 15px 130px; padding: 22px 15px; background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.95)); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 16px; text-align: center; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(56, 189, 248, 0.1); backdrop-filter: blur(10px); position: relative; overflow: hidden; }
        .developer-credit::before { content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent); animation: shine 3s infinite; }
        @keyframes shine { 100% { left: 200%; } }
        .dev-title { font-size: 12px; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px; }
        .dev-name { font-size: 22px; font-weight: 900; background: linear-gradient(45deg, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }
        .dev-desc { font-size: 13.5px; color: #cbd5e1; margin-bottom: 18px; line-height: 1.5; }
        .dev-btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; background: linear-gradient(45deg, #0ea5e9, #2563eb); color: white; padding: 12px 24px; border-radius: 30px; font-size: 15px; font-weight: bold; border: none; cursor: pointer; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4); transition: 0.2s; position: relative; z-index: 10; }
        .dev-btn:active { transform: scale(0.95); }

        .floating-btn { position: fixed; right: 15px; color: white; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; z-index: 500; cursor: pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .btn-18 { bottom: 205px; background: linear-gradient(45deg, #ff0000, #990000); font-weight: bold; font-size: 16px; border: 2px solid white; }
        .btn-tg { bottom: 145px; background: linear-gradient(45deg, #24A1DE, #1b7ba8); }
        .btn-req { bottom: 85px; background: linear-gradient(45deg, #10b981, #059669); }

        .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); display: none; align-items: center; justify-content: center; z-index: 3000; backdrop-filter: blur(5px); }
        .modal-content { background: #1e293b; width: 92%; max-width: 400px; padding: 25px; border-radius: 20px; text-align: center; border: 1px solid #334155; max-height: 85vh; overflow-y: auto; position: relative; }
        .close-icon { position: absolute; top: 12px; right: 15px; width: 32px; height: 32px; border-radius: 50%; background: #334155; color: #fff; display: flex; align-items: center; justify-content: center; cursor: pointer; }
        
        .rgb-border { position: relative; background: linear-gradient(45deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 200%; padding: 4px; border-radius: 14px; margin-bottom: 12px; cursor: pointer; width: 100%; }
        .rgb-inner { display: flex; justify-content: space-between; align-items: center; background: #0f172a; padding: 20px 18px; border-radius: 12px; color: white; font-weight: 900; font-size: 18px; }

        .btn-submit { background: linear-gradient(45deg, #10b981, #059669); color: white; border: none; padding: 15px 20px; border-radius: 12px; font-weight: bold; width: 100%; font-size: 18px; cursor: pointer; }

        .dl-rgb-wrap { position: relative; background: linear-gradient(45deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 200%; padding: 4px; border-radius: 16px; width: 100%; max-width: 350px; margin: auto; }
        .dl-inner-box { background: rgba(15, 23, 42, 0.98); border-radius: 12px; padding: 30px 20px; display: flex; flex-direction: column; align-items: center; gap: 15px; }
        
        .spinner-new { width: 65px; height: 65px; border: 5px solid rgba(255,255,255,0.1); border-left-color: #10b981; border-radius: 50%; animation: spin-fast 1s linear infinite; margin: 0 auto 15px; }
        @keyframes spin-fast { 100% { transform: rotate(360deg); } }
        .big-processing-text { font-size: 26px; font-weight: 900; color: #4ade80; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
        
        .wheel-slice { position: absolute; width: 50%; height: 50%; transform-origin: 100% 100%; }
        .spin-win-anim { animation: spin-stop-effect 4s cubic-bezier(0.25, 0.1, 0.25, 1) forwards; }
        
        @keyframes spinRing {
            100% { transform: rotate(360deg); }
        }
        @keyframes pulseGlow {
            from { text-shadow: 0 0 10px #38bdf8, 0 0 18px #0ea5e9; transform: scale(1); }
            to { text-shadow: 0 0 20px #38bdf8, 0 0 35px #2563eb, 0 0 45px #2563eb; transform: scale(1.02); }
        }
    </style>
</head>
<body onclick="closeMenu(event)">
    <div id="startupSplash" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #0f172a; z-index: 999999; display: flex; flex-direction: column; align-items: center; justify-content: center; opacity: 1; visibility: visible; transition: opacity 0.8s ease, visibility 0.8s ease;">
        <div style="position: relative; width: 160px; height: 160px; display: flex; align-items: center; justify-content: center; margin-bottom: 25px;">
            <div style="position: absolute; width: 100%; height: 100%; border-radius: 50%; background: conic-gradient(#ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); animation: spinRing 3s linear infinite; filter: blur(8px); opacity: 0.85;"></div>
            <div style="position: absolute; width: calc(100% - 8px); height: calc(100% - 8px); border-radius: 50%; background: conic-gradient(#ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); animation: spinRing 3s linear infinite;"></div>
            
            <div style="position: absolute; width: calc(100% - 16px); height: calc(100% - 16px); background: #1e293b; border-radius: 50%; display: flex; align-items: center; justify-content: center; overflow: hidden; box-shadow: inset 0 0 20px rgba(0,0,0,0.8); z-index: 2;">
                <div style="font-size: 36px; font-weight: 900; background: linear-gradient(45deg, #0ea5e9, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">MZ</div>
            </div>
        </div>
        <h1 id="splashWelcomeText" style="font-size: 30px; font-weight: 900; color: #fff; text-shadow: 0 0 10px #38bdf8, 0 0 20px #0ea5e9; animation: pulseGlow 1.5s ease-in-out infinite alternate; text-align: center; margin-bottom: 12px; letter-spacing: 1px;">BD Viral Link</h1>
        <p style="font-size: 13.5px; font-weight: 700; color: #94a3b8; letter-spacing: 2px; text-transform: uppercase;">Loading Premium Experience...</p>
    </div>

    <header>
        <div class="logo">BD Viral<span>Link</span></div>
        <button onclick="goHome()" class="home-btn"><i class="fa-solid fa-house"></i> Home Page</button>
    </header>
    
    <div id="dropdownMenu" class="dropdown-menu">
        <div style="padding: 12px 15px; border-bottom: 1px solid #334155; display: flex; align-items: center; gap: 12px;">
            <div style="width: 40px; height: 40px; background: #3b82f6; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; flex-shrink: 0;">
                <i class="fa-solid fa-user"></i>
            </div>
            <div style="flex-grow: 1; text-align: left;">
                <div style="font-size: 15px; font-weight: bold; color: white; line-height: 1.2;" id="menuUname">Guest</div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;" id="menuStatus">Free User</div>
            </div>
            <div style="text-align: right;">
                <div id="coinDisplay" class="coin-tag" style="display:inline-block; margin-bottom:4px;"><i class="fa-solid fa-gem"></i> 0</div>
                <div id="vipBadge" class="vip-tag" style="display:inline-block;">VIP</div>
            </div>
        </div>
        
        <a onclick="openReferModal()"><i class="fa-solid fa-share-nodes text-blue-400"></i> Refer & Earn</a>
        <a onclick="openRequestsTrackerModal()"><i class="fa-solid fa-code-pull-request text-green-400"></i> Request Video & Track</a>
        <a onclick="openWatchlistModal()"><i class="fa-solid fa-bookmark text-red-400"></i> My Watchlist</a>
        <a onclick="openAdCampModal()"><i class="fa-solid fa-bullhorn text-yellow-400"></i> Promote Channel/Web</a>
        <div style="height: 1px; background: #334155; margin: 4px 0;"></div>
        <a onclick="tg.showAlert(`How to Download:\n1. Click the Download button.\n2. Wait for ${AD_WAIT_TIME} seconds on the opened link.\n3. Return to the mini app and the video will be automatically sent to your bot inbox!`)"><i class="fa-solid fa-circle-question text-red-400"></i> How to Download</a>
        <a onclick="window.open('{{TG_LINK}}')"><i class="fa-solid fa-bullhorn text-green-400"></i> Our Channel</a>
        <a onclick="window.open('{{SUPPORT_LINK}}')"><i class="fa-brands fa-telegram text-blue-400"></i> Support / Contact</a>
        
        <a onclick="window.open(window.location.origin + '/admin', '_blank')" id="adminMenuBtn" style="display: none; color: #ef4444;"><i class="fa-solid fa-screwdriver-wrench"></i> Admin Panel</a>
    </div>

    <div class="search-box">
        <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search Videos...">
    </div>

    <div id="trendingWrapper">
        <div class="section-title"><i class="fa-solid fa-bolt text-yellow-400"></i>Trending now</div>
        <div class="trending-container" id="trendingGrid"></div>
    </div>

    <div class="section-title" id="recentTitle"><i class="fa-solid fa-clock-rotate-left text-blue-400"></i> Recently Added</div>
    <div class="grid" id="movieGrid"></div>
    
    <!-- ⚡ বাটন পেজিনেশনের জায়গায় আধুনিক ইনফিনিট স্ক্রল লোডার যুক্ত করা হলো -->
    <div class="infinite-scroll-loader" id="infiniteLoader">
        <div class="spinner-new" style="width: 35px; height: 35px; border-width: 4px; margin: 0;"></div>
    </div>
    
    <div id="communityBox"></div>

    <div class="developer-credit">
        <div class="dev-title"><i class="fa-solid fa-laptop-code"></i> Developed & Deployed By</div>
        <div class="dev-name">Bot Developer</div>
        <div class="dev-desc">Do you want remove any content from bot & if you face any Problem ? Contact us today.</div>
        <button class="dev-btn" onclick="window.open('https://t.me/contentremoval_1bot', '_blank')">
            <i class="fa-brands fa-telegram"></i> Contact Developer
        </button>
    </div>

    <div class="floating-btn btn-18" onclick="window.open('{{LINK_18}}')">18+</div>
    <div class="floating-btn btn-tg" onclick="window.open('{{TG_LINK}}')"><i class="fa-brands fa-telegram"></i></div>
    <div class="floating-btn btn-req" onclick="openRequestsTrackerModal()"><i class="fa-solid fa-code-pull-request"></i></div>

    <div class="bottom-nav">
        <div class="nav-item active" id="navHome" onclick="goHome()">
            <i class="fa-solid fa-house"></i>
            <span>Home</span>
        </div>
        <div class="nav-item" id="navSearch" onclick="focusSearch()">
            <i class="fa-solid fa-magnifying-glass"></i>
            <span>Search</span>
        </div>
        <div class="nav-item" id="navVip" onclick="openVipModal()">
            <i class="fa-solid fa-gem"></i>
            <span>Premium</span>
        </div>
        <div class="nav-item" id="navProfile" onclick="toggleMenu(event)">
            <i class="fa-solid fa-user"></i>
            <span>Profile</span>
        </div>
    </div>

    <div id="qualityModal" class="modal">
        <div class="modal-content">
            <div class="close-icon" onclick="document.getElementById('qualityModal').style.display='none'"><i class="fa-solid fa-xmark"></i></div>
            <h2 id="modalTitle" style="color:#38bdf8; margin-bottom: 5px; font-size: 22px; font-weight:900;">Video Title</h2>
            
            <div style="margin-bottom: 15px; display: flex; justify-content: center; gap: 10px;">
                <button id="bookmarkBtn" class="home-btn" style="border-radius: 12px; font-size: 13px;" onclick="toggleWatchlist()"></button>
                <span id="avgRatingBadge" style="background: rgba(251,191,36,0.1); color: #fbbf24; border: 1px solid rgba(251,191,36,0.4); padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 13px; display: flex; align-items: center; gap: 4px;"><i class="fa-solid fa-star"></i> <span id="avgRatingVal">0.0</span></span>
            </div>

            <div style="background: rgba(15, 23, 42, 0.9); border-left: 4px solid #f59e0b; padding: 12px; border-radius: 8px; text-align: left; margin-bottom: 15px;">
                <p style="color:#f59e0b; font-weight:bold; font-size: 14px; margin-bottom: 5px;"><i class="fa-solid fa-circle-info"></i> How to Download?</p>
                <p style="color:#cbd5e1; font-size: 12.5px; line-height: 1.5;">1. Click the download button below.<br>2. A new page will open, wait there for <b>{{AD_TIME}} seconds</b>.<br>3. Return to the mini app and the video will be automatically sent to your bot inbox!</p>
            </div>

            <div id="qualityList" style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px;"></div>

            <div style="border-top: 1px solid #334155; padding-top: 15px; text-align: left;">
                <h3 style="font-size: 16px; font-weight: bold; margin-bottom: 10px; color: #cbd5e1;"><i class="fa-solid fa-comments text-blue-400"></i> Reviews & Ratings</h3>
                
                <div style="background: rgba(15, 23, 42, 0.5); padding: 12px; border-radius: 10px; border: 1px solid #334155; margin-bottom: 15px;">
                    <p style="font-size: 12px; color: #94a3b8; margin-bottom: 6px; font-weight:bold;">Your Rating:</p>
                    <div style="display: flex; gap: 6px; font-size: 20px; color: #475569; cursor: pointer; margin-bottom: 10px;" id="starRatingSelect">
                        <i class="fa-solid fa-star" onclick="setSelectRating(1)"></i>
                        <i class="fa-solid fa-star" onclick="setSelectRating(2)"></i>
                        <i class="fa-solid fa-star" onclick="setSelectRating(3)"></i>
                        <i class="fa-solid fa-star" onclick="setSelectRating(4)"></i>
                        <i class="fa-solid fa-star" onclick="setSelectRating(5)"></i>
                    </div>
                    <textarea id="reviewText" style="width: 100%; height: 50px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: white; padding: 8px; font-size: 13px; outline: none; resize: none; margin-bottom: 8px;" placeholder="Write a review..."></textarea>
                    <button class="btn-submit" style="font-size: 13px; padding: 6px 12px; width: auto;" onclick="submitReview()">Submit Review</button>
                </div>

                <div id="modalReviewsList" style="max-height: 150px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px;"></div>
            </div>
        </div>
    </div>

    <div id="directLinkModal" class="modal">
        <div class="modal-content" style="background: transparent; border: none; padding: 0;">
            <div class="close-icon" onclick="document.getElementById('directLinkModal').style.display='none'" style="top: -15px; right: 5px; z-index: 1000;"><i class="fa-solid fa-xmark"></i></div>
            <div class="dl-rgb-wrap">
                <div class="dl-inner-box">
                    <h2 style="color: #4ade80; font-size: 24px; font-weight: 900;"><i class="fa-solid fa-unlock-keyhole"></i> Unlock Video</h2>
                    <p id="dlDescText" style="color: #cbd5e1; font-size: 15px; font-weight: 600; text-align:center;">
                        To unlock this file, wait <b>{{AD_TIME}} seconds</b> on the link below.
                    </p>
                    <button id="dlClickBtn" class="btn-submit" style="background: linear-gradient(45deg, #ef4444, #f97316); margin-top: 10px;" onclick="executeDirectLink()">🔗 Click Here (Open Link)</button>
                </div>
            </div>
        </div>
    </div>

    <div id="vipModal" class="modal">
        <div class="modal-content">
            <div class="close-icon" onclick="document.getElementById('vipModal').style.display='none'"><i class="fa-solid fa-xmark"></i></div>
            
            <div style="display: flex; gap: 5px; margin-bottom: 15px; border-bottom: 1px solid #334155; padding-bottom: 8px;">
                <button class="cat-btn active" id="btnTabVip" onclick="switchVipModalTab('vip')">💎 VIP & Buy</button>
                <button class="cat-btn" id="btnTabSpin" onclick="switchVipModalTab('spin')">🎡 Lucky Spin</button>
                <button class="cat-btn" id="btnTabLeader" onclick="switchVipModalTab('leader')">🏆 Leaders</button>
            </div>

            <div id="modalTabVipContent">
                <h2 style="color:#fbbf24; font-size: 22px; margin-bottom:12px;"><i class="fa-solid fa-gem"></i> Premium & Points</h2>
                <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid #10b981; padding: 12px; border-radius: 12px; margin-bottom: 15px; text-align: left;">
                    <p style="color:#4ade80; font-size: 14px; font-weight:bold; margin-bottom: 6px;"><i class="fa-solid fa-star"></i> VIP Benefits:</p>
                    <ul style="color:#cbd5e1; font-size: 12px; line-height: 1.5; padding-left: 15px;">
                        <li style="margin-bottom: 3px;"><b>Zero Ads:</b> Direct video unlock. No waiting.</li>
                        <li style="margin-bottom: 3px;"><b>Priority Requests:</b> Admins prioritize your videos.</li>
                        <li><b>Exclusive Badge:</b> Golden VIP profile badge.</li>
                    </ul>
                </div>

                <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid #3b82f6; padding: 12px; border-radius: 12px; margin-bottom: 15px;">
                    <p style="color:#94a3b8; font-size: 13px; font-weight:bold;">Your Current Points:</p>
                    <h1 style="color:#38bdf8; font-size: 30px; font-weight:900; margin: 3px 0;"><span id="modalCoinText">0</span> <i class="fa-solid fa-gem"></i></h1>
                    <p style="color:#cbd5e1; font-size: 11px;">(<span id="vipDaysText">1</span> Days VIP = <span id="vipCostText">30</span> Points)</p>
                </div>
                
                <button id="dailyCheckinBtn" class="btn-submit" style="background: linear-gradient(45deg, #10b981, #3b82f6); margin-bottom: 12px;" onclick="claimDailyCheckin()">
                    📅 Daily Check-in (+5 Points)
                </button>

                <button class="btn-submit" style="background: linear-gradient(45deg, #3b82f6, #2563eb); margin-bottom: 12px;" onclick="window.open('{{SUPPORT_LINK}}')">
                    <i class="fa-brands fa-telegram"></i> Buy Points from Admin
                </button>

                <button id="coinAdBtn" class="btn-submit" style="background: linear-gradient(45deg, #ef4444, #f97316); margin-bottom: 12px;" onclick="executeCoinAd()">
                    <i class="fa-solid fa-play"></i> Watch Ad & Get 5 Points
                </button>
                
                <button class="btn-submit" style="background: linear-gradient(45deg, #10b981, #059669);" onclick="buyVipWithCoins()">
                    <i class="fa-solid fa-crown"></i> Get <span id="btnVipDays">1</span> Days VIP for <span id="btnVipCost">30</span> Points
                </button>
            </div>

            <div id="modalTabSpinContent" style="display: none;">
                <h2 style="color:#f59e0b; font-size: 22px; margin-bottom:10px;"><i class="fa-solid fa-circle-notch"></i> Lucky Spin Wheel</h2>
                <p style="color:#94a3b8; font-size:12px; margin-bottom:15px;">Spend <b>5 Points</b> to spin the wheel and win huge points or VIP!</p>
                
                <div style="position: relative; width: 180px; height: 180px; margin: auto; border: 6px solid #334155; border-radius: 50%; overflow: hidden; background: #0f172a;" id="wheelOuter">
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 45px; height: 45px; background: white; border-radius: 50%; border: 4px solid #334155; z-index: 10; display:flex; align-items:center; justify-content:center; color:#0f172a; font-size:18px;"><i class="fa-solid fa-arrow-up"></i></div>
                    <div id="wheelInner" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 50%; background: conic-gradient(#ef4444 0deg 60deg, #3b82f6 60deg 120deg, #10b981 120deg 180deg, #f59e0b 180deg 240deg, #8b5cf6 240deg 300deg, #ec4899 300deg 360deg); transition: transform 4s cubic-bezier(0.25, 0.1, 0.25, 1);"></div>
                </div>

                <button id="spinBtn" class="btn-submit" style="background: linear-gradient(45deg, #f59e0b, #ef4444); margin-top: 20px;" onclick="spinWheel()">
                    🎡 Spin (Cost: 5 Points)
                </button>
            </div>

            <div id="modalTabLeaderContent" style="display: none;">
                <h2 style="color:#60a5fa; font-size: 22px; margin-bottom:12px;"><i class="fa-solid fa-trophy"></i> Referrers Leaderboard</h2>
                <p style="color:#94a3b8; font-size:12px; margin-bottom:15px;">Top referrers ranking. Refer friends and reach the top!</p>
                
                <div id="leaderboardList" style="text-align: left; display: flex; flex-direction: column; gap: 8px; max-height: 250px; overflow-y: auto;"></div>
            </div>
        </div>
    </div>

    <div id="referModal" class="modal">
        <div class="modal-content">
            <div class="close-icon" onclick="document.getElementById('referModal').style.display='none'"><i class="fa-solid fa-xmark"></i></div>
            <i class="fa-solid fa-share-nodes" style="font-size:60px; color:#38bdf8;"></i>
            <h2 style="margin:15px 0; color:white; font-size: 24px;">Refer & Earn</h2>
            <p style="color:#cbd5e1; font-size:15px; margin-bottom:15px;">Get <b>10 Points</b> for each successful referral!</p>
            <div style="background:#0f172a; padding:15px; border:1px dashed #3b82f6; margin-bottom:15px; word-break:break-all;" id="refLinkText">...</div>
            <button class="btn-submit" onclick="copyReferLink()">Copy Link</button>
        </div>
    </div>
    
    <div id="watchlistModal" class="modal">
        <div class="modal-content">
            <div class="close-icon" onclick="document.getElementById('watchlistModal').style.display='none'"><i class="fa-solid fa-xmark"></i></div>
            <h2 style="color:#38bdf8; font-size: 22px; margin-bottom:15px;"><i class="fa-solid fa-bookmark"></i> My Watchlist</h2>
            <div id="watchlistModalList" class="grid" style="padding:0; max-height: 60vh; overflow-y:auto; gap: 15px;">
                <p style="color: #94a3b8;">Loading watchlist...</p>
            </div>
        </div>
    </div>

    <div id="requestsTrackerModal" class="modal">
        <div class="modal-content">
            <div class="close-icon" onclick="document.getElementById('requestsTrackerModal').style.display='none'"><i class="fa-solid fa-xmark"></i></div>
            <h2 style="color:#10b981; font-size: 22px; margin-bottom:10px;"><i class="fa-solid fa-code-pull-request"></i> Video Request Status</h2>
            <p style="color:#cbd5e1; font-size:13px; margin-bottom:15px;">Submit and track the processing status of your requested videos!</p>
            
            <div style="display:flex; gap:10px; margin-bottom: 20px;">
                <input type="text" id="reqTrackerInput" class="search-input" style="border-radius:12px; text-align:left; padding:10px 15px; font-size:15px;" placeholder="Enter Video name...">
                <button class="btn-submit" style="width: auto; padding:0 20px; font-size:14px;" onclick="submitReqTracker()">Request</button>
            </div>

            <div id="requestsTrackerList" style="text-align: left; display: flex; flex-direction: column; gap: 12px; max-height: 45vh; overflow-y: auto;"></div>
        </div>
    </div>

    <div id="adCampModal" class="modal">
        <div class="modal-content">
            <div class="close-icon" onclick="document.getElementById('adCampModal').style.display='none'"><i class="fa-solid fa-xmark"></i></div>
            <h2 style="color:#fcd34d; font-size: 22px; margin-bottom:10px;"><i class="fa-solid fa-bullhorn"></i> Promote Channel</h2>
            <p style="color:#cbd5e1; font-size:13px; margin-bottom:15px;">Run your advertisement in front of thousands of users!</p>
            
            <input type="text" id="campTitle" class="search-input" style="border-radius:10px; margin-bottom:10px; font-size:15px;" placeholder="Ad Title (e.g. Join Best Video Bot)">
            <input type="text" id="campSubtitle" class="search-input" style="border-radius:10px; margin-bottom:10px; font-size:15px;" placeholder="Ad Subtitle (e.g. একদম ফ্রি।)">
            <input type="url" id="campLink" class="search-input" style="border-radius:10px; margin-bottom:10px; font-size:15px;" placeholder="https://t.me/yourlink">
            <input type="url" id="campImg" class="search-input" style="border-radius:10px; margin-bottom:15px; font-size:15px;" placeholder="Image URL (Optional)">
            
            <select id="campPackage" class="search-input" style="border-radius:10px; margin-bottom:15px; font-size:15px; background:#1e293b; color:white; text-align:left;">
                <option value="1">1 Day Campaign - 500 Points</option>
                <option value="3">3 Days Campaign - 1200 Points</option>
                <option value="7">7 Days Campaign - 2500 Points</option>
            </select>
            
            <button id="campBtn" class="btn-submit" style="background: linear-gradient(45deg, #f59e0b, #d97706);" onclick="submitAdCampaign()">
                Pay Points & Start
            </button>
        </div>
    </div>

    <script>
        let tg = window.Telegram.WebApp; tg.expand();
        const DIRECT_LINKS = {{DIRECT_LINKS}};
        const SOCIAL_LINKS = {{SOCIAL_LINKS}};
        const INIT_DATA = tg.initData || "";
        const BOT_UNAME = "{{BOT_USER}}";
        const AD_WAIT_TIME = {{AD_TIME}}; 
        const AD_INTERVAL = {{AD_INTERVAL}}; 
        
        let uid = tg.initDataUnsafe?.user?.id || 0;
        let isUserVip = false;
        let userCoins = 0;
        let loadedMovies = {}; 
        let currentPage = 1; 
        let searchQuery = "";
        let autoScrollInterval;
        let activeAds = [];
        
        let currentSelectRating = 0;
        let isCurrentMovieBookmarked = false;

        // ⚡ ইনফিনিট স্ক্রল ও রিকোয়েস্ট ম্যানেজমেন্ট গ্লোবাল ভ্যারিয়েবলস
        let hasNextPage = true;
        let isMoviesLoading = false;
        let activeFetchController = null; // অতিরিক্ত সমান্তরাল রিকোয়েস্ট প্রতিরোধ কন্ট্রোলার

        function setNavActive(index) {
            const items = document.querySelectorAll('.nav-item');
            items.forEach((item, i) => {
                if(i === index) item.classList.add('active');
                else item.classList.remove('active');
            });
        }

        async function fetchUserInfo() {
            try {
                const res = await fetch('/api/user/' + uid);
                const data = await res.json();
                isUserVip = data.vip;
                userCoins = data.coins || 0;
                
                const vCost = data.vip_cost || 30;
                const vDays = data.vip_days || 1;

                document.getElementById('vipDaysText').innerText = vDays;
                document.getElementById('vipCostText').innerText = vCost;
                document.getElementById('btnVipDays').innerText = vDays;
                document.getElementById('btnVipCost').innerText = vCost;

                let firstName = tg.initDataUnsafe?.user?.first_name || 'Guest';
                document.getElementById('menuUname').innerText = firstName;
                
                document.getElementById('coinDisplay').innerHTML = `<i class="fa-solid fa-gem"></i> ${userCoins}`;
                document.getElementById('modalCoinText').innerText = userCoins;
                
                if(isUserVip) {
                    document.getElementById('vipBadge').style.display = 'inline-block';
                    document.getElementById('menuStatus').innerText = '👑 VIP User';
                    document.getElementById('menuStatus').style.color = '#fbbf24';
                } else {
                    document.getElementById('vipBadge').style.display = 'none';
                    document.getElementById('menuStatus').innerText = 'Free User';
                    document.getElementById('menuStatus').style.color = '#94a3b8';
                }
                
                if(data.admin) {
                    document.getElementById('adminMenuBtn').style.display = 'flex';
                }

                document.getElementById('refLinkText').innerText = `https://t.me/${BOT_UNAME}?start=ref_${uid}`;
            } catch(e) {}
        }

        async function fetchActiveAds() {
            try {
                const res = await fetch('/api/ads/active');
                activeAds = await res.json();
            } catch(e) {}
        }

        function getAdCarouselHTML(indexId) {
            if(activeAds.length === 0) return '';
            let sliderId = "slider_" + indexId;
            
            let adCards = activeAds.map(ad => {
                let imgHtml = ad.image_url ? `<img src="${ad.image_url}" onerror="this.src='https://via.placeholder.com/640x360?text=No+Image'">` : `<div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#cbd5e1;"><i class="fa-solid fa-bullhorn text-slate-400" style="font-size:40px;"></i></div>`;
                let subText = ad.subtitle || "দেরি না করে এখনো সবাই নিয়ে নিন";
                return `
                <div class="ad-carousel-card" onclick="window.open('${ad.link}', '_blank')">
                    <div class="ad-carousel-img-wrap">
                        ${imgHtml}
                    </div>
                    <div class="ad-carousel-body">
                        <div class="ad-carousel-title">${ad.title}</div>
                        <div class="ad-carousel-subtitle">${subText}</div>
                        <button class="ad-carousel-btn">Click Now</button>
                    </div>
                </div>`;
            }).join('');

            let dotsHtml = activeAds.map((_, dotIdx) => {
                return `<span class="ad-carousel-dot ${dotIdx === 0 ? 'active' : ''}" id="dot_${sliderId}_${dotIdx}"></span>`;
            }).join('');

            return `
            <div class="ad-carousel-container">
                <div class="ad-carousel-track" id="track_${sliderId}" onscroll="syncAdDots('${sliderId}', ${activeAds.length})">
                    ${adCards}
                </div>
                <div class="ad-carousel-dots">
                    ${dotsHtml}
                </div>
            </div>`;
        }

        function syncAdDots(sliderId, totalAds) {
            const track = document.getElementById('track_' + sliderId);
            if(!track) return;
            let scrollPos = track.scrollLeft;
            let activeIdx = Math.round(scrollPos / 262);
            
            if (activeIdx >= totalAds) activeIdx = totalAds - 1;
            if (activeIdx < 0) activeIdx = 0;

            for (let i = 0; i < totalAds; i++) {
                const dot = document.getElementById(`dot_${sliderId}_${i}`);
                if (dot) {
                    if (i === activeIdx) dot.classList.add('active');
                    else dot.classList.remove('active');
                }
            }
        }

        function toggleMenu(e) { 
            e.stopPropagation(); 
            setNavActive(3);
            const m = document.getElementById('dropdownMenu'); 
            m.style.display = m.style.display === 'block' ? 'none' : 'block'; 
        }
        
        function closeMenu() { 
            document.getElementById('dropdownMenu').style.display = 'none'; 
        }
        
        function goHome() { 
            setNavActive(0);
            document.getElementById('searchInput').value = ""; 
            searchQuery = ""; 
            
            document.getElementById('trendingWrapper').style.display = 'block';
            loadTrending();
            loadMovies(1, false); // false = ওভাররাইট মোড (নতুন করে লোড)
            closeMenu(); 
            window.scrollTo({ top: 0, behavior: 'smooth' }); 
        }
        
        function focusSearch() {
            setNavActive(1);
            closeMenu();
            window.scrollTo({ top: 0, behavior: 'smooth' });
            setTimeout(() => document.getElementById('searchInput').focus(), 300);
        }
        
        function openVipModal() { 
            setNavActive(2);
            switchVipModalTab('vip');
            document.getElementById('vipModal').style.display = 'flex'; 
            history.pushState({modal: 'vipModal'}, "");
            checkAndToggleTelegramBackButton();
            closeMenu(); 
        }

        function switchVipModalTab(tab) {
            document.getElementById('modalTabVipContent').style.display = tab === 'vip' ? 'block' : 'none';
            document.getElementById('modalTabSpinContent').style.display = tab === 'spin' ? 'block' : 'none';
            document.getElementById('modalTabLeaderContent').style.display = 'none';
            
            document.getElementById('btnTabVip').className = tab === 'vip' ? 'cat-btn active' : 'cat-btn';
            document.getElementById('btnTabSpin').className = tab === 'spin' ? 'cat-btn active' : 'cat-btn';
            document.getElementById('btnTabLeader').className = tab === 'leader' ? 'cat-btn active' : 'cat-btn';

            if (tab === 'leader') { renderLeaderboard(); }
        }

        function openReferModal() { 
            document.getElementById('referModal').style.display = 'flex'; 
            history.pushState({modal: 'referModal'}, "");
            checkAndToggleTelegramBackButton();
            closeMenu(); 
        }
        
        function copyReferLink() { navigator.clipboard.writeText(document.getElementById('refLinkText').innerText); tg.showAlert("✅ Copied!"); }
        
        function openWatchlistModal() {
            document.getElementById('watchlistModal').style.display = 'flex';
            history.pushState({modal: 'watchlistModal'}, "");
            checkAndToggleTelegramBackButton();
            closeMenu();
            renderWatchlist();
        }

        async function renderWatchlist() {
            try {
                const res = await fetch(`/api/watchlist/list/${uid}`);
                const data = await res.json();
                let html = '';
                if (!data.watchlist || data.watchlist.length === 0) {
                    html = '<p style="color: #cbd5e1; text-align:center; padding: 20px;">Your Watchlist is empty!</p>';
                } else {
                    data.watchlist.forEach(m => {
                        loadedMovies[m.title] = {
                            _id: m.title,
                            photo_id: m.photo_id,
                            files: m.files,
                            clicks: m.clicks || 0
                        };
                        
                        html += `
                        <a href="/video/${encodeURIComponent(m.title)}" style="text-decoration: none; color: inherit; display: block;">
                            <div class="card" data-title="${encodeURIComponent(m.title)}">
                                <div class="post-content shimmer-placeholder">
                                    <img src="/api/image/${m.photo_id}" loading="lazy" onload="this.parentNode.classList.remove('shimmer-placeholder')" onerror="this.src='https://via.placeholder.com/640x360?text=No+Image'">
                                    <div class="ep-badge"><i class="fa-solid fa-bookmark text-yellow-400"></i> Saved</div>
                                </div>
                                <div class="card-footer">
                                    <div class="channel-logo">MB</div>
                                    <div class="title-text">${m.title}</div>
                                </div>
                            </div>
                        </a>`;
                    });
                }
                document.getElementById('watchlistModalList').innerHTML = html;
            } catch(e) {
                console.error("Watchlist render error:", e);
            }
        }

        async function toggleWatchlist() {
            const title = document.getElementById('modalTitle').innerText;
            let endpoint = isCurrentMovieBookmarked ? '/api/watchlist/remove' : '/api/watchlist/add';
            try {
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ uid: uid, title: title, initData: INIT_DATA })
                });
                const d = await res.json();
                if (d.ok) {
                    isCurrentMovieBookmarked = !isCurrentMovieBookmarked;
                    updateBookmarkButtonUI();
                    tg.showAlert(isCurrentMovieBookmarked ? "💾 Added to Watchlist!" : "❌ Removed from Watchlist!");
                }
            } catch(e) {}
        }

        function updateBookmarkButtonUI() {
            const btn = document.getElementById('bookmarkBtn');
            if (isCurrentMovieBookmarked) {
                btn.innerHTML = '<i class="fa-solid fa-bookmark text-yellow-400"></i> Saved';
                btn.style.background = 'rgba(250,204,21,0.1)';
                btn.style.borderColor = 'rgba(250,204,21,0.4)';
            } else {
                btn.innerHTML = '<i class="fa-regular fa-bookmark"></i> Save Later';
                btn.style.background = 'rgba(59, 130, 246, 0.1)';
                btn.style.borderColor = 'rgba(59, 130, 246, 0.5)';
            }
        }

        function setSelectRating(r) {
            currentSelectRating = r;
            const stars = document.querySelectorAll('#starRatingSelect i');
            stars.forEach((star, index) => {
                if (index < r) {
                    star.className = "fa-solid fa-star text-yellow-400";
                } else {
                    star.className = "fa-solid fa-star text-gray-600";
                }
            });
        }

        async function submitReview() {
            const title = document.getElementById('modalTitle').innerText;
            const rText = document.getElementById('reviewText').value.trim();
            const uname = tg.initDataUnsafe?.user?.first_name || 'Guest';

            if (currentSelectRating === 0) { tg.showAlert("Please select a star rating!"); return; }
            if (!rText) { tg.showAlert("Please write a review message!"); return; }

            try {
                const res = await fetch('/api/reviews/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        uid: uid,
                        uname: uname,
                        title: title,
                        rating: currentSelectRating,
                        review: rText,
                        initData: INIT_DATA
                    })
                });
                const data = await res.json();
                if (data.ok) {
                    tg.showAlert("🎉 Review submitted successfully!");
                    document.getElementById('reviewText').value = '';
                    setSelectRating(0);
                    loadReviews(title);
                }
            } catch(e) {}
        }

        async function loadReviews(title) {
            try {
                const res = await fetch(`/api/reviews/get/${encodeURIComponent(title)}`);
                const data = await res.json();
                
                document.getElementById('avgRatingVal').innerText = data.avg_rating > 0 ? data.avg_rating.toFixed(1) : '0.0';
                
                let html = '';
                data.reviews.forEach(r => {
                    let starsHtml = '';
                    for(let i=1; i<=5; i++) {
                        starsHtml += i <= r.rating ? '<i class="fa-solid fa-star text-yellow-400 text-xs"></i>' : '<i class="fa-solid fa-star text-gray-700 text-xs"></i>';
                    }
                    html += `
                    <div style="background: rgba(15, 23, 42, 0.4); padding: 10px; border-radius: 8px; border: 1px solid #334155;">
                        <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
                            <span style="font-weight:bold; font-size:12px; color:#cbd5e1;">${r.uname}</span>
                            <div>${starsHtml}</div>
                        </div>
                        <p style="font-size:12px; color:#94a3b8; line-height:1.4;">${r.review}</p>
                    </div>`;
                });
                document.getElementById('modalReviewsList').innerHTML = html || '<p style="color: #64748b; font-size: 12px;">No reviews yet. Be the first to review!</p>';
            } catch(e) {}
        }

        async function claimDailyCheckin() {
            try {
                const res = await fetch('/api/gamification/daily_checkin', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ uid: uid, initData: INIT_DATA })
                });
                const d = await res.json();
                if (d.ok) {
                    tg.showAlert(`🎉 Checked-in Successfully! You received +5 Points.`);
                    fetchUserInfo();
                } else {
                    tg.showAlert(`⚠️ ${d.msg}`);
                }
            } catch(e) {}
        }

        let isSpinning = false;
        async function spinWheel() {
            if (isSpinning) return;
            try {
                const res = await fetch('/api/gamification/spin', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ uid: uid, initData: INIT_DATA })
                });
                const data = await res.json();
                if (!data.ok) {
                    tg.showAlert(`⚠️ ${data.msg}`);
                    return;
                }

                isSpinning = true;
                const inner = document.getElementById('wheelInner');
                
                const degMap = {
                    0: 25,   
                    2: 75,   
                    5: 125,  
                    10: 175, 
                    20: 225, 
                    50: 275, 
                    vip: 325 
                };

                let prizeKey = data.reward.type === 'points' ? data.reward.amount : 'vip';
                let targetDeg = degMap[prizeKey] || 25;
                let extraRotations = 5 * 360; 
                let finalRotation = extraRotations + (360 - targetDeg);

                inner.style.transform = `rotate(${finalRotation}deg)`;

                setTimeout(() => {
                    tg.showAlert(data.msg);
                    isSpinning = false;
                    inner.style.transition = 'none';
                    inner.style.transform = `rotate(${360 - targetDeg}deg)`;
                    setTimeout(() => { inner.style.transition = 'transform 4s cubic-bezier(0.25, 0.1, 0.25, 1)'; }, 50);
                    fetchUserInfo();
                }, 4100);

            } catch(e) { isSpinning = false; }
        }

        async function renderLeaderboard() {
            try {
                const res = await fetch('/api/gamification/leaderboard');
                const d = await res.json();
                let html = '';
                d.leaderboard.forEach((user, idx) => {
                    let rankMedal = idx === 0 ? "🥇" : idx === 1 ? "🥈" : idx === 2 ? "🥉" : `[${idx+1}]`;
                    html += `
                    <div style="background: rgba(30,41,59,0.5); padding: 10px 15px; border-radius: 12px; border:1px solid #334155; display:flex; justify-content:space-between; align-items:center;">
                        <div style="display:flex; align-items:center; gap: 10px;">
                            <span style="font-size:16px;">${rankMedal}</span>
                            <span style="font-weight:bold; color:white;">${user.name}</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="color:#fbbf24; font-weight:bold; font-size:13px;"><i class="fa-solid fa-share-nodes"></i> ${user.refer_count} Ref</span>
                        </div>
                    </div>`;
                });
                document.getElementById('leaderboardList').innerHTML = html || '<p class="text-gray-500">No leaderboard entries.</p>';
            } catch(e) {}
        }

        function openRequestsTrackerModal() {
            document.getElementById('requestsTrackerModal').style.display = 'flex';
            history.pushState({modal: 'requestsTrackerModal'}, "");
            checkAndToggleTelegramBackButton();
            closeMenu();
            renderRequestsTracker();
        }

        async function submitReqTracker() {
            const val = document.getElementById('reqTrackerInput').value.trim();
            if (!val) return;
            const uname = tg.initDataUnsafe?.user?.first_name || 'Guest';

            try {
                await fetch('/api/request', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ uid: uid, uname: uname, movie: val, initData: INIT_DATA })
                });
                document.getElementById('reqTrackerInput').value = '';
                tg.showAlert('🎉 Request successfully queued!');
                renderRequestsTracker();
            } catch(e) {}
        }

        async function renderRequestsTracker() {
            try {
                const res = await fetch(`/api/requests/user_list/${uid}`);
                const d = await res.json();
                let html = '';
                d.requests.forEach(req => {
                    let statusText = req.status === 'pending' ? '⏳ Pending Review' : req.status === 'processing' ? '⚙️ Processing Video' : '✅ Uploaded successfully!';
                    let pct = req.status === 'pending' ? 30 : req.status === 'processing' ? 70 : 100;
                    let barColor = req.status === 'pending' ? '#f59e0b' : req.status === 'processing' ? '#3b82f6' : '#10b981';
                    
                    html += `
                    <div style="background: rgba(30,41,59,0.5); padding: 15px; border-radius: 12px; border:1px solid #334155;">
                        <div style="display:flex; justify-content:space-between; margin-bottom: 6px;">
                            <span style="font-weight:bold; color:white;">${req.movie}</span>
                            <span style="font-size:11px; font-weight:bold; color:${barColor};">${statusText}</span>
                        </div>
                        <div style="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
                            <div style="height:100%; width:${pct}%; background:${barColor}; border-radius:10px;"></div>
                        </div>
                    </div>`;
                });
                document.getElementById('requestsTrackerList').innerHTML = html || '<p style="color: #64748b; text-align:center;">You have not made any video requests yet.</p>';
            } catch(e) {}
        }

        function openReqModal() { openRequestsTrackerModal(); }

        function openAdCampModal() {
            document.getElementById('adCampModal').style.display = 'flex';
            history.pushState({modal: 'adCampModal'}, "");
            checkAndToggleTelegramBackButton();
            closeMenu();
        }

        async function submitAdCampaign() {
            const title = document.getElementById('campTitle').value;
            const subtitle = document.getElementById('campSubtitle').value || "দেরি না করে এখনো সবাই নিয়ে নিন";
            const link = document.getElementById('campLink').value;
            const img = document.getElementById('campImg').value;
            const packageDays = parseInt(document.getElementById('campPackage').value);
            
            let cost = 500;
            if(packageDays === 3) cost = 1200;
            if(packageDays === 7) cost = 2500;
            
            if(!title || !link) { tg.showAlert("Title and Link are required!"); return; }
            
            if(confirm(`Cost is ${cost} Points for ${packageDays} Days. Proceed?`)) {
                try {
                    const res = await fetch('/api/ads/create', { 
                        method: 'POST', 
                        headers: {'Content-Type': 'application/json'}, 
                        body: JSON.stringify({uid: uid, initData: INIT_DATA, title: title, subtitle: subtitle, link: link, image_url: img, package: packageDays}) 
                    });
                    const data = await res.json();
                    
                    if(data.ok) {
                        tg.showAlert("🎉 Campaign Started Successfully!");
                        document.getElementById('adCampModal').style.display = 'none';
                        fetchUserInfo(); 
                        fetchActiveAds(); 
                    } else {
                        tg.showAlert("⚠️ " + data.msg);
                    }
                } catch(e) { tg.showAlert("Network Error!"); }
            }
        }

        function formatViews(n) { if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'; if (n >= 1000) return (n / 1000).toFixed(1) + 'K'; return n; }
        function makeSafeId(str) { return str.replace(/[^a-zA-Z0-9]/g, '_'); }

        function startAutoScroll() {
            if(autoScrollInterval) clearInterval(autoScrollInterval);
            autoScrollInterval = setInterval(() => {
                let grid = document.getElementById('trendingGrid');
                if(grid) {
                    if (grid.scrollLeft >= (grid.scrollWidth - grid.clientWidth - 10)) grid.scrollTo({ left: 0, behavior: 'smooth' });
                    else grid.scrollBy({ left: 295, behavior: 'smooth' });
                }
            }, 3000);
        }

        async function loadTrending() {
            try {
                const r = await fetch(`/api/trending?uid=${uid}`);
                const data = await r.json();
                const grid = document.getElementById('trendingGrid');
                if(data.length === 0) return document.getElementById('trendingWrapper').style.display = 'none';
                grid.innerHTML = data.map(m => {
                    loadedMovies[m._id] = m;
                    let totalParts = m.files.length;
                    let partText = totalParts === 1 ? 'Part' : 'Parts';
                    
                    return `<a href="/video/${encodeURIComponent(m._id)}" style="text-decoration: none; color: inherit; display: block;">
                        <div class="trending-card" data-title="${encodeURIComponent(m._id)}">
                            <div class="post-content shimmer-placeholder">
                                <div class="top-badge">🔥 TOP</div>
                                <img src="/api/image/${m.photo_id}" loading="lazy" onload="this.parentNode.classList.remove('shimmer-placeholder')" onerror="this.src='https://via.placeholder.com/640x360?text=No+Image'">
                                <div class="ep-badge"><i class="fa-solid fa-list"></i> ${totalParts} ${partText}</div>
                                <div class="view-badge" id="trend-view-${makeSafeId(m._id)}"><i class="fa-solid fa-eye"></i> ${formatViews(m.clicks)}</div>
                            </div>
                            <div class="card-footer">
                                <div class="channel-logo">MB</div>
                                <div class="title-text">${m._id}</div>
                            </div>
                        </div>
                    </a>`;
                }).join('');
                setTimeout(startAutoScroll, 1000);
            } catch(e) {}
        }

        // ⚡ চূড়ান্ত আধুনিক ইনফিনিট স্ক্রল ভিত্তিক লোডার লজিক
        async function loadMovies(page = 1, append = false) {
            if (isMoviesLoading) return;
            isMoviesLoading = true;
            currentPage = page;

            const grid = document.getElementById('movieGrid');
            const loader = document.getElementById('infiniteLoader');
            
            if (!append) {
                grid.innerHTML = "<p style='color:white; text-align:center; padding: 20px;'>Loading...</p>";
                hasNextPage = true;
            } else {
                loader.style.display = 'flex';
            }

            // যদি আগের কোনো সার্চ বা রিকোয়েস্ট পেন্ডিং থাকে তবে তা বাতিল করে নতুন রিকোয়েস্ট পাঠানো হবে
            if (activeFetchController) {
                activeFetchController.abort();
            }
            activeFetchController = new AbortController();
            const signal = activeFetchController.signal;

            try {
                const r = await fetch(`/api/list?page=${currentPage}&q=${encodeURIComponent(searchQuery)}&uid=${uid}`, { signal });
                const data = await r.json();
                
                loader.style.display = 'none';
                
                if (data.movies.length === 0) {
                    hasNextPage = false;
                    if (!append) {
                        grid.innerHTML = `<p style='text-align:center; color:#fbbf24; padding: 20px;'>No videos found!</p>`;
                    }
                    isMoviesLoading = false;
                    return;
                }

                let htmlContent = "";
                data.movies.forEach((m, index) => {
                    loadedMovies[m._id] = m; 
                    let totalParts = m.files.length;
                    let partText = totalParts === 1 ? 'Part' : 'Parts';
                    
                    let cardHtml = `<a href="/video/${encodeURIComponent(m._id)}" style="text-decoration: none; color: inherit; display: block;">
                        <div class="card" data-title="${encodeURIComponent(m._id)}">
                            <div class="post-content shimmer-placeholder">
                                <img src="/api/image/${m.photo_id}" loading="lazy" onload="this.parentNode.classList.remove('shimmer-placeholder')" onerror="this.src='https://via.placeholder.com/640x360?text=No+Image'">
                                <div class="ep-badge"><i class="fa-solid fa-list"></i> ${totalParts} ${partText}</div>
                                <div class="view-badge" id="list-view-${makeSafeId(m._id)}"><i class="fa-solid fa-eye"></i> ${formatViews(m.clicks)}</div>
                            </div>
                            <div class="card-footer">
                                <div class="channel-logo">MB</div>
                                <div class="title-text">${m._id}</div>
                            </div>
                        </div>
                    </a>`;
                    htmlContent += cardHtml;
                    
                    let visualIndex = index + 1 + ((currentPage - 1) * 15);
                    if (activeAds.length > 0 && visualIndex % AD_INTERVAL === 0) {
                        htmlContent += getAdCarouselHTML(visualIndex);
                    }
                });
                
                if (append) {
                    grid.insertAdjacentHTML('beforeend', htmlContent);
                } else {
                    grid.innerHTML = htmlContent;
                }

                // যদি এটিই শেষ পেজ হয় তবে ইনফিনিট স্ক্রল বন্ধ করে দেওয়া হবে
                if (currentPage >= data.total_pages) {
                    hasNextPage = false;
                }

            } catch(e) {
                if (e.name !== 'AbortError') {
                    console.error("Movie fetch error:", e);
                }
            } finally {
                isMoviesLoading = false;
            }
        }

        // ⚡ স্ক্রল ইভেন্ট লুপ (ইনফিনিট স্ক্রল কার্যকর করার জন্য)
        window.addEventListener('scroll', () => {
            if (!hasNextPage || isMoviesLoading) return;

            // স্ক্রিনের শেষ সীমানা থেকে ২৫০ পিক্সেল উপরে থাকতেই নতুন পেজ রিকোয়েস্ট পাঠানো হবে
            if ((window.innerHeight + window.scrollY) >= (document.documentElement.scrollHeight - 250)) {
                loadMovies(currentPage + 1, true);
            }
        });

        let timeout = null;
        document.getElementById('searchInput').addEventListener('input', function(e) {
            clearTimeout(timeout); 
            searchQuery = e.target.value.trim();
            
            const elementsToToggle = [
                document.getElementById('trendingWrapper'),
                document.getElementById('recentTitle'),
                document.getElementById('communityBox'),
                document.querySelector('.developer-credit')
            ];

            if(searchQuery !== "") { 
                elementsToToggle.forEach(el => { if(el) el.style.display = 'none'; });
            } 
            else { 
                if(document.getElementById('trendingWrapper')) document.getElementById('trendingWrapper').style.display = 'block';
                if(document.getElementById('recentTitle')) document.getElementById('recentTitle').style.display = 'flex';
                if(document.getElementById('communityBox')) document.getElementById('communityBox').style.display = 'block';
                if(document.querySelector('.developer-credit')) document.querySelector('.developer-credit').style.display = 'block';
            }
            
            timeout = setTimeout(() => {
                hasNextPage = true;
                loadMovies(1, false);
            }, 500); 
        });

        async function openQualityModal(element) {
            let title = decodeURIComponent(element.getAttribute('data-title'));
            const movie = loadedMovies[title];
            if (!movie) {
                console.error("Video not found in loadedMovies:", title);
                return;
            }
            
            document.getElementById('modalTitle').innerText = title;
            document.getElementById('qualityList').innerHTML = movie.files.map(f => {
                let isFree = f.is_unlocked || isUserVip;
                let icon = isFree ? '<i class="fa-solid fa-paper-plane text-green-400"></i>' : '<i class="fa-solid fa-lock text-red-400"></i>';
                let cls = isFree ? 'border-left: 5px solid #10b981;' : 'border-left: 5px solid #ef4444;';
                return `<div class="rgb-border" onclick="handleQualityClick('${f.id}', ${f.is_unlocked})"><div class="rgb-inner" style="${cls}"><span><i class="fa-solid fa-download"></i> ${f.quality}</span> ${icon}</div></div>`;
            }).join('');
            document.getElementById('qualityModal').style.display = 'flex';
            
            history.pushState({modal: 'qualityModal'}, "");
            checkAndToggleTelegramBackButton();
            
            document.getElementById('bookmarkBtn').innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Checking...';
            document.getElementById('avgRatingVal').innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            document.getElementById('modalReviewsList').innerHTML = '<div style="text-align:center; padding:10px; color:#94a3b8;"><i class="fa-solid fa-spinner fa-spin"></i> Loading reviews...</div>';
            
            setSelectRating(0);
            
            fetch(`/api/watchlist/list/${uid}`)
                .then(res => res.json())
                .then(wlData => {
                    isCurrentMovieBookmarked = wlData.watchlist.some(w => w.title === title);
                    updateBookmarkButtonUI();
                })
                .catch(e => {
                    isCurrentMovieBookmarked = false;
                    updateBookmarkButtonUI();
                });
            
            loadReviews(title);
            
            fetch('/api/view_movie', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title: title})
            }).catch(e => console.log(e));
            
            movie.clicks += 1;
            let safeId = makeSafeId(title);
            let tBadge = document.getElementById('trend-view-' + safeId);
            let lBadge = document.getElementById('list-view-' + safeId);
            if(tBadge) tBadge.innerHTML = '<i class="fa-solid fa-eye"></i> ' + formatViews(movie.clicks);
            if(lBadge) lBadge.innerHTML = '<i class="fa-solid fa-eye"></i> ' + formatViews(movie.clicks);
        }

        let currentFileId = null; 

        function handleQualityClick(fileId, isUnlocked) {
            document.getElementById('qualityModal').style.display = 'none';
            if(isUnlocked || isUserVip) { 
                sendFileAndClose(fileId); 
            } else { 
                currentFileId = fileId; 
                document.getElementById('directLinkModal').style.display = 'flex';
                history.replaceState({modal: 'directLinkModal'}, "");
                checkAndToggleTelegramBackButton();
                resetDlButton();
            }
        }

        let linkOpenedAt = 0;
        let isWaitingForReturn = false;
        let dlTimerInterval = null;

        function resetDlButton() {
            const btn = document.getElementById('dlClickBtn');
            btn.onclick = executeDirectLink;
            btn.innerText = "🔗 Click Here (Open Link)";
            btn.style.background = "linear-gradient(45deg, #ef4444, #f97316)";
            btn.disabled = false;
        }

        function executeDirectLink() {
            if (!DIRECT_LINKS || DIRECT_LINKS.length === 0) { 
                document.getElementById('directLinkModal').style.display = 'none'; 
                if (currentFileId) sendFileAndClose(currentFileId); 
                return; 
            }
            
            tg.openLink(DIRECT_LINKS[Math.floor(Math.random() * DIRECT_LINKS.length)]);
            linkOpenedAt = Date.now(); 
            isWaitingForReturn = true;
            
            const btn = document.getElementById('dlClickBtn');
            btn.disabled = true; 
            btn.style.background = "#475569";
            
            if (dlTimerInterval) clearInterval(dlTimerInterval);
            
            dlTimerInterval = setInterval(() => {
                const elapsed = Date.now() - linkOpenedAt;
                const remaining = Math.ceil((AD_WAIT_TIME * 1000 - elapsed) / 1000);
                
                if (remaining > 0) {
                    btn.innerText = `⏳ Please wait... (${remaining}s)`;
                } else {
                    clearInterval(dlTimerInterval);
                    if (isWaitingForReturn) {
                        isWaitingForReturn = false;
                        document.getElementById('directLinkModal').style.display = 'none';
                        if (currentFileId) sendFileAndClose(currentFileId);
                    }
                }
            }, 200); 
        }

        let coinLinkOpenedAt = 0; 
        let isWaitingForCoinReturn = false; 
        let coinTimerInterval = null;

        function resetCoinButton() {
            const btn = document.getElementById('coinAdBtn');
            btn.disabled = false;
            btn.onclick = executeCoinAd;
            btn.innerHTML = '<i class="fa-solid fa-play"></i> Watch Ad & Get 5 Points';
            btn.style.background = "linear-gradient(45deg, #ef4444, #f97316)";
        }

        function executeCoinAd() {
            if (!DIRECT_LINKS || DIRECT_LINKS.length === 0) { tg.showAlert("⚠️ No ads available right now!"); return; }
            tg.openLink(DIRECT_LINKS[Math.floor(Math.random() * DIRECT_LINKS.length)]);
            
            coinLinkOpenedAt = Date.now(); 
            isWaitingForCoinReturn = true;
            
            const btn = document.getElementById('coinAdBtn');
            btn.disabled = true; 
            btn.style.background = "#475569";
            
            if (coinTimerInterval) clearInterval(coinTimerInterval);
            
            coinTimerInterval = setInterval(() => {
                const elapsed = Date.now() - coinLinkOpenedAt;
                const remaining = Math.ceil((AD_WAIT_TIME * 1000 - elapsed) / 1000);
                
                if (remaining > 0) {
                    btn.innerHTML = `<i class="fa-solid fa-play"></i> Please wait... (${remaining}s)`;
                } else {
                    clearInterval(coinTimerInterval);
                    if (isWaitingForCoinReturn) {
                        isWaitingForCoinReturn = false;
                        claimAdCoin();
                        resetCoinButton();
                    }
                }
            }, 200);
        }

        document.addEventListener("visibilitychange", function() {
            if (document.visibilityState === 'visible') {
                let now = Date.now();
                
                if (isWaitingForReturn) {
                    let elapsedSeconds = (now - linkOpenedAt) / 1000;
                    if (elapsedSeconds < AD_WAIT_TIME - 0.5) { 
                        let remaining = Math.ceil(AD_WAIT_TIME - elapsedSeconds);
                        tg.showAlert(`⚠️ You must wait full ${AD_WAIT_TIME} seconds on the link. ${remaining}s remaining.`);
                        isWaitingForReturn = false;
                        clearInterval(dlTimerInterval);
                        resetDlButton();
                    } else { 
                        isWaitingForReturn = false; 
                        clearInterval(dlTimerInterval);
                        document.getElementById('directLinkModal').style.display = 'none'; 
                        if (currentFileId) sendFileAndClose(currentFileId); 
                    }
                }
                
                if (isWaitingForCoinReturn) {
                    let elapsedSeconds = (now - coinLinkOpenedAt) / 1000;
                    if (elapsedSeconds < AD_WAIT_TIME - 0.5) {
                        let remaining = Math.ceil(AD_WAIT_TIME - elapsedSeconds);
                        tg.showAlert(`⚠️ You must wait full ${AD_WAIT_TIME} seconds on the link. ${remaining}s remaining.`);
                        isWaitingForCoinReturn = false;
                        clearInterval(coinTimerInterval);
                        resetCoinButton();
                    } else { 
                        isWaitingForCoinReturn = false; 
                        clearInterval(coinTimerInterval);
                        claimAdCoin(); 
                        resetCoinButton();
                    }
                }
            }
        });

        async function claimAdCoin() {
            try {
                const res = await fetch('/api/add_coin', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({uid: uid, initData: INIT_DATA}) });
                const data = await res.json();
                if(data.ok) { 
                    tg.showAlert("🎉 Congratulations! You received 5 Points.");
                    fetchUserInfo(); 
                } else { tg.showAlert("⚠️ Error receiving points."); }
            } catch (e) {}
        }

        async function buyVipWithCoins() {
            const vCost = parseInt(document.getElementById('btnVipCost').innerText) || 30;
            const vDays = parseInt(document.getElementById('btnVipDays').innerText) || 1;
            
            if(userCoins < vCost) {
                tg.showAlert(`⚠️ Not enough points! You need ${vCost} points. Watch ads or refer friends to earn points.`);
                return;
            }
            if(confirm(`Do you want to buy ${vDays} Days VIP for ${vCost} points?`)) {
                try {
                    const res = await fetch('/api/buy_vip', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({uid: uid, initData: INIT_DATA}) });
                    const data = await res.json();
                    if(data.ok) { 
                        document.getElementById('vipModal').style.display = 'none';
                        tg.showAlert("🎉 Success! Your VIP has been activated.");
                        fetchUserInfo(); 
                    } else { tg.showAlert(data.msg); }
                } catch (e) {}
            }
        }

        function showProcessingUI() {
            let procModal = document.getElementById('processingModalCustom');
            if(!procModal) {
                procModal = document.createElement('div');
                procModal.id = 'processingModalCustom';
                procModal.style.cssText = 'position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.95); z-index:9999; display:flex; align-items:center; justify-content:center; flex-direction:column; backdrop-filter: blur(5px);';
                procModal.innerHTML = `
                    <div class="spinner-new"></div>
                    <div class="big-processing-text">Sending File...</div>
                    <div style="color:#cbd5e1; margin-top:15px; font-size:16px; font-weight:bold;">Please wait, video is going to your bot inbox!</div>
                `;
                document.body.appendChild(procModal);
            }
            procModal.style.display = 'flex';
        }

        function hideProcessingUI() {
            let procModal = document.getElementById('processingModalCustom');
            if(procModal) procModal.style.display = 'none';
        }

        async function sendFileAndClose(id) {
            showProcessingUI(); 
            try {
                const res = await fetch('/api/send', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({userId: uid, movieId: id, initData: INIT_DATA}) });
                const data = await res.json();
                
                if(data.ok) { 
                    setTimeout(() => {
                        tg.close();
                    }, 500);
                } else {
                    hideProcessingUI();
                    tg.showAlert("⚠️ Session expired! Please close and reopen the mini app.");
                }
            } catch (e) {
                hideProcessingUI();
                tg.showAlert("⚠️ Network error! Please try again.");
            }
        }

        function renderCommunitySection() {
            let html = '';
            if(SOCIAL_LINKS.fb_group) html += `<a href="${SOCIAL_LINKS.fb_group}" target="_blank" class="social-btn fb-btn"><i class="fa-brands fa-facebook"></i> FB Group</a>`;
            if(SOCIAL_LINKS.fb_page) html += `<a href="${SOCIAL_LINKS.fb_page}" target="_blank" class="social-btn fb-btn"><i class="fa-brands fa-facebook-f"></i> FB Page</a>`;
            if(SOCIAL_LINKS.youtube) html += `<a href="${SOCIAL_LINKS.youtube}" target="_blank" class="social-btn yt-btn"><i class="fa-brands fa-youtube"></i> YouTube</a>`;
            if(SOCIAL_LINKS.review_channel) html += `<a href="${SOCIAL_LINKS.review_channel}" target="_blank" class="social-btn tg-btn"><i class="fa-solid fa-film"></i> Video Reviews</a>`;
            
            if(html !== '') {
                document.getElementById('communityBox').innerHTML = `
                <div class="community-section">
                    <div class="section-title" style="justify-content: center; font-size: 18px;"><i class="fa-solid fa-users" style="color: #38bdf8;"></i> Join Our Community</div>
                    <div class="social-grid">${html}</div>
                </div>`;
            }
        }

        history.replaceState({page: 'home'}, "");

        function checkAndToggleTelegramBackButton() {
            const modals = ['qualityModal', 'directLinkModal', 'vipModal', 'referModal', 'watchlistModal', 'requestsTrackerModal', 'adCampModal'];
            let anyOpen = false;
            modals.forEach(id => {
                const el = document.getElementById(id);
                if (el && el.style.display === 'flex') {
                    anyOpen = true;
                }
            });
            if (anyOpen) {
                tg.BackButton.show();
            } else {
                tg.BackButton.hide();
            }
        }

        window.addEventListener('popstate', function(event) {
            const modals = ['qualityModal', 'directLinkModal', 'vipModal', 'referModal', 'watchlistModal', 'requestsTrackerModal', 'adCampModal'];
            modals.forEach(id => {
                const el = document.getElementById(id);
                if (el && el.style.display === 'flex') {
                    el.style.display = 'none';
                }
            });
            checkAndToggleTelegramBackButton();
        });

        tg.BackButton.onClick(function() {
            history.back();
        });

        document.querySelectorAll('.close-icon').forEach(btn => {
            btn.removeAttribute('onclick');
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                history.back();
            });
        });

        let splashStartTime = Date.now();
        let welcomeSoundPlayed = false;

        function playWelcomeSound() {
            if (welcomeSoundPlayed) return;
            try {
                let audioUrl = "https://assets.mixkit.co/active_storage/sfx/2568/2568-preview.mp3";
                let audio = new Audio(audioUrl);
                audio.volume = 0.8;
                audio.play()
                    .then(() => {
                        welcomeSoundPlayed = true;
                    })
                    .catch(err => {});
            } catch (e) {}
        }

        ['click', 'touchstart', 'mousedown'].forEach(eventName => {
            document.addEventListener(eventName, function triggerAudio() {
                playWelcomeSound();
                document.removeEventListener(eventName, triggerAudio);
            }, { passive: true });
        });

        async function hideSplashScreen() {
            let elapsed = Date.now() - splashStartTime;
            let delay = Math.max(0, 3000 - elapsed);
            
            setTimeout(() => {
                let splash = document.getElementById('startupSplash');
                if (splash) {
                    splash.style.opacity = '0';
                    splash.style.visibility = 'hidden';
                    setTimeout(() => splash.remove(), 800);
                }
            }, delay);
        }

        let adScrollInterval;
        function startAdCarouselsAutoScroll() {
            if (adScrollInterval) clearInterval(adScrollInterval);
            adScrollInterval = setInterval(() => {
                const tracks = document.querySelectorAll('.ad-carousel-track');
                tracks.forEach(track => {
                    if (!track) return;
                    const cardWidth = 262; 
                    const maxScroll = track.scrollWidth - track.clientWidth;
                    
                    if (track.scrollLeft >= maxScroll - 10) {
                        track.scrollTo({ left: 0, behavior: 'smooth' });
                    } else {
                        track.scrollBy({ left: cardWidth, behavior: 'smooth' });
                    }
                });
            }, 4000); 
        }

        async function initApp() {
            try {
                await Promise.all([
                    fetchUserInfo(),
                    fetchActiveAds(),
                    loadTrending(),
                    loadMovies(1, false) // ১ম পেজ ফ্রেশ লোড
                ]);
                renderCommunitySection();
                startAdCarouselsAutoScroll(); 
            } catch(e) {} finally {
                hideSplashScreen();
            }
        }

        initApp();
    </script>
</body>
</html>
"""
