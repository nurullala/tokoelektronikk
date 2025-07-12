#!/usr/bin/env python3
"""
Aplikasi Web dengan Flask - Integrated with MongoDB and Neo4j
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from datetime import datetime
import os
from config import Config
import uuid
from werkzeug.utils import secure_filename
from src.auth import AuthManager, UserActivityTracker, login_required, admin_required
from neo4j import GraphDatabase
from bson import ObjectId

# Try to import database modules, but handle gracefully if they fail
try:
    from src.database import mongodb, neo4j_db
    DB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Database modules not available: {e}")
    DB_AVAILABLE = False
    # Create dummy classes for when database is not available
    class DummyAuthManager:
        @staticmethod
        def get_current_user():
            return None
        @staticmethod
        def login_user(email, password):
            return False, "Database not available"
        @staticmethod
        def register_user(data):
            pass
        @staticmethod
        def logout_user():
            pass
    
    class DummyUserActivityTracker:
        @staticmethod
        def track_product_view(product_id, data):
            pass
        @staticmethod
        def track_purchase(user_id, product_id, data):
            pass
        
        @staticmethod
        def track_like(user_id, product_id, data):
            pass

        @staticmethod
        def track_add_to_cart(user_id, product_id, data):
            pass
        
        @staticmethod
        def get_user_activity(user_id):
            return {'purchases': [], 'views': []}
        
    AuthManager = DummyAuthManager
    UserActivityTracker = DummyUserActivityTracker
    def login_required(f):
        def decorated_function(*args, **kwargs):
            # In dummy mode, we can't check login, so we just pass through
            return f(*args, **kwargs)
        return decorated_function

app = Flask(__name__)
app.config.from_object(Config)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """Halaman utama"""
    current_user = AuthManager.get_current_user()
    recommendations = []
    all_products = []
    featured_products = []
    if DB_AVAILABLE:
        try:
            # Semua produk
            all_products = list(mongodb.db.products.find().sort('name', 1))
            # Produk unggulan: produk yang PERNAH dibeli ATAU PERNAH disukai
            purchases_pipeline = [
                {"$group": {"_id": "$product_id", "count": {"$sum": 1}}},
            ]
            purchases = list(mongodb.db.purchases.aggregate(purchases_pipeline))
            likes_pipeline = [
                {"$match": {"interaction_type": "like"}},
                {"$group": {"_id": "$product_id", "count": {"$sum": 1}}},
            ]
            likes = list(mongodb.db.user_interactions.aggregate(likes_pipeline))
            def to_str(val):
                try:
                    return str(val)
                except Exception:
                    return None
            purchase_count = {to_str(p['_id']): p['count'] for p in purchases if to_str(p['_id']) is not None}
            like_count = {to_str(l['_id']): l['count'] for l in likes if to_str(l['_id']) is not None}
            union_ids = set(purchase_count.keys()) | set(like_count.keys())
            combined = [(pid, purchase_count.get(pid, 0) + like_count.get(pid, 0)) for pid in union_ids]
            combined.sort(key=lambda x: x[1], reverse=True)
            featured_ids = [pid for pid, _ in combined][:5]
            if featured_ids:
                featured_products = [p for p in all_products if to_str(p.get('id')) in featured_ids]
                featured_products.sort(key=lambda p: featured_ids.index(to_str(p.get('id'))))
            else:
                featured_products = []
        except Exception as e:
            print(f"Error fetching products from MongoDB: {e}")
            flash('Tidak dapat memuat produk dari database.', 'error')
    if current_user and DB_AVAILABLE:
        try:
            recommendations = neo4j_db.get_user_recommendations(current_user['user_id'])
        except Exception as e:
            print(f"Warning: Could not get recommendations: {e}")
    return render_template('index.html', products=all_products, user=current_user, recommendations=recommendations, featured_products=featured_products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Halaman detail untuk satu produk"""
    current_user = AuthManager.get_current_user()
    product = None
    if DB_AVAILABLE:
        try:
            product = mongodb.db.products.find_one({'id': product_id})
            print(f"[DEBUG] Product detail request for ID: {product_id}")
            print(f"[DEBUG] Product found: {product is not None}")
            if product:
                print(f"[DEBUG] Product name: {product.get('name', 'N/A')}")
        except Exception as e:
            print(f"[ERROR] Error fetching product {product_id}: {e}")
            flash('Terjadi kesalahan saat memuat produk.', 'error')
            return redirect(url_for('home'))

    if not product:
        print(f"[DEBUG] Product {product_id} not found")
        flash('Produk tidak ditemukan.', 'error')
        return redirect(url_for('home'))

    # Pastikan semua field penting ada agar tidak error di template
    product.setdefault('tags', [])
    product.setdefault('image', None)
    product.setdefault('category', '')
    product.setdefault('description', '')
    product.setdefault('price', 0)
    product.setdefault('name', '')
    
    # Lacak bahwa produk ini dilihat
    if current_user and DB_AVAILABLE:
        UserActivityTracker.track_product_view(
            str(product_id), 
            {'product_name': product.get('name')}
        )

    # Ambil rekomendasi
    similar_products_content = []
    similar_products_collab = []
    frequently_bought_together = []
    if DB_AVAILABLE:
        try:
            # Rekomendasi berdasarkan konten (kategori/tags)
            try:
                similar_products_content = neo4j_db.get_content_based_similar_products(str(product_id))
            except Exception as e:
                print(f"[WARNING] Error get_content_based_similar_products for product {product_id}: {e}")
                similar_products_content = []
            # Rekomendasi berdasarkan kolaborasi (pengguna lain)
            try:
                similar_products_collab = neo4j_db.get_similar_products(str(product_id))
            except Exception as e:
                print(f"[WARNING] Error get_similar_products for product {product_id}: {e}")
                similar_products_collab = []
            # Rekomendasi berdasarkan pembelian bersama
            try:
                frequently_bought_together = neo4j_db.get_frequently_bought_together(str(product_id))
            except Exception as e:
                print(f"[WARNING] Error get_frequently_bought_together for product {product_id}: {e}")
                frequently_bought_together = []
        except Exception as e:
            print(f"[WARNING] Error getting recommendations for product {product_id}: {e}")
            # Jangan tampilkan flash message untuk rekomendasi yang gagal
            # karena ini tidak kritis untuk menampilkan halaman produk
            
    # Ambil produk sejenis berdasarkan tags
    similar_products_content = []
    if DB_AVAILABLE and product.get('tags'):
        try:
            # Cari produk lain yang memiliki minimal satu tag yang sama, dan bukan produk ini sendiri
            similar_products_content = list(
                mongodb.db.products.find({
                    'tags': {'$in': product['tags']},
                    'id': {'$ne': product['id']}
                }).limit(6)
            )
        except Exception as e:
            print(f'[WARNING] Error fetching similar products by tags: {e}')
            similar_products_content = []

    return render_template(
        'product_detail.html', 
        product=product, 
        user=current_user,
        similar_products=similar_products_content,  # Tambahkan variabel yang hilang
        similar_products_content=similar_products_content,
        similar_products_collab=similar_products_collab,
        frequently_bought_together=frequently_bought_together
    )

