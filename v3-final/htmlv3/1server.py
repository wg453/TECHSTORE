from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, unquote
from pathlib import Path
import sqlite3

import secrets
import hmac
import time
import hashlib
from http.cookies import SimpleCookie
import json
import re
import unicodedata

BASE_DIR = Path(__file__).resolve().parent
PRODUCTS_PATH = BASE_DIR / "products.json"
PUBLIC_DIR = BASE_DIR / "public"
DB_PATH = BASE_DIR / "users.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """)

        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(users)")
        }

        if "password_hash" not in columns:
            conn.execute("""
                ALTER TABLE users
                ADD COLUMN password_hash TEXT
            """)

        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_users_email ON users(email COLLATE NOCASE)
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price INTEGER NOT NULL CHECK(price >= 0)
            )
        """)
        products = [
            ("acer-nitro-ei491crpbmiiipx", "Acer Nitro EI491CRPbmiiipx", 649990),
            ("philips-32e1n3500", "Philips 32E1N3500", 159990),
            ("dell-p2425d", "Dell P2425D", 144990),
            ("dell-pro-32-plus-p3225de", "Dell Pro 32 Plus P3225DE", 289990),
            ("dell-pro-p-27-p2726h", "Dell Pro P 27 P2726H", 149990),
            ("google-pixel-9-pro", "Google Pixel 9 Pro", 449990),
            ("google-pixel-8-pro", "Google Pixel 8 Pro", 319990),
            ("xiaomi-poco-x7-pro", "Xiaomi Poco X7 Pro", 219990),
            ("samsung-galaxy-s25-5g", "Samsung Galaxy S25 5G", 449990),
            ("nubia-red-magic-11-pro", "Nubia Red Magic 11 Pro", 584990),
            ("msi-venturepro-17-ai", "MSI VenturePro 17 AI", 1109900),
            ("msi-modern-15-f1mg", "MSI Modern 15 F1MG", 379990),
            ("msi-cyborg-15-c2wf015xru", "MSI Cyborg 15 C2WF015XRU", 949990),
            ("lenovo-slim-5-14imh10", "Lenovo IdeaPad Slim 5 14IMH10", 449990),
            ("msi-thin-15-b2rve3450xru", "MSI Thin 15 B2RVE3450XRU", 749990)
        ]

        conn.executemany("""
            INSERT OR IGNORE INTO products (id, name, price)
            VALUES (?, ?, ?)
        """, products)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_price INTEGER NOT NULL CHECK(total_price >= 0),
                status TEXT NOT NULL DEFAULT 'new',
                created_at INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        order_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(orders)")
        }

        new_columns = {
            "customer_name": "TEXT NOT NULL DEFAULT ''",
            "phone": "TEXT NOT NULL DEFAULT ''",
            "email": "TEXT NOT NULL DEFAULT ''",
            "address": "TEXT NOT NULL DEFAULT ''"
        }

        for column, definition in new_columns.items():
            if column not in order_columns:
                conn.execute(
                    f"ALTER TABLE orders ADD COLUMN {column} {definition}"
                )

        conn.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price INTEGER NOT NULL CHECK(unit_price >= 0),
                FOREIGN KEY (order_id) REFERENCES orders(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

def hash_password(password):
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )

    return salt.hex() + ":" + password_hash.hex()

def has_forbidden_chars(value):
    return any(
        unicodedata.category(char) in ("Cc", "Cf", "Cs")
        for char in value
    )


def is_valid_email(email):
    pattern = (
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@"
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
    )

    return (
        len(email) <= 254
        and re.fullmatch(pattern, email) is not None
        and ".." not in email
    )


def verify_password(password, stored_hash):
    try:
        salt_hex, hash_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )

    return hmac.compare_digest(actual_hash, expected_hash)

init_db()

def load_product_details():
    with open(PRODUCTS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def create_error_page(status, title, message):
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{status} — TECHSTORE</title>
    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            background: linear-gradient(0deg, #21154A, #111A30, #080D1B);
            color: #F1F5FF;
            font-family: "Trebuchet MS", sans-serif;
        }}

        .error-container {{
            width: min(520px, 100%);
            padding: 40px 28px;
            text-align: center;
            background: linear-gradient(145deg, #111A30, #17152E);
            border: 1px solid #393057;
            border-radius: 16px;
        }}

        .error-code {{
            margin: 0 0 15px;
            color: #A99BFF;
            font-size: 76px;
            font-weight: bold;
        }}

        .error-title {{
            margin: 0 0 15px;
            font-size: 25px;
        }}

        .error-message {{
            margin: 0 0 28px;
            color: #B9A8FF;
            font-size: 16px;
            line-height: 1.6;
        }}

        .home-button {{
            display: inline-block;
            padding: 13px 24px;
            border-radius: 9px;
            background: #393057;
            border: 1px solid #A99BFF;
            color: #F1F5FF;
            text-decoration: none;
            transition: 0.2s;
        }}

        .home-button:hover {{
            background: #21154A;
            border-color: #00D5E8;
            color: #00D5E8;
        }}
    </style>
</head>
<body>
    <main class="error-container">
        <div class="error-code">{status}</div>
        <h1 class="error-title">{title}</h1>
        <p class="error-message">{message}</p>
        <a href="/" class="home-button">Вернуться на главную</a>
    </main>
</body>
</html>"""



