#!/usr/bin/env python3
"""
Aplikasi Web dengan Flask - MongoDB Version
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from datetime import datetime
import os
from pymongo import MongoClient
import uuid
import hashlib
from bson import ObjectId

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

# MongoDB Connection
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['tokoelektronik']
    print("✅ MongoDB connected successfully!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    db = None

# Data dummy untuk demo
products = [
    {
        'id': 1,
        'name': 'Laptop Gaming',
        'price': 15000000,
        'description': 'Laptop gaming performa tinggi dengan GPU RTX 4060',
        'image': 'https://via.placeholder.com/300x200/4CAF50/FFFFFF?text=Laptop+Gaming',
        'category': 'Electronics'
    },
    {
        'id': 2,
        'name': 'Smartphone',
        'price': 5000000,
        'description': 'Smartphone terbaru dengan kamera 108MP',
        'image': 'https://via.placeholder.com/300x200/2196F3/FFFFFF?text=Smartphone',
        'category': 'Electronics'
    },
    {
        'id': 3,
        'name': 'Headphone Wireless',
        'price': 1500000,
        'description': 'Headphone wireless dengan noise cancelling',
        'image': 'https://via.placeholder.com/300x200/FF9800/FFFFFF?text=Headphone',
        'category': 'Electronics'
    },
    {
        'id': 4,
        'name': 'Smart Watch',
        'price': 2500000,
        'description': 'Smart watch dengan fitur kesehatan lengkap',
        'image': 'https://via.placeholder.com/300x200/9C27B0/FFFFFF?text=Smart+Watch',
        'category': 'Electronics'
    }
]

def hash_password(password):
    """Hash password menggunakan SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_user():
    """Mendapatkan data user yang sedang login"""
    if 'user_id' not in session:
        return None
    
    if db is not None:
        return db.users.find_one({'user_id': session['user_id']})
    return None

@app.route('/')
def home():
    """Halaman utama"""
    current_user = get_current_user()
    recommendations = []
    
    if current_user and db is not None:
        # Ambil rekomendasi berdasarkan riwayat pembelian
        user_purchases = list(db.purchases.find({'user_id': session['user_id']}).limit(5))
        if user_purchases:
            # Ambil produk yang sering dibeli
            recommendations = products[:3]  # Dummy recommendations
    
    return render_template('index.html', products=products, user=current_user, recommendations=recommendations)

@app.route('/about')
def about():
    """Halaman tentang"""
    current_user = get_current_user()
    return render_template('about.html', user=current_user)

