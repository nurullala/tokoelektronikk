# Toko Elektronik - Aplikasi Python

Aplikasi toko elektronik modern berbasis Python yang menyediakan berbagai mode: Console, GUI (Tkinter), dan Web (Flask) dengan dukungan database MongoDB & Neo4j. Dirancang untuk demo, pengembangan, dan pembelajaran sistem e-commerce.

---

## ✨ Deskripsi Singkat
Toko Elektronik adalah aplikasi demo e-commerce yang memungkinkan pengguna untuk:
- Melihat, mencari, dan membeli produk elektronik
- Registrasi, login, dan mengelola profil
- Mendapatkan rekomendasi produk berbasis riwayat & preferensi
- Menyimpan riwayat pembelian dan aktivitas
- Menyediakan mode fallback (dummy) jika database tidak tersedia

> **Visi:** Menjadi toko elektronik terdepan yang menyediakan produk berkualitas, harga terbaik, dan layanan pelanggan memuaskan.

---

## 🚀 Fitur Utama
- **Aplikasi Web (Flask):**
  - Browse, detail, dan pencarian produk
  - Register, login, logout, profil user
  - Keranjang belanja, checkout, riwayat pembelian
  - Rekomendasi produk (Neo4j)
  - Admin: tambah/edit/hapus produk, kelola pesanan
  - Fallback mode: tetap berjalan tanpa database
- **Aplikasi GUI (Tkinter):**
  - Demo input nama, waktu, dan sapaan interaktif
- **Aplikasi Console:**
  - Demo fungsi utilitas, input, dan perhitungan sederhana
- **API:**
  - Endpoint produk, pencarian, pembelian, aktivitas user
- **Testing Otomatis:**
  - `test_apps.py` untuk verifikasi semua mode aplikasi

---

## 🏗️ Struktur Proyek
```
tokoelektorik/
├── main.py              # Entry point & menu utama
├── app_web.py           # Web app (Flask, MongoDB, Neo4j, fallback)
├── app_web_mongodb.py   # Web app (Flask + MongoDB saja)
├── app_web_simple.py    # Web app sederhana (tanpa database)
├── app_gui.py           # GUI Tkinter
├── src/                 # Modul auth, database, utils
├── templates/           # HTML template (Jinja2)
├── static/              # Asset statis & gambar produk
├── requirements.txt     # Daftar dependensi
├── DATABASE_SETUP.md    # Panduan setup database
├── test_apps.py         # Script testing otomatis
└── README.md            # Dokumentasi ini
```

---

## ⚙️ Instalasi & Setup
1. **Clone repo & install dependensi:**
   ```bash
   git clone <repo-url>
   cd tokoelektorik
   pip install -r requirements.txt
   ```
2. **(Opsional) Setup database:**
   - Lihat [DATABASE_SETUP.md](DATABASE_SETUP.md) untuk instruksi lengkap MongoDB & Neo4j
   - Atur variabel environment di file `.env` atau edit `config.py`

   Contoh `.env`:
   ```env
   MONGODB_URI=mongodb://localhost:27017/
   MONGODB_DB=tokoelektronik
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   FLASK_SECRET_KEY=your-secret-key-here
   FLASK_DEBUG=True
   ```

---

## 💻 Cara Menjalankan
### 1. **Menu Utama (semua mode):**
```bash
python main.py
```
Pilih mode: Console, GUI, atau Web.

### 2. **Langsung Web App:**
- **Sederhana (tanpa database):**
  ```bash
  python app_web_simple.py
  # http://localhost:5000
  ```
- **Dengan MongoDB:**
  ```bash
  python app_web_mongodb.py
  # http://localhost:5000
  ```
- **Lengkap (MongoDB + Neo4j, fallback jika DB error):**
  ```bash
  python app_web.py
  # http://localhost:5000
  ```

### 3. **Testing Otomatis:**
```bash
python test_apps.py
```

---

## 🗄️ Database & Konfigurasi
- **MongoDB:**
  - Data user, produk, pembelian, preferensi
- **Neo4j:**
  - Relasi user-produk, rekomendasi, collaborative filtering
- **Fallback/Dummy Mode:**
  - Jika database tidak tersedia, aplikasi tetap berjalan (data tidak persisten)

Lihat [DATABASE_SETUP.md](DATABASE_SETUP.md) untuk detail setup, struktur koleksi, dan troubleshooting.

---

## 📊 Status & Mode Aplikasi
| Aplikasi                | Status   | Database   | Fitur Utama                  |
|-------------------------|----------|------------|------------------------------|
| app_web_simple.py       | ✅ Ready | ❌         | Basic UI, memory storage     |
| app_web_mongodb.py      | ✅ Ready | ✅ MongoDB | Full features + MongoDB      |
| app_web.py              | ✅ Ready | ⚠️ Opsional| Full features + fallback     |

- **Dummy Mode:**
  - Test login: `test@test.com` / `test123`
  - Semua fitur UI tetap bisa dicoba

---

## 🎨 Keunggulan & Visi-Misi
- Produk elektronik berkualitas, harga kompetitif
- Pengiriman cepat, customer service 24/7
- Garansi resmi, pembayaran aman
- Rekomendasi produk cerdas
- UI modern, responsif, dan ramah pengguna
- **Visi:** Menjadi toko elektronik terdepan
- **Misi:**
  - Menyediakan produk berkualitas & harga terbaik
  - Layanan pelanggan profesional & responsif
  - Garansi resmi & kepuasan pelanggan

---

## 🔒 Keamanan & Best Practice
- Password di-hash (SHA-256)
- Session management aman
- Null checks & error handling di semua mode
- Fallback mechanism jika database error
- Gunakan environment variable untuk credential

---

## 🤝 Kontribusi
Pull request & issue sangat diterima untuk pengembangan lebih lanjut!

---

## 📄 Lisensi
Aplikasi ini untuk keperluan demo, pembelajaran, dan pengembangan internal. 