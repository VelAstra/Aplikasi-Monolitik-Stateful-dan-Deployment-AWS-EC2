-- Schema database SQLite untuk Aplikasi Monolitik Stateful
-- Sumber: Penugasan Terstruktur PACS262521
-- Nama: Rayhan Haldi Hermawan | NIM: 24/545406/PA/23176

-- Tabel users
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nama     TEXT NOT NULL,
    no_id    TEXT NOT NULL
);

-- Tabel puisi (dengan Foreign Key ke users)
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
