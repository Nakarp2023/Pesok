import os
import sqlite3
import secrets
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

DB_PATH = os.getenv("PESOK_DB_PATH", "pesok.db")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
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
            city = c.execute("INSERT INTO cities(name) VALUES(?)", ("Невьянск",)).lastrowid
            for name, desc in [("ОЛЬГА", "Песок. Уточните характеристики перед заказом."), ("МИША", "Песок. Уточните характеристики перед заказом.")]:
                pid = c.execute("INSERT INTO products(city_id,name,description) VALUES(?,?,?)", (city,name,desc)).lastrowid
                for grams in (0.5, 1, 2, 3):
                    c.execute("INSERT INTO variants(product_id,grams,price) VALUES(?,?,?)", (pid,grams,0))
            c.execute("INSERT INTO quarries(city_id,name,address,instructions) VALUES(?,?,?,?)", (city,"Точка выдачи — настроить","Добавьте адрес в админ-панели","Точка пока не настроена."))
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
:root{color-scheme:dark;--bg:#111512;--panel:#1b211c;--line:#303a31;--muted:#aab5aa;--lime:#c5f36b;--white:#f4f7f1}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--white);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}header{padding:24px 18px 20px;background:linear-gradient(135deg,#202b21,#111512 70%);border-bottom:1px solid var(--line)}.top{display:flex;justify-content:space-between;align-items:center}.logo{font-weight:900;letter-spacing:2px;font-size:27px}.logo span{color:var(--lime)}.tag{color:var(--muted);font-size:12px;margin-top:7px}.pill{border:1px solid #56644f;border-radius:99px;padding:8px 11px;color:var(--lime);font-size:12px}main{max-width:760px;margin:auto;padding:18px}.hero{padding:20px 0 16px}.eyebrow{font-size:11px;letter-spacing:2px;color:var(--lime);text-transform:uppercase}.hero h1{font-size:32px;line-height:1.05;margin:9px 0}.hero p{color:var(--muted);font-size:14px;line-height:1.5}.label{font-size:12px;color:var(--muted);margin:20px 0 10px}.cities{display:flex;gap:8px;flex-wrap:wrap}.city{border:1px solid var(--line);background:var(--panel);color:var(--white);padding:10px 14px;border-radius:12px}.city.active{border-color:var(--lime);color:var(--lime)}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.product{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:15px;min-width:0}.product-art{height:105px;border-radius:13px;background:radial-gradient(ellipse at 70% 20%,#87916b,#3e4936 40%,#252d24 75%);display:flex;align-items:center;justify-content:center;font-size:35px;margin-bottom:14px}.product h3{margin:0;font-size:20px}.desc{color:var(--muted);font-size:12px;line-height:1.4;min-height:32px;margin:6px 0 12px}.product select,.adminbox input,.adminbox select,.adminbox textarea{width:100%;padding:11px;background:#101410;color:var(--white);border:1px solid var(--line);border-radius:10px;margin:5px 0 10px}.price{font-weight:800;font-size:17px;margin:10px 0 12px}.btn{background:var(--lime);border:0;color:#151a12;border-radius:12px;font-weight:800;padding:13px;width:100%;cursor:pointer}.btn.secondary{background:#293329;color:var(--white);border:1px solid var(--line)}.notice{background:#252d22;border:1px solid #44533d;padding:13px;border-radius:12px;color:#d8e6cf;font-size:13px;line-height:1.5;margin:14px 0}.tabs{display:flex;gap:8px;margin:20px 0}.tabs button{flex:1}.hide{display:none!important}.adminbox{border:1px solid var(--line);background:var(--panel);border-radius:16px;padding:16px;margin-top:14px}.foot{color:var(--muted);font-size:11px;line-height:1.5;padding:24px 0}.order{border-bottom:1px solid var(--line);padding:10px 0;font-size:13px}.small{font-size:11px;color:var(--muted)}@media(min-width:600px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}.hero h1{font-size:42px}}
</style></head><body><header><div class="top"><div><div class="logo">PE<span>S</span>OK</div><div class="tag">МАТЕРИАЛ. ТОЧНО ПО ДЕЛУ.</div></div><div class="pill">МАГАЗИН · 01</div></div></header>
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
function renderProducts(){let ps=catalog.products.filter(p=>p.city_id===cityId);document.getElementById('products').innerHTML=ps.length?ps.map(p=>'<article class="product"><div class="product-art">⛰</div><h3>'+esc(p.name)+'</h3><div class="desc">'+esc(p.description||'Песок · уточните характеристики')+'</div><select id="v'+p.id+'" onchange="priceUpdate('+p.id+')">'+p.variants.map(v=>'<option value="'+v.id+'" data-price="'+v.price+'">'+v.grams.toLocaleString('ru-RU')+' г</option>').join('')+'</select><div class="price" id="price'+p.id+'">'+(p.variants.length?rub(p.variants[0].price):'Цена уточняется')+'</div><button class="btn" onclick="makeOrder('+p.id+')">Оформить заказ</button></article>').join():'<div class="notice">В этом городе пока нет товаров.</div>'}
function priceUpdate(pid){let s=document.getElementById('v'+pid),v=s.options[s.selectedIndex];document.getElementById('price'+pid).textContent=rub(Number(v.dataset.price))}
async function makeOrder(pid){let p=catalog.products.find(x=>x.id===pid),v=Number(document.getElementById('v'+pid).value);if(!p)return;try{let r=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({city_id:cityId,product_id:pid,variant_id:v,quantity:1,customer_id:tg&&tg.initDataUnsafe&&tg.initDataUnsafe.user?String(tg.initDataUnsafe.user.id):''})});let d=await r.json();let el=document.getElementById('orderResult');el.classList.remove('hide');el.innerHTML=r.ok?'<b>Заказ создан: '+esc(d.order_id)+'</b><br>Сумма: '+rub(d.total)+'<br>'+esc(d.message):'Ошибка: '+esc(d.detail||'Не удалось оформить заказ');el.scrollIntoView({behavior:'smooth',block:'center'})}catch(e){alert('Не удалось связаться с сервером')}}
function showAdmin(){document.getElementById('admin').classList.toggle('hide');document.getElementById('admin').scrollIntoView({behavior:'smooth'})}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
async function apiAdmin(path,body){let r=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json','X-Admin-Password':adminPass},body:body?JSON.stringify(body):undefined});let d=await r.json();if(!r.ok)throw Error(d.detail||'Ошибка');return d}
async function adminLogin(){adminPass=document.getElementById('adminPassword').value;await loadAdmin()}
async function loadAdmin(){let el=document.getElementById('adminContent');try{let d=await apiAdmin('/api/admin/data');let cityOpts=d.cities.map(c=>'<option value="'+c.id+'">'+esc(c.name)+'</option>').join('');let variantOpts=d.variants.map(v=>{let p=d.products.find(p=>p.id===v.product_id);return '<option value="'+v.product_id+'" data-grams="'+v.grams+'">'+esc(p?p.name:'Товар')+' · '+v.grams+' г · '+rub(v.price)+'</option>'}).join('');el.innerHTML='<div class="notice">Админ-панель подключена.</div><h3>Добавить город</h3><input id="newCity" placeholder="Название города"><button class="btn" onclick="addCity()">Добавить город</button><h3>Добавить товар</h3><select id="newProductCity">'+cityOpts+'</select><input id="newProductName" placeholder="Название товара"><textarea id="newProductDesc" placeholder="Описание"></textarea><button class="btn" onclick="addProduct()">Добавить товар</button><h3>Установить цену</h3><select id="variantId">'+variantOpts+'</select><input id="newPrice" type="number" min="0" placeholder="Цена в рублях"><button class="btn" onclick="savePrice()">Сохранить цену</button><h3>Добавить карьер / точку выдачи</h3><select id="quarryCity">'+cityOpts+'</select><input id="quarryName" placeholder="Название точки"><input id="quarryAddress" placeholder="Адрес"><input id="quarryCoords" placeholder="Координаты или ссылка на карту"><input id="quarryPhoto" placeholder="Ссылка на фото"><textarea id="quarryInstructions" placeholder="Инструкции по получению"></textarea><button class="btn" onclick="addQuarry()">Добавить точку</button><h3>Последние заказы</h3>'+(d.orders.map(o=>'<div class="order"><b>'+esc(o.id)+'</b> · '+rub(o.total)+'<br>Статус: '+esc(o.status)+' · '+esc(o.created_at)+'</div>').join('')||'<p class="small">Заказов пока нет</p>')}catch(e){el.innerHTML='<div class="notice">'+esc(e.message)+'. Проверьте пароль и переменные Render.</div>'}}
async function adminAction(path,body){try{await apiAdmin(path,body);await loadCatalog();await loadAdmin();alert('Сохранено')}catch(e){alert(e.message)}}
function addCity(){adminAction('/api/admin/cities',{name:document.getElementById('newCity').value})}
function addProduct(){adminAction('/api/admin/products',{city_id:Number(document.getElementById('newProductCity').value),name:document.getElementById('newProductName').value,description:document.getElementById('newProductDesc').value})}
function savePrice(){let s=document.getElementById('variantId').selectedOptions[0];adminAction('/api/admin/variants',{product_id:Number(s.value),grams:Number(s.dataset.grams),price:Number(document.getElementById('newPrice').value)})}
function addQuarry(){adminAction('/api/admin/quarries',{city_id:Number(document.getElementById('quarryCity').value),name:document.getElementById('quarryName').value,address:document.getElementById('quarryAddress').value,coordinates:document.getElementById('quarryCoords').value,photo_url:document.getElementById('quarryPhoto').value,instructions:document.getElementById('quarryInstructions').value})}
loadCatalog();
</script></body></html>"""