@app.route('/add_product', methods=['GET', 'POST'])
@admin_required
@login_required
def add_product():
    """Menampilkan form dan memproses penambahan produk baru"""
    if not DB_AVAILABLE:
        flash('Database tidak tersedia, tidak dapat menambah produk.', 'error')
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        # Ambil data dari form
        form_id = request.form.get('product_id')
        form_name = request.form.get('name')
        form_category = request.form.get('category')
        form_description = request.form.get('description')
        form_price = request.form.get('price')
        form_tags = request.form.get('tags')

        # Handle file upload
        image_url = None
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'])
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
                file.save(os.path.join(upload_path, filename))
                image_url = url_for('static', filename=f'uploads/{filename}')

        # Validasi wajib
        if not form_name or not form_price:
            flash('Nama dan Harga produk wajib diisi.', 'error')
            return render_template('add_product.html', product=request.form, user=AuthManager.get_current_user())

        try:
            products_collection = mongodb.get_collection('products')
            # Penentuan ID produk
            if not form_id:
                last_product = products_collection.find_one(sort=[("id", -1)])
                next_id = (last_product['id'] + 1) if last_product and last_product.get('id') else 1
                product_id = next_id
            else:
                try:
                    product_id = int(form_id)
                except (ValueError, TypeError):
                    product_id = 1

            # Konversi price
            try:
                price = int(form_price) if form_price is not None else 0
            except (ValueError, TypeError):
                price = 0

            # Konversi tags
            if isinstance(form_tags, str) and form_tags.strip():
                tags = [tag.strip() for tag in form_tags.split(',') if tag.strip()]
            else:
                tags = []

            # Siapkan dokumen produk
            product_doc = {
                'id': product_id,
                'name': form_name or '',
                'category': form_category or '',
                'description': form_description or '',
                'price': price,
                'tags': tags,
                'image': image_url,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
            }

            products_collection.insert_one(product_doc.copy())
            neo4j_db.create_product_node(str(product_doc['id']), product_doc)

            flash('Produk berhasil ditambahkan!', 'success')
            return redirect(url_for('product_detail', product_id=product_doc['id']))
        except Exception as e:
            flash(f'Gagal menambahkan produk: {e}', 'error')
            return render_template('add_product.html', product=request.form, user=AuthManager.get_current_user())

    return render_template('add_product.html', user=AuthManager.get_current_user())


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if DB_AVAILABLE:
            result, status_code = AuthManager.login_user(email, password)
            if status_code == 200:
                flash('Login berhasil!', 'success')
                return redirect(url_for('home'))
            else:
                error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
                flash(f'Login gagal: {error_msg}', 'error')
        else:
            flash('Database tidak tersedia.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Halaman registrasi"""
    if request.method == 'POST':
        if DB_AVAILABLE:
            user_data = {
                'name': request.form.get('name'),
                'email': request.form.get('email'),
                'password': request.form.get('password'),
                'role': request.form.get('role', 'customer')
            }
            try:
                register_result = AuthManager.register_user(user_data)
                if register_result is None:
                    result, status_code = {'error': 'Unknown error'}, 500
                elif isinstance(register_result, tuple) and len(register_result) == 2:
                    result, status_code = register_result
                else:
                    result, status_code = {'error': str(register_result)}, 500
                if status_code == 201:
                    flash('Pendaftaran berhasil! Silakan login.', 'success')
                    return redirect(url_for('login'))
                else:
                    error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
                    flash(f'Gagal mendaftarkan user: {error_msg}', 'error')
            except Exception as e:
                flash(f'Gagal mendaftarkan user: {e}', 'error')
        else:
            flash('Database tidak tersedia.', 'error')
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Proses logout"""
    AuthManager.logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    """Halaman profil user"""
    current_user = AuthManager.get_current_user()
    if not current_user:
        return redirect(url_for('login'))
    activity = {'purchases': [], 'views': []}
    order_history = []
    if DB_AVAILABLE:
        try:
            activity = UserActivityTracker.get_user_activity(current_user['user_id'])
            # Ambil riwayat pesanan user (status selesai)
            order_history = list(mongodb.db.orders.find({
                'user_id': current_user['user_id'],
                'status': 'selesai'
            }).sort('created_at', -1))
        except Exception as e:
            print(f"Warning: could not get user activity: {e}")
            flash(f'Gagal memuat aktivitas pengguna: {e}', 'warning')
    return render_template('profile.html', user=current_user, activity=activity, order_history=order_history)

@app.route('/about')
def about():
    """Halaman tentang"""
    return render_template('about.html', user=AuthManager.get_current_user())

@app.route('/contact')
def contact():
    """Halaman kontak"""
    return render_template('contact.html', user=AuthManager.get_current_user())

@app.route('/cart')
@login_required
def view_cart():
    """Halaman keranjang belanja"""
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    if DB_AVAILABLE and cart:
        for product_id, item in cart.items():
            product = mongodb.db.products.find_one({'id': int(product_id)})
            if product:
                quantity = item.get('quantity', 1)
                subtotal = product['price'] * quantity
                total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
    return render_template('cart.html', cart_items=cart_items, total=total, user=AuthManager.get_current_user())

@app.route('/cart/checkout', methods=['GET', 'POST'])
@login_required
def checkout_cart():
    """Halaman checkout sederhana"""
    cart = session.get('cart', {})
    current_user = AuthManager.get_current_user()
    if request.method == 'POST':
        if DB_AVAILABLE and cart and current_user:
            try:
                # Siapkan data pesanan
                order_items = []
                total = 0
                for product_id, item in cart.items():
                    product = mongodb.db.products.find_one({'id': int(product_id)})
                    if product:
                        quantity = item.get('quantity', 1)
                        subtotal = product['price'] * quantity
                        total += subtotal
                        order_items.append({
                            'product_id': product['id'],
                            'name': product['name'],
                            'price': product['price'],
                            'quantity': quantity,
                            'subtotal': subtotal
                        })
                order_doc = {
                    'user_id': current_user['user_id'],
                    'user_name': current_user.get('name', ''),
                    'items': order_items,
                    'total': total,
                    'status': 'pending',
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                mongodb.db.orders.insert_one(order_doc)
                session['cart'] = {}
                flash('Checkout berhasil! Pesanan Anda sedang diproses admin.', 'success')
                return redirect(url_for('home'))
            except Exception as e:
                flash(f'Gagal menyimpan pesanan: {e}', 'error')
                return redirect(url_for('view_cart'))
        else:
            # Proses checkout: kosongkan keranjang
            session['cart'] = {}
            flash('Checkout berhasil! Terima kasih sudah berbelanja.', 'success')
            return redirect(url_for('home'))
    cart_items = []
    total = 0
    if DB_AVAILABLE and cart:
        for product_id, item in cart.items():
            product = mongodb.db.products.find_one({'id': int(product_id)})
            if product:
                quantity = item.get('quantity', 1)
                subtotal = product['price'] * quantity
                total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
    return render_template('checkout.html', cart_items=cart_items, total=total, user=AuthManager.get_current_user())

@app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
@login_required
def edit_product(product_id):
    if not DB_AVAILABLE:
        flash('Database tidak tersedia.', 'error')
        return redirect(url_for('home'))
    products_collection = mongodb.get_collection('products')
    product = products_collection.find_one({'id': product_id})
    if not product:
        flash('Produk tidak ditemukan.', 'error')
        return redirect(url_for('home'))
    if request.method == 'POST':
        try:
            form_name = request.form.get('name')
            form_category = request.form.get('category')
            form_description = request.form.get('description')
            form_price = request.form.get('price')
            form_tags = request.form.get('tags')
            image_url = product.get('image')
            if 'image_file' in request.files:
                file = request.files['image_file']
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                    upload_path = os.path.join(app.config['UPLOAD_FOLDER'])
                    if not os.path.exists(upload_path):
                        os.makedirs(upload_path)
                    file.save(os.path.join(upload_path, filename))
                    image_url = url_for('static', filename=f'uploads/{filename}')
            try:
                price = int(form_price) if form_price is not None else 0
            except (ValueError, TypeError):
                price = 0
            tags = [tag.strip() for tag in form_tags.split(',')] if form_tags else []
            update_doc = {
                'name': form_name or '',
                'category': form_category or '',
                'description': form_description or '',
                'price': price,
                'tags': tags,
                'image': image_url,
                'updated_at': datetime.now(),
            }
            products_collection.update_one({'id': product_id}, {'$set': update_doc})
            neo4j_db.create_product_node(str(product_id), update_doc)
            flash('Produk berhasil diperbarui!', 'success')
            return redirect(url_for('product_detail', product_id=product_id))
        except Exception as e:
            flash(f'Gagal memperbarui produk: {e}', 'error')
            return render_template('add_product.html', product=product, user=AuthManager.get_current_user(), edit_mode=True)
    return render_template('add_product.html', product=product, user=AuthManager.get_current_user(), edit_mode=True)

@app.route('/product/<int:product_id>/delete', methods=['POST'])
@admin_required
@login_required
def delete_product(product_id):
    if not DB_AVAILABLE:
        flash('Database tidak tersedia.', 'error')
        return redirect(url_for('home'))
    products_collection = mongodb.get_collection('products')
    product = products_collection.find_one({'id': product_id})
    if not product:
        flash('Produk tidak ditemukan.', 'error')
        return redirect(url_for('home'))
    products_collection.delete_one({'id': product_id})
    neo4j_db.delete_product_node(str(product_id))
    flash('Produk berhasil dihapus.', 'success')
    return redirect(url_for('home'))

@app.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        session['cart'] = cart
        flash('Produk dihapus dari keranjang.', 'success')
    else:
        flash('Produk tidak ditemukan di keranjang.', 'warning')
    return redirect(url_for('view_cart'))

# === API Endpoints ===

@app.route('/api/products')
def api_products():
    """API untuk mendapatkan data produk"""
    if DB_AVAILABLE:
        try:
            all_products = list(mongodb.db.products.find().sort('name', 1))
            return jsonify(all_products)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify([])

@app.route('/api/search')
def search_products():
    """API untuk mencari produk"""
    query = request.args.get('q', '').strip()
    print(f"[DEBUG] Search query: '{query}'")
    if DB_AVAILABLE:
        try:
            all_products = list(mongodb.db.products.find().sort('name', 1))
            print(f"[DEBUG] All products fetched: {len(all_products)}")
            if query:
                filtered = []
                for p in all_products:
                    name = p.get('name', '')
                    desc = p.get('description', '')
                    if (isinstance(name, str) and query.lower() in name.lower()) or \
                       (isinstance(desc, str) and query.lower() in desc.lower()):
                        filtered.append(p)
                print(f"[DEBUG] Products after filtering: {len(filtered)}")
                for p in filtered:
                    if '_id' in p and isinstance(p['_id'], ObjectId):
                        p['_id'] = str(p['_id'])
                return jsonify(filtered)
            else:
                for p in all_products:
                    if '_id' in p and isinstance(p['_id'], ObjectId):
                        p['_id'] = str(p['_id'])
                return jsonify(all_products)
        except Exception as e:
            print(f"[ERROR] Search exception: {e}")
            # Always return a list, even on error
            return jsonify([])
    print("[ERROR] DB not available")
    return jsonify([])

@app.route('/api/purchase', methods=['POST'])
@login_required
def api_purchase():
    """API untuk memproses pembelian"""
    current_user = AuthManager.get_current_user()
    if not current_user:
        return jsonify({'error': 'User not logged in'}), 401
    if DB_AVAILABLE:
        data = request.json
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid request data'}), 400
        product_id = data.get('product_id')
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400
        # Validasi produk benar-benar ada
        product = mongodb.db.products.find_one({'id': int(product_id)})
        if not product:
            return jsonify({'error': 'Produk tidak ditemukan'}), 404
        try:
            UserActivityTracker.track_purchase(current_user['user_id'], str(product_id), data)
            return jsonify({'message': f'Pembelian produk {product_id} berhasil dicatat.'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'message': 'Pembelian dicatat (dummy).'})

@app.route('/api/user/preferences', methods=['GET', 'POST'])
@login_required
def api_user_preferences():
    current_user = AuthManager.get_current_user()
    if not current_user: return jsonify({'error': 'Authentication required'}), 401
    user_id = current_user.get('user_id')
    
    if request.method == 'POST' and DB_AVAILABLE:
        prefs = request.json
        mongodb.save_user_preference(user_id, prefs)
        return jsonify({'message': 'Preferensi disimpan'})
    elif request.method == 'GET' and DB_AVAILABLE:
        prefs = mongodb.get_user_preferences(user_id)
        return jsonify(prefs if prefs else {})
    return jsonify({})

@app.route('/api/user/activity')
@login_required
def api_user_activity():
    current_user = AuthManager.get_current_user()
    if not current_user: return jsonify({'error': 'Authentication required'}), 401
    
    if DB_AVAILABLE:
        activity = UserActivityTracker.get_user_activity(current_user.get('user_id'))
        return jsonify(activity)
    return jsonify({})

@app.route('/api/recommendations')
@login_required
def api_recommendations():
    current_user = AuthManager.get_current_user()
    if not current_user: return jsonify({'error': 'Authentication required'}), 401

    if DB_AVAILABLE:
        try:
            recs = neo4j_db.get_user_recommendations(current_user.get('user_id'))
            return jsonify(recs)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify([])

@app.route('/api/product/<int:product_id>/like', methods=['POST'])
@login_required
def api_like_product(product_id):
    current_user = AuthManager.get_current_user()
    if not current_user: return jsonify({'error': 'User not found'}), 404
    if DB_AVAILABLE:
        try:
            product = mongodb.db.products.find_one({'id': product_id})
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            UserActivityTracker.track_like(current_user['user_id'], str(product_id), {'product_name': product['name']})
            return jsonify({'message': 'Product liked successfully'})
        except Exception as e:
            print(f"Error liking product: {e}")
            return jsonify({'error': 'Could not process like'}), 500
    return jsonify({'error': 'Database not available'}), 503

@app.route('/api/product/<int:product_id>/add_to_cart', methods=['POST'])
@login_required
def api_add_to_cart(product_id):
    current_user = AuthManager.get_current_user()
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    if DB_AVAILABLE:
        try:
            product = mongodb.db.products.find_one({'id': product_id})
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            # Simpan ke session keranjang
            cart = session.get('cart', {})
            if str(product_id) in cart:
                cart[str(product_id)]['quantity'] += 1
            else:
                cart[str(product_id)] = {'quantity': 1}
            session['cart'] = cart
            UserActivityTracker.track_add_to_cart(current_user['user_id'], str(product_id), {'product_name': product['name'], 'quantity': cart[str(product_id)]['quantity']})
            return jsonify({'message': 'Product added to cart successfully'})
        except Exception as e:
            print(f"Error adding to cart: {e}")
            return jsonify({'error': 'Could not process add to cart'}), 500
    return jsonify({'error': 'Database not available'}), 503

@app.route('/admin/orders')
@admin_required
@login_required
def admin_orders():
    if not DB_AVAILABLE:
        flash('Database tidak tersedia.', 'error')
        return redirect(url_for('home'))
    orders = list(mongodb.db.orders.find().sort('created_at', -1))
    return render_template('admin_orders.html', orders=orders, user=AuthManager.get_current_user())

@app.route('/admin/orders/<order_id>', methods=['GET', 'POST'])
@admin_required
@login_required
def admin_order_detail(order_id):
    if not DB_AVAILABLE:
        flash('Database tidak tersedia.', 'error')
        return redirect(url_for('admin_orders'))
    from bson import ObjectId
    order = mongodb.db.orders.find_one({'_id': ObjectId(order_id)})
    if not order:
        flash('Pesanan tidak ditemukan.', 'error')
        return redirect(url_for('admin_orders'))
    if request.method == 'POST':
        new_status = request.form.get('status')
        if new_status:
            mongodb.db.orders.update_one({'_id': ObjectId(order_id)}, {'$set': {'status': new_status, 'updated_at': datetime.now()}})
            flash('Status pesanan diperbarui.', 'success')
            return redirect(url_for('admin_order_detail', order_id=order_id))
    return render_template('admin_order_detail.html', order=order, user=AuthManager.get_current_user())

@app.route('/admin/orders/<order_id>/selesai', methods=['POST'])
@admin_required
@login_required
def admin_order_selesai(order_id):
    if not DB_AVAILABLE:
        flash('Database tidak tersedia.', 'error')
        return redirect(url_for('admin_orders'))
    from bson import ObjectId
    mongodb.db.orders.update_one({'_id': ObjectId(order_id)}, {'$set': {'status': 'selesai', 'updated_at': datetime.now()}})
    flash('Status pesanan diubah menjadi selesai.', 'success')
    return redirect(url_for('admin_orders'))

if __name__ == '__main__':
    if not os.path.exists('instance'):
        os.makedirs('instance')
    app.run(debug=False, port=5001) 