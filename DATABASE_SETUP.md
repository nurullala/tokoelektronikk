# Setup Database untuk Aplikasi Toko Elektronik

## 📋 **Persyaratan Database**

Aplikasi ini menggunakan dua database:
1. **MongoDB** - Untuk menyimpan data user, riwayat pembelian, dan preferensi
2. **Neo4j** - Untuk menyimpan relasi antar user dan produk (rekomendasi)

## 🗄️ **1. Setup MongoDB**

### **Instalasi MongoDB Community Edition**

#### **Windows:**
1. Download MongoDB Community Server dari [mongodb.com](https://www.mongodb.com/try/download/community)
2. Install dengan default settings
3. MongoDB akan berjalan di `mongodb://localhost:27017/`

#### **Menggunakan Docker:**
```bash
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

### **Verifikasi MongoDB:**
```bash
# Cek apakah MongoDB berjalan
mongo --eval "db.runCommand('ping')"
```

## 🕸️ **2. Setup Neo4j**

### **Instalasi Neo4j Community Edition**

#### **Windows:**
1. Download Neo4j Desktop dari [neo4j.com](https://neo4j.com/download/)
2. Install dan buat database baru
3. Set password default: `password`

#### **Menggunakan Docker:**
```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
```

### **Verifikasi Neo4j:**
- Buka browser: `http://localhost:7474`
- Login dengan username: `neo4j`, password: `password`

## ⚙️ **3. Konfigurasi Aplikasi**

### **File Konfigurasi**
Buat file `.env` di root folder (atau gunakan `config.py` yang sudah ada):

```env
# Database Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=tokoelektronik

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True
```

## 🚀 **4. Menjalankan Aplikasi**

### **Install Dependensi:**
```bash
pip install -r requirements.txt
```

### **Jalankan Aplikasi:**
```bash
python app_web.py
```

### **Atau melalui menu utama:**
```bash
python main.py
# Pilih opsi 3 (Aplikasi Web)
```

## 📊 **5. Struktur Database**

### **MongoDB Collections:**

#### **users**
```json
{
  "_id": ObjectId,
  "user_id": "uuid-string",
  "name": "Nama User",
  "email": "user@example.com",
  "password": "hashed-password",
  "phone": "081234567890",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### **purchases**
```json
{
  "_id": ObjectId,
  "user_id": "uuid-string",
  "purchase_id": "uuid-string",
  "product_id": "1",
  "product_name": "Laptop Gaming",
  "quantity": 1,
  "price": 15000000,
  "total_amount": 15000000,
  "purchase_date": "2024-01-15T10:30:00Z"
}
```

#### **product_views**
```json
{
  "_id": ObjectId,
  "user_id": "uuid-string",
  "product_id": "1",
  "view_id": "uuid-string",
  "product_name": "Laptop Gaming",
  "category": "Electronics",
  "viewed_at": "2024-01-15T10:30:00Z"
}
```

#### **user_preferences**
```json
{
  "_id": ObjectId,
  "user_id": "uuid-string",
  "preferred_categories": ["Electronics", "Gaming"],
  "budget_range": "10000000-20000000",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### **Neo4j Graph Structure:**

#### **Nodes:**
- **User Node:** `(u:User {user_id, name, email})`
- **Product Node:** `(p:Product {product_id, name, category})`

#### **Relationships:**
- **VIEWED:** `(u:User)-[r:VIEWED {viewed_at}]->(p:Product)`
- **PURCHASED:** `(u:User)-[r:PURCHASED {purchase_id, quantity, price}]->(p:Product)`

## 🔧 **6. Fitur Database**

### **MongoDB Features:**
- ✅ User registration dan authentication
- ✅ Riwayat pembelian
- ✅ Tracking produk yang dilihat
- ✅ Preferensi user
- ✅ Session management

### **Neo4j Features:**
- ✅ Relasi user-product
- ✅ Rekomendasi produk berdasarkan preferensi
- ✅ Produk yang mirip
- ✅ Collaborative filtering

## 🛠️ **7. Troubleshooting**

### **MongoDB Connection Error:**
```bash
# Cek status MongoDB
netstat -an | findstr :27017

# Restart MongoDB service
net stop MongoDB
net start MongoDB
```

### **Neo4j Connection Error:**
```bash
# Cek status Neo4j
netstat -an | findstr :7687

# Restart Neo4j service
neo4j stop
neo4j start
```

### **Python Connection Error:**
```bash
# Test koneksi MongoDB
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print(client.admin.command('ping'))"

# Test koneksi Neo4j
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')); print(driver.verify_connectivity())"
```

## 📈 **8. Monitoring**

### **MongoDB Monitoring:**
- MongoDB Compass untuk GUI
- `db.stats()` untuk statistik database

### **Neo4j Monitoring:**
- Neo4j Browser: `http://localhost:7474`
- Cypher queries untuk analisis

## 🔒 **9. Security**

### **Production Setup:**
- Gunakan environment variables untuk credentials
- Enable authentication di MongoDB
- Set strong password untuk Neo4j
- Use HTTPS untuk aplikasi web
- Regular backup database

---

**Note:** Untuk development, gunakan konfigurasi default. Untuk production, pastikan mengikuti best practices security. 