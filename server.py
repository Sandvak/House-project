"""Локальный сервер Mega House. Запуск: python server.py (Python 3.10+)."""
from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import io
import json
import math
import mimetypes
import os
from pathlib import Path
import re
import secrets
import smtplib
import sqlite3
import ssl
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, unquote, urlparse
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent
DATA = Path(os.getenv("MH_DATA_DIR", str(Path.home() / ".mega-house-demo"))).resolve()
PORT = int(os.getenv("MH_PORT", "8000"))
PG = os.getenv("MH_DATABASE_URL")
ROLES = ("Администратор", "Менеджер", "Контент-менеджер")
ADMIN, MANAGER, EDITOR = ROLES
STATUSES = ("Новая", "В работе", "Назначена встреча", "Закрыта", "Отказ")
CONTENT = ("home", "about", "contacts")
LOCK = threading.Lock()
attempts = {}
sessions = {}
challenges = {}


class Problem(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message


def require(condition, message, status=400):
    if not condition:
        raise Problem(status, message)


def clean(data, key, limit=250):
    value = data.get(key, "")
    require(isinstance(value, str) and len(value) <= limit, "Проверьте поле «" + key + "».")
    return value.strip()


def encode_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 260000)
    return salt + ":" + digest.hex()


def password_matches(password, stored):
    return hmac.compare_digest(encode_password(password, stored.split(":")[0]), stored)


def new_id():
    return uuid.uuid4().hex


def now():
    return datetime.now().isoformat(timespec="seconds")


def dump(value):
    return json.dumps(value, ensure_ascii=False)


@contextmanager
def database():
    if PG:
        import psycopg
        from psycopg.rows import dict_row
        conn = psycopg.connect(PG, row_factory=dict_row)
    else:
        conn = sqlite3.connect(DATA / "mega-house.sqlite", timeout=10)
        conn.row_factory = sqlite3.Row
    try:
        yield lambda sql, args=(): conn.execute(sql.replace("?", "%s") if PG else sql, args)
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def init():
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "media").mkdir(exist_ok=True)
    with database() as q:
        for definition in (
            "users (id TEXT PRIMARY KEY, login TEXT UNIQUE NOT NULL, password TEXT, email TEXT, phone TEXT, role TEXT, created TEXT)",
            "houses (id TEXT PRIMARY KEY, payload TEXT NOT NULL)",
            "leads (id TEXT PRIMARY KEY, payload TEXT NOT NULL, status TEXT, owner TEXT, created TEXT, meeting TEXT)",
            "content (id TEXT PRIMARY KEY, body TEXT)",
            "visits (day TEXT PRIMARY KEY, total INTEGER NOT NULL)",
            "settings (id TEXT PRIMARY KEY, value TEXT)",
        ):
            q("CREATE TABLE IF NOT EXISTS " + definition)
        if not q("SELECT id FROM settings WHERE id='seeded'").fetchone():
            houses = json.loads((ROOT / "data/houses.json").read_text("utf-8"))
            for house in houses:
                q("INSERT INTO houses VALUES (?,?)", (house["id"], dump(house)))
            q("INSERT INTO settings VALUES ('seeded','1')")
        if not q("SELECT id FROM users").fetchone():
            password = secrets.token_urlsafe(10) + "A7"
            q("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
              (new_id(), "megaadmin", encode_password(password), os.getenv("MH_ADMIN_EMAIL", "admin@example.com"), "", ADMIN, now()))
            print("Первый вход — логин: megaadmin   пароль:", password, flush=True)


def mail(recipient, subject, body):
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = os.environ["MH_SMTP_USER"]
    message["To"] = recipient
    message.set_content(body)
    with smtplib.SMTP_SSL(os.environ["MH_SMTP_HOST"], int(os.getenv("MH_SMTP_PORT", "465")), timeout=8, context=ssl.create_default_context()) as smtp:
        smtp.login(os.environ["MH_SMTP_USER"], os.environ["MH_SMTP_PASSWORD"])
        smtp.send_message(message)


def rate(key, limit, window):
    current = time.time()
    with LOCK:
        entries = [ts for ts in attempts.get(key, []) if current - ts < window]
        require(len(entries) < limit, "Слишком много попыток. Попробуйте позже.", 429)
        attempts[key] = entries + [current]


