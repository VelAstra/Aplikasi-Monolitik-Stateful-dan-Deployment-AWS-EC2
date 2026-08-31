-- Data awal (opsional) untuk Aplikasi Monolitik Stateful
-- Catatan: backend membuat schema secara otomatis saat pertama kali berjalan.
-- Skema jauh lebih disarankan dibuat otomatis dari src/app.py (fungsi init_db)
-- daripada dijalankan manual, agar sesuai dengan struktur single-file backend.

-- Contoh seed user (password di-hash; jangan jalankan manual tanpa hash)
-- INSERT INTO users (username, password, nama, no_id) VALUES
--   ('rayhan', '<hash_password>', 'Rayhan Haldi Hermawan', '24/545406/PA/23176');
