# Panduan Deployment Aplikasi Monolitik Stateful pada AWS EC2

**Penulis**: Rayhan Haldi Hermawan
**NIM**: 24/545406/PA/23176
**Aplikasi**: Aplikasi Monolitik Stateful dan Deployment pada AWS EC2

---

## Daftar Isi

1. [Pengenalan](#pengenalan)
2. [Prasyarat](#prasyarat)
3. [Meluncurkan EC2 Instance](#meluncurkan-ec2-instance)
4. [Konfigurasi Security Group](#konfigurasi-security-group)
5. [Koneksi SSH](#koneksi-ssh)
6. [Menjalankan Script Deployment](#menjalankan-script-deployment)
7. [Konfigurasi Post-Deployment](#konfigurasi-post-deployment)
8. [Setup SSL/HTTPS](#setup-sslhttps)
9. [Monitoring dan Maintenance](#monitoring-dan-maintenance)
10. [Troubleshooting](#troubleshooting)

---

## Pengenalan

Panduan ini menjelaskan cara mendeploy aplikasi Monolitik Stateful ke AWS EC2.
Stack yang dipakai:

- **Compute**: AWS EC2 (t2.micro untuk free tier)
- **OS**: Ubuntu 22.04 LTS
- **Web Server**: Nginx (reverse proxy)
- **Application**: Backend Python murni (modul `http.server`) via systemd
- **Database**: SQLite lokal pada instance yang sama
- **Session**: Server-side (file sesi lokal) — bersifat stateful

Karena sesi disimpan secara lokal, aplikasi ini hanya berjalan pada **satu
instance** saja. Inilah esensi arsitektur *stateful* yang menjadi baseline
penugasan.

---

## Prasyarat

### Akun AWS

- AWS Account dengan akses ke EC2, VPC, dan Security Groups
- Kartu kredit untuk verifikasi (free tier tanpa charge selama 12 bulan)
- AWS Console access

### Tools Lokal

- SSH client
  - Linux/Mac: OpenSSH (built-in)
  - Windows: OpenSSH via PowerShell/Command Prompt atau WSL2
- Git (untuk clone repository)

### Pengetahuan

- Dasar Linux/Unix commands
- Memahami konsep SSH dan public key authentication
- Familiar dengan command line interface

---

## Meluncurkan EC2 Instance

### Step 1: Login ke AWS Console

1. Buka https://console.aws.amazon.com
2. Login dengan credentials AWS Anda
3. Pilih region yang dekat (misal ap-southeast-1 untuk Indonesia)

### Step 2: Navigasi ke EC2 Dashboard

1. Di AWS Console, cari "EC2", lalu klik pada "EC2" di services
2. Di sidebar kiri, klik "Instances"
3. Klik tombol "Launch instances"

### Step 3: Konfigurasi Instance

- **AMI**: Pilih "Ubuntu 22.04 LTS" bertanda "Free tier eligible"
- **Instance type**: `t2.micro` (Free tier)
- **Network**: Default VPC, Auto-assign IPv4: Enable
- **Storage**: 20 GB (free tier memungkinkan hingga 30 GB)
- **Tags**: `Name` = `aplikasi-monolitik`
- **Security group**: lihat section berikutnya

### Step 4: Review dan Launch

1. Klik "Launch"
2. Pilih "Create a new key pair" (misal `my-app-key`)
3. Download file `.pem` dan simpan dengan aman
4. Klik "Launch Instance"

### Step 5: Tunggu Instance Running

1. Status instance berubah `pending` → `running` (1-2 menit)
2. **Catat Public IPv4 Address** (contoh: 54.123.45.67)

---

## Konfigurasi Security Group

Di tab "Inbound rules", tambahkan:

| Type | Protocol | Port | Source | Deskripsi |
|------|----------|------|--------|----------|
| SSH | TCP | 22 | Your IP | Akses SSH dari komputer Anda |
| HTTP | TCP | 80 | 0.0.0.0/0 | Public HTTP access |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Public HTTPS access |

> Untuk SSH, gunakan IP komputer Anda, bukan 0.0.0.0/0 (lebih aman).
> Outbound: biarkan default (allow all).

---

## Koneksi SSH

```bash
# Linux/Mac
chmod 400 my-app-key.pem
ssh -i my-app-key.pem ubuntu@54.123.45.67

# Windows (PowerShell / CMD)
ssh -i my-app-key.pem ubuntu@54.123.45.67
```

Jika gagal, cek dengan `ssh -vvv -i my-app-key.pem ubuntu@YOUR_IP` dan pastikan
Security Group mengizinkan akses SSH dari IP Anda, serta instance sudah
`running`.

---

## Menjalankan Script Deployment

```bash
git clone https://github.com/VelAstra/Aplikasi-Monolitik-Stateful-dan-Deployment-AWS-EC2.git
cd Aplikasi-Monolitik-Stateful-dan-Deployment-AWS-EC2
chmod +x deployment/deploy.sh
sudo ./deployment/deploy.sh
```

Script akan otomatis:

1. Update system packages
2. Install `python3`, `nginx`, `git`, `curl`, `wget`, `ufw`
3. Membuat user `appuser`
4. Clone repo ke `/home/appuser/app`
5. Membuat direktori log
6. Setup **systemd service** untuk menjalankan `python app.py` di port 8000
7. Konfigurasi Nginx sebagai reverse proxy
8. Mengaktifkan UFW firewall (SSH 22, HTTP 80, HTTPS 443)

> Tidak ada PostgreSQL/Gunicorn/Supervisor — aplikasi murni Python + SQLite.
> Database `src/puisi.db` dan folder sesi `src/sessions/` dibuat otomatis
> saat pertama kali service berjalan.

**Durasi**: 3-5 menit (tergantung koneksi internet).

---

## Konfigurasi Post-Deployment

### Verifikasi Service

```bash
sudo systemctl status app_monolitik
# Output: Active: active (running)
```

### Verifikasi Aplikasi

```bash
# Dari dalam server
curl http://localhost:8000/app.py?action=status
# Output: {"sukses": true, "login": false}
```

### Akses via Browser

```
http://54.123.45.67
```

Ganti IP dengan Public IPv4 Anda.

---

## Setup SSL/HTTPS

Jika punya domain:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot certonly --nginx -d app.example.com
```

Lalu ubah `/etc/nginx/sites-available/app_monolitik` dengan blok server `ssl`,
dan aktifkan redirect HTTP → HTTPS. Terakhir `sudo nginx -t` dan
`sudo systemctl restart nginx`.

---

## Monitoring dan Maintenance

### Status Aplikasi

```bash
sudo systemctl status app_monolitik
sudo systemctl status nginx
```

### Log

```bash
# Log aplikasi
sudo tail -f /home/appuser/app/logs/app.log

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart

```bash
sudo systemctl restart app_monolitik
sudo systemctl restart nginx
```

### Update dari Repository

```bash
cd /home/appuser/app
git pull origin main
sudo systemctl restart app_monolitik
```

### Backup Database (SQLite)

```bash
# Salin file database
sudo cp /home/appuser/app/src/puisi.db \
  /home/appuser/backup_$(date +%Y%m%d_%H%M%S).db
```

---

## Troubleshooting

### Aplikasi Tidak Berjalan

```bash
sudo systemctl status app_monolitik
sudo journalctl -u app_monolitik -n 50
```

### Port Sudah Dipakai

```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Nginx Not Responding

```bash
sudo nginx -t
sudo systemctl restart nginx
sudo tail -f /var/log/nginx/error.log
```

### Permintaan Terproteksi Selalu "Anda harus login"

Pastikan browser mengirim cookie `puisi_session` (buka tab *Network* di DevTools
dan periksa header Cookie pada request `daftar_puisi` / `submit_puisi`).
Karena sesi tersimpan di file lokal, sesi yang dibuat sebelum service di-restart
dengan database baru tidak akan ditemukan — login ulang diperlukan.

---

## Catatan Penting (Stateful)

Aplikasi ini **stateful**: file sesi disimpan di `src/sessions/` pada mesin yang
sama. Artinya:

- Sesi tidak bisa dibagikan antar instance tanpa solusi *shared session*.
- Untuk mendukung *horizontal scaling*, perlu beralih ke arsitektur stateless
  (misal sesi di memori bersama / database) — topik selanjutnya di perkuliahan.

---

## Resources dan References

- [AWS EC2 User Guide](https://docs.aws.amazon.com/ec2/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Python http.server](https://docs.python.org/3/library/http.server.html)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

**Dokumen ini dibuat oleh**: Rayhan Haldi Hermawan (24/545406/PA/23176)
**Last Updated**: 31 Agustus 2026
**Untuk**: Mata Kuliah Pengembangan Perangkat Lunak Scalable (PACS262521)
