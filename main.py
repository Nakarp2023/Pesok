import os
import sqlite3
import secrets
import base64
import json
import hmac
import hashlib
import urllib.parse
import urllib.request
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from collections import defaultdict, deque
from threading import Lock
import time
from pydantic import BaseModel, Field

DB_PATH = os.getenv("PESOK_DB_PATH", "pesok.db")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_TELEGRAM_CHAT_ID = os.getenv("ADMIN_TELEGRAM_CHAT_ID", "").strip()
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://pesok-store.onrender.com").rstrip("/")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
BETAPAY_API_KEY = os.getenv("BETAPAY_API_KEY", "").strip()
BETAPAY_WEBHOOK_SECRET = os.getenv("BETAPAY_WEBHOOK_SECRET", "").strip()
BETAPAY_API_BASE = "https://b-pay-provider.com/api/v1"
PHOTO_OLGA_B64 = "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"
PHOTO_MISHA_B64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDABsSFBcUERsXFhceHBsgKEIrKCUlKFE6PTBCYFVlZF9VXVtqeJmBanGQc1tdhbWGkJ6jq62rZ4C8ybqmx5moq6T/2wBDARweHigjKE4rK06kbl1upKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKT/wAARCAC0AUADASIAAhEBAxEB/8QAGgABAAIDAQAAAAAAAAAAAAAAAAIDAQQFBv/EADEQAAICAgEEAQQBBAAGAwAAAAABAgMEESEFEjFBURMiYXEyBhRCgRUjscHR4TNSof/EABYBAQEBAAAAAAAAAAAAAAAAAAABAv/EABcRAQEBAQAAAAAAAAAAAAAAAAABESH/2gAMAwEAAhEDEQA/APMgAAAAAAAAAAAAAAAAAAAAABmKcmlFNt+EgMEqq5W2Rrgtyk9JHUweg5GXR9VyjWn/AB3zv/wdnE6BjY0o2fdZZHlOXhP9FxNY6J01YMbJW9rsb4nrwteDrPhb9EVtPmL18luuCivj4cl+iqcY9z3HcfL34NnwVzTaaaT35A05OFt1tE65dmk+f4yNHO6FjWY7ePD6c487W3s6sop6aXLMvUOE/IR4KyPZOUd709ETqdejixypOqTldJ7nrXav/ZyzLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAG/HpOd2Qtrq7t6a7JLaNFJt6S22e26NjW0YFcL5d0tfH8V8FF2DK2eJXK6p1Wa5i/+ptRS8/IfK0jKSCHakPJkBWNEZJSWiz0QSCK+zS0iE9J+C5mHFN7ZR4nreN/bZ8u1ahZ96/7mge8ysGnKpnVYuJrXcvKOd1LoMclQdM41yrh2JdvEtEHlATtrlVbKueu6L09fJAigAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAdr+m8CGTdO66HdCHCUltNgcXyZUW96T48/g97LEoU4TjTBShvt1FIlHFqhKcoVxTs5nx5Lia8r/TPZ/xRKUE9xem14Z7CJTRiU48puqqMJWPctIv1oDMY6ewZQ0FAABkwzOzDa8EEdbElxrwSMSKKudeTLfHC2Zku1mEEeY670+dVDypxg7J2tzlHfC9HCPcdTxYZmO6Zt6bTWv8AH8nkeo4bwcj6Tmp8b2hRqgAigAAAAAAAAAAAAAAAAAAAAAAAAJ11ztmoVxcpP0kb+X0qePhws7ZOzf368IDSox7MixV1Rcpv18HV6Xm2dHusxsmEnGXMVHl7/wDZo9OunjZcLHCbjLzrfKPR2dNryMunJ12uLUt/PwWRHUqk51RlKLi2tuL9FkItctka1pafLLAMa52ZfIfjgwthWTJjwZIMewGYbAyRUdMbe9MyUZQMbGwI2fPwRRJvjkxtJaCK7Y+/Z4vrFNtOfZ9XlzfcmvaPbS5TOZn4MMqp12NrT2mvKA8eDarwL7arbIR+2vzvhmqRQEo1zlFyUG4r3oiAAAAAAAAAAAAAAAZacXppp/kwABuV9Ly59rdXZFrfdJ6SR0aujZONtwtrlGUdSbjyv0XE1xaabL5qFUHOT9JHY6b0h2dt2XqKT0q9ef2bHRbacaduLZ2xshNpSf8AkS6hlXX5ccbFi3F67mo8r5ZZDW7jYFdeXPIh9qlHtaXj9m92prWkzNdahXGKbelrb9mUtMqIxpgmn2ra8ceCXC40T4GlvZBKJIwjJFZA9AisMAwyjPox4GyMpegDZnZXyyaCMNvY2Yl5Ip8gTIyWuSUU2QnvuabAw3sqmnvZPnZXbtppeSimcNtnF61gVwqWRUlDT04pednal3L7pJL9DtVkV3x49JoI4ssCf9rXVFSrjJpzTeynI6R9m8ZuTS32v2d+cZaS7ePkhVCFaUUtL8geQnXOuXbOMoy+GiJ7dwhN7ai36bR5fq+G8bKlJa7Jtta9EsXWgACKAAAAABsYN0MfKhZOtWRXplMIxk33TUePaLcLG/u8iNP1FW5eGwNnqfUIZsIpV9sovh/g18TCuy21Ulx8vR2Luh1xw5KEk7oralJ62Q/p6HZVbdtNSfb+jWdRu4Ga5R+ll1OEofY5Jbi38GcjqEln1YtSjKuS+5/v8mzjwpTssp7VKT3PtflleVTSnHInGMXVz3a8IrK+ONjb26K973txW9mwlHevleimlxurbhPcWuGidVTqhFLb0kvIVbCXpJ6LEiKZYvBAa2Y0Z3zwYfCCsokVp7J70QSBgwt7IrJHfJJmGig0yuaJ6/JFvygglwGiPeo+ST8AR7eG29jjX5G0uNkZvWufJRYppIjYt8og+Y8FkXuKAhFEJrT2ybfJXa2lsCnu1JbJvxwYdacd+yMHLlaTX4CMKfrltlGVY4190dccsu2mmox3IplCU4OMltpPgDGNd/cY6klrZXk4k8nFac1GUlrTjvRq5OdPEnFW1ahNentott6lCnHrulCbjZ40BycvpdmJS7bLYPnSS9mgdDqucsxwUIOMY/L8s55mtAAAAAAXOm6mNdsouMZcxkUk3bZKCg5ycFyot8ID1FM8t9MUnGErHHhuXlfLPPTrtxLfpX90Iy05dr8ohVl3Va7LJrt8afg2lk2dTvppyJQST/lrTZrUdvClRDGUcRqxPwl5b/Pwc6WflXZKxbseMVKSUoM6uN9ChduP9OMV/Jpkoxq6l9K+ifFU99zj5+UVGxiwrprUIppLjbNqKTXyUdvbxrfy0SU9aSAsjFp/gmQj44Yk9PT9kVnu5Y9lctrbRhOW0/QRalzsnwQ3pGO/kKs4MOxL3yVSscnFLjfj8mY1qW3IC7l8mX4I70iSZFRIS229Fr5RDQQjGKQ42FwiMpa3sCuxfdsqssg09Pktctpr0a0YqU2+5NFRbCf2cslXdHlLwUXLvf06/wCTWivExraKmpa87A3U1vaYlBWR09kHwlpb/Jn6nYuV5ArnF17iudL/AGa2LKyzv+zlPl/Jvxj9zk+W+CP8JtJcP4A141xW+/exK19raj3euDYsgp6bbWvg0rU/75V1y1GMO5r8v0Bz+q4dl+M8iyajKvbcd8a/8nFqqvvhJ1xlONa2+fB2+o52PYrcWycq5JabS2ja6dDAhWnjdrbWm0+X+wry91dlclG2EoPW0mis7mZkYSzLqrq2/C7tb9Lg1MuHT3GUqrJRkofbFR4bJg5wAIoAAAAABcA2On0Qycyuqx6jJ8gdno3SVKMMnIfvivX/AFO7XTCitV0xUILwkc3++rxcuvDSSXakpb8fCOhTKT7u5p7fo2ysi4xSi3yzCrk3w0YslFR0/wDZVjXbUm4tfc/9gW1VuuUtzb2/DLNNyfwRdkFHbkkRut7I7XAFc7Wp9jS/JdBqSfO0cuVk8y+LVdtChz3f/c3KWqUlZPz7fsDZnN67V5Ney2MItykuPJftb35Ryb8l1zahRba/8uyPCA3sPKqyq++l7in2/pmz3vuSXlnDr6vRX9RyhOEtbUXHW/g2XkunGrycicpd7XbGKXG/X5A68npcE0ajs7nHt2v2bEXwiKnsi3yYb5MqK1tvkgyvBCUW0T/BiT14A1rV9m/XgpprnWpSkuG+F8I3J8x8GlmWuENd8VN8R38lRdJLiUeH+fBfH+HJzKbZSudbtU5Jb8ra/wBDNyr4Thj0V99s+ef4pAX3d0G5Re0/j0at3UVQ4KbSc3pNmxByuplC2lxl/GS3w/0ziZ3T3/eVRXdGmbUY8t9oHfxpOyUrXPuT4WvBP6c224ySW+Fo1cOmOFS64zk60+NvwXfWUYOzvTXnh8FFyWl/o5PWctYyUZQk1Ymk09NF2B1erKulS12yTfa299yOb/UtqsdSW9rZBxpSUudvfvZsY+XbRTOqrtUbPPHJqGU2iNEm3Jtvb+SdNU77Y1wW5SeisuxMieLfG2vW18+CCzN6ffhJSs7XGT0mmapt5+ddmyi7Gu2K4jHx+zUAAAAAAJV9v1I9/wDHa3r4LcmVKyXLEU41r+O3yUACxNyl3N8/J2cO3qGJjy3VKVcluPd6/RxITcJJ62k96Z6Gv+oYKvmjUteE+DUqVpwzuoZOXCuNmpb1rWlr8nbnc6YSnYo8c6XBxOsXYysqsxJf8yW5SlF8o0Lcq2+W7rJT18sumOr/AMet7uaIOPrnkrzur25FUI1Ls+375e9/g50ZRlHxyT0wN3H6xfGVau+6uP8ALXDf5Nqzrm69U16nv/PlI5SS9vZhrwEehv6pDGxqpRnXdOUkpKL8L2dCNsJVRcZLsktr8nJ6f02iVf1buyaaT88L8HK6jOt5UoURcIw+3Sk+QNzrNTycuMseDnqH3OPPshHqkI0wqyMfcqmtNetfh+zp9NzaZ4cNuEJw+2S8HO6rPHtvhdVJT2vu0wKJ52ZZJQ+pONc3uO+ON/J6Si/aXdKPfrxs4+Vn0W4Mq6pJ2SS+3XhFPSo4tbV+RdGNifEW/AHo3kQ+i7U9xUW/BKq1WQjKO9SW1tHOyepY2PFLuVs34jHk24XxnUrOeVvXtAbWyDsip9rfJrV2Tssai/tS5NHqOTkY2ZFRx53Q7e5tf9iDsNfD4OL/AFFTN4rtVn27W4teP0zo0ZPfjwnOLrlL/F8tFeZLa7WotfDWwOP0TDl3rLnOSlyo/n0X9VqyanO6rIfa0k0vKI2XRxMGf0r+6T/hzvTZrUdY7cacL4Oy1+JfP7A2odbqrxEkpytiktS9/nZs9Oz682MnZXGLg96b3x8nmnp7b4MUXzqfdBtS/HwFen6rGUcKyVM5QcVvj2jzCfG9tJ/kvXUb40WUuffCcXHUudfo0tvWvQtGxXKVU4zhJxkuUyq6cpzbnJyfy2Q2/kwRQHUr6JdLElbJ/frcYLnZy2tPT8kAAAAAAAAAAAAAAAAGW2/JgAAdrp2Dj39Odtl/ZJtpvuXBxTKk0tb4LBmTak0pbS438l9e+xGsXVT0mm/HgQXRVnPZJ6fOkySg5Lc1yyqM9v7W9r2WwsTWm+TTKEq5JN8aLIQag18md8BMCFdXbPbexdDa2lyT2IyXd9ybX4A6PScemWHK1RTuW993/wCGjd1HKsg6nJQXh9vsol3P+LcU/P5MpJegNzo2W8XI7bH9k1rbk9I7VuVRZHv+pFxW0m3w2vR5iSTX5Ic/P+gN27q98nuhfTjrT3y9kMXIVl05ZmTao68Jvk1WZSXkircqvHVzljSbr14a9mvLW+FoteuzRX2gQbS42VE7Gt8ECKAAgAADpV9Yy4L/AOSLWtacTnNttt+WYAAAAAAAAAAAAAAAAAAAAAAAAAGVJrwzPfLe9kQBdG5+JeC2E1LlGoWV2dm01tFlRtb2glsoru29MtjYnLSKJvzoi1szLwgteih7MaJEHYo+SDLRhrWyLuglxshO5PWgJd2vJGx7g2mtezH1E0VN7IMAAigAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZT0wANiuTkltlu+GAaRRZZJS4ZW5OSewAIAAyoAAAAAAAAAAAAAAAAAAP//Z"
app = FastAPI(title="PESOK Store", version="0.1.0")

