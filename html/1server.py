from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from pathlib import Path

BASE_DIR = Path(_file_).resolve().parent


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        requested_path = self.path.split("?")[0].lstrip("/")

        if requested_path == "favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        if not requested_path:
            requested_path = "index.html"

        path = (BASE_DIR / requested_path).resolve()

        if not path.is_relative_to(BASE_DIR):
            self.send_error(403, "Доступ запрещён")
            return

        if not path.is_file():
            self.send_error(404, "Файл не найден")
            return

        page = path.read_bytes()

        if path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        else:
            content_type = "text/html; charset=utf-8"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self):
        if self.path != "/register":
            self.send_error(404, "Неизвестный адрес")
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        data = parse_qs(body)

        username = data.get("username", [""])[0]
        email = data.get("email", [""])[0]
        password = data.get("key", [""])[0]
        password_confirm = data.get("key-confirm", [""])[0]

        print("Получена регистрация")
        print("Логин:", username)
        print("Email:", email)

        if not username or not email or not password:
            message = "Заполни все обязательные поля"
            status = 400
        elif password != password_confirm:
            message = "Пароли не совпадают"
            status = 400
        else:
            message = "Данные получены сервером"
            status = 200

        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))


server = HTTPServer(("0.0.0.0", 8000), Handler)

print("Сервер запущен на порту 8000")
server.serve_forever()