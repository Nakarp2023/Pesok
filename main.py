import os
import sqlite3
import secrets
import base64
import json
import urllib.parse
import urllib.request
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

DB_PATH = os.getenv("PESOK_DB_PATH", "pesok.db")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://pesok-store.onrender.com").rstrip("/")
PHOTO_OLGA_B64 = "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"
PHOTO_MISHA_B64 = "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"
app = FastAPI(title="PESOK Store", version="0.1.0")

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
        # Keep the agreed price list in sync for existing databases too.
        for product in c.execute("SELECT id, name FROM products WHERE name IN ('Песок Ольга', 'Песок Миша')").fetchall():
            prices = (2500, 5000, 7000, 10000) if product["name"] == "Песок Ольга" else (2000, 4000, 8000, 11000)
            for grams, price in zip((0.5, 1, 2, 3), prices):
                c.execute("UPDATE variants SET price=? WHERE product_id=? AND grams=?", (price, product["id"], grams))
init_db()

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

@app.post("/api/orders")
def create_order(order: OrderIn):
    with db() as c:
        v = c.execute("""SELECT v.*, p.city_id FROM variants v JOIN products p ON p.id=v.product_id
          WHERE v.id=? AND p.id=? AND p.city_id=? AND v.active=1 AND p.active=1""",
          (order.variant_id, order.product_id, order.city_id)).fetchone()
        if not v:
            raise HTTPException(400, "Выбранный вариант больше недоступен")
        total = int(v["price"]) * order.quantity
        oid = secrets.token_urlsafe(9)
        c.execute("INSERT INTO orders(id,city_id,product_id,variant_id,quantity,total,customer_id,status) VALUES(?,?,?,?,?,?,?,?)",
          (oid, order.city_id, order.product_id, order.variant_id, order.quantity, total, order.customer_id[:100], "demo_pending"))
        return {"order_id": oid, "total": total, "status": "demo_pending",
                "message": "Тестовый заказ сохранён. Оплата не подключена; деньги не списываются."}