class Handler(BaseHTTPRequestHandler):



    def send_custom_error(self, status, title, message):
        page = create_error_page(status, title, message)

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        self.wfile.write(page.encode("utf-8"))



    def create_session(self, user_id):
        token = secrets.token_urlsafe(32)

        token_hash = hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

        expires_at = int(time.time()) + 7 * 24 * 60 * 60

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO sessions
                    (token_hash, user_id, expires_at)
                VALUES (?, ?, ?)
            """, (token_hash, user_id, expires_at))

        cookie = (
            f"session_id={token}; "
            "HttpOnly; SameSite=Lax; Path=/; Max-Age=604800"
        )

        return cookie

    def get_current_user(self):
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))

        if "session_id" not in cookie:
            return None

        token = cookie["session_id"].value

        token_hash = hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

        with sqlite3.connect(DB_PATH) as conn:
            user = conn.execute("""
                SELECT users.id, users.username, users.email
                FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.token_hash = ?
                  AND sessions.expires_at > ?
            """, (token_hash, int(time.time()))).fetchone()

        return user

    def send_order_response(self, response, status):
        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        self.wfile.write(
            json.dumps(response).encode("utf-8")
        )


    def do_order(self):
        user = self.get_current_user()

        if user is None:
            response = {
                "success": False,
                "message": "Для оформления заказа необходимо войти в аккаунт"
            }

            return self.send_order_response(response, 401)

        length = int(self.headers.get("Content-Length", 0))

        if length <= 0 or length > 20_000:
            response = {
                "success": False,
                "message": "Некорректный размер запроса"
            }

            return self.send_order_response(response, 400)

        try:
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)

        except (UnicodeDecodeError, json.JSONDecodeError):
            response = {
                "success": False,
                "message": "Не удалось прочитать данные заказа"
            }

            return self.send_order_response(response, 400)

        if not isinstance(data, dict):
            response = {
                "success": False,
                "message": "Неверный формат данных заказа"
            }

            return self.send_order_response(response, 400)

        required_fields = ("name", "phone", "email", "address")

        if not all(
            isinstance(data.get(field), str)
            for field in required_fields
        ):
            response = {
                "success": False,
                "message": "Некорректные данные покупателя"
            }

            return self.send_order_response(response, 400)

        name = data["name"].strip()
        phone = data["phone"].strip()
        email = data["email"].strip().lower()
        address = data["address"].strip()
        cart = data.get("cart")

        if not name or not phone or not email or not address:
            response = {
                "success": False,
                "message": "Заполни все данные доставки"
            }

            return self.send_order_response(response, 400)

        if not isinstance(cart, list) or not cart:
            response = {
                "success": False,
                "message": "Корзина пуста или имеет неверный формат"
            }

            return self.send_order_response(response, 400)

        if len(cart) > 50:
            response = {
                "success": False,
                "message": "Слишком много товаров в заказе"
            }

            return self.send_order_response(response, 400)

        cart_items = []
        seen_product_ids = set()

        for item in cart:

            if not isinstance(item, dict):
                response = {
                    "success": False,
                    "message": "Некорректный товар в корзине"
                }

                return self.send_order_response(response, 400)

            product_id = item.get("id")
            quantity = item.get("quantity")

            if not isinstance(product_id, str) or not product_id.strip():
                response = {
                    "success": False,
                    "message": "Некорректный ID товара"
                }

                return self.send_order_response(response, 400)

            if type(quantity) is not int or quantity < 1 or quantity > 99:
                response = {
                    "success": False,
                    "message": "Некорректное количество товара"
                }

                return self.send_order_response(response, 400)

            product_id = product_id.strip()

            if product_id in seen_product_ids:
                response = {
                    "success": False,
                    "message": "Один товар не должен повторяться в корзине"
                }

                return self.send_order_response(response, 400)

            seen_product_ids.add(product_id)

            cart_items.append({
                "id": product_id,
                "quantity": quantity
            })

        order_items = []
        total_price = 0



        order_items = []
        total_price = 0

        try:
            with sqlite3.connect(DB_PATH) as conn:

                conn.execute("PRAGMA foreign_keys = ON")


                for item in cart_items:

                    product = conn.execute("""
                        SELECT id, name, price
                        FROM products
                        WHERE id = ?
                    """, (item["id"],)).fetchone()

                    if product is None:
                        response = {
                            "success": False,
                            "message": "Один из товаров не найден в каталоге"
                        }

                        return self.send_order_response(response, 400)

                    product_id, product_name, unit_price = product
                    quantity = item["quantity"]

                    total_price += unit_price * quantity

                    order_items.append({
                        "product_id": product_id,
                        "product_name": product_name,
                        "quantity": quantity,
                        "unit_price": unit_price
                    })

                cursor = conn.execute("""
                    INSERT INTO orders (
                        user_id,
                        total_price,
                        created_at,
                        customer_name,
                        phone,
                        email,
                        address
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user[0],
                    total_price,
                    int(time.time()),
                    name,
                    phone,
                    email,
                    address
                ))

                order_id = cursor.lastrowid

                # 3. Сохраняем товары этого заказа
                conn.executemany("""
                    INSERT INTO order_items (
                        order_id,
                        product_id,
                        product_name,
                        quantity,
                        unit_price
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, [
                    (
                        order_id,
                        item["product_id"],
                        item["product_name"],
                        item["quantity"],
                        item["unit_price"]
                    )
                    for item in order_items
                ])

        except sqlite3.Error as error:
            print("Ошибка сохранения заказа:", error)

            response = {
                "success": False,
                "message": "Не удалось сохранить заказ"
            }

            return self.send_order_response(response, 500)

        # 4. Отправляем подтверждение после сохранения
        response = {
            "success": True,
            "message": "Заказ успешно сохранён",
            "order_id": order_id,
            "total_price": total_price
        }

        return self.send_order_response(response, 200)



    def do_GET(self):
        requested_path = unquote(self.path.split("?")[0].lstrip("/"))

        if requested_path == "session":
            user = self.get_current_user()

            if user is None:
                response = {
                    "logged_in": False
                }
            else:
                response = {
                    "logged_in": True,
                    "username": user[1],
                    "email": user[2]
                }

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

            self.wfile.write(
                json.dumps(response).encode("utf-8")
            )
            return

        if requested_path.startswith("api/products/"):
            product_id = requested_path[len("api/products/"):]

            with sqlite3.connect(DB_PATH) as connection:
                cursor = connection.cursor()

                cursor.execute(
                    "SELECT id, name, price FROM products WHERE id = ?",
                    (product_id,)
                )

                product = cursor.fetchone()

            if product is None:
                self.send_error(404, "Товар не найден")
                return

            products_details = load_product_details()
            details = products_details.get(product_id)

            if details is None:
                self.send_error(404, "Подробности товара не найдены")
                return

            response = {
                "id": product[0],
                "name": product[1],
                "price": product[2],
                "image": details["image"],
                "short_description": details["short_description"],
                "full_description": details["full_description"],
                "specifications": details["specifications"],
            }

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

            self.wfile.write(
                json.dumps(response, ensure_ascii=False).encode("utf-8")
            )
            return

        if requested_path == "favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        if not requested_path:
            requested_path = "index.html"

        # ========================================
        # ДОСТУП ТОЛЬКО К ПУБЛИЧНОЙ ПАПКЕ
        # ========================================

        public_root = PUBLIC_DIR.resolve()
        path = (public_root / requested_path).resolve()

        # Запрет выход за пределы public
        if not path.is_relative_to(public_root):
            self.send_custom_error(
                403,
                "Доступ запрещён",
                "У вас нет разрешения на просмотр этой страницы."
            )
            return

        # Проверка существования файла
        if not path.is_file():
            self.send_custom_error(
                404,
                "Страница не найдена",
                "Возможно, адрес указан неверно или страница больше не существует."
            )
            return

        # Разрешённые типы публичных файлов
        allowed_extensions = {
            ".html",
            ".css",
            ".js",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".gif",
            ".svg",
            ".ico",
            ".woff",
            ".woff2",
            ".ttf",
            ".otf"
        }

        if path.suffix.lower() not in allowed_extensions:
            self.send_custom_error(
                403,
                "Доступ запрещён",
                "Запрашиваемый файл недоступен для просмотра."
            )
            return

        # Чтение публичного файла
        page = path.read_bytes()

        # Определение типа содержимого
        import mimetypes

        content_type, _ = mimetypes.guess_type(str(path))

        if content_type is None:
            content_type = "application/octet-stream"

        if content_type.startswith("text/") or content_type in (
            "application/javascript",
            "application/json"
        ):
            content_type += "; charset=utf-8"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()

        self.wfile.write(page)


    def do_POST(self):
        print("ПОЛУЧЕННЫЙ АДРЕС:", repr(self.path))

        if self.path == "/order":
            self.do_order()
            return


        if self.path == "/logout":
            self.do_logout()
            return


        if self.path not in ("/register", "/login"):
            self.send_error(404, "Неизвестный адрес")
            return

        length = int(self.headers.get("Content-Length", 0))

        if length > 10_000:
            self.send_error(413, "Слишком большой запрос")
            return

        body = self.rfile.read(length).decode("utf-8")
        data = parse_qs(body)

        email = data.get("email", [""])[0].strip().lower()
        password = data.get("key", [""])[0]
        cookie = None

        if self.path == "/register":
            username = data.get("username", [""])[0].strip()
            password_confirm = data.get("key_confirm", [""])[0]
            agreement = data.get("agreement", [""])[0]

            if not username or not email or not password:
                message = "Заполни все обязательные поля"
                status = 400

            elif len(username) > 64:
                message = "Логин слишком длинный"
                status = 400

            elif len(username) < 5:
                message = "Логин должен содержать не менее 5 символов"
                status = 400

            elif not re.fullmatch(r"[A-Za-z0-9_]+", username):
                message = (
                    "Логин содержит недопустимые символы. "
                    "Разрешены: A–Z, a–z, 0–9, _"
                )
                status = 400

            elif len(email) > 254:
                message = "Почта слишком длинная"
                status = 400

            elif not is_valid_email(email):
                message = "Некорректный адрес электронной почты"
                status = 400

            elif len(password) > 128:
                message = "Пароль слишком длинный"
                status = 400

            elif len(password) < 8:
                message = "Пароль должен содержать не менее 8 символов"
                status = 400

            elif has_forbidden_chars(username + email + password + password_confirm):
                message = "Поле содержит недопустимые символы"
                status = 400

            elif password != password_confirm:
                message = "Пароли не совпадают"
                status = 400

            elif agreement != "yes":
                message = "Необходимо согласиться с условиями"
                status = 400

            else:
                try:
                    password_hash = hash_password(password)

                    with sqlite3.connect(DB_PATH) as conn:
                        cursor = conn.execute("""
                            INSERT INTO users
                                (username, email, password_hash)
                            VALUES (?, ?, ?)
                        """, (username, email, password_hash))

                        user_id = cursor.lastrowid

                    cookie = self.create_session(user_id)

                    message = "Регистрация успешна!"
                    status = 201

                except sqlite3.IntegrityError:
                    message = "Пользователь с таким email уже существует"
                    status = 409

            print("Регистрация:", email, status)

        else:
            with sqlite3.connect(DB_PATH) as conn:
                user = conn.execute("""
                    SELECT id, username, password_hash
                    FROM users
                    WHERE email = ?
                """, (email,)).fetchone()

            if (
                user is not None
                and user[2] is not None
                and verify_password(password, user[2])
            ):
                cookie = self.create_session(user[0])
                message = "Вход успешен! Пользователь: " + user[1]
                status = 200
            else:
                message = "Неверный email или пароль"
                status = 401

            print("Попытка входа:", email, status)

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )

        if cookie:
            self.send_header("Set-Cookie", cookie)

        self.end_headers()
        self.wfile.write(message.encode("utf-8"))


    def do_logout(self):
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))

        if "session_id" in cookie:
            token = cookie["session_id"].value

            token_hash = hashlib.sha256(
                token.encode("utf-8")
            ).hexdigest()

            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("""
                    DELETE FROM sessions
                    WHERE token_hash = ?
                """, (token_hash,))

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )
        self.send_header(
            "Set-Cookie",
            "session_id=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"
        )
        self.end_headers()

        self.wfile.write("Выход выполнен".encode("utf-8"))


server = HTTPServer(("0.0.0.0", 8000), Handler)

print("Сервер запущен на порту 8000")
server.serve_forever()