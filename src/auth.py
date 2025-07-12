"""
Modul autentikasi untuk login, register, dan session management
"""

from flask import session, request, redirect, url_for, flash
from functools import wraps
from src.database import mongodb, neo4j_db
import hashlib
import secrets
from datetime import datetime

def hash_password(password):
    """Hash password menggunakan SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_session_token():
    """Generate token session yang aman"""
    return secrets.token_urlsafe(32)

def login_required(f):
    """Decorator untuk halaman yang memerlukan login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return {'error': 'Login required'}, 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = AuthManager.get_current_user()
        if not user or user.get('role') != 'admin':
            flash('Akses hanya untuk admin.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

class AuthManager:
    """Kelas untuk mengelola autentikasi"""
    
    @staticmethod
    def register_user(user_data):
        """Register user baru"""
        try:
            # Cek apakah email sudah terdaftar
            existing_user = mongodb.get_user_by_email(user_data['email'])
            if existing_user:
                return {'error': 'Email sudah terdaftar'}, 400
            
            # Hash password
            user_data['password'] = hash_password(user_data['password'])

            # Tambahkan role jika belum ada (default: customer)
            if 'role' not in user_data:
                user_data['role'] = 'customer'
            
            # Buat user di MongoDB
            user_id = mongodb.create_user(user_data)
            
            # Buat node user di Neo4j
            neo4j_db.create_user_node(user_id, user_data)
            
            return {'message': 'User berhasil didaftarkan', 'user_id': user_id}, 201
            
        except Exception as e:
            return {'error': f'Gagal mendaftarkan user: {str(e)}'}, 500
    
    @staticmethod
    def login_user(email, password):
        """Login user"""
        try:
            # Cari user berdasarkan email
            user = mongodb.get_user_by_email(email)
            if not user:
                return {'error': 'Email atau password salah'}, 401
            
            # Verifikasi password
            if user['password'] != hash_password(password):
                return {'error': 'Email atau password salah'}, 401
            
            # Buat session
            session['user_id'] = user['user_id']
            session['user_name'] = user.get('name', '')
            session['user_email'] = user['email']
            
            return {
                'message': 'Login berhasil',
                'user': {
                    'user_id': user['user_id'],
                    'name': user.get('name', ''),
                    'email': user['email']
                }
            }, 200
            
        except Exception as e:
            return {'error': f'Gagal login: {str(e)}'}, 500
    
    @staticmethod
    def logout_user():
        """Logout user"""
        session.clear()
        return {'message': 'Logout berhasil'}, 200
    
    @staticmethod
    def get_current_user():
        """Mendapatkan data user yang sedang login"""
        if 'user_id' not in session:
            return None
        
        return mongodb.get_user_by_id(session['user_id'])
    
    @staticmethod
    def update_user_profile(user_id, update_data):
        """Update profil user"""
        try:
            # Update di MongoDB
            result = mongodb.update_user(user_id, update_data)
            
            # Update di Neo4j jika ada perubahan nama atau email
            if 'name' in update_data or 'email' in update_data:
                neo4j_db.driver.session().run("""
                    MATCH (u:User {user_id: $user_id})
                    SET u.name = $name, u.email = $email
                """, user_id=user_id, 
                     name=update_data.get('name'),
                     email=update_data.get('email'))
            
            return {'message': 'Profil berhasil diupdate'}, 200
            
        except Exception as e:
            return {'error': f'Gagal update profil: {str(e)}'}, 500

class UserActivityTracker:
    """Kelas untuk melacak aktivitas user"""
    
    @staticmethod
    def track_product_view(product_id, view_data=None):
        """Melacak produk yang dilihat user"""
        if 'user_id' not in session:
            return
        
        try:
            user_id = session['user_id']
            
            # Simpan di MongoDB
            mongodb.save_product_view(user_id, product_id, view_data)
            
            # Buat relasi di Neo4j
            neo4j_db.create_viewed_relationship(user_id, product_id)
            
        except Exception as e:
            print(f"Error tracking product view: {e}")
    
    @staticmethod
    def track_like(user_id, product_id, like_data=None):
        """Melacak saat user menyukai produk"""
        try:
            # Simpan interaksi di MongoDB
            mongodb.save_interaction(user_id, product_id, 'like', like_data)
            
            # Buat relasi di Neo4j
            neo4j_db.create_likes_relationship(user_id, product_id)
            
        except Exception as e:
            print(f"Error tracking like: {e}")

    @staticmethod
    def track_add_to_cart(user_id, product_id, cart_data=None):
        """Melacak saat user menambahkan produk ke keranjang"""
        try:
            # Simpan interaksi di MongoDB
            mongodb.save_interaction(user_id, product_id, 'add_to_cart', cart_data)
            
            # Buat relasi di Neo4j
            neo4j_db.create_in_cart_relationship(user_id, product_id)
            
        except Exception as e:
            print(f"Error tracking add_to_cart: {e}")
    
    @staticmethod
    def track_purchase(user_id, product_id, purchase_data):
        """Melacak pembelian user"""
        try:
            # Ambil data produk jika perlu
            product = mongodb.get_collection('products').find_one({'id': int(product_id)})
            # Siapkan data pembelian yang lengkap
            safe_purchase = {
                'user_id': user_id,
                'product_id': product_id,
                'product_name': purchase_data.get('product_name') or (product['name'] if product else '-'),
                'quantity': purchase_data.get('quantity', 1),
                'price': purchase_data.get('price') if purchase_data.get('price') is not None else (product['price'] if product else 0),
                'total_amount': purchase_data.get('total_amount') if purchase_data.get('total_amount') is not None else (product['price'] * purchase_data.get('quantity', 1) if product else 0),
                'purchase_date': purchase_data.get('purchase_date') or datetime.now(),
            }
            # Simpan di MongoDB
            mongodb.save_purchase_history(user_id, safe_purchase)
            # Buat relasi di Neo4j
            neo4j_db.create_purchased_relationship(user_id, product_id, safe_purchase)
        except Exception as e:
            print(f"Error tracking purchase: {e}")
    
    @staticmethod
    def get_user_activity(user_id):
        """Mendapatkan aktivitas user"""
        try:
            # Riwayat pembelian
            purchases = mongodb.get_purchase_history(user_id)
            
            # Produk yang dilihat
            views = mongodb.get_product_views(user_id)
            
            # Preferensi
            preferences = mongodb.get_user_preferences(user_id)
            
            return {
                'purchases': purchases,
                'views': views,
                'preferences': preferences
            }
            
        except Exception as e:
            print(f"Error getting user activity: {e}")
            return None
    
    @staticmethod
    def get_recommendations(user_id, limit=5):
        """Mendapatkan rekomendasi produk untuk user"""
        try:
            return neo4j_db.get_user_recommendations(user_id, limit)
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return [] 