def safe_image(value):
    return isinstance(value, str) and bool(re.fullmatch(r"(?:/?images/[\w.-]+|/media/[0-9a-f]{32})\.(?:webp|png|jpg|jpeg)", value, re.I))


def validate_house(body, house_id):
    house = {"id": house_id}
    for key in ("title", "district", "material", "status", "utilities", "description", "address", "manager"):
        house[key] = clean(body, key, 6000 if key == "description" else 300)
    require(house["title"], "Укажите название дома.")
    for key in ("price", "area", "plot", "floors", "rooms", "popularity"):
        try:
            number = float(body.get(key) or 0)
        except (TypeError, ValueError):
            raise Problem(400, "Проверьте числовые характеристики дома.")
        require(math.isfinite(number) and 0 <= number <= 10**12, "Проверьте числовые характеристики дома.")
        if key in ("floors", "rooms", "price"):
            require(number.is_integer(), "Цена, этажность и число комнат должны быть целыми.")
        house[key] = int(number) if number.is_integer() else number
    require(all(house[k] > 0 for k in ("price", "area", "floors", "rooms")), "Укажите цену, площадь, этажность и число комнат.")
    gallery = body.get("gallery", [])
    require(isinstance(gallery, list) and 5 <= len(gallery) <= 30 and all(safe_image(p) for p in gallery), "Проверьте фотографии.")
    image = clean(body, "image")
    require(safe_image(image), "Выберите обложку дома.")
    house["image"] = image
    house["gallery"] = gallery or [image]
    plan = clean(body, "plan")
    require(not plan or safe_image(plan), "Проверьте файл планировки.")
    house["plan"] = plan
    return house