# Basic in-process throttling for administrative endpoints. For a multi-instance deployment,
# move this limiter to a shared store (e.g. Redis/Key Value).
_ADMIN_FAILS = defaultdict(deque)
_ADMIN_LIMIT_LOCK = Lock()
_ADMIN_WINDOW_SECONDS = 600
_ADMIN_MAX_FAILURES = 10

@app.middleware("http")
async def protect_admin_routes(request: Request, call_next):
    if request.url.path == "/" or request.url.path.startswith("/api/admin/"):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        with _ADMIN_LIMIT_LOCK:
            attempts = _ADMIN_FAILS[client_ip]
            while attempts and now - attempts[0] > _ADMIN_WINDOW_SECONDS:
                attempts.popleft()
            if len(attempts) >= _ADMIN_MAX_FAILURES:
                return JSONResponse(status_code=429, content={"detail": "Слишком много неудачных попыток. Повторите позже."},
                                    headers={"Cache-Control": "no-store", "Retry-After": "600"})
        response = await call_next(request)
        if response.status_code == 401:
            with _ADMIN_LIMIT_LOCK:
                attempts = _ADMIN_FAILS[client_ip]
                while attempts and now - attempts[0] > _ADMIN_WINDOW_SECONDS:
                    attempts.popleft()
                attempts.append(now)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        return response
    return await call_next(request)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS cities(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, city_id INTEGER NOT NULL REFERENCES cities(id), name TEXT NOT NULL, description TEXT DEFAULT '', active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS variants(id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE, grams REAL NOT NULL, price INTEGER NOT NULL DEFAULT 0, active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS quarries(id INTEGER PRIMARY KEY, city_id INTEGER NOT NULL REFERENCES cities(id), name TEXT NOT NULL, address TEXT DEFAULT '', coordinates TEXT DEFAULT '', instructions TEXT DEFAULT '', photo_url TEXT DEFAULT '', active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, city_id INTEGER NOT NULL, product_id INTEGER NOT NULL, variant_id INTEGER NOT NULL, quarry_id INTEGER, customer_id TEXT DEFAULT '', quantity INTEGER NOT NULL DEFAULT 1, total INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'demo_pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS inventory_items(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          city_id INTEGER NOT NULL REFERENCES cities(id),
          product_id INTEGER NOT NULL REFERENCES products(id),
          variant_id INTEGER NOT NULL REFERENCES variants(id),
          address TEXT NOT NULL,
          photo_url TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'available',
          order_id TEXT UNIQUE,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS support_sessions(
          chat_id TEXT PRIMARY KEY,
          order_id TEXT DEFAULT '',
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS wallet_accounts(
          telegram_id TEXT PRIMARY KEY,
          balance INTEGER NOT NULL DEFAULT 0 CHECK(balance >= 0),
          updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS wallet_ledger(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          telegram_id TEXT NOT NULL,
          amount INTEGER NOT NULL,
          kind TEXT NOT NULL,
          reference_id TEXT NOT NULL UNIQUE,
          description TEXT NOT NULL DEFAULT '',
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS wallet_topups(
          id TEXT PRIMARY KEY,
          telegram_id TEXT NOT NULL,
          amount INTEGER NOT NULL CHECK(amount > 0),
          provider_order_id TEXT UNIQUE NOT NULL,
          public_id TEXT,
          payment_url TEXT,
          status TEXT NOT NULL DEFAULT 'CREATED',
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS bot_last_messages(
          chat_id TEXT PRIMARY KEY,
          message_id INTEGER NOT NULL,
          updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS bot_users(
          telegram_id TEXT PRIMARY KEY,
          first_name TEXT DEFAULT '',
          username TEXT DEFAULT '',
          is_blocked INTEGER NOT NULL DEFAULT 0,
          started_at TEXT DEFAULT CURRENT_TIMESTAMP,
          last_seen_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        if c.execute("SELECT COUNT(*) FROM cities").fetchone()[0] == 0:
            city_ids = {}
            for city_name in ("Невьянск", "Екатеринбург", "Нижний Тагил", "Первоуральск", "Верхняя Пышма", "Кировград"):
                city_ids[city_name] = c.execute("INSERT INTO cities(name) VALUES(?)", (city_name,)).lastrowid
            for city_name, city_id in city_ids.items():
                for name, desc in [
                    ("Песок Ольга", "Чистый строительный песок от карьера Ольга"),
                    ("Песок Миша", "Песок средней фракции от карьера Миша")
                ]:
                    pid = c.execute("INSERT INTO products(city_id,name,description) VALUES(?,?,?)", (city_id,name,desc)).lastrowid
                    prices = (2500, 5000, 7000, 10000) if name == "Песок Ольга" else (2000, 4000, 8000, 11000)
                    for grams, price in zip((0.5, 1, 2, 3), prices):
                        c.execute("INSERT INTO variants(product_id,grams,price) VALUES(?,?,?)", (pid,grams,price))
                c.execute("INSERT INTO quarries(city_id,name,address,instructions) VALUES(?,?,?,?)", (city_id,"Карьер Ольга / Миша","Адрес уточняется у администратора","Точка выдачи будет подтверждена после оформления заказа."))
        order_cols = [r["name"] for r in c.execute("PRAGMA table_info(orders)").fetchall()]
        if "photo_sent" not in order_cols:
            c.execute("ALTER TABLE orders ADD COLUMN photo_sent INTEGER NOT NULL DEFAULT 0")
        if "inventory_item_id" not in order_cols:
            c.execute("ALTER TABLE orders ADD COLUMN inventory_item_id INTEGER")
        if "payment_public_id" not in order_cols:
            c.execute("ALTER TABLE orders ADD COLUMN payment_public_id TEXT")
        if "payment_url" not in order_cols:
            c.execute("ALTER TABLE orders ADD COLUMN payment_url TEXT")
        if "payment_status" not in order_cols:
            c.execute("ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'NOT_CREATED'")
        variant_cols = [r["name"] for r in c.execute("PRAGMA table_info(variants)").fetchall()]
        if "stock" not in variant_cols:
            c.execute("ALTER TABLE variants ADD COLUMN stock INTEGER NOT NULL DEFAULT 0")
        # Hide all 0.5 g variants from sale while retaining old order/inventory history.
        c.execute("UPDATE variants SET active=0 WHERE grams=0.5")
        # Keep the agreed price list in sync for existing databases too.
        for product in c.execute("SELECT id, name FROM products WHERE name IN ('Песок Ольга', 'Песок Миша')").fetchall():
            prices = (2500, 5000, 7000, 10000) if product["name"] == "Песок Ольга" else (2000, 4000, 8000, 11000)
            for grams, price in zip((0.5, 1, 2, 3), prices):
                c.execute("UPDATE variants SET price=? WHERE product_id=? AND grams=?", (price, product["id"], grams))
init_db()

def telegram_user_from_init_data(init_data: str) -> str:
    if not TELEGRAM_BOT_TOKEN or not init_data:
        raise HTTPException(401, "Откройте личный кабинет через Telegram")
    try:
        pairs = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
        data = dict(pairs)
        received_hash = data.pop("hash", "")
        if not received_hash:
            raise ValueError("missing hash")
        check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
        secret_key = hmac.new(b"WebAppData", TELEGRAM_BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()
        calculated = hmac.new(secret_key, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calculated, received_hash):
            raise ValueError("invalid hash")
        auth_date = int(data.get("auth_date", "0"))
        if auth_date <= 0 or abs(int(time.time()) - auth_date) > 86400:
            raise ValueError("expired init data")
        user = json.loads(data.get("user", "{}"))
        user_id = str(user.get("id", ""))
        if not user_id.isdigit():
            raise ValueError("missing user id")
        return user_id
    except Exception:
        raise HTTPException(401, "Не удалось подтвердить профиль Telegram. Закройте и заново откройте Mini App")

def require_telegram_user(request: Request) -> str:
    return telegram_user_from_init_data(request.headers.get("X-Telegram-Init-Data", ""))

class WalletTopupIn(BaseModel):
    amount: int = Field(ge=3000, le=75000)

class WalletPayIn(BaseModel):
    order_id: str = Field(min_length=1, max_length=100)

class OrderIn(BaseModel):
    city_id: int
    product_id: int
    variant_id: int
    quantity: int = Field(default=1, ge=1, le=50)
    customer_id: str = ""

class CityIn(BaseModel):
    name: str

class ProductIn(BaseModel):
    city_id: int
    name: str
    description: str = ""

class VariantIn(BaseModel):
    product_id: int
    grams: float
    price: int = Field(ge=0)

class QuarryIn(BaseModel):
    city_id: int
    name: str
    address: str = ""
    coordinates: str = ""
    instructions: str = ""
    photo_url: str = ""

class InventoryIn(BaseModel):
    city_id: int
    product_id: int
    variant_id: int
    address: str = Field(min_length=3, max_length=500)
    photo_url: str = Field(min_length=8, max_length=2000)

def admin_guard(password: Optional[str]):
    if not ADMIN_PASSWORD:
        raise HTTPException(503, "Администрирование отключено: задайте ADMIN_PASSWORD в настройках сервиса.")
    if not password or not secrets.compare_digest(password, ADMIN_PASSWORD):
        raise HTTPException(401, "Неверный пароль администратора")

@app.get("/media/olga.jpg")
def photo_olga():
    from fastapi.responses import Response
    return Response(content=base64.b64decode(PHOTO_OLGA_B64), media_type="image/jpeg")

@app.get("/media/misha.jpg")
def photo_misha():
    from fastapi.responses import Response
    return Response(content=base64.b64decode(PHOTO_MISHA_B64), media_type="image/jpeg")

@app.on_event("startup")
def register_telegram_webhook():
    """Register the Telegram webhook automatically after deployment."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_WEBHOOK_SECRET:
        print("Telegram webhook not registered: set TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET in Render.")
        return
    payload = urllib.parse.urlencode({
        "url": PUBLIC_BASE_URL + "/api/telegram/webhook",
        "secret_token": TELEGRAM_WEBHOOK_SECRET,
        "allowed_updates": json.dumps(["message", "edited_message", "callback_query"])
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/setWebhook",
        data=payload,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            result = json.loads(response.read().decode("utf-8"))
        if result.get("ok"):
            print("Telegram webhook registered: " + PUBLIC_BASE_URL + "/api/telegram/webhook")
        else:
            print("Telegram webhook registration failed: " + str(result.get("description", "unknown"))[:200])
    except Exception as exc:
        print("Telegram webhook registration failed: " + str(exc)[:200])

def telegram_api(method: str, payload_obj: dict):
    payload = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/" + method,
        data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(str(result.get("description", "Telegram API error"))[:200])
    return result

def bot_send(chat_id, text_out: str, keyboard=None, photo=None):
    # Always keep a personal-account shortcut as the first button for customers.
    is_admin = bool(ADMIN_TELEGRAM_CHAT_ID) and str(chat_id) == str(ADMIN_TELEGRAM_CHAT_ID)
    if not is_admin:
        markup = dict(keyboard or {})
        rows = list(markup.get("inline_keyboard") or [])
        has_account = any(
            any(str(button.get("callback_data") or "") == "account" for button in row)
            for row in rows
        )
        if not has_account:
            rows.insert(0, [{"text": "👤 Личный кабинет", "callback_data": "account"}])
        has_support_contact = any(
            any(str(button.get("url") or "") == "https://t.me/sergotripcfs" for button in row)
            for row in rows
        )
        if not has_support_contact:
            rows.append([{"text": "🆘 Связаться с поддержкой", "url": "https://t.me/sergotripcfs"}])
        markup["inline_keyboard"] = rows
        keyboard = markup
    payload = {"chat_id": chat_id}
    if photo:
        payload["photo"] = photo
        payload["caption"] = text_out
    else:
        payload["text"] = text_out
    if keyboard:
        payload["reply_markup"] = keyboard
    result = telegram_api("sendPhoto" if photo else "sendMessage", payload)
    # Keep the chat tidy: replace the previous bot message after the new one is sent.
    if not is_admin:
        new_message_id = (result.get("result") or {}).get("message_id")
        with db() as c:
            previous = c.execute("SELECT message_id FROM bot_last_messages WHERE chat_id=?", (str(chat_id),)).fetchone()
            c.execute("INSERT INTO bot_last_messages(chat_id,message_id,updated_at) VALUES(?,?,CURRENT_TIMESTAMP) "
                      "ON CONFLICT(chat_id) DO UPDATE SET message_id=excluded.message_id,updated_at=CURRENT_TIMESTAMP",
                      (str(chat_id), int(new_message_id or 0)))
        if previous and previous["message_id"] and previous["message_id"] != new_message_id:
            try:
                telegram_api("deleteMessage", {"chat_id": chat_id, "message_id": int(previous["message_id"])})
            except Exception as exc:
                print("Previous bot message cleanup skipped: " + str(exc)[:120])
    return result

def city_keyboard():
    with db() as c:
        rows = c.execute("SELECT id,name FROM cities ORDER BY name").fetchall()
    return {"inline_keyboard": [[{"text": row["name"], "callback_data": "city:" + str(row["id"])}] for row in rows]}

def product_keyboard(city_id: int):
    with db() as c:
        rows = c.execute("SELECT id,name FROM products WHERE city_id=? AND active=1 ORDER BY name", (city_id,)).fetchall()
    buttons = [[{"text": row["name"], "callback_data": "prod:" + str(city_id) + ":" + str(row["id"])}] for row in rows]
    buttons.append([{"text": "⬅️ Выбрать другой город", "callback_data": "cities"}])
    return {"inline_keyboard": buttons}

def variant_keyboard(city_id: int, product_id: int):
    with db() as c:
        product = c.execute("SELECT name FROM products WHERE id=? AND city_id=? AND active=1", (product_id, city_id)).fetchone()
        rows = c.execute("SELECT id,grams,price FROM variants WHERE product_id=? AND active=1 ORDER BY grams", (product_id,)).fetchall()
    if not product:
        return None, None
    buttons = [[{"text": str(row["grams"]) + " г — " + str(row["price"]) + " ₽", "callback_data": "buy:" + str(city_id) + ":" + str(product_id) + ":" + str(row["id"])}] for row in rows]
    buttons.append([{"text": "⬅️ К товарам", "callback_data": "city:" + str(city_id)}])
    return product["name"], {"inline_keyboard": buttons}

def telegram_create_order(chat_id: int, city_id: int, product_id: int, variant_id: int):
    with db() as c:
        c.execute("BEGIN IMMEDIATE")
        v = c.execute("""SELECT v.*, p.name AS product_name, p.city_id FROM variants v
            JOIN products p ON p.id=v.product_id
            WHERE v.id=? AND p.id=? AND p.city_id=? AND v.active=1 AND p.active=1""",
            (variant_id, product_id, city_id)).fetchone()
        if not v:
            return None, "Этот вариант больше недоступен. Выберите товар заново."
        item = c.execute("""SELECT id,photo_url,address FROM inventory_items WHERE city_id=? AND product_id=? AND variant_id=?
            AND status='available' ORDER BY id LIMIT 1""", (city_id, product_id, variant_id)).fetchone()
        if not item:
            return None, "Сейчас этой позиции нет в наличии. Напишите администратору."
        order_id = secrets.token_urlsafe(9)
        total = int(v["price"])
        c.execute("""INSERT INTO orders(id,city_id,product_id,variant_id,quantity,total,customer_id,status,inventory_item_id)
            VALUES(?,?,?,?,?,?,?,?,?)""", (order_id, city_id, product_id, variant_id, 1, total, str(chat_id), "demo_pending", item["id"]))
        c.execute("UPDATE inventory_items SET status='reserved',order_id=? WHERE id=? AND status='available'", (order_id, item["id"]))
        if c.execute("SELECT changes()").fetchone()[0] != 1:
            raise RuntimeError("Позицию уже забрал другой заказ. Попробуйте ещё раз.")
    notify_admin_new_order(order_id, city_id, product_id, variant_id, total, str(chat_id))
    return {"order_id": order_id, "total": total, "product": v["product_name"], "grams": v["grams"], "photo_url": item["photo_url"], "address": item["address"]}, None

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """Telegram bot: welcome, city/product/variant menus and order creation."""
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(503, "Telegram bot is not configured")
    if not TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(503, "Set TELEGRAM_WEBHOOK_SECRET in Render Environment")
    supplied_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not hmac.compare_digest(supplied_secret, TELEGRAM_WEBHOOK_SECRET):
        raise HTTPException(403, "Invalid Telegram webhook secret")
    try:
        update = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON update")
    try:
        callback = update.get("callback_query")
        if callback:
            callback_id = callback.get("id")
            data = str(callback.get("data") or "")
            message = callback.get("message") or {}
            chat_id = (message.get("chat") or {}).get("id")
            if callback_id:
                try:
                    telegram_api("answerCallbackQuery", {"callback_query_id": callback_id})
                except Exception:
                    pass
            if not chat_id:
                return {"ok": True}
            if data == "account":
                telegram_id = str(chat_id)
                with db() as c:
                    c.execute("INSERT OR IGNORE INTO wallet_accounts(telegram_id,balance) VALUES(?,0)", (telegram_id,))
                    account = c.execute("SELECT balance FROM wallet_accounts WHERE telegram_id=?", (telegram_id,)).fetchone()
                    recent = c.execute("""SELECT o.id,o.total,o.status,o.created_at,p.name AS product_name,v.grams
                        FROM orders o LEFT JOIN products p ON p.id=o.product_id
                        LEFT JOIN variants v ON v.id=o.variant_id
                        WHERE o.customer_id=? ORDER BY o.created_at DESC LIMIT 5""", (telegram_id,)).fetchall()
                message = "👤 Личный кабинет PESOK\n\n💳 Баланс: " + str(int(account["balance"])) + " ₽\n\n🛍 Последние покупки:"
                if recent:
                    for row in recent:
                        message += "\n• " + str(row["product_name"] or "Заказ") + " · " + str(row["grams"] or "—") + " г — " + str(row["total"]) + " ₽\n  Статус: " + str(row["status"]) + " · № " + str(row["id"])
                else:
                    message += "\nПокупок пока нет."
                message += "\n\nДля пополнения кошелька и подробной истории откройте Mini App."
                bot_send(chat_id, message, {"inline_keyboard": [[{"text":"💳 Пополнить баланс / кабинет","web_app":{"url":PUBLIC_BASE_URL + "/"}}], [{"text":"📍 Каталог","callback_data":"cities"}]]})
            elif data == "support":
                bot_send(chat_id, "🆘 Поддержка PESOK\nНапишите следующим сообщением, с какой сложностью столкнулись, или свяжитесь напрямую: @sergotripcfs", {"inline_keyboard":[[{"text":"✉️ Написать в поддержку @sergotripcfs","url":"https://t.me/sergotripcfs"}]]})
            elif data.startswith("support:"):
                support_order_id = data.split(":", 1)[1]
                with db() as c:
                    c.execute("INSERT OR REPLACE INTO support_sessions(chat_id,order_id,created_at) VALUES(?,?,CURRENT_TIMESTAMP)", (str(chat_id), support_order_id))
                bot_send(chat_id, "🆘 Поддержка PESOK\nЗаказ: " + support_order_id + "\nОпишите проблему здесь или свяжитесь напрямую: @sergotripcfs.", {"inline_keyboard":[[{"text":"✉️ Написать в поддержку @sergotripcfs","url":"https://t.me/sergotripcfs"}]]})
            elif data == "cities":
                bot_send(chat_id, "📍 Выберите город:", city_keyboard())
            elif data.startswith("city:"):
                city_id = int(data.split(":")[1])
                with db() as c:
                    city = c.execute("SELECT name FROM cities WHERE id=?", (city_id,)).fetchone()
                if city:
                    bot_send(chat_id, "📍 Город: " + city["name"] + "\nВыберите товар:", product_keyboard(city_id))
            elif data.startswith("prod:"):
                _, city_raw, product_raw = data.split(":")
                city_id, product_id = int(city_raw), int(product_raw)
                name, keyboard = variant_keyboard(city_id, product_id)
                if name and keyboard:
                    bot_send(chat_id, "🛒 " + name + "\nВыберите фасовку и цену:", keyboard)
                else:
                    bot_send(chat_id, "Товар больше недоступен. Выберите город заново.", city_keyboard())
            elif data.startswith("buy:"):
                _, city_raw, product_raw, variant_raw = data.split(":")
                order, error = telegram_create_order(int(chat_id), int(city_raw), int(product_raw), int(variant_raw))
                if error:
                    bot_send(chat_id, "⚠️ " + error, {"inline_keyboard": [[{"text": "📍 В каталог", "callback_data": "cities"}]]})
                else:
                    bot_send(chat_id, "✅ Заказ: " + order["order_id"] + "\nТовар: " + order["product"] + " · " + str(order["grams"]) + " г\nСумма: " + str(order["total"]) + " ₽\nФото заказа: " + order["photo_url"] + "\n\nЗаказ зарезервирован. Оплата пока не подключена, списания нет.", {"inline_keyboard": [[{"text": "👤 Личный кабинет", "callback_data": "account"}], [{"text": "🆘 Поддержка", "callback_data": "support:" + order["order_id"]}], [{"text": "🛒 Открыть Mini App", "web_app": {"url": PUBLIC_BASE_URL + "/"}}], [{"text": "Выбрать ещё", "callback_data": "cities"}]]})
            return {"ok": True}
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        text_in = str(message.get("text") or "").strip()
        chat_id = chat.get("id")
        command = text_in.split(" ", 1)[0].split("@", 1)[0]
        if chat_id and chat.get("type") == "private":
            user_obj = message.get("from") or {}
            with db() as conn:
                conn.execute("""INSERT INTO bot_users(telegram_id,first_name,username,last_seen_at)
                    VALUES(?,?,?,CURRENT_TIMESTAMP)
                    ON CONFLICT(telegram_id) DO UPDATE SET first_name=excluded.first_name,
                    username=excluded.username,last_seen_at=CURRENT_TIMESTAMP""",
                    (str(chat_id),str(user_obj.get("first_name") or "")[:200],str(user_obj.get("username") or "")[:100]))
        if chat_id and command in ("/start", "/shop", "/menu"):
            welcome = ("Добро пожаловать в PESOK market! 🏖️\n"
                       "Выберите город и товар прямо в чате или откройте магазин.\n"
                       "Наличие и стоимость отображаются в меню.")
            keyboard = {"inline_keyboard": [
                [{"text": "👤 Личный кабинет", "callback_data": "account"}],
                [{"text": "📍 Выбрать город и товар", "callback_data": "cities"}],
                [{"text": "🛒 Открыть PESOK market", "web_app": {"url": PUBLIC_BASE_URL + "/"}}]
            ]}
            bot_send(chat_id, welcome, keyboard, photo="https://d2jqrm6oza8nb6.cloudfront.net/datasets/adc51246-1c49-4004-940c-fbf6eb1f24a3.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiZDQ1Yjc3YTMxZjU1OGI4OCIsImJ1Y2tldCI6InJ1bndheS1kYXRhc2V0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5Mjg2MDE5NX0.vT_b5R0pUd1xxd99mlldGy3q8h5Njfa-sSuIHv6SpTI")
        elif chat_id and command in ("/help", "/support"):
            with db() as c:
                c.execute("INSERT OR REPLACE INTO support_sessions(chat_id,order_id,created_at) VALUES(?,?,CURRENT_TIMESTAMP)", (str(chat_id), "",))
            bot_send(chat_id, "🆘 Поддержка PESOK\nОпишите проблему следующим сообщением или напишите напрямую: @sergotripcfs.", {"inline_keyboard": [[{"text": "✉️ Написать в поддержку @sergotripcfs", "url": "https://t.me/sergotripcfs"}], [{"text": "📍 Каталог", "callback_data": "cities"}], [{"text": "🆘 Поддержка", "callback_data": "support"}]]})
        elif chat_id and text_in and not text_in.startswith("/"):
            with db() as c:
                session = c.execute("SELECT order_id FROM support_sessions WHERE chat_id=?", (str(chat_id),)).fetchone()
            if session and ADMIN_TELEGRAM_CHAT_ID:
                forwarded = "🆘 Обращение PESOK\nЗаказ: " + str(session["order_id"] or "не указан") + "\nTelegram ID клиента: " + str(chat_id) + "\nСообщение: " + text_in[:3000]
                bot_send(ADMIN_TELEGRAM_CHAT_ID, forwarded)
                bot_send(chat_id, "✅ Обращение передано в поддержку. Номер заказа: " + str(session["order_id"] or "не указан") + ".")
    except Exception as exc:
        print("Telegram webhook processing failed: " + str(exc)[:240])
    return {"ok": True}

@app.get("/health")
def health():
    return {"ok": True, "app": "PESOK"}

@app.get("/api/catalog")
def catalog():
    with db() as c:
        cities = [dict(r) for r in c.execute("SELECT * FROM cities ORDER BY name")]
        products = []
        for p in c.execute("SELECT * FROM products WHERE active=1 ORDER BY name"):
            item = dict(p)
            item["variants"] = [dict(v) for v in c.execute("SELECT * FROM variants WHERE product_id=? AND active=1 ORDER BY grams", (p["id"],))]
            products.append(item)
        quarries = [dict(r) for r in c.execute("SELECT id,city_id,name,address,coordinates,instructions,photo_url FROM quarries WHERE active=1")]
        return {"cities": cities, "products": products, "quarries": quarries}

def notify_admin_new_order(order_id: str, city_id: int, product_id: int, variant_id: int, total: int, customer_id: str):
    """Best-effort Telegram alert; notification failure must not cancel the customer's order."""
    if not TELEGRAM_BOT_TOKEN or not ADMIN_TELEGRAM_CHAT_ID:
        return
    try:
        with db() as c:
            row = c.execute("""SELECT ci.name AS city_name, p.name AS product_name, v.grams
                FROM cities ci JOIN products p ON p.city_id=ci.id
                JOIN variants v ON v.product_id=p.id
                WHERE ci.id=? AND p.id=? AND v.id=?""", (city_id, product_id, variant_id)).fetchone()
        if not row:
            return
        text_msg = ("🛒 Новый заказ в PESOK\n"
                    + "Заказ: " + order_id + "\n"
                    + "Город: " + str(row["city_name"]) + "\n"
                    + "Товар: " + str(row["product_name"]) + " · " + str(row["grams"]) + " г\n"
                    + "Сумма: " + str(total) + " ₽\n"
                    + "Telegram ID клиента: " + (customer_id or "не указан") + "\n"
                    + "Статус: ожидает подтверждения\n"
                    + "Админка: " + PUBLIC_BASE_URL + "/")
        payload = urllib.parse.urlencode({"chat_id": ADMIN_TELEGRAM_CHAT_ID, "text": text_msg, "disable_web_page_preview": "true"}).encode()
        request = urllib.request.Request("https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage", data=payload, method="POST")
        with urllib.request.urlopen(request, timeout=8) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not result.get("ok"):
            print("Admin Telegram notification failed: " + str(result.get("description", "unknown error"))[:200])
    except Exception as exc:
        print("Admin Telegram notification failed: " + str(exc)[:200])

@app.post("/api/orders")
def create_order(order: OrderIn, request: Request):
    telegram_id = require_telegram_user(request)
    if order.quantity != 1:
        raise HTTPException(400, "Одна позиция склада оформляется на один заказ. Создайте отдельные заказы для нескольких позиций.")
    with db() as c:
        c.execute("BEGIN IMMEDIATE")
        v = c.execute("""SELECT v.*, p.city_id FROM variants v JOIN products p ON p.id=v.product_id
          WHERE v.id=? AND p.id=? AND p.city_id=? AND v.active=1 AND p.active=1""",
          (order.variant_id, order.product_id, order.city_id)).fetchone()
        if not v:
            raise HTTPException(400, "Выбранный вариант больше недоступен")
        item = c.execute("""SELECT id FROM inventory_items
          WHERE city_id=? AND product_id=? AND variant_id=? AND status='available'
          ORDER BY id LIMIT 1""", (order.city_id, order.product_id, order.variant_id)).fetchone()
        if not item:
            raise HTTPException(409, "В этом городе нет свободных позиций такого товара. Обратитесь к администратору.")
        total = int(v["price"])
        oid = secrets.token_urlsafe(9)
        c.execute("INSERT INTO orders(id,city_id,product_id,variant_id,quantity,total,customer_id,status,inventory_item_id) VALUES(?,?,?,?,?,?,?,?,?)",
          (oid, order.city_id, order.product_id, order.variant_id, 1, total, telegram_id, "demo_pending", item["id"]))
        c.execute("UPDATE inventory_items SET status='reserved', order_id=? WHERE id=? AND status='available'", (oid, item["id"]))
        if c.execute("SELECT changes()").fetchone()[0] != 1:
            raise HTTPException(409, "Позиция только что была зарезервирована другим заказом. Попробуйте ещё раз.")
        notify_admin_new_order(oid, order.city_id, order.product_id, order.variant_id, total, telegram_id)
        return {"order_id": oid, "total": total, "status": "demo_pending",
                "message": "Заказ сохранён, позиция зарезервирована. Оплата пока не подключена; списания нет."}

@app.get("/api/is-admin")
def check_is_admin(request: Request):
    telegram_id = require_telegram_user(request)
    return {"is_admin": bool(ADMIN_TELEGRAM_CHAT_ID) and telegram_id == str(ADMIN_TELEGRAM_CHAT_ID)}

@app.get("/api/me")
def get_my_account(request: Request):
    telegram_id = require_telegram_user(request)
    with db() as c:
        c.execute("INSERT OR IGNORE INTO wallet_accounts(telegram_id,balance) VALUES(?,0)", (telegram_id,))
        account = c.execute("SELECT balance FROM wallet_accounts WHERE telegram_id=?", (telegram_id,)).fetchone()
        orders = c.execute("""SELECT o.id,o.total,o.status,o.created_at,p.name AS product_name,v.grams
          FROM orders o LEFT JOIN products p ON p.id=o.product_id
          LEFT JOIN variants v ON v.id=o.variant_id
          WHERE o.customer_id=? ORDER BY o.created_at DESC LIMIT 10""", (telegram_id,)).fetchall()
        ledger = c.execute("""SELECT amount,kind,reference_id,description,created_at
          FROM wallet_ledger WHERE telegram_id=? ORDER BY id DESC LIMIT 20""", (telegram_id,)).fetchall()
    return {"telegram_id":telegram_id,"balance":int(account["balance"]),
            "orders":[dict(x) for x in orders],"operations":[dict(x) for x in ledger]}

@app.post("/api/wallet/topup")
def create_wallet_topup(payload: WalletTopupIn, request: Request):
    telegram_id = require_telegram_user(request)
    if not BETAPAY_API_KEY:
        raise HTTPException(503, "Приём платежей временно недоступен")
    topup_id = secrets.token_urlsafe(10)
    provider_order_id = "wallet_" + topup_id
    payment = bpay_create_payment(payload.amount, provider_order_id)
    with db() as c:
        c.execute("INSERT INTO wallet_topups(id,telegram_id,amount,provider_order_id,public_id,payment_url,status) VALUES(?,?,?,?,?,?,?)",
          (topup_id,telegram_id,payload.amount,provider_order_id,payment["public_id"],payment["payment_url"],str(payment.get("status") or "CREATED")))
    return {"ok":True,"topup_id":topup_id,"amount":payload.amount,"payment_url":payment["payment_url"]}

@app.post("/api/wallet/pay-order")
def wallet_pay_order(payload: WalletPayIn, request: Request):
    telegram_id = require_telegram_user(request)
    with db() as c:
        c.execute("BEGIN IMMEDIATE")
        order = c.execute("""SELECT o.*, p.name AS product_name, i.address AS item_address, i.photo_url AS item_photo_url
          FROM orders o LEFT JOIN products p ON p.id=o.product_id
          LEFT JOIN inventory_items i ON i.id=o.inventory_item_id
          WHERE o.id=? AND o.customer_id=?""", (payload.order_id,telegram_id)).fetchone()
        if not order:
            raise HTTPException(404, "Заказ не найден в вашем кабинете")
        if order["status"] == "paid":
            raise HTTPException(409, "Заказ уже оплачен")
        if order["payment_public_id"] and order["payment_status"] in ("CREATED", "PENDING"):
            raise HTTPException(409, "Для этого заказа уже создана прямая оплата. Завершите её или создайте новый заказ.")
        account = c.execute("SELECT balance FROM wallet_accounts WHERE telegram_id=?", (telegram_id,)).fetchone()
        balance = int(account["balance"]) if account else 0
        amount = int(order["total"])
        if balance < amount:
            raise HTTPException(409, "Недостаточно средств на балансе")
        reference = "order_" + payload.order_id
        if c.execute("SELECT 1 FROM wallet_ledger WHERE reference_id=?", (reference,)).fetchone():
            raise HTTPException(409, "Заказ уже оплачен с баланса")
        c.execute("INSERT OR IGNORE INTO wallet_accounts(telegram_id,balance) VALUES(?,0)", (telegram_id,))
        c.execute("UPDATE wallet_accounts SET balance=balance-?,updated_at=CURRENT_TIMESTAMP WHERE telegram_id=? AND balance>=?", (amount,telegram_id,amount))
        if c.execute("SELECT changes()").fetchone()[0] != 1:
            raise HTTPException(409, "Недостаточно средств на балансе")
        c.execute("INSERT INTO wallet_ledger(telegram_id,amount,kind,reference_id,description) VALUES(?,?,?,?,?)",
          (telegram_id,-amount,"purchase",reference,"Оплата заказа "+payload.order_id))
        c.execute("UPDATE orders SET status='paid',payment_status='PAID' WHERE id=? AND customer_id=?", (payload.order_id,telegram_id))
        c.execute("UPDATE inventory_items SET status='sold' WHERE order_id=? AND status='reserved'", (payload.order_id,))
    delivered = False
    if TELEGRAM_BOT_TOKEN and str(telegram_id).isdigit() and str(order["item_photo_url"] or "").startswith("https://") and order["item_address"]:
        caption = "Заказ оплачен с баланса! Заказ " + payload.order_id + "\\n" + str(order["product_name"] or "Товар") + " — " + str(amount) + " ₽.\\nАдрес выдачи: " + str(order["item_address"]) + "\\nФото заказа: " + str(order["item_photo_url"])
        body = json.dumps({"chat_id":telegram_id,"photo":order["item_photo_url"],"caption":caption},ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request("https://api.telegram.org/bot"+TELEGRAM_BOT_TOKEN+"/sendPhoto",data=body,headers={"Content-Type":"application/json"},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=20) as response:
                delivered = bool(json.loads(response.read().decode("utf-8")).get("ok"))
        except Exception as exc:
            print("Wallet order delivery failed: "+str(exc)[:200])
    with db() as c:
        if delivered:
            c.execute("UPDATE orders SET photo_sent=1 WHERE id=?", (payload.order_id,))
    if not delivered and ADMIN_TELEGRAM_CHAT_ID:
        try:
            bot_send(ADMIN_TELEGRAM_CHAT_ID, "⚠️ Заказ оплачен с баланса, но выдача требует проверки. Заказ: "+payload.order_id)
        except Exception:
            pass
    return {"ok":True,"order_id":payload.order_id,"balance":balance-amount,"delivered":delivered}

def bpay_create_payment(amount: int, order_id: str):
    if not BETAPAY_API_KEY:
        raise HTTPException(503, "Не задан BETAPAY_API_KEY в Render Environment")
    payload = {"amount": amount, "currency": "RUB", "order_id": order_id,
               "description": "PESOK market — заказ " + order_id,
               "success_url": PUBLIC_BASE_URL + "/?payment=success&order_id=" + urllib.parse.quote(order_id),
               "fail_url": PUBLIC_BASE_URL + "/?payment=failed&order_id=" + urllib.parse.quote(order_id)}
    req = urllib.request.Request(BETAPAY_API_BASE + "/payment/create",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + BETAPAY_API_KEY, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        detail = str(exc)
        if hasattr(exc, "read"):
            try: detail = exc.read().decode("utf-8")[:300]
            except Exception: pass
        raise HTTPException(502, "Ошибка B PAY: " + detail[:250])
    payment = result.get("payment") if isinstance(result, dict) else None
    if not result.get("ok") or not isinstance(payment, dict):
        raise HTTPException(502, "B PAY не создал платёж. Проверьте API-ключ и настройки проекта.")
    public_id = str(payment.get("public_id") or "")
    payment_url = str(payment.get("payment_url") or "")
    if str(payment.get("order_id") or order_id) != order_id or int(payment.get("amount", -1)) != amount or not public_id or not payment_url.startswith("https://"):
        raise HTTPException(502, "Ответ B PAY не прошёл проверку заказа и суммы.")
    return payment

@app.post("/api/orders/{order_id}/payment")
def create_order_payment(order_id: str):
    with db() as c:
        order = c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order: raise HTTPException(404, "Заказ не найден")
        if order["status"] == "paid": raise HTTPException(409, "Заказ уже оплачен")
        if order["payment_url"] and order["payment_status"] in ("CREATED", "PENDING"):
            return {"ok": True, "payment_url": order["payment_url"], "public_id": order["payment_public_id"]}
        amount = int(order["total"])
    payment = bpay_create_payment(amount, order_id)
    with db() as c:
        c.execute("UPDATE orders SET payment_public_id=?, payment_url=?, payment_status=?, status='payment_pending' WHERE id=? AND status!='paid'",
            (payment["public_id"], payment["payment_url"], str(payment.get("status") or "CREATED"), order_id))
    return {"ok": True, "payment_url": payment["payment_url"], "public_id": payment["public_id"], "order_id": order_id}

@app.post("/api/payments/bpay/webhook")
async def bpay_webhook(request: Request):
    if not BETAPAY_WEBHOOK_SECRET: raise HTTPException(503, "BETAPAY_WEBHOOK_SECRET is not configured")
    raw = await request.body()
    signature = request.headers.get("X-Betapay-Signature", "")
    secret_bytes = BETAPAY_WEBHOOK_SECRET.encode("utf-8")
    expected = "sha256=" + hmac.new(secret_bytes, raw, hashlib.sha256).hexdigest()
    # Safe diagnostics: never log the secret, received signature, or calculated digest.
    if not signature or not signature.startswith("sha256="):
        print("B PAY webhook signature rejected: header_missing_or_wrong_format; "
              f"header_present={bool(signature)} raw_bytes={len(raw)} secret_bytes={len(secret_bytes)}")
        raise HTTPException(403, "Invalid B PAY signature")
    if not hmac.compare_digest(signature.strip(), expected):
        print("B PAY webhook signature rejected: digest_mismatch; "
              f"header_length={len(signature)} raw_bytes={len(raw)} secret_bytes={len(secret_bytes)}")
        raise HTTPException(403, "Invalid B PAY signature")
    try: event_obj = json.loads(raw.decode("utf-8"))
    except Exception: raise HTTPException(400, "Invalid JSON")
    event = str(event_obj.get("event") or "")
    data = event_obj.get("data") if isinstance(event_obj.get("data"), dict) else event_obj
    if event != "payment.success": return {"ok": True, "ignored": event}
    order_id = str(data.get("order_id") or "")
    public_id = str(data.get("public_id") or "")
    if not order_id or not public_id or str(data.get("currency") or "RUB") != "RUB": raise HTTPException(400, "Invalid payment data")
    try: amount = int(data.get("amount"))
    except (TypeError, ValueError): raise HTTPException(400, "Invalid amount")
    if order_id.startswith("wallet_"):
        with db() as c:
            topup = c.execute("SELECT * FROM wallet_topups WHERE provider_order_id=?", (order_id,)).fetchone()
            if not topup:
                print("B PAY wallet webhook ignored: topup_not_found")
                return {"ok": True, "ignored": "topup_not_found"}
            if int(topup["amount"]) != amount or str(topup["public_id"] or "") != public_id:
                raise HTTPException(400, "Wallet top-up payment does not match")
            if topup["status"] == "PAID":
                return {"ok": True, "duplicate": True, "wallet_topup": True}
            c.execute("INSERT OR IGNORE INTO wallet_accounts(telegram_id,balance) VALUES(?,0)", (topup["telegram_id"],))
            reference = "topup_" + topup["id"]
            if not c.execute("SELECT 1 FROM wallet_ledger WHERE reference_id=?", (reference,)).fetchone():
                c.execute("UPDATE wallet_accounts SET balance=balance+?,updated_at=CURRENT_TIMESTAMP WHERE telegram_id=?", (amount,topup["telegram_id"]))
                c.execute("INSERT INTO wallet_ledger(telegram_id,amount,kind,reference_id,description) VALUES(?,?,?,?,?)",
                  (topup["telegram_id"],amount,"topup",reference,"Пополнение через B PAY"))
            c.execute("UPDATE wallet_topups SET status='PAID' WHERE id=?", (topup["id"],))
        return {"ok": True, "paid": True, "wallet_topup": True}
    with db() as c:
        order = c.execute("SELECT o.*, p.name AS product_name, i.address AS item_address, i.photo_url AS item_photo_url FROM orders o JOIN products p ON p.id=o.product_id LEFT JOIN inventory_items i ON i.id=o.inventory_item_id WHERE o.id=?", (order_id,)).fetchone()
        if not order:
            # B PAY's dashboard test may send a synthetic order_id. The signature
            # has already been verified, so acknowledge unknown test/stale orders
            # to avoid pointless webhook retries; never mark anything as paid.
            print("B PAY webhook ignored: order_not_found; "
                  f"order_id_present={bool(order_id)} public_id_present={bool(public_id)}")
            return {"ok": True, "ignored": "order_not_found"}
        if int(order["total"]) != amount or str(order["payment_public_id"] or "") != public_id: raise HTTPException(400, "Payment does not match order")
        if order["status"] == "paid" and order["photo_sent"]: return {"ok": True, "duplicate": True}
        c.execute("UPDATE orders SET status='paid', payment_status='PAID' WHERE id=?", (order_id,))
    delivered = False
    if TELEGRAM_BOT_TOKEN and str(order["customer_id"]).isdigit() and str(order["item_photo_url"] or "").startswith("https://") and order["item_address"]:
        caption = "Оплата подтверждена! Заказ " + order_id + "\n" + order["product_name"] + " — " + str(amount) + " ₽.\nАдрес выдачи: " + order["item_address"] + "\nФото заказа: " + order["item_photo_url"]
        payload = json.dumps({"chat_id": order["customer_id"], "photo": order["item_photo_url"], "caption": caption}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request("https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendPhoto", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=20) as response: delivered = bool(json.loads(response.read().decode("utf-8")).get("ok"))
        except Exception as exc: print("Paid order delivery failed: " + str(exc)[:200])
    # Once payment is confirmed, never leave the reserved item available for resale
    # just because Telegram photo delivery temporarily failed.
    with db() as c:
        c.execute("UPDATE inventory_items SET status='sold' WHERE id=? AND order_id=? AND status IN ('reserved','sold')",
                  (order["inventory_item_id"], order_id))
        if delivered:
            c.execute("UPDATE orders SET photo_sent=1 WHERE id=?", (order_id,))
    if not delivered and ADMIN_TELEGRAM_CHAT_ID:
        try: bot_send(ADMIN_TELEGRAM_CHAT_ID, "⚠️ Оплата подтверждена, но выдача требует проверки. Заказ: " + order_id)
        except Exception: pass
    return {"ok": True, "paid": True, "delivered": delivered}

class BroadcastIn(BaseModel):
    message: str = Field(min_length=1, max_length=3500)

@app.post("/api/admin/broadcast")
def admin_broadcast(payload: BroadcastIn, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(503, "Не задан TELEGRAM_BOT_TOKEN")
    message = payload.message.strip()
    if not message:
        raise HTTPException(400, "Введите текст рассылки")
    with db() as conn:
        users = [r["telegram_id"] for r in conn.execute("SELECT telegram_id FROM bot_users WHERE is_blocked=0 ORDER BY started_at")]
    sent = failed = blocked = 0
    for user_id in users:
        try:
            result = telegram_api("sendMessage", {"chat_id":user_id,"text":message,"disable_web_page_preview":"true",
                "reply_markup":{"inline_keyboard":[[{"text":"🛒 Открыть PESOK market","web_app":{"url":PUBLIC_BASE_URL+"/"}}]]}})
            if result.get("ok"):
                sent += 1
            else:
                failed += 1
                desc = str(result.get("description") or "").lower()
                if "blocked" in desc or "chat not found" in desc or "deactivated" in desc:
                    blocked += 1
                    with db() as conn:
                        conn.execute("UPDATE bot_users SET is_blocked=1 WHERE telegram_id=?", (user_id,))
        except Exception:
            failed += 1
    return {"ok":True,"total":len(users),"sent":sent,"failed":failed,"blocked":blocked}

@app.get("/api/admin/data")
def admin_data(x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    with db() as c:
        return {
          "cities":[dict(r) for r in c.execute("SELECT * FROM cities ORDER BY name")],
          "products":[dict(r) for r in c.execute("SELECT * FROM products ORDER BY id DESC")],
          "variants":[dict(r) for r in c.execute("SELECT * FROM variants ORDER BY product_id,grams")],
          "quarries":[dict(r) for r in c.execute("SELECT * FROM quarries ORDER BY id DESC")],
          "orders":[dict(r) for r in c.execute("SELECT o.*, p.name AS product_name FROM orders o LEFT JOIN products p ON p.id=o.product_id ORDER BY o.created_at DESC LIMIT 100")],
          "inventory":[dict(r) for r in c.execute("""SELECT i.*, c.name AS city_name, p.name AS product_name, v.grams, v.price
            FROM inventory_items i JOIN cities c ON c.id=i.city_id JOIN products p ON p.id=i.product_id
            JOIN variants v ON v.id=i.variant_id ORDER BY i.id DESC LIMIT 500""")]
        }


@app.post("/api/admin/orders/{order_id}/mark-paid")
def mark_order_paid(order_id: str, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(503, "Не задан TELEGRAM_BOT_TOKEN в Render → Environment")
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        order = conn.execute("""SELECT o.*, p.name AS product_name, i.address AS item_address, i.photo_url AS item_photo_url,
            i.status AS item_status FROM orders o JOIN products p ON p.id=o.product_id
            LEFT JOIN inventory_items i ON i.id=o.inventory_item_id WHERE o.id=?""", (order_id,)).fetchone()
        if not order:
            raise HTTPException(404, "Заказ не найден")
        if order["photo_sent"]:
            return {"ok": True, "message": "Фото и адрес уже отправлены"}
        if not str(order["customer_id"]).isdigit():
            raise HTTPException(400, "Нет Telegram ID покупателя. Покупатель должен открыть бота и нажать /start до заказа.")
        if not order["inventory_item_id"] or order["item_status"] != "reserved":
            raise HTTPException(409, "За заказом не закреплена зарезервированная позиция склада. Проверьте заказ в админке.")
        photo_url = str(order["item_photo_url"] or "").strip()
        address = str(order["item_address"] or "").strip()
        if not photo_url.startswith(("https://", "http://")) or not address:
            raise HTTPException(409, "У позиции склада не указаны корректная ссылка на фото и адрес.")
        caption = "Оплата подтверждена! Заказ " + order_id + "\n" + order["product_name"] + " — " + str(order["total"]) + " ₽.\nАдрес выдачи: " + address + "\nФото этой позиции: " + photo_url
        payload = urllib.parse.urlencode({"chat_id": order["customer_id"], "photo": photo_url, "caption": caption}).encode()
        request = urllib.request.Request("https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendPhoto", data=payload, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
            if not result.get("ok"):
                detail = str(result.get("description") or "Telegram отклонил запрос")
                raise HTTPException(502, "Telegram: " + detail[:240] + ". Проверьте, что ссылка открывает само изображение, а покупатель запускал бота через /start.")
        except HTTPException:
            raise
        except Exception as exc:
            detail = str(exc)
            if hasattr(exc, "read"):
                try:
                    upstream = json.loads(exc.read().decode("utf-8"))
                    detail = str(upstream.get("description") or detail)
                except Exception:
                    pass
            raise HTTPException(502, "Не удалось отправить фото позиции: " + detail[:220] + ". Нужна прямая HTTPS-ссылка на изображение.")
        conn.execute("UPDATE inventory_items SET status='sold' WHERE id=? AND status='reserved' AND order_id=?", (order["inventory_item_id"], order_id))
        if conn.execute("SELECT changes()").fetchone()[0] != 1:
            raise HTTPException(409, "Не удалось отметить позицию как проданную.")
        conn.execute("UPDATE orders SET status='paid', photo_sent=1 WHERE id=?", (order_id,))
        return {"ok": True, "message": "Оплата отмечена, адрес и фото конкретной позиции отправлены покупателю"}

@app.post("/api/admin/cities")
def add_city(item: CityIn, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    name = item.name.strip()
    if not name: raise HTTPException(400, "Укажите название города")
    try:
        with db() as c:
            cur = c.execute("INSERT INTO cities(name) VALUES(?)", (name,))
            return {"id": cur.lastrowid, "name": name}
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Такой город уже есть")

@app.post("/api/admin/products")
def add_product(item: ProductIn, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    with db() as c:
        if not c.execute("SELECT id FROM cities WHERE id=?", (item.city_id,)).fetchone():
            raise HTTPException(404, "Город не найден")
        cur = c.execute("INSERT INTO products(city_id,name,description) VALUES(?,?,?)", (item.city_id,item.name.strip(),item.description.strip()))
        pid = cur.lastrowid
        for grams in (1, 2, 3):
            c.execute("INSERT INTO variants(product_id,grams,price) VALUES(?,?,0)", (pid,grams))
        return {"id": pid}


@app.post("/api/admin/cities/{city_id}/delete")
def delete_city(city_id: int, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    with db() as c:
        c.execute("BEGIN IMMEDIATE")
        city = c.execute("SELECT id FROM cities WHERE id=?", (city_id,)).fetchone()
        if not city:
            raise HTTPException(404, "Город не найден")
        used = c.execute("""SELECT
            (SELECT COUNT(*) FROM products WHERE city_id=?) +
            (SELECT COUNT(*) FROM inventory_items WHERE city_id=?) +
            (SELECT COUNT(*) FROM orders WHERE city_id=?)""", (city_id, city_id, city_id)).fetchone()[0]
        if used:
            raise HTTPException(409, "Нельзя удалить город, пока в нём есть товары, складские позиции или заказы. Сначала удалите свободные позиции и товары; история заказов сохраняется.")
        c.execute("DELETE FROM cities WHERE id=?", (city_id,))
        return {"ok": True, "message": "Город удалён"}

@app.post("/api/admin/products/{product_id}/delete")
def delete_product(product_id: int, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    with db() as c:
        c.execute("BEGIN IMMEDIATE")
        product = c.execute("SELECT id FROM products WHERE id=?", (product_id,)).fetchone()
        if not product:
            raise HTTPException(404, "Товар не найден")
        used = c.execute("""SELECT
            (SELECT COUNT(*) FROM inventory_items WHERE product_id=?) +
            (SELECT COUNT(*) FROM orders WHERE product_id=?)""", (product_id, product_id)).fetchone()[0]
        if used:
            raise HTTPException(409, "Нельзя удалить товар, связанный со складом или заказами. Удалите свободные позиции склада; товары с историей заказов сохраняются.")
        c.execute("DELETE FROM variants WHERE product_id=?", (product_id,))
        c.execute("DELETE FROM products WHERE id=?", (product_id,))
        return {"ok": True, "message": "Товар удалён"}

@app.post("/api/admin/variants/{variant_id}/delete")
def delete_variant(variant_id: int, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    with db() as c:
        c.execute("BEGIN IMMEDIATE")
        variant = c.execute("SELECT id FROM variants WHERE id=?", (variant_id,)).fetchone()
        if not variant:
            raise HTTPException(404, "Фасовка не найдена")
        used = c.execute("""SELECT
            (SELECT COUNT(*) FROM inventory_items WHERE variant_id=?) +
            (SELECT COUNT(*) FROM orders WHERE variant_id=?)""", (variant_id, variant_id)).fetchone()[0]
        if used:
            raise HTTPException(409, "Нельзя удалить фасовку, связанную со складом или заказами. История должна сохраниться.")
        c.execute("DELETE FROM variants WHERE id=?", (variant_id,))
        return {"ok": True, "message": "Фасовка удалена"}

@app.post("/api/admin/inventory")
def add_inventory_item(item: InventoryIn, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    address = item.address.strip()
    photo_url = item.photo_url.strip()
    if not address or not photo_url.startswith("https://"):
        raise HTTPException(400, "Укажите адрес и полную HTTPS-ссылку на фото.")
    with db() as c:
        row = c.execute("""SELECT v.id FROM variants v JOIN products p ON p.id=v.product_id
          WHERE v.id=? AND v.product_id=? AND p.city_id=? AND p.active=1 AND v.active=1""",
          (item.variant_id, item.product_id, item.city_id)).fetchone()
        if not row:
            raise HTTPException(400, "Город, товар и фасовка не соответствуют друг другу")
        cur = c.execute("""INSERT INTO inventory_items(city_id,product_id,variant_id,address,photo_url,status)
          VALUES(?,?,?,?,?,'available')""", (item.city_id,item.product_id,item.variant_id,address,photo_url))
        return {"ok": True, "id": cur.lastrowid, "message": "Позиция добавлена на склад"}

@app.post("/api/admin/inventory/{item_id}/delete")
def delete_inventory_item(item_id: int, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    with db() as c:
        c.execute("BEGIN IMMEDIATE")
        item = c.execute("SELECT id, status, order_id FROM inventory_items WHERE id=?", (item_id,)).fetchone()
        if not item:
            raise HTTPException(404, "Позиция склада не найдена")
        if item["status"] != "available" or item["order_id"]:
            raise HTTPException(409, "Можно удалить только свободную позицию. Зарезервированные и проданные позиции сохраняются в истории заказов.")
        c.execute("DELETE FROM inventory_items WHERE id=? AND status='available' AND order_id IS NULL", (item_id,))
        if c.execute("SELECT changes()").fetchone()[0] != 1:
            raise HTTPException(409, "Позицию не удалось удалить. Обновите список склада.")
        return {"ok": True, "message": "Позиция удалена со склада"}

@app.post("/api/admin/variants/stock")
def update_variant_stock(payload: dict, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    try:
        variant_id = int(payload.get("variant_id"))
        stock = int(payload.get("stock"))
        if stock < 0 or stock > 1000000:
            raise ValueError()
    except (TypeError, ValueError):
        raise HTTPException(400, "Остаток должен быть целым числом от 0 до 1000000")
    with db() as c:
        row = c.execute("SELECT id FROM variants WHERE id=?", (variant_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Вариант не найден")
        reserved = c.execute("SELECT COALESCE(SUM(quantity),0) FROM orders WHERE variant_id=? AND status='demo_pending'", (variant_id,)).fetchone()[0]
        if stock < int(reserved):
            raise HTTPException(409, "Нельзя установить остаток ниже количества зарезервированных заказов: " + str(reserved))
        c.execute("UPDATE variants SET stock=? WHERE id=?", (stock, variant_id))
        return {"ok": True, "stock": stock}

@app.post("/api/admin/variants")
def update_variant(item: VariantIn, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    with db() as c:
        v = c.execute("SELECT id FROM variants WHERE product_id=? AND grams=?", (item.product_id,item.grams)).fetchone()
        if not v: raise HTTPException(404, "Вариант не найден")
        c.execute("UPDATE variants SET price=? WHERE id=?", (item.price,v["id"]))
        return {"ok": True}

@app.post("/api/admin/quarries")
def add_quarry(item: QuarryIn, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    with db() as c:
        if not c.execute("SELECT id FROM cities WHERE id=?", (item.city_id,)).fetchone():
            raise HTTPException(404, "Город не найден")
        cur = c.execute("INSERT INTO quarries(city_id,name,address,coordinates,instructions,photo_url) VALUES(?,?,?,?,?,?)",
          (item.city_id,item.name.strip(),item.address.strip(),item.coordinates.strip(),item.instructions.strip(),item.photo_url.strip()))
        return {"id": cur.lastrowid}

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML

HTML = r"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#151a16"><title>PESOK — магазин</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
:root{color-scheme:light;--bg:#f5f7fa;--panel:#fff;--line:#e3e8ef;--muted:#727b88;--blue:#1684f8;--white:#17202b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--white);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}header{padding:15px 18px;background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:3}.top{display:flex;justify-content:space-between;align-items:center}.brand{display:flex;align-items:center;gap:11px}.brand-mark{width:48px;height:48px;flex:0 0 48px;border-radius:50%;display:block;filter:drop-shadow(0 2px 7px #d59a2630)}.brand-copy{display:flex;flex-direction:column}.logo{font-weight:900;letter-spacing:1.6px;font-size:20px;color:#1c1a16;line-height:1}.logo span{color:#c88a22}.tag{color:#8c6b35;font-size:9px;letter-spacing:2.4px;margin-top:5px;font-weight:750}.pill{display:none}main{width:100%;max-width:760px;margin:0 auto;padding:16px}.hero{padding:22px 18px 20px;border-radius:20px;background:linear-gradient(135deg,#dcecff,#fff 75%);margin-bottom:20px}.eyebrow{font-size:11px;letter-spacing:1.5px;color:var(--blue);text-transform:uppercase}.hero h1{font-size:32px;line-height:1.05;margin:9px 0}.hero p{color:var(--muted);font-size:14px;line-height:1.5}.label{font-size:12px;color:var(--muted);margin:20px 0 10px;font-weight:700}.cities{display:flex;gap:8px;flex-wrap:wrap}.city{border:1px solid var(--line);background:#fff;color:var(--white);padding:10px 13px;border-radius:12px}.city.active{background:var(--blue);border-color:var(--blue);color:#fff}.grid{display:flex!important;flex-flow:row wrap!important;align-items:stretch;justify-content:flex-start;gap:10px;width:100%}.product{display:block;flex:0 0 calc(50% - 5px)!important;width:calc(50% - 5px)!important;max-width:calc(50% - 5px)!important;background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:12px;min-width:0;box-shadow:0 3px 12px #152c4510}.product-art{height:94px;border-radius:13px;background:linear-gradient(145deg,#d8c3a0,#a98c65 45%,#ead7b8);display:flex;align-items:center;justify-content:center;font-size:35px;margin-bottom:12px}.product h3{margin:0;font-size:16px;line-height:1.2}.desc{color:var(--muted);font-size:11px;line-height:1.35;min-height:44px;margin:6px 0 10px}.variants{display:grid;gap:6px;margin:8px 0 12px}.variant{display:flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:10px;padding:8px 7px;font-size:11px;line-height:1.2;cursor:pointer;min-width:0}.variant:has(input:checked){border-color:var(--blue);background:#edf6ff}.variant input{accent-color:var(--blue);margin:0;flex:0 0 auto}.variant .grams{font-weight:700;white-space:nowrap}.variant .variant-price{font-weight:800;margin-left:auto;white-space:nowrap}.product .btn{font-size:12px;padding:12px 5px}.product .variants{width:100%}.variant{min-width:0}.variant .grams{font-size:11px}.variant .variant-price{font-size:11px}@media(max-width:360px){.grid{gap:6px}.product{flex-basis:calc(50% - 3px);width:calc(50% - 3px);max-width:calc(50% - 3px);padding:8px}.product-art{height:76px}.product h3{font-size:14px}.variant{padding:7px 4px;gap:4px}.variant input{width:13px;height:13px}.variant .grams,.variant .variant-price{font-size:10px}}.product select,.adminbox input,.adminbox select,.adminbox textarea{width:100%;padding:11px;background:#fff;color:var(--white);border:1px solid var(--line);border-radius:10px;margin:5px 0 10px}.price{font-weight:800;font-size:17px;margin:10px 0 12px}.btn{background:var(--blue);border:0;color:#fff;border-radius:12px;font-weight:750;padding:13px;width:100%;cursor:pointer}#orderResult a.btn{display:inline-flex;align-items:center;justify-content:center;width:auto;max-width:100%;margin:14px 0 8px;position:static;vertical-align:top;clear:both;line-height:1.35;white-space:normal}.btn.secondary{background:#fff;color:var(--blue);border:1px solid var(--line)}.notice{background:#eef6ff;border:1px solid #d1e7ff;padding:13px;border-radius:12px;color:#284b70;font-size:13px;line-height:1.5;margin:14px 0}.tabs{display:flex;gap:8px;margin:20px 0}.tabs button{flex:1}.hide{display:none!important}.adminbox{border:1px solid var(--line);background:var(--panel);border-radius:16px;padding:16px;margin-top:14px}.foot{color:var(--muted);font-size:11px;line-height:1.5;padding:24px 0}.order{border-bottom:1px solid var(--line);padding:10px 0;font-size:13px}.small{font-size:11px;color:var(--muted)}@media(min-width:600px){.hero h1{font-size:42px}}
</style></head><body><header><div class="top"><div class="brand"><svg class="brand-mark" viewBox="0 0 100 100" role="img" aria-label="PESOK MARKET"><defs><linearGradient id="gold" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff0a5"/><stop offset=".45" stop-color="#d99b2b"/><stop offset="1" stop-color="#8b5512"/></linearGradient></defs><circle cx="50" cy="50" r="46" fill="#17130e" stroke="url(#gold)" stroke-width="4"/><path d="M25 39 20 18 40 29 Q50 25 60 29 L80 18 75 39 Q83 51 75 64 L63 75 37 75 25 64Q17 51 25 39Z" fill="url(#gold)" stroke="#f8d77c" stroke-width="1.5"/><path d="M28 44 39 39 47 45 43 53 31 52ZM72 44 61 39 53 45 57 53 69 52Z" fill="#17130e"/><ellipse cx="38" cy="47" rx="3" ry="4" fill="#fff4d0"/><ellipse cx="62" cy="47" rx="3" ry="4" fill="#fff4d0"/><path d="M43 59 Q50 54 57 59 L50 65Z" fill="#17130e"/><path d="M37 68 Q50 75 63 68" fill="none" stroke="#17130e" stroke-width="2.5" stroke-linecap="round"/><path d="M35 80h30l-4 8H39Z" fill="url(#gold)"/></svg><div class="brand-copy"><div class="logo">PES<span>O</span>K</div><div class="tag">M A R K E T</div></div></div><div aria-hidden="true"></div></div></header>
<main><section class="hero"><div class="eyebrow">Песок рядом</div><h1>Выбирай.<br>Заказывай.</h1><p>Каталог по городам и точкам выдачи. Выбери позицию и фасовку, чтобы оформить заказ.</p></section>
<div class="label">ВАШ ГОРОД</div><div class="cities" id="cities"></div><div class="label">КАТАЛОГ</div><section class="grid" id="products"><div class="notice">Загружаем каталог…</div></section>
<section class="adminbox" id="customerCabinet">
  <h2>Личный кабинет</h2><div id="accountSummary" class="notice">Загружаем баланс…</div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0">
    <input id="walletAmount" type="number" min="3000" max="75000" step="100" value="3000" placeholder="Сумма пополнения" style="flex:1;min-width:130px;padding:12px;border:1px solid var(--line);border-radius:10px">
    <button class="btn" style="width:auto" onclick="topupWallet()">Пополнить</button>
  </div>
  <h3>Последние покупки</h3><div id="accountOrders" class="small">—</div>
  <h3>Операции по кошельку</h3><div id="walletOperations" class="small">—</div>
  <button class="btn secondary" onclick="loadAccount()">Обновить кабинет</button>
</section>
<section id="orderResult" class="notice hide"></section>
<div class="tabs"><button id="adminPanelButton" class="btn secondary hide" onclick="showAdmin()">Админ-панель</button><button class="btn secondary" onclick="loadCatalog()">Обновить каталог</button></div>
<section id="admin" class="hide"><div class="adminbox"><h3>Вход администратора</h3><input id="adminPassword" type="password" placeholder="Пароль из ADMIN_PASSWORD"><button class="btn" onclick="adminLogin()">Войти</button><div id="adminContent"></div></div></section>
</main>
<script>
const tg=window.Telegram&&window.Telegram.WebApp;if(tg){tg.ready();tg.expand();}
let catalog={cities:[],products:[],quarries:[]},cityId=null,adminPass="";
const rub=n=>new Intl.NumberFormat('ru-RU').format(n)+' ₽';
async function loadCatalog(){try{let r=await fetch('/api/catalog');catalog=await r.json();if(!cityId&&catalog.cities.length)cityId=catalog.cities[0].id;renderCities();renderProducts()}catch(e){document.getElementById('products').innerHTML='<div class="notice">Не удалось загрузить каталог. Обновите страницу.</div>'}}
function renderCities(){document.getElementById('cities').innerHTML=catalog.cities.map(c=>'<button class="city '+(c.id===cityId?'active':'')+'" onclick="cityId='+c.id+';renderCities();renderProducts()">'+esc(c.name)+'</button>').join('')}
function renderProducts(){
  const ps=catalog.products.filter(p=>p.city_id===cityId);
  document.getElementById('products').innerHTML=ps.length?ps.map(p=>{
    return '<article class="product"><h3>'+esc(p.name)+'</h3><div class="desc">'+esc(p.description||'Песок · уточните характеристики')+'</div><div class="variants" role="radiogroup" aria-label="Выберите фасовку">'+p.variants.map((v,i)=>'<label class="variant"><input type="radio" name="variant'+p.id+'" value="'+v.id+'" data-price="'+v.price+'" '+(i===0?'checked':'')+' onchange="priceUpdate('+p.id+')"><span class="grams">'+v.grams.toLocaleString('ru-RU')+' г</span><span class="variant-price">'+rub(v.price)+'</span></label>').join('')+'</div><button class="btn" onclick="makeOrder('+p.id+')">Выбрать и заказать</button></article>';
  }).join(''):'<div class="notice">В этом городе пока нет товаров.</div>';
}
function priceUpdate(pid){let s=document.querySelector('input[name="variant'+pid+'"]:checked');if(s){let p=catalog.products.find(x=>x.id===pid);let b=document.querySelector('#products .product');}}
function telegramHeaders(){return {'Content-Type':'application/json','X-Telegram-Init-Data':tg&&tg.initData?tg.initData:''}}
async function loadAccount(){const summary=document.getElementById('accountSummary');try{if(!tg||!tg.initData){summary.textContent='Откройте Mini App через Telegram, чтобы войти в личный кабинет.';return}const r=await fetch('/api/me',{headers:telegramHeaders(),cache:'no-store'}),d=await r.json();if(!r.ok)throw Error(d.detail||'Не удалось загрузить кабинет');summary.innerHTML='<div class="small">ДЕНЕЖНЫЙ БАЛАНС</div><div style="font-size:28px;font-weight:800;margin:6px 0">'+rub(d.balance)+'</div><div class="small">Пополнение от 3 000 до 75 000 ₽. Заказы можно оплачивать с баланса или напрямую через B PAY.</div>';document.getElementById('accountOrders').innerHTML=d.orders.length?d.orders.map(o=>'<div class="order"><b>'+esc(o.product_name||'Заказ')+'</b> · '+esc(String(o.grams||'—'))+' г<br>'+rub(o.total)+' · '+esc(o.status)+'<br><span class="small">'+esc(o.created_at)+' · № '+esc(o.id)+'</span></div>').join(''):'Покупок пока нет';document.getElementById('walletOperations').innerHTML=d.operations.length?d.operations.map(o=>'<div class="order">'+esc(o.description)+'<br><b>'+(o.amount>0?'+':'')+rub(o.amount)+'</b> · '+esc(o.created_at)+'</div>').join(''):'Операций пока нет'}catch(e){summary.textContent=e.message}}
async function topupWallet(){const amount=Number(document.getElementById('walletAmount').value);if(!Number.isInteger(amount)||amount<3000||amount>75000){alert('Сумма пополнения должна быть от 3 000 до 75 000 ₽');return}try{const r=await fetch('/api/wallet/topup',{method:'POST',headers:telegramHeaders(),body:JSON.stringify({amount})}),d=await r.json();if(!r.ok)throw Error(d.detail||'Не удалось создать платёж');if(d.payment_url){if(tg&&tg.openLink)tg.openLink(d.payment_url);else window.open(d.payment_url,'_blank');}}catch(e){alert(e.message)}}
async function payOrderFromWallet(orderId){try{const r=await fetch('/api/wallet/pay-order',{method:'POST',headers:telegramHeaders(),body:JSON.stringify({order_id:orderId})}),d=await r.json();if(!r.ok)throw Error(d.detail||'Не удалось оплатить с баланса');alert('Заказ оплачен с баланса. Остаток: '+rub(d.balance));await loadAccount();await loadCatalog()}catch(e){alert(e.message)}}
async function makeOrder(pid){let p=catalog.products.find(x=>x.id===pid),selected=document.querySelector('input[name="variant'+pid+'"]:checked'),v=selected?Number(selected.value):null;if(!p||!v){alert('Выберите один вариант фасовки');return}try{let r=await fetch('/api/orders',{method:'POST',headers:telegramHeaders(),body:JSON.stringify({city_id:cityId,product_id:pid,variant_id:v,quantity:1})});let d=await r.json();let el=document.getElementById('orderResult');el.classList.remove('hide');if(!r.ok){el.innerHTML='Ошибка: '+esc(d.detail||'Не удалось оформить заказ')}else{el.innerHTML='<b>Заказ: '+esc(d.order_id)+'</b><br>Сумма: '+rub(d.total)+'<br><button class="btn" style="width:auto;margin:14px 8px 8px 0" onclick="payDirect(\''+esc(d.order_id)+'\')">Оплатить через B PAY</button><button class="btn secondary" style="width:auto;margin:14px 0 8px" onclick="payOrderFromWallet(\''+esc(d.order_id)+'\')">Оплатить с баланса</button><br><small>Заказ будет обработан после подтверждения оплаты.</small>'}el.scrollIntoView({behavior:'smooth',block:'center'});await loadAccount()}catch(e){alert('Не удалось связаться с сервером')}}
async function payDirect(orderId){const el=document.getElementById('orderResult');try{el.insertAdjacentHTML('beforeend','<div class="small">Создаём платёжную ссылку…</div>');const r=await fetch('/api/orders/'+encodeURIComponent(orderId)+'/payment',{method:'POST'}),d=await r.json();if(!r.ok)throw Error(d.detail||'Не удалось создать платёж');if(tg&&tg.openLink)tg.openLink(d.payment_url);else window.open(d.payment_url,'_blank')}catch(e){alert(e.message)}}
function showAdmin(){document.getElementById('admin').classList.toggle('hide');document.getElementById('admin').scrollIntoView({behavior:'smooth'})}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
async function apiAdmin(path,body){let r=await fetch(path,{method:body?'POST':'GET',cache:'no-store',headers:{'Content-Type':'application/json','X-Admin-Password':adminPass},body:body?JSON.stringify(body):undefined});let d=await r.json();if(!r.ok){let msg=d.detail;if(Array.isArray(msg))msg=msg.map(x=>x.msg||JSON.stringify(x)).join('; ');else if(msg&&typeof msg==='object')msg=msg.msg||JSON.stringify(msg);throw Error(typeof msg==='string'?msg:'Ошибка запроса ('+r.status+')')}return d}
async function adminLogin(){adminPass=document.getElementById('adminPassword').value;await loadAdmin()}
async function loadAdmin(){let el=document.getElementById('adminContent');try{let d=await apiAdmin('/api/admin/data');let cityOpts=d.cities.map(c=>'<option value="'+c.id+'">'+esc(c.name)+'</option>').join('');let productOpts=d.products.map(p=>'<option value="'+p.id+'" data-city="'+p.city_id+'">'+esc(p.name)+' · '+esc((d.cities.find(c=>c.id===p.city_id)||{}).name||'')+'</option>').join('');let variantOpts=d.variants.map(v=>{let p=d.products.find(p=>p.id===v.product_id);return '<option value="'+v.id+'" data-product="'+v.product_id+'" data-grams="'+v.grams+'" data-city="'+(p?p.city_id:'')+'">'+esc(p?p.name:'Товар')+' · '+v.grams+' г · '+rub(v.price)+'</option>'}).join('');el.innerHTML='<div class="notice">Выберите город и фасовку, вставьте ссылку на фото и нажмите «Готово». Каждое добавление создаёт отдельную позицию на складе.</div><h3>Добавить на склад</h3><label>Город<select id="invCity" onchange="filterInventoryOptions()">'+cityOpts+'</select></label><label>Позиция<select id="invProduct" onchange="filterInventoryOptions()">'+productOpts+'</select></label><label>Фасовка<select id="invVariant">'+variantOpts+'</select></label><input id="invPhoto" type="url" placeholder="Ссылка на фото (https://...)"><button class="btn" onclick="addInventory()">Готово</button><h3>Позиции склада</h3>'+(d.inventory.map(i=>'<div class="order"><b>'+esc(i.city_name)+' · '+esc(i.product_name)+' · '+i.grams+' г</b><br><a href="'+esc(i.photo_url)+'" target="_blank" rel="noopener">Открыть фото</a><br>Статус: <b>'+esc(i.status)+'</b>'+(i.order_id?'<br>Заказ: '+esc(i.order_id):'')+(i.status==='available'?'<br><button class="btn secondary" onclick="deleteInventory('+i.id+')">Удалить позицию</button>':'<br><span class="small">Удаление недоступно для занятой позиции</span>')+'</div>').join('')||'<p class="small">Склад пока пуст</p>')+'<h3>Добавить город</h3><input id="newCity" placeholder="Название города"><button class="btn" onclick="addCity()">Добавить город</button><h4>Удалить город</h4>'+(d.cities.map(c=>'<div class="order">'+esc(c.name)+'<br><button class="btn secondary" onclick="deleteAdminItem(\'/api/admin/cities/'+c.id+'/delete\',\'Удалить город '+esc(c.name)+'?\')">Удалить город</button></div>').join('')||'<p class="small">Городов нет</p>')+'<h3>Добавить товар</h3><select id="newProductCity">'+cityOpts+'</select><input id="newProductName" placeholder="Название товара"><textarea id="newProductDesc" placeholder="Описание"></textarea><button class="btn" onclick="addProduct()">Добавить товар</button><h4>Удалить товар</h4>'+(d.products.map(p=>'<div class="order">'+esc(p.name)+' · '+esc((d.cities.find(c=>c.id===p.city_id)||{}).name||'')+'<br><button class="btn secondary" onclick="deleteAdminItem(\'/api/admin/products/'+p.id+'/delete\',\'Удалить товар '+esc(p.name)+'?\')">Удалить товар</button></div>').join('')||'<p class="small">Товаров нет</p>')+'<h3>Установить цену</h3><select id="variantId">'+variantOpts+'</select><input id="newPrice" type="number" min="0" placeholder="Цена в рублях"><button class="btn" onclick="savePrice()">Сохранить цену</button><h4>Удалить фасовку</h4>'+(d.variants.map(v=>{let p=d.products.find(p=>p.id===v.product_id);return '<div class="order">'+esc(p?p.name:'Товар')+' · '+v.grams+' г · '+rub(v.price)+'<br><button class="btn secondary" onclick="deleteAdminItem(\'/api/admin/variants/'+v.id+'/delete\',\'Удалить фасовку '+v.grams+' г?\')">Удалить фасовку</button></div>'}).join('')||'<p class="small">Фасовок нет</p>')+'<h3>Рассылка клиентам</h3><div class="notice">Сообщение будет отправлено всем пользователям, которые запускали бота. Перед отправкой проверьте текст — отменить рассылку нельзя.</div><textarea id="broadcastMessage" placeholder="Текст сообщения для клиентов" rows="5" maxlength="3500"></textarea><button class="btn" onclick="sendBroadcast()">Отправить рассылку</button><div id="broadcastResult" class="small"></div><h3>Последние заказы</h3>'+(d.orders.map(o=>'<div class="order"><b>'+esc(o.id)+'</b> · '+rub(o.total)+'<br>'+esc(o.product_name||'Товар')+' · статус: '+esc(o.status)+' · '+esc(o.created_at)+(o.customer_id?'<br>Telegram ID: '+esc(o.customer_id):'<br>Нет Telegram ID')+(o.photo_sent?'<br>Фото отправлено':(o.status!=='paid'?'<br><button class="btn" onclick="markPaid(\''+esc(o.id)+'\')">Подтвердить оплату и отправить фото</button>':''))+'</div>').join('')||'<p class="small">Заказов пока нет</p>');filterInventoryOptions()}catch(e){el.innerHTML='<div class="notice">'+esc(e.message)+'. Проверьте пароль и переменные Render.</div>'}}
async function sendBroadcast(){const message=document.getElementById('broadcastMessage').value.trim();if(!message){alert('Введите текст рассылки');return}if(!confirm('Отправить сообщение всем пользователям, которые запускали PESOK-бота?'))return;const out=document.getElementById('broadcastResult');out.textContent='Выполняется рассылка…';try{const d=await apiAdmin('/api/admin/broadcast',{message});out.textContent='Доставлено: '+d.sent+' из '+d.total+'. Ошибок: '+d.failed+'. Недоступных чатов: '+d.blocked+'.';alert(out.textContent)}catch(e){out.textContent='Ошибка: '+e.message;alert(e.message)}}
async function saveStock(id){const stock=Number(document.getElementById('stock'+id).value);if(!Number.isInteger(stock)||stock<0){alert('Укажи целое неотрицательное количество');return}try{await apiAdmin('/api/admin/variants/stock',{variant_id:id,stock});await loadCatalog();await loadAdmin();alert('Остаток сохранён')}catch(e){alert(e.message)}}
async function adminAction(path,body){try{await apiAdmin(path,body);await loadCatalog();await loadAdmin();alert('Сохранено')}catch(e){alert(e.message)}}
function filterInventoryOptions(){const city=String(document.getElementById('invCity').value),prod=document.getElementById('invProduct'),variant=document.getElementById('invVariant');Array.from(prod.options).forEach(o=>o.hidden=o.dataset.city!==city);if(prod.selectedOptions.length&&prod.selectedOptions[0].hidden){const next=Array.from(prod.options).find(o=>!o.hidden);if(next)prod.value=next.value;}Array.from(variant.options).forEach(o=>{const p=prod.selectedOptions[0];o.hidden=!p||o.dataset.product!==p.value||o.dataset.city!==city});if(variant.selectedOptions.length&&variant.selectedOptions[0].hidden){const next=Array.from(variant.options).find(o=>!o.hidden);if(next)variant.value=next.value;}}
async function addInventory(){const photo=document.getElementById('invPhoto').value.trim();if(!photo){alert('Вставьте ссылку на фото');return}let parsed;try{parsed=new URL(photo)}catch(e){alert('Введите полную ссылку на изображение, начинающуюся с https://');return}if(parsed.protocol!=='https:'||/\/images\/touch\/search|\/images\/search|\/search\?/i.test(parsed.pathname+parsed.search)){alert('Это ссылка на страницу поиска, а не на фотографию. Нужна прямая HTTPS-ссылка на само изображение.');return}const product=document.getElementById('invProduct').selectedOptions[0];if(!product){alert('Сначала добавьте товар для выбранного города');return}const city=Number(document.getElementById('invCity').value);const productId=Number(product.value);const variantId=Number(document.getElementById('invVariant').value);try{await apiAdmin('/api/admin/inventory',{city_id:city,product_id:productId,variant_id:variantId,address:'Адрес указан на фото',photo_url:photo});await loadCatalog();await loadAdmin();alert('Позиция добавлена на склад')}catch(e){alert(e.message||'Не удалось добавить позицию')}}
async function deleteInventory(id){if(!confirm('Удалить свободную позицию #'+id+' со склада? Действие необратимо.'))return;try{await apiAdmin('/api/admin/inventory/'+id+'/delete',{});await loadCatalog();await loadAdmin();alert('Позиция удалена со склада')}catch(e){alert(e.message||'Не удалось удалить позицию')}}
async function deleteAdminItem(path,message){if(!confirm(message+' Это действие необратимо.'))return;try{await apiAdmin(path,{});await loadCatalog();await loadAdmin();alert('Удалено')}catch(e){alert(e.message||'Не удалось удалить. Возможно, объект связан со складом или заказами.')}}
function addCity(){adminAction('/api/admin/cities',{name:document.getElementById('newCity').value})}
function addProduct(){adminAction('/api/admin/products',{city_id:Number(document.getElementById('newProductCity').value),name:document.getElementById('newProductName').value,description:document.getElementById('newProductDesc').value})}
function savePrice(){let s=document.getElementById('variantId').selectedOptions[0];const raw=document.getElementById('newPrice').value.trim();const price=Number(raw);if(!s){alert('Выберите фасовку');return}if(raw===''||!Number.isInteger(price)||price<0){alert('Введите целую неотрицательную цену в рублях');return}adminAction('/api/admin/variants',{product_id:Number(s.dataset.product),grams:Number(s.dataset.grams),price:price})}
async function markPaid(id){if(!confirm("Вы проверили поступление денег по заказу "+id+"? После подтверждения клиенту будет отправлено фото товара."))return;try{await apiAdmin("/api/admin/orders/"+encodeURIComponent(id)+"/mark-paid",{});await loadAdmin();alert("Оплата отмечена, фото отправлено покупателю")}catch(e){alert(e.message)}}
function addQuarry(){adminAction('/api/admin/quarries',{city_id:Number(document.getElementById('quarryCity').value),name:document.getElementById('quarryName').value,address:document.getElementById('quarryAddress').value,coordinates:document.getElementById('quarryCoords').value,photo_url:document.getElementById('quarryPhoto').value,instructions:document.getElementById('quarryInstructions').value})}
async function revealAdminButton(){try{if(!tg||!tg.initData)return;const r=await fetch("/api/is-admin",{headers:telegramHeaders(),cache:"no-store"});if(!r.ok)return;const d=await r.json();if(d.is_admin)document.getElementById("adminPanelButton").classList.remove("hide")}catch(e){}}
loadCatalog();loadAccount();revealAdminButton();
</script></body></html>"""