@app.get("/api/admin/data")
def admin_data(x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    with db() as c:
        return {
          "cities":[dict(r) for r in c.execute("SELECT * FROM cities ORDER BY name")],
          "products":[dict(r) for r in c.execute("SELECT * FROM products ORDER BY id DESC")],
          "variants":[dict(r) for r in c.execute("SELECT * FROM variants ORDER BY product_id,grams")],
          "quarries":[dict(r) for r in c.execute("SELECT * FROM quarries ORDER BY id DESC")],
          "orders":[dict(r) for r in c.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 100")]
        }


@app.post("/api/admin/orders/{order_id}/mark-paid")
def mark_order_paid(order_id: str, x_admin_password: Optional[str] = Header(default=None)):
    admin_guard(x_admin_password)
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(503, "Не задан TELEGRAM_BOT_TOKEN в Render → Environment")
    with db() as conn:
        order = conn.execute("SELECT o.*, p.name AS product_name FROM orders o JOIN products p ON p.id=o.product_id WHERE o.id=?", (order_id,)).fetchone()
        if not order:
            raise HTTPException(404, "Заказ не найден")
        if not str(order["customer_id"]).isdigit():
            raise HTTPException(400, "Нет Telegram ID покупателя. Покупатель должен открыть бота и нажать /start до заказа.")
        if order["photo_sent"]:
            return {"ok": True, "message": "Фото уже отправлено"}
        photo_path = "olga.jpg" if "Ольга" in order["product_name"] else "misha.jpg"
        photo_url = PUBLIC_BASE_URL + "/media/" + photo_path
        caption = "Оплата подтверждена! Заказ " + order_id + ". " + order["product_name"] + " — " + str(order["total"]) + " ₽."
        payload = urllib.parse.urlencode({"chat_id": order["customer_id"], "photo": photo_url, "caption": caption}).encode()
        request = urllib.request.Request("https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendPhoto", data=payload, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
            if not result.get("ok"):
                raise HTTPException(502, "Telegram не принял фото. Проверьте, что покупатель запустил бота командой /start.")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(502, "Не удалось отправить фото. Проверьте токен бота и доступность Telegram.")
        conn.execute("UPDATE orders SET status='paid', photo_sent=1 WHERE id=?", (order_id,))
        return {"ok": True, "message": "Оплата отмечена, фото отправлено"}

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
        for grams in (0.5, 1, 2, 3):
            c.execute("INSERT INTO variants(product_id,grams,price) VALUES(?,?,0)", (pid,grams))
        return {"id": pid}

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
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--white);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}header{padding:15px 18px;background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:3}.top{display:flex;justify-content:space-between;align-items:center}.logo{font-weight:850;letter-spacing:.5px;font-size:20px}.logo span{color:var(--blue)}.tag{color:var(--muted);font-size:10px;margin-top:3px}.pill{display:none}main{width:100%;max-width:760px;margin:0 auto;padding:16px}.hero{padding:22px 18px 20px;border-radius:20px;background:linear-gradient(135deg,#dcecff,#fff 75%);margin-bottom:20px}.eyebrow{font-size:11px;letter-spacing:1.5px;color:var(--blue);text-transform:uppercase}.hero h1{font-size:32px;line-height:1.05;margin:9px 0}.hero p{color:var(--muted);font-size:14px;line-height:1.5}.label{font-size:12px;color:var(--muted);margin:20px 0 10px;font-weight:700}.cities{display:flex;gap:8px;flex-wrap:wrap}.city{border:1px solid var(--line);background:#fff;color:var(--white);padding:10px 13px;border-radius:12px}.city.active{background:var(--blue);border-color:var(--blue);color:#fff}.grid{display:flex!important;flex-flow:row wrap!important;align-items:stretch;justify-content:flex-start;gap:10px;width:100%}.product{display:block;flex:0 0 calc(50% - 5px)!important;width:calc(50% - 5px)!important;max-width:calc(50% - 5px)!important;background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:12px;min-width:0;box-shadow:0 3px 12px #152c4510}.product-art{height:94px;border-radius:13px;background:linear-gradient(145deg,#d8c3a0,#a98c65 45%,#ead7b8);display:flex;align-items:center;justify-content:center;font-size:35px;margin-bottom:12px}.product h3{margin:0;font-size:16px;line-height:1.2}.desc{color:var(--muted);font-size:11px;line-height:1.35;min-height:44px;margin:6px 0 10px}.variants{display:grid;gap:6px;margin:8px 0 12px}.variant{display:flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:10px;padding:8px 7px;font-size:11px;line-height:1.2;cursor:pointer;min-width:0}.variant:has(input:checked){border-color:var(--blue);background:#edf6ff}.variant input{accent-color:var(--blue);margin:0;flex:0 0 auto}.variant .grams{font-weight:700;white-space:nowrap}.variant .variant-price{font-weight:800;margin-left:auto;white-space:nowrap}.product .btn{font-size:12px;padding:12px 5px}.product .variants{width:100%}.variant{min-width:0}.variant .grams{font-size:11px}.variant .variant-price{font-size:11px}@media(max-width:360px){.grid{gap:6px}.product{flex-basis:calc(50% - 3px);width:calc(50% - 3px);max-width:calc(50% - 3px);padding:8px}.product-art{height:76px}.product h3{font-size:14px}.variant{padding:7px 4px;gap:4px}.variant input{width:13px;height:13px}.variant .grams,.variant .variant-price{font-size:10px}}.product select,.adminbox input,.adminbox select,.adminbox textarea{width:100%;padding:11px;background:#fff;color:var(--white);border:1px solid var(--line);border-radius:10px;margin:5px 0 10px}.price{font-weight:800;font-size:17px;margin:10px 0 12px}.btn{background:var(--blue);border:0;color:#fff;border-radius:12px;font-weight:750;padding:13px;width:100%;cursor:pointer}.btn.secondary{background:#fff;color:var(--blue);border:1px solid var(--line)}.notice{background:#eef6ff;border:1px solid #d1e7ff;padding:13px;border-radius:12px;color:#284b70;font-size:13px;line-height:1.5;margin:14px 0}.tabs{display:flex;gap:8px;margin:20px 0}.tabs button{flex:1}.hide{display:none!important}.adminbox{border:1px solid var(--line);background:var(--panel);border-radius:16px;padding:16px;margin-top:14px}.foot{color:var(--muted);font-size:11px;line-height:1.5;padding:24px 0}.order{border-bottom:1px solid var(--line);padding:10px 0;font-size:13px}.small{font-size:11px;color:var(--muted)}@media(min-width:600px){.hero h1{font-size:42px}}
</style></head><body><header><div class="top"><div><div class="logo">PE<span>S</span>OK</div><div class="tag">МАТЕРИАЛ. ТОЧНО ПО ДЕЛУ.</div></div><div aria-hidden="true"></div></div></header>
<main><section class="hero"><div class="eyebrow">Песок рядом</div><h1>Выбирай.<br>Заказывай.</h1><p>Каталог по городам и точкам выдачи. Выбери позицию и фасовку, чтобы оформить заказ.</p></section>
<div class="label">ВАШ ГОРОД</div><div class="cities" id="cities"></div><div class="label">КАТАЛОГ</div><section class="grid" id="products"><div class="notice">Загружаем каталог…</div></section>
<div class="notice">🧪 Демоверсия: платежи пока не подключены. Заказ можно создать для проверки, списания денег нет.</div><section id="orderResult" class="notice hide"></section>
<div class="tabs"><button class="btn secondary" onclick="showAdmin()">Админ-панель</button><button class="btn secondary" onclick="loadCatalog()">Обновить каталог</button></div>
<section id="admin" class="hide"><div class="adminbox"><h3>Вход администратора</h3><input id="adminPassword" type="password" placeholder="Пароль из ADMIN_PASSWORD"><button class="btn" onclick="adminLogin()">Войти</button><div id="adminContent"></div></div></section>
<div class="foot">PESOK · версия 0.1 · Тестовое оформление заказа. Уточняйте характеристики, наличие и условия выдачи у администратора.</div></main>
<script>
const tg=window.Telegram&&window.Telegram.WebApp;if(tg){tg.ready();tg.expand();}
let catalog={cities:[],products:[],quarries:[]},cityId=null,adminPass="";
const rub=n=>new Intl.NumberFormat('ru-RU').format(n)+' ₽';
async function loadCatalog(){try{let r=await fetch('/api/catalog');catalog=await r.json();if(!cityId&&catalog.cities.length)cityId=catalog.cities[0].id;renderCities();renderProducts()}catch(e){document.getElementById('products').innerHTML='<div class="notice">Не удалось загрузить каталог. Обновите страницу.</div>'}}
function renderCities(){document.getElementById('cities').innerHTML=catalog.cities.map(c=>'<button class="city '+(c.id===cityId?'active':'')+'" onclick="cityId='+c.id+';renderCities();renderProducts()">'+esc(c.name)+'</button>').join('')}
function renderProducts(){
  const ps=catalog.products.filter(p=>p.city_id===cityId);
  const imageOlga='data:image/jpeg;base64,'+"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";
  const imageMisha='data:image/jpeg;base64,'+"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";
  document.getElementById('products').innerHTML=ps.length?ps.map(p=>{
    const photo=p.name==='Песок Ольга'?imageOlga:(p.name==='Песок Миша'?imageMisha:'');
    const art=photo?'<img alt="'+esc(p.name)+'" src="'+photo+'" style="display:block;width:100%;height:100%;object-fit:cover;border-radius:13px">':'⛰';
    return '<article class="product"><div class="product-art">'+art+'</div><h3>'+esc(p.name)+'</h3><div class="desc">'+esc(p.description||'Песок · уточните характеристики')+'</div><div class="variants" role="radiogroup" aria-label="Выберите фасовку">'+p.variants.map((v,i)=>'<label class="variant"><input type="radio" name="variant'+p.id+'" value="'+v.id+'" data-price="'+v.price+'" '+(i===0?'checked':'')+' onchange="priceUpdate('+p.id+')"><span class="grams">'+v.grams.toLocaleString('ru-RU')+' г</span><span class="variant-price">'+rub(v.price)+'</span></label>').join('')+'</div><button class="btn" onclick="makeOrder('+p.id+')">Выбрать и заказать</button></article>';
  }).join(''):'<div class="notice">В этом городе пока нет товаров.</div>';
}
function priceUpdate(pid){let s=document.querySelector('input[name="variant'+pid+'"]:checked');if(s){let p=catalog.products.find(x=>x.id===pid);let b=document.querySelector('#products .product');}}
async function makeOrder(pid){let p=catalog.products.find(x=>x.id===pid),selected=document.querySelector('input[name="variant'+pid+'"]:checked'),v=selected?Number(selected.value):null;if(!p||!v){alert('Выберите один вариант фасовки');return;}try{let r=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({city_id:cityId,product_id:pid,variant_id:v,quantity:1,customer_id:tg&&tg.initDataUnsafe&&tg.initDataUnsafe.user?String(tg.initDataUnsafe.user.id):''})});let d=await r.json();let el=document.getElementById('orderResult');el.classList.remove('hide');el.innerHTML=r.ok?'<b>Заказ создан: '+esc(d.order_id)+'</b><br>Сумма: '+rub(d.total)+'<br>'+esc(d.message):'Ошибка: '+esc(d.detail||'Не удалось оформить заказ');el.scrollIntoView({behavior:'smooth',block:'center'})}catch(e){alert('Не удалось связаться с сервером')}}
function showAdmin(){document.getElementById('admin').classList.toggle('hide');document.getElementById('admin').scrollIntoView({behavior:'smooth'})}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
async function apiAdmin(path,body){let r=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json','X-Admin-Password':adminPass},body:body?JSON.stringify(body):undefined});let d=await r.json();if(!r.ok)throw Error(d.detail||'Ошибка');return d}
async function adminLogin(){adminPass=document.getElementById('adminPassword').value;await loadAdmin()}
async function loadAdmin(){let el=document.getElementById('adminContent');try{let d=await apiAdmin('/api/admin/data');let cityOpts=d.cities.map(c=>'<option value="'+c.id+'">'+esc(c.name)+'</option>').join('');let variantOpts=d.variants.map(v=>{let p=d.products.find(p=>p.id===v.product_id);return '<option value="'+v.product_id+'" data-grams="'+v.grams+'">'+esc(p?p.name:'Товар')+' · '+v.grams+' г · '+rub(v.price)+'</option>'}).join('');el.innerHTML='<div class="notice">Админ-панель подключена.</div><h3>Добавить город</h3><input id="newCity" placeholder="Название города"><button class="btn" onclick="addCity()">Добавить город</button><h3>Добавить товар</h3><select id="newProductCity">'+cityOpts+'</select><input id="newProductName" placeholder="Название товара"><textarea id="newProductDesc" placeholder="Описание"></textarea><button class="btn" onclick="addProduct()">Добавить товар</button><h3>Установить цену</h3><select id="variantId">'+variantOpts+'</select><input id="newPrice" type="number" min="0" placeholder="Цена в рублях"><button class="btn" onclick="savePrice()">Сохранить цену</button><h3>Добавить карьер / точку выдачи</h3><select id="quarryCity">'+cityOpts+'</select><input id="quarryName" placeholder="Название точки"><input id="quarryAddress" placeholder="Адрес"><input id="quarryCoords" placeholder="Координаты или ссылка на карту"><input id="quarryPhoto" placeholder="Ссылка на фото"><textarea id="quarryInstructions" placeholder="Инструкции по получению"></textarea><button class="btn" onclick="addQuarry()">Добавить точку</button><h3>Последние заказы</h3>'+(d.orders.map(o=>'<div class="order"><b>'+esc(o.id)+'</b> · '+rub(o.total)+'<br>'+esc(o.product_name||'Товар')+' · статус: '+esc(o.status)+' · '+esc(o.created_at)+(o.customer_id?'<br>Telegram ID: '+esc(o.customer_id):'<br>Нет Telegram ID')+(o.photo_sent?'<br>Фото отправлено':(o.status!=='paid'?'<br><button class="btn" onclick="markPaid(\''+esc(o.id)+'\')">Подтвердить оплату и отправить фото</button>':''))+'</div>').join('')||'<p class="small">Заказов пока нет</p>')}catch(e){el.innerHTML='<div class="notice">'+esc(e.message)+'. Проверьте пароль и переменные Render.</div>'}}
async function adminAction(path,body){try{await apiAdmin(path,body);await loadCatalog();await loadAdmin();alert('Сохранено')}catch(e){alert(e.message)}}
function addCity(){adminAction('/api/admin/cities',{name:document.getElementById('newCity').value})}
function addProduct(){adminAction('/api/admin/products',{city_id:Number(document.getElementById('newProductCity').value),name:document.getElementById('newProductName').value,description:document.getElementById('newProductDesc').value})}
function savePrice(){let s=document.getElementById('variantId').selectedOptions[0];adminAction('/api/admin/variants',{product_id:Number(s.value),grams:Number(s.dataset.grams),price:Number(document.getElementById('newPrice').value)})}
async function markPaid(id){if(!confirm("Вы проверили поступление денег по заказу "+id+"? После подтверждения клиенту будет отправлено фото товара."))return;try{await apiAdmin("/api/admin/orders/"+encodeURIComponent(id)+"/mark-paid",{});await loadAdmin();alert("Оплата отмечена, фото отправлено покупателю")}catch(e){alert(e.message)}}
function addQuarry(){adminAction('/api/admin/quarries',{city_id:Number(document.getElementById('quarryCity').value),name:document.getElementById('quarryName').value,address:document.getElementById('quarryAddress').value,coordinates:document.getElementById('quarryCoords').value,photo_url:document.getElementById('quarryPhoto').value,instructions:document.getElementById('quarryInstructions').value})}
loadCatalog();
</script></body></html>"""
