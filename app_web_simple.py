#!/usr/bin/env python3
"""
Aplikasi Web dengan Flask - Versi Sederhana (Tanpa Database)
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

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

# Data dummy untuk user (simulasi database)
users = {}
purchases = []
product_views = []

def hash_password(password):
    """Hash password sederhana"""
    return str(hash(password))

@app.route('/')
def home():
    """Halaman utama"""
    current_user = None
    if 'user_id' in session:
        current_user = users.get(session['user_id'])
    
    return render_template('index.html', products=products, user=current_user, recommendations=[])

@app.route('/about')
def about():
    """Halaman tentang"""
    current_user = None
    if 'user_id' in session:
        current_user = users.get(session['user_id'])
    return render_template('about.html', user=current_user)

@app.route('/contact')
def contact():
    """Halaman kontak"""
    current_user = None
    if 'user_id' in session:
        current_user = users.get(session['user_id'])
    return render_template('contact.html', user=current_user)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Halaman detail produk"""
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return redirect(url_for('home'))
    
    # Track product view jika user login
    if 'user_id' in session:
        product_views.append({
            'user_id': session['user_id'],
            'product_id': product_id,
            'viewed_at': datetime.now()
        })
    
    current_user = None
    if 'user_id' in session:
        current_user = users.get(session['user_id'])
    
    return render_template('product_detail.html', product=product, user=current_user, similar_products=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Cari user berdasarkan email
        user = None
        for user_id, user_data in users.items():
            if user_data['email'] == email and user_data['password'] == hash_password(password):
                user = user_data
                break
        
        if user:
            session['user_id'] = user['user_id']
            flash('Login berhasil!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Email atau password salah', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Halaman register"""
    if request.method == 'POST':
        user_data = {
            'user_id': str(len(users) + 1),
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'password': hash_password(request.form.get('password')),
            'phone': request.form.get('phone', ''),
            'created_at': datetime.now()
        }
        
        # Cek apakah email sudah terdaftar
        for user in users.values():
            if user['email'] == user_data['email']:
                flash('Email sudah terdaftar', 'error')
                return render_template('register.html')
        
        # Simpan user
        users[user_data['user_id']] = user_data
        
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
    
    current_user = users.get(session['user_id'])
    if not current_user:
        session.clear()
        flash('User tidak ditemukan', 'error')
        return redirect(url_for('login'))
    
    # Ambil riwayat pembelian user
    user_purchases = [p for p in purchases if p['user_id'] == session['user_id']]
    
    # Ambil produk yang dilihat user
    user_views = [v for v in product_views if v['user_id'] == session['user_id']]
    
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
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        product = next((p for p in products if p['id'] == int(product_id)), None)
        if not product:
            return jsonify({'error': 'Produk tidak ditemukan'}), 404
        
        purchase_data = {
            'purchase_id': str(len(purchases) + 1),
            'user_id': session['user_id'],
            'product_id': product_id,
            'product_name': product['name'],
            'quantity': quantity,
            'price': product['price'],
            'total_amount': product['price'] * quantity,
            'purchase_date': datetime.now()
        }
        
        purchases.append(purchase_data)
        
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
    
    user_purchases = [p for p in purchases if p['user_id'] == session['user_id']]
    user_views = [v for v in product_views if v['user_id'] == session['user_id']]
    
    return jsonify({
        'purchases': user_purchases,
        'views': user_views
    }), 200

if __name__ == '__main__':
    print("🚀 Menjalankan aplikasi web sederhana (tanpa database)...")
    print("📱 Buka browser dan kunjungi: http://localhost:5000")
    print("💡 Fitur: Register, Login, Browse produk, Pembelian")
    print("⚠️  Data disimpan sementara di memory (akan hilang jika aplikasi di-restart)")
    print("⏹️  Tekan Ctrl+C untuk menghentikan server")
    app.run(debug=True, host='0.0.0.0', port=5000) 