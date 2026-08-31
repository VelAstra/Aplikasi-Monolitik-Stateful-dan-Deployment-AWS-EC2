/**
 * Aplikasi Monolitik Stateful - Frontend
 * Vanilla JavaScript (tanpa framework).
 *
 * Komunikasi dengan backend memakai Fetch API. Semua endpoint melewati
 * single URL path:  /app.py?action=<aksi>
 *
 * Cookie sesi (puisi_session) dikelola otomatis oleh browser. Perhatikan tab
 * Network untuk melihat header Set-Cookie pada respons login, dan header
 * Cookie yang dikirim browser ke endpoint terproteksi (submit_puisi,
 * daftar_puisi).
 */

const APP_URL = '/app.py';

const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const puisiForm = document.getElementById('puisiForm');
const logoutBtn = document.getElementById('logoutBtn');
const authPanel = document.getElementById('authPanel');
const appPanel = document.getElementById('appPanel');
const statusBox = document.getElementById('statusBox');
const greetName = document.getElementById('greetName');
const puisiList = document.getElementById('puisiList');
const tabs = document.querySelectorAll('.tab-btn');

function setStatus(msg, type) {
    statusBox.innerHTML = msg
        ? `<div class="status-msg ${type}">${msg}</div>`
        : '';
}

function setMsg(el, msg, type) {
    el.textContent = msg || '';
    el.className = 'form-msg ' + (type || '');
}

/* Tab switching login/register */
tabs.forEach((btn) => {
    btn.addEventListener('click', () => {
        tabs.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        if (btn.dataset.tab === 'login') {
            loginForm.classList.remove('hidden');
            registerForm.classList.add('hidden');
        } else {
            registerForm.classList.remove('hidden');
            loginForm.classList.add('hidden');
        }
    });
});

/* Register */
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = document.getElementById('registerMsg');
    const data = {
        username: registerForm.username.value.trim(),
        nama: registerForm.nama.value.trim(),
        no_id: registerForm.no_id.value.trim(),
        password: registerForm.password.value,
    };
    setMsg(msg, 'Mendaftarkan...');
    try {
        const res = await fetch(`${APP_URL}?action=register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const json = await res.json();
        setMsg(msg, json.pesan, json.sukses ? 'ok' : 'err');
        if (json.sukses) {
            registerForm.reset();
        }
    } catch (err) {
        setMsg(msg, 'Terjadi kesalahan jaringan.', 'err');
    }
});

/* Login */
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = document.getElementById('loginMsg');
    const data = {
        username: loginForm.username.value.trim(),
        password: loginForm.password.value,
    };
    setMsg(msg, 'Login...');
    try {
        const res = await fetch(`${APP_URL}?action=login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const json = await res.json();
        if (json.sukses) {
            setMsg(msg, 'Login berhasil.');
            loginForm.reset();
            await refreshSession();
        } else {
            setMsg(msg, json.pesan, 'err');
        }
    } catch (err) {
        setMsg(msg, 'Terjadi kesalahan jaringan.', 'err');
    }
});

/* Logout */
logoutBtn.addEventListener('click', async () => {
    await fetch(`${APP_URL}?action=logout`, { method: 'POST' });
    await refreshSession();
});

/* Submit puisi */
puisiForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = document.getElementById('puisiMsg');
    const data = {
        judul: puisiForm.judul.value.trim(),
        tgl_submit: puisiForm.tgl_submit.value,
        kategori: puisiForm.kategori.value,
        keyword: puisiForm.keyword.value.trim(),
        isi: puisiForm.isi.value.trim(),
    };
    setMsg(msg, 'Menyimpan puisi...');
    try {
        const res = await fetch(`${APP_URL}?action=submit_puisi`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const json = await res.json();
        setMsg(msg, json.pesan, json.sukses ? 'ok' : 'err');
        if (json.sukses) {
            puisiForm.reset();
            muatDaftarPuisi();
        }
    } catch (err) {
        setMsg(msg, 'Terjadi kesalahan jaringan.', 'err');
    }
});

/* Cek status sesi */
async function refreshSession() {
    try {
        const res = await fetch(`${APP_URL}?action=status`);
        const json = await res.json();
        if (json.login) {
            authPanel.classList.add('hidden');
            appPanel.classList.remove('hidden');
            greetName.textContent = json.nama || json.username;
            setStatus(`Login sebagai <strong>${json.username}</strong> (sesi server-side aktif).`, 'ok');
            muatDaftarPuisi();
        } else {
            appPanel.classList.add('hidden');
            authPanel.classList.remove('hidden');
            setStatus('Belum login. Silakan login atau daftar.', 'info');
        }
    } catch (err) {
        setStatus('Tidak dapat terhubung ke server.', 'err');
    }
}

/* Muat daftar puisi */
async function muatDaftarPuisi() {
    try {
        const res = await fetch(`${APP_URL}?action=daftar_puisi`);
        const json = await res.json();
        puisiList.innerHTML = '';
        if (!json.sukses) {
            puisiList.innerHTML = `<div class="puisi-empty">${json.pesan}</div>`;
            return;
        }
        if (!json.daftar || json.daftar.length === 0) {
            puisiList.innerHTML = '<div class="puisi-empty">Belum ada puisi. Yuk submit puisi pertama!</div>';
            return;
        }
        json.daftar.forEach((p) => {
            const item = document.createElement('div');
            item.className = 'puisi-item';
            item.innerHTML = `
                <div class="judul">${esc(p.judul)}</div>
                <div class="meta">📅 ${esc(p.tgl_submit)} &nbsp;·&nbsp; ${esc(p.kategori)}</div>`;
            puisiList.appendChild(item);
        });
    } catch (err) {
        puisiList.innerHTML = '<div class="puisi-empty">Gagal memuat daftar puisi.</div>';
    }
}

function esc(str) {
    const div = document.createElement('div');
    div.textContent = str == null ? '' : String(str);
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', () => {
    const today = new Date().toISOString().slice(0, 10);
    document.querySelector('input[name="tgl_submit"]').value = today;
    refreshSession();
});
