#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Aplikasi Monolitik Stateful - Penugasan PACS262521
# Backend murni Python tanpa framework, single path app.py?action=...
# Sesi disimpan di sisi server (file) => stateful, bukan JWT/stateless.
# Rayhan Haldi Hermawan - 24/545406/PA/23176

import json
import os
import sqlite3
import sys
import hashlib
import secrets
import re
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'puisi.db')
SESSION_DIR = os.path.join(BASE_DIR, 'sessions')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', '8000'))

PATH_APP = '/app.py'
PATH_INDEX = '/'
STATIC_PREFIX = '/static/'


def init_db():
    # bikin folder sesi sekalian
    os.makedirs(SESSION_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nama     TEXT NOT NULL,
            no_id    TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS puisi (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            judul      TEXT NOT NULL,
            tgl_submit TEXT NOT NULL,
            isi        TEXT NOT NULL,
            kategori   TEXT NOT NULL,
            keyword    TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_puisi_user ON puisi(user_id);
    """)
    conn.commit()
    conn.close()


def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------- session (disimpan jadi file biar stateful) ----------

def baca_sesi(sid):
    if not sid:
        return None
    path = os.path.join(SESSION_DIR, sid + '.json')
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def simpan_sesi(sid, data):
    path = os.path.join(SESSION_DIR, sid + '.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def hapus_sesi(sid):
    if not sid:
        return
    path = os.path.join(SESSION_DIR, sid + '.json')
    if os.path.exists(path):
        os.remove(path)


def get_session(handler):
    # ambil cookie puisi_session dari header
    cookies = handler.headers.get('Cookie', '')
    for part in cookies.split(';'):
        part = part.strip()
        if part.startswith('puisi_session='):
            return baca_sesi(part.split('=', 1)[1])
    return None


# ---------- helper kecil ----------

def hash_password(pw):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', pw.encode(), bytes.fromhex(salt), 100000)
    return salt + ':' + digest.hex()


def verify_password(pw, stored):
    try:
        salt, digest = stored.split(':', 1)
        check = hashlib.pbkdf2_hmac('sha256', pw.encode(), bytes.fromhex(salt), 100000)
        return check.hex() == digest
    except Exception:
        return False


def ok_username(u):
    return bool(re.match(r'^[A-Za-z0-9_.]{3,30}$', u or ''))


def cookie_header(sid, expires=''):
    if expires:
        return f'puisi_session={sid}; Path=/; HttpOnly; Expires={expires}; SameSite=Lax'
    return f'puisi_session={sid}; Path=/; HttpOnly; SameSite=Lax'


def date_cookie(days):
    dt = datetime.now(timezone.utc) + timedelta(days=days)
    return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')


def date_now():
    return datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')


def send_json(h, status, obj, extra=None):
    body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
    h.send_response(status)
    h.send_header('Content-Type', 'application/json; charset=utf-8')
    h.send_header('Content-Length', str(len(body)))
    if extra:
        for k, v in extra.items():
            h.send_header(k, v)
    h.end_headers()
    h.wfile.write(body)


def send_page(h, content, ct='text/html; charset=utf-8'):
    body = content.encode('utf-8')
    h.send_response(200)
    h.send_header('Content-Type', ct)
    h.send_header('Content-Length', str(len(body)))
    h.end_headers()
    h.wfile.write(body)


# ---------- aksi ----------

def aksi_register(h, params, body):
    username = (body.get('username') or '').strip()
    nama = (body.get('nama') or '').strip()
    password = body.get('password') or ''
    no_id = (body.get('no_id') or '').strip()

    if not (username and nama and password and no_id):
        return send_json(h, 400, {'sukses': False, 'pesan': 'Semua field wajib diisi.'})
    if not ok_username(username):
        return send_json(h, 400, {'sukses': False, 'pesan': 'Username 3-30 karakter (huruf, angka, titik, underscore).'})
    if len(password) < 6:
        return send_json(h, 400, {'sukses': False, 'pesan': 'Password minimal 6 karakter.'})

    conn = db_connect()
    try:
        ada = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if ada:
            return send_json(h, 409, {'sukses': False, 'pesan': 'Username sudah terdaftar.'})
        conn.execute(
            'INSERT INTO users (username, password, nama, no_id) VALUES (?,?,?,?)',
            (username, hash_password(password), nama, no_id)
        )
        conn.commit()
        return send_json(h, 201, {'sukses': True, 'pesan': 'Registrasi berhasil. Silakan login.'})
    except sqlite3.Error:
        return send_json(h, 500, {'sukses': False, 'pesan': 'Terjadi kesalahan server.'})
    finally:
        conn.close()


def aksi_login(h, params, body):
    username = (body.get('username') or '').strip()
    password = body.get('password') or ''
    if not (username and password):
        return send_json(h, 400, {'sukses': False, 'pesan': 'Username dan password wajib diisi.'})

    conn = db_connect()
    try:
        row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if not row or not verify_password(password, row['password']):
            return send_json(h, 401, {'sukses': False, 'pesan': 'Username atau password salah.'})

        sid = secrets.token_hex(32)
        simpan_sesi(sid, {
            'user_id': row['id'],
            'username': row['username'],
            'nama': row['nama'],
            'login_at': datetime.now().isoformat()
        })
        return send_json(h, 200, {'sukses': True, 'pesan': 'Login berhasil.'},
                         extra={'Set-Cookie': cookie_header(sid, date_cookie(7))})
    finally:
        conn.close()


def aksi_logout(h, params, body):
    sid = None
    for part in (h.headers.get('Cookie', '') or '').split(';'):
        part = part.strip()
        if part.startswith('puisi_session='):
            sid = part.split('=', 1)[1]
    if sid:
        hapus_sesi(sid)
    return send_json(h, 200, {'sukses': True, 'pesan': 'Logout berhasil.'},
                     extra={'Set-Cookie': f'puisi_session=; Path=/; HttpOnly; Expires={date_now()}; Max-Age=0; SameSite=Lax'})


def aksi_submit_puisi(h, params, body):
    sesi = get_session(h)
    if not sesi:
        return send_json(h, 401, {'sukses': False, 'pesan': 'Anda harus login terlebih dahulu.'})

    judul = (body.get('judul') or '').strip()
    isi = (body.get('isi') or '').strip()
    tgl = (body.get('tgl_submit') or '').strip()
    kategori = (body.get('kategori') or '').strip()
    keyword = (body.get('keyword') or '').strip()

    if not (judul and isi and tgl and kategori and keyword):
        return send_json(h, 400, {'sukses': False, 'pesan': 'Semua field puisi wajib diisi.'})

    conn = db_connect()
    try:
        conn.execute(
            'INSERT INTO puisi (user_id, judul, tgl_submit, isi, kategori, keyword) VALUES (?,?,?,?,?,?)',
            (sesi['user_id'], judul, tgl, isi, kategori, keyword)
        )
        conn.commit()
        return send_json(h, 201, {'sukses': True, 'pesan': 'Puisi berhasil disubmit.'})
    except sqlite3.Error:
        return send_json(h, 500, {'sukses': False, 'pesan': 'Gagal menyimpan puisi.'})
    finally:
        conn.close()


def aksi_daftar_puisi(h, params):
    sesi = get_session(h)
    if not sesi:
        return send_json(h, 401, {'sukses': False, 'pesan': 'Anda harus login terlebih dahulu.'})

    conn = db_connect()
    try:
        rows = conn.execute(
            'SELECT id, judul, tgl_submit, kategori FROM puisi WHERE user_id = ? ORDER BY tgl_submit DESC, id DESC',
            (sesi['user_id'],)
        ).fetchall()
        daftar = [{'id': r['id'], 'judul': r['judul'], 'tgl_submit': r['tgl_submit'], 'kategori': r['kategori']}
                  for r in rows]
        return send_json(h, 200, {'sukses': True, 'daftar': daftar})
    finally:
        conn.close()


def aksi_status(h, params):
    sesi = get_session(h)
    if sesi:
        return send_json(h, 200, {'sukses': True, 'login': True, 'nama': sesi['nama'],
                                  'username': sesi['username'], 'user_id': sesi['user_id']})
    return send_json(h, 200, {'sukses': True, 'login': False})


AKSI = {
    'register': aksi_register,
    'login': aksi_login,
    'logout': aksi_logout,
    'submit_puisi': aksi_submit_puisi,
    'daftar_puisi': aksi_daftar_puisi,
    'status': aksi_status,
}


class AppHandler(BaseHTTPRequestHandler):
    server_version = 'MonolitikStateful/1.0'
    protocol_version = 'HTTP/1.0'

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == PATH_INDEX:
            return send_page(self, baca_template('index.html'))

        if path == PATH_APP:
            params = parse_qs(parsed.query)
            action = (params.get('action') or [''])[0]
            if action == 'daftar_puisi':
                return aksi_daftar_puisi(self, params)
            if action == 'status':
                return aksi_status(self, params)
            return send_json(self, 400, {'sukses': False, 'pesan': 'Aksi GET tidak dikenali.'})

        if path.startswith(STATIC_PREFIX):
            return self.serve_static(path)

        return send_json(self, 404, {'sukses': False, 'pesan': 'Halaman tidak ditemukan.'})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != PATH_APP:
            return send_json(self, 404, {'sukses': False, 'pesan': 'Halaman tidak ditemukan.'})

        params = parse_qs(parsed.query)
        action = (params.get('action') or [''])[0]
        body = self.read_json_body()

        fn = AKSI.get(action)
        if fn is None:
            return send_json(self, 400, {'sukses': False, 'pesan': 'Aksi tidak dikenali.'})
        return fn(self, params, body)

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def read_json_body(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
        except (TypeError, ValueError):
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode('utf-8'))
        except Exception:
            return {}

    def serve_static(self, path):
        rel = path[len(STATIC_PREFIX):]
        safe = os.path.normpath(rel)
        if safe.startswith('..') or os.path.isabs(safe):
            return send_json(self, 403, {'sukses': False, 'pesan': 'Akses ditolak.'})

        full = os.path.join(STATIC_DIR, safe)
        if not os.path.isfile(full):
            return send_json(self, 404, {'sukses': False, 'pesan': 'File tidak ditemukan.'})

        with open(full, 'rb') as f:
            data = f.read()

        ctype = {
            '.css': 'text/css; charset=utf-8',
            '.js': 'application/javascript; charset=utf-8',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
        }.get(os.path.splitext(rel)[1].lower(), 'application/octet-stream')

        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def baca_template(name):
    with open(os.path.join(TEMPLATES_DIR, name), encoding='utf-8') as f:
        return f.read()


def main():
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print("Aplikasi jalan di http://%s:%d" % (HOST, PORT))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDimatikan.")
        server.server_close()


if __name__ == '__main__':
    main()