def safe_csv(value):
    string = str(value or "")
    return "'" + string if string.lstrip().startswith(("=", "+", "-", "@")) else string


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(self.command, urlparse(self.path).path, args[1] if len(args) > 1 else "", flush=True)

    def send(self, status, data=b"", mime="application/json; charset=utf-8", headers=None):
        if not isinstance(data, bytes):
            data = dump(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        require(self.headers.get_content_type() == "application/json", "Ожидается JSON.", 415)
        length = int(self.headers.get("Content-Length", "0"))
        maximum = 8_000_000 if self.route == "/api/media" else 90_000
        require(0 < length <= maximum, "Слишком большой или пустой запрос.", 413)
        try:
            parsed = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            raise Problem(400, "Некорректный JSON.")
        require(isinstance(parsed, dict), "Ожидается объект JSON.")
        return parsed

    def session(self, roles=None):
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        self.sid = cookie["mh_session"].value if "mh_session" in cookie else ""
        with LOCK:
            item = sessions.get(self.sid)
        require(item and item[1] > time.time(), "Войдите в админ-панель.", 401)
        with database() as q:
            user = q("SELECT id,login,email,phone,role,created FROM users WHERE id=?", (item[0],)).fetchone()
        require(user, "Сеанс завершён.", 401)
        require(not roles or user["role"] in roles, "Недостаточно прав.", 403)
        return dict(user)

    def dispatch(self):
        self.route = unquote(urlparse(self.path).path)
        self.method = self.command
        host = self.headers.get("Host", "")
        require(host.split(":")[0] in ("localhost", "127.0.0.1"), "Недопустимый адрес сервера.", 403)
        if self.method != "GET":
            origin = self.headers.get("Origin")
            require(not origin or origin == "http://" + host, "Запрос с другого сайта отклонён.", 403)
        p = self.route
        if p == "/sitemap.xml" and self.method == "GET":
            urls = ["/"] + ["/page/" + slug + ".html" for slug in
                ("catalog", "constructor", "about", "contacts", "privacy", "consent")]
            with database() as q:
                for row in q("SELECT id FROM houses ORDER BY id"):
                    slug = row["id"]
                    if slug in ("kazansky", "laishevo", "volzhsky"):
                        urls.append("/page/" + slug + ".html")
                    else:
                        urls.append("/page/house.html?id=" + quote(slug, safe=""))
            sitemap = ElementTree.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
            for route in urls:
                entry = ElementTree.SubElement(sitemap, "url")
                ElementTree.SubElement(entry, "loc").text = "http://" + host + route
            return self.send(200, ElementTree.tostring(sitemap, encoding="utf-8", xml_declaration=True),
                             "application/xml; charset=utf-8")
        if not p.startswith("/api/"):
            require(self.method == "GET", "Метод недоступен.", 405)
            if p.startswith("/media/"):
                require(safe_image(p), "Файл не найден.", 404)
                file = DATA / "media" / p.split("/")[-1]
            else:
                file = (ROOT / p.lstrip("/")).resolve()
                if file.is_dir():
                    file = file / "index.html"
                allowed = (".html", ".js", ".css", ".webp", ".jpg", ".jpeg", ".png", ".svg", ".ico", ".woff2", ".woff", ".json", ".txt", ".xml", ".webmanifest")
                require(ROOT in file.parents, "Файл не найден.", 404)
                if file.is_file():
                    require(file.suffix.lower() in allowed, "Файл не найден.", 404)
            if not file.is_file():
                if (ROOT / "404.html").is_file():
                    html = (ROOT / "404.html").read_bytes().replace(b"<head>", b'<head><base href="/">', 1)
                    return self.send(404, html, "text/html; charset=utf-8")
                raise Problem(404, "Файл не найден.")
            mime = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
            return self.send(200, file.read_bytes(), mime)
        if p.startswith("/api/auth/"):
            return self.auth()
        if self.method == "GET" and p == "/api/houses":
            with database() as q:
                return self.send(200, [json.loads(r["payload"]) for r in q("SELECT payload FROM houses ORDER BY id")])
        if self.method == "GET" and p == "/api/content":
            with database() as q:
                return self.send(200, {r["id"]: r["body"] for r in q("SELECT * FROM content")})
        if self.method == "POST" and p == "/api/leads":
            return self.intake()
        if self.method == "POST" and p == "/api/visit":
            self.body()
            rate(("visit", self.client_address[0]), 120, 60)
            with database() as q:
                q("INSERT INTO visits VALUES (?,1) ON CONFLICT(day) DO UPDATE SET total=visits.total+1", (date.today().isoformat(),))
            return self.send(200, {"ok": True})
        return self.admin()

    def auth(self):
        action = self.route.split("/")[-1]
        if action == "me" and self.method == "GET":
            return self.send(200, self.session())
        require(self.method == "POST", "Метод недоступен.", 405)
        data = self.body()
        if action == "logout":
            self.session()
            with LOCK:
                sessions.pop(self.sid, None)
            return self.send(200, {"ok": True}, headers={"Set-Cookie": "mh_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"})
        if action == "start":
            rate(("login", self.client_address[0]), 12, 300)
            with database() as q:
                user = q("SELECT * FROM users WHERE login=?", (clean(data, "login"),)).fetchone()
            require(user and password_matches(clean(data, "password"), user["password"]), "Проверьте логин и пароль.", 401)
            code = str(secrets.randbelow(1000000)).zfill(6)
            challenge = secrets.token_urlsafe(32)
            if os.getenv("MH_SMTP_HOST"):
                try:
                    mail(user["email"], "Код для Mega House", "Ваш код для входа: " + code)
                except (OSError, KeyError, smtplib.SMTPException):
                    raise Problem(503, "Не удалось доставить код. Проверьте параметры SMTP.")
                delivery = "Код отправлен на почту."
            else:
                print(f"Код для {user['login']}: {code}", flush=True)
                delivery = "Код показан в окне запущенного локального сервера."
            with LOCK:
                for key in list(challenges):
                    if challenges[key][0] == user["id"] or challenges[key][2] <= time.time():
                        challenges.pop(key, None)
                challenges[challenge] = [user["id"], code, time.time() + 300, 5]
            return self.send(200, {"challenge": challenge, "message": delivery})
        require(action == "confirm", "Маршрут не найден.", 404)
        challenge = clean(data, "challenge")
        code = clean(data, "code")
        with LOCK:
            item = challenges.get(challenge)
            require(item and item[2] > time.time() and item[3] > 0, "Запросите новый код.", 401)
            item[3] -= 1
            require(hmac.compare_digest(code.encode(), item[1].encode()), "Неверный код.", 401)
            del challenges[challenge]
            sid = secrets.token_urlsafe(36)
            sessions[sid] = (item[0], time.time() + 3600 * 8)
        return self.send(200, {"ok": True}, headers={"Set-Cookie": "mh_session=" + sid + "; HttpOnly; Path=/; SameSite=Strict; Max-Age=28800"})

    def intake(self):
        data = self.body()
        rate(("lead", self.client_address[0]), 20, 600)
        require(not data.get("website"), "Не удалось сохранить заявку.")
        fields = {k: clean(data, k, 4000 if k == "comment" else 200) for k in ("name", "phone", "email", "comment", "house", "request_type")}
        require(fields["name"] and re.fullmatch(r"\+?[0-9]{7,15}", re.sub(r"[\s()\-]", "", fields["phone"])), "Проверьте имя и телефон.")
        require(not fields["email"] or re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", fields["email"]), "Проверьте адрес электронной почты.")
        require(data.get("agree") in (True, "true", "on"), "Необходимо согласие на обработку данных.")
        fields["agree"] = True
        with database() as q:
            q("INSERT INTO leads VALUES (?,?,?,?,?,?)", (new_id(), dump(fields), STATUSES[0], "", now(), ""))
        if os.getenv("MH_NOTIFY_EMAIL") and os.getenv("MH_SMTP_HOST"):
            try:
                mail(os.environ["MH_NOTIFY_EMAIL"], "Новая заявка Mega House", "В админ-панели появилась новая заявка.")
            except (OSError, KeyError, smtplib.SMTPException):
                print("Заявка сохранена. Не удалось отправить уведомление менеджеру.", flush=True)
        self.send(201, {"ok": True})

    def admin(self):
        path = self.route.strip("/").split("/")
        require(2 <= len(path) <= 3, "Страница не найдена.", 404)
        group, item = path[1], path[2] if len(path) == 3 else None
        roles = {"houses": (ADMIN, EDITOR), "media": (ADMIN, EDITOR), "leads": (ADMIN, MANAGER),
                 "users": (ADMIN,), "stats": ROLES, "content": (ADMIN, EDITOR)}
        require(group in roles, "Маршрут не найден.", 404)
        user = self.session(roles[group])
        method = self.method
        data = self.body() if method in ("POST", "PUT") else {}
        result = {"ok": True}
        with database() as q:
            if group == "stats" and method == "GET":
                result = {"houses": q("SELECT COUNT(*) AS n FROM houses").fetchone()["n"]}
                if user["role"] in (MANAGER, ADMIN):
                    result["leads"] = q("SELECT COUNT(*) AS n FROM leads").fetchone()["n"]
                for key, days in (("day", 1), ("week", 7), ("month", 30)):
                    start = date.today() - timedelta(days=days-1)
                    result[key] = q("SELECT COALESCE(SUM(total),0) AS n FROM visits WHERE day>=?", (start.isoformat(),)).fetchone()["n"]
            elif group == "houses" and method in ("POST", "PUT", "DELETE"):
                if method == "POST":
                    require(not item, "Некорректный адрес.")
                    item = new_id()
                    house = validate_house(data, item)
                    q("INSERT INTO houses VALUES (?,?)", (item, dump(house)))
                    result["id"] = item
                else:
                    require(q("SELECT id FROM houses WHERE id=?", (item,)).fetchone(), "Дом не найден.", 404)
                    if method == "DELETE":
                        q("DELETE FROM houses WHERE id=?", (item,))
                    else:
                        q("UPDATE houses SET payload=? WHERE id=?", (dump(validate_house(data, item)), item))
            elif group == "media" and method == "POST":
                try:
                    content = base64.b64decode(data.get("bytes", ""), validate=True)
                except (ValueError, TypeError):
                    raise Problem(400, "Не удалось прочитать файл.")
                require(0 < len(content) <= 5 * 1024 * 1024, "Максимальный размер изображения — 5 МБ.")
                if content.startswith(b"\xff\xd8\xff"):
                    ext = ".jpg"
                elif content.startswith(b"\x89PNG\r\n\x1a\n"):
                    ext = ".png"
                elif content[:4] == b"RIFF" and content[8:12] == b"WEBP":
                    ext = ".webp"
                else:
                    raise Problem(400, "Поддерживаются файлы JPEG, PNG и WebP.")
                name = new_id() + ext
                (DATA / "media" / name).write_bytes(content)
                result["path"] = "/media/" + name
            elif group == "leads" and method == "GET":
                rows = []
                for row in q("SELECT * FROM leads ORDER BY created DESC"):
                    entry = dict(row)
                    entry.update(json.loads(entry.pop("payload")))
                    rows.append(entry)
                if item == "export":
                    out = io.StringIO()
                    writer = csv.writer(out, delimiter=";")
                    writer.writerow(("Имя","Телефон","Email","Тип","Дом","Комментарий","Статус","Встреча","Получена"))
                    for row in rows:
                        writer.writerow(safe_csv(row.get(k)) for k in ("name","phone","email","request_type","house","comment","status","meeting","created"))
                    return self.send(200, out.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8", {"Content-Disposition": 'attachment; filename="mega-house-leads.csv"'})
                result = rows
            elif group == "leads" and item and method == "PUT":
                status = clean(data, "status")
                meeting = clean(data, "meeting") if status == "Назначена встреча" else ""
                require(status in STATUSES, "Выберите статус.")
                if meeting:
                    try:
                        datetime.fromisoformat(meeting)
                    except ValueError:
                        raise Problem(400, "Проверьте дату встречи.")
                require(status != "Назначена встреча" or meeting, "Выберите время встречи.")
                row = q("SELECT owner FROM leads WHERE id=?", (item,)).fetchone()
                require(row, "Заявка не найдена.", 404)
                owner = row["owner"] or user["id"]
                if user["role"] == ADMIN:
                    q("UPDATE leads SET status=?,meeting=?,owner=? WHERE id=?", (status, meeting, owner, item))
                else:
                    changed = q("UPDATE leads SET status=?,meeting=?,owner=? WHERE id=? AND (owner='' OR owner=?)",
                                (status, meeting, user["id"], item, user["id"]))
                    require(changed.rowcount == 1, "Заявка закреплена за другим сотрудником.", 403)
            elif group == "content" and item in CONTENT and method == "PUT":
                body = clean(data, "body", 6000)
                q("INSERT INTO content VALUES (?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body", (item, body))
            elif group == "users":
                result = self.users(q, user, method, item, data)
            else:
                raise Problem(405, "Метод недоступен.")
        self.send(200, result)

    def users(self, q, current, method, item, data):
        if method == "GET":
            return [dict(r) for r in q("SELECT id,login,email,phone,role,created FROM users ORDER BY created")]
        require(method in ("POST", "PUT", "DELETE"), "Метод недоступен.", 405)
        existing = q("SELECT * FROM users WHERE id=?", (item,)).fetchone() if item else None
        require(method == "POST" or existing, "Пользователь не найден.", 404)
        if method == "DELETE":
            require(item != current["id"], "Нельзя удалить текущий профиль.")
            q("UPDATE leads SET owner='' WHERE owner=?", (item,))
            q("DELETE FROM users WHERE id=?", (item,))
        else:
            login, password, email, phone, role = (clean(data, k) for k in ("login","password","email","phone","role"))
            require(re.fullmatch("[a-z]{6,}", login), "Логин — от 6 строчных латинских букв.")
            require(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email), "Проверьте почту.")
            require(role in ROLES and (item != current["id"] or role == ADMIN), "Проверьте роль.")
            other = q("SELECT id FROM users WHERE login=?", (login,)).fetchone()
            require(not other or other["id"] == item, "Логин уже занят.")
            if password or method == "POST":
                require(len(password) >= 6 and re.search("[A-Z]", password) and re.search("[0-9]", password), "Пароль — от 6 символов, заглавная латинская буква и цифра.")
                hashed = encode_password(password)
            else:
                hashed = existing["password"]
            if method == "POST":
                q("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (new_id(),login,hashed,email,phone,role,now()))
            else:
                q("UPDATE users SET login=?,password=?,email=?,phone=?,role=? WHERE id=?", (login,hashed,email,phone,role,item))
        if item and item != current["id"]:
            with LOCK:
                for key in list(sessions):
                    if sessions[key][0] == item:
                        del sessions[key]
        return {"ok": True}

    def run(self):
        try:
            self.dispatch()
        except Problem as error:
            self.send(error.status, {"error":error.message})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as error:
            print("Ошибка запроса:", type(error).__name__, file=sys.stderr)
            self.send(500, {"error":"Операция не выполнена. Повторите попытку."})

    do_GET = do_POST = do_PUT = do_DELETE = run


if __name__ == "__main__":
    init()
    print(f"Сайт: http://127.0.0.1:{PORT}/   Админка: http://127.0.0.1:{PORT}/admin/login.html", flush=True)
    try:
        ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        pass
