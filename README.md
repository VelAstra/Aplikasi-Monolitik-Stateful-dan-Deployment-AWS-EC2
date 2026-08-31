# Aplikasi Monolitik Stateful dan Deployment pada AWS EC2

**Mata Kuliah**: Pengembangan Perangkat Lunak Scalable (PACS262521)

**Nama**: Rayhan Haldi Hermawan
**NIM**: 24/545406/PA/23176

---

## Deskripsi

Penugasan terstruktur ini membangun aplikasi **monolitik stateful** sebagai
*ground truth* / baseline untuk memahami manajemen **server-side session** dan
ketergantungan sesi pada satu mesin, sebelum melangkah ke arsitektur stateless
dan horizontal scaling.

Aplikasi dibuat dengan **bahasa murni (Python)** TANPA framework besar,
menggunakan pola **Single-Path Routing**: semua permintaan masuk melalui satu
URL Path yaitu `/app.py?action=<aksi>`. Manajemen sesi diwajibkan secara
**server-side lokal** (file sesi pada mesin yang sama) — bukan JWT/token
stateless.

---

## Arsitektur

- **Backend**: Python murni (pustaka standar `http.server`, `sqlite3`).
  Windows/Unix alike, tidak butuh install dependency.
- **Database**: RDBMS lokal **SQLite** pada instance yang sama, lengkap dengan
  **Foreign Key** antara tabel `users` dan `puisi`.
- **Session**: Server-side, disimpan sebagai file di folder `src/sessions/`
  pada mesin yang sama → **stateful**, hanya valid di satu instance.
- **Frontend**: HTML + CSS + JavaScript vanilla (tanpa Bootstrap/Tailwind/React).

### Single-Path Routing

```
http://host/app.py?action=register
http://host/app.py?action=login
http://host/app.py?action=logout
http://host/app.py?action=submit_puisi
http://host/app.py?action=daftar_puisi
http://host/app.py?action=status
```

---

## Aksi Endpoint (Wajib)

| Aksi | Metode | Protesi | Input | Output |
|------|--------|---------|-------|--------|
| `register` | POST | - | username, nama, password, no_id | Pesan sukses/gagal |
| `login` | POST | - | username, password | Set-Cookie sesi + pesan |
| `submit_puisi` | POST | ✅ session | judul, isi, tgl_submit, kategori, keyword | Pesan sukses/gagal |
| `daftar_puisi` | GET | ✅ session | - | tgl_submit, judul, kategori |

`submit_puisi` dan `daftar_puisi` **terproteksi session**. Browser mengelola
cookie `puisi_session` (hasil header `Set-Cookie`) secara otomatis sehingga
permintaan berikutnya tetap membawa konteks sesi yang valid.

---

## Struktur Database

### Tabel `users`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | INTEGER (PK) | Primary key |
| username | TEXT UNIQUE | Username login |
| password | TEXT | Hash PBKDF2 |
| nama | TEXT | Nama lengkap |
| no_id | TEXT | No. identitas (NIM) |

### Tabel `puisi`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | INTEGER (PK) | Primary key |
| user_id | INTEGER (FK) → users.id | Foreign key, ON DELETE CASCADE |
| judul | TEXT | Judul puisi |
| tgl_submit | TEXT | Tanggal submit |
| isi | TEXT | Isi puisi |
| kategori | TEXT | Kategori puisi |
| keyword | TEXT | Keyword puisi |

---

## Instalasi & Menjalankan

### Prasyarat

- Python 3.8+ (tidak perlu pustaka eksternal)

### Jalankan Lokal

```bash
cd src
python app.py
```

Aplikasi berjalan di `http://localhost:8000`.

> Database `puisi.db` dan folder sesi dibuat otomatis saat pertama kali
> server dijalankan.

---

## Frontend

Frontend satu halaman (`src/templates/index.html`) menyediakan:

- Form **Register** dan **Login** (tab).
- Form **Submit Puisi** dengan input judul, tanggal, kategori, keyword, isi.
- **Daftar Puisi** milik user yang sedang login.
- Komunikasi memakai **Fetch API** ke endpoint `?action=...`.
- **Observasi state**: buka tab *Network* browser saat login untuk melihat
  header `Set-Cookie`, dan pastikan cookie `puisi_session` terkirim saat
  `submit_puisi` / `daftar_puisi`.

---

## Struktur Proyek

```
.
├── src/
│   ├── app.py                # Backend murni Python (single-file, single-path)
│   ├── requirements.txt      # Kosong (tanpa dependency eksternal)
│   ├── templates/
│   │   └── index.html        # Frontend vanilla HTML
│   └── static/
│       ├── css/style.css     # Styling vanilla
│       └── js/script.js      # Fetch API vanilla JS
├── database/
│   └── schema.sql            # Skema SQLite (users + puisi, FK)
└── deployment/
    ├── deploy.sh             # Skrip setup AWS EC2
    ├── nginx.conf            # Konfigurasi reverse proxy
    ├── security_group.sh     # Aturan security group AWS
    └── systemd/app.service   # Unit service systemd
```

---

## Deployment AWS EC2

1. Launch instance Ubuntu 22.04 LTS.
2. Atur security group (SSH 22, HTTP 80, HTTPS 443) — lihat `security_group.sh`.
3. SSH ke instance lalu clone & deploy:

```bash
git clone https://github.com/VelAstra/Aplikasi-Monolitik-Stateful-dan-Deployment-AWS-EC2.git
cd Aplikasi-Monolitik-Stateful-dan-Deployment-AWS-EC2
chmod +x deployment/deploy.sh
sudo ./deployment/deploy.sh
```

4. Akses aplikasi di `http://YOUR_EC2_PUBLIC_IP`.

> Karena **stateful** (server-side session), aplikasi ini hanya berjalan baik
> pada satu instance. Untuk skala, nantinya perlu arsitektur stateless dan
> shared session — itulah esensi yang dibuktikan penugasan ini.

---

## Kontak

**Nama**: Rayhan Haldi Hermawan
**NIM**: 24/545406/PA/23176
**Mata Kuliah**: Pengembangan Perangkat Lunak Scalable (PACS262521)
