# helpers.py
import os
import asyncio
import time
import glob
import hmac
import hashlib
import urllib.parse
import secrets
from PIL import Image, ImageFilter
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasicCredentials
from config import logger, TOKEN, ADMIN_PASS, security

def cleanup_temp_files():
    patterns = ["temp_video_*.mp4", "collage_*.jpg", "temp_frame_*.jpg", "temp_in_*.jpg", "temp_out_*.jpg"]
    count = 0
    for p in patterns:
        for f in glob.glob(p):
            try:
                os.remove(f)
                count += 1
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    if count > 0:
        logger.info(f"Cleaned up {count} leftover temp files.")

def make_wide_thumbnail(input_path, output_path):
    try:
        img = Image.open(input_path).convert('RGB')
        w, h = img.size
        target_w = int(h * 1.777)
        canvas = Image.new('RGB', (target_w, h))
        bg = img.resize((target_w, h))
        bg = bg.filter(ImageFilter.GaussianBlur(15))
        canvas.paste(bg, (0, 0))
        offset_x = (target_w - w) // 2
        canvas.paste(img, (offset_x, 0))
        canvas.save(output_path, quality=90)
        return True
    except Exception as e: 
        logger.error(f"Thumbnail error: {e}")
        return False

async def get_video_duration(file_path):
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=60.0)
            return float(stdout.decode().strip())
        except asyncio.TimeoutError:
            process.kill()
            return 10.0
    except Exception: 
        return 10.0 

async def generate_collage(video_path, output_path):
    duration = await get_video_duration(video_path)
    timestamps = [max(1, duration * 0.2), duration * 0.5, duration * 0.8]
    images = []
    for i, t in enumerate(timestamps):
        img_name = f"temp_frame_{i}_{int(time.time())}.jpg"
        cmd = f'ffmpeg -y -ss {t} -i "{video_path}" -vframes 1 -q:v 2 "{img_name}"'
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            await asyncio.wait_for(process.communicate(), timeout=120.0)
        except asyncio.TimeoutError:
            process.kill()
            continue

        if os.path.exists(img_name):
            try:
                img = Image.open(img_name)
                h_percent = (360 / float(img.size[1]))
                w_size = int((float(img.size[0]) * float(h_percent)))
                img = img.resize((w_size, 360), Image.Resampling.LANCZOS)
                images.append(img)
            except Exception: pass
            finally:
                if os.path.exists(img_name): os.remove(img_name)
    
    if not images: return False
    while len(images) < 3: images.append(images[-1].copy())
        
    img_w, img_h = images[0].size
    padding = 8
    poster_w = (img_w * 3) + (padding * 4)
    poster_h = img_h + (padding * 2)
    collage = Image.new('RGB', (poster_w, poster_h), color=(15, 23, 42))
    positions = [(padding, padding), (img_w + padding * 2, padding), (img_w * 2 + padding * 3, padding)]
    
    for idx, img in enumerate(images[:3]):
        if img.size != (img_w, img_h): img = img.resize((img_w, img_h), Image.Resampling.LANCZOS)
        collage.paste(img, positions[idx])
        
    collage.save(output_path, quality=90)
    return True

def validate_tg_data(init_data: str) -> bool:
    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data))
        hash_val = parsed_data.pop('hash', None)
        auth_date = int(parsed_data.get('auth_date', 0))
        if not hash_val or time.time() - auth_date > 86400: return False
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        secret_key = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        return calculated_hash == hash_val
    except Exception: return False

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect Info", headers={"WWW-Authenticate": "Basic"})
    return True

def format_views(n):
    if n >= 1000000: return f"{n/1000000:.1f}M".replace(".0M", "M")
    if n >= 1000: return f"{n/1000:.1f}K".replace(".0K", "K")
    return str(n)