@app.route('/contact')
def contact():
    """Halaman kontak"""
    current_user = get_current_user()
    return render_template('contact.html', user=current_user)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Halaman detail produk"""
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return redirect(url_for('home'))
    
    # Track product view jika user login
    if 'user_id' in session and db is not None:
        view_data = {
            'user_id': session['user_id'],
            'product_id': str(product_id),
            'product_name': product['name'],
            'viewed_at': datetime.now()
        }
        db.product_views.insert_one(view_data)
    
    current_user = get_current_user()
    return render_template('product_detail.html', product=product, user=current_user, similar_products=products[:3])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if db is None:
            flash('Database tidak tersedia', 'error')
            return render_template('login.html')
        
        # Cari user berdasarkan email
        user = db.users.find_one({'email': email})
        
        if user and user['password'] == hash_password(password):
            session['user_id'] = user['user_id']
            session['user_name'] = user.get('name', '')
            session['user_email'] = user['email']
            flash('Login berhasil!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Email atau password salah', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Halaman register"""
    if request.method == 'POST':
        if db is None:
            flash('Database tidak tersedia', 'error')
            return render_template('register.html')
        
        user_data = {
            'user_id': str(uuid.uuid4()),
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'password': hash_password(request.form.get('password')),
            'phone': request.form.get('phone', ''),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Cek apakah email sudah terdaftar
        existing_user = db.users.find_one({'email': user_data['email']})
        if existing_user:
            flash('Email sudah terdaftar', 'error')
            return render_template('register.html')
        
        # Simpan user
        db.users.insert_one(user_data)
        
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('Logout berhasil!', 'success')
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    """Halaman profil user"""
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu', 'error')
        return redirect(url_for('login'))
    
    current_user = get_current_user()
    if not current_user:
        session.clear()
        flash('User tidak ditemukan', 'error')
        return redirect(url_for('login'))
    
    # Ambil riwayat pembelian user
    user_purchases = []
    if db is not None:
        user_purchases = list(db.purchases.find({'user_id': session['user_id']}).sort('purchase_date', -1))
    
    # Ambil produk yang dilihat user
    user_views = []
    if db is not None:
        user_views = list(db.product_views.find({'user_id': session['user_id']}).sort('viewed_at', -1).limit(10))
    
    return render_template('profile.html', user=current_user, 
                         activity={'purchases': user_purchases, 'views': user_views}, 
                         recommendations=[])

@app.route('/api/products')
def api_products():
    """API untuk mendapatkan data produk"""
    return jsonify(products)

@app.route('/api/search')
def search_products():
    """API untuk mencari produk"""
    query = request.args.get('q', '').lower()
    if query:
        filtered_products = [p for p in products if query in p['name'].lower() or query in p['description'].lower()]
        return jsonify(filtered_products)
    return jsonify(products)

@app.route('/api/purchase', methods=['POST'])
def api_purchase():
    """API untuk melakukan pembelian"""
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    if db is None:
        return jsonify({'error': 'Database tidak tersedia'}), 500
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        product = next((p for p in products if p['id'] == int(product_id)), None)
        if not product:
            return jsonify({'error': 'Produk tidak ditemukan'}), 404
        
        purchase_data = {
            'purchase_id': str(uuid.uuid4()),
            'user_id': session['user_id'],
            'product_id': str(product_id),
            'product_name': product['name'],
            'quantity': quantity,
            'price': product['price'],
            'total_amount': product['price'] * quantity,
            'purchase_date': datetime.now()
        }
        
        db.purchases.insert_one(purchase_data)
        
        return jsonify({
            'message': 'Pembelian berhasil',
            'purchase': purchase_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Gagal melakukan pembelian: {str(e)}'}), 500

@app.route('/api/user/activity')
def api_user_activity():
    """API untuk mendapatkan aktivitas user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    if db is None:
        return jsonify({'error': 'Database tidak tersedia'}), 500
    
    user_purchases = list(db.purchases.find({'user_id': session['user_id']}).sort('purchase_date', -1))
    user_views = list(db.product_views.find({'user_id': session['user_id']}).sort('viewed_at', -1))
    
    return jsonify({
        'purchases': user_purchases,
        'views': user_views
    }), 200

@app.route('/api/user/preferences', methods=['GET', 'POST'])
def api_user_preferences():
    """API untuk mengelola preferensi user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    if db is None:
        return jsonify({'error': 'Database tidak tersedia'}), 500
    
    if request.method == 'POST':
        try:
            preference_data = request.get_json()
            preference_data['user_id'] = session['user_id']
            preference_data['updated_at'] = datetime.now()
            
            db.user_preferences.update_one(
                {'user_id': session['user_id']},
                {'$set': preference_data},
                upsert=True
            )
            return jsonify({'message': 'Preferensi berhasil disimpan'}), 200
        except Exception as e:
            return jsonify({'error': f'Gagal menyimpan preferensi: {str(e)}'}), 500
    
    else:  # GET
        try:
            preferences = db.user_preferences.find_one({'user_id': session['user_id']})
            return jsonify(preferences or {}), 200
        except Exception as e:
            return jsonify({'error': f'Gagal mengambil preferensi: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Menjalankan aplikasi web dengan MongoDB...")
    print("📱 Buka browser dan kunjungi: http://localhost:5000")
    print("💡 Fitur: Register, Login, Browse produk, Pembelian, Database MongoDB")
    if db is not None:
        print("✅ MongoDB: Connected")
    else:
        print("❌ MongoDB: Not connected")
    print("⏹️  Tekan Ctrl+C untuk menghentikan server")
    app.run(debug=True, host='0.0.0.0', port=5000) 