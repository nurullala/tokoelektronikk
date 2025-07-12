"""
Modul database untuk koneksi MongoDB dan Neo4j
"""

from pymongo import MongoClient
from neo4j import GraphDatabase
from datetime import datetime
import uuid
from config import Config

class MongoDB:
    """Kelas untuk mengelola koneksi dan operasi MongoDB"""
    
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.MONGODB_DB]
        
    def get_collection(self, collection_name):
        """Mendapatkan collection MongoDB"""
        return self.db[collection_name]
    
    def create_user(self, user_data):
        """Membuat user baru"""
        users = self.get_collection('users')
        user_data['user_id'] = str(uuid.uuid4())
        user_data['created_at'] = datetime.now()
        user_data['updated_at'] = datetime.now()
        result = users.insert_one(user_data)
        return user_data['user_id']
    
    def get_user_by_id(self, user_id):
        """Mendapatkan user berdasarkan ID"""
        users = self.get_collection('users')
        return users.find_one({'user_id': user_id})
    
    def get_user_by_email(self, email):
        """Mendapatkan user berdasarkan email"""
        users = self.get_collection('users')
        return users.find_one({'email': email})
    
    def update_user(self, user_id, update_data):
        """Update data user"""
        users = self.get_collection('users')
        update_data['updated_at'] = datetime.now()
        return users.update_one(
            {'user_id': user_id},
            {'$set': update_data}
        )
    
    def save_purchase_history(self, user_id, purchase_data):
        """Menyimpan riwayat pembelian"""
        purchases = self.get_collection('purchases')
        purchase_data['user_id'] = user_id
        purchase_data['purchase_id'] = str(uuid.uuid4())
        purchase_data['purchase_date'] = datetime.now()
        return purchases.insert_one(purchase_data)
    
    def get_purchase_history(self, user_id):
        """Mendapatkan riwayat pembelian user"""
        purchases = self.get_collection('purchases')
        return list(purchases.find({'user_id': user_id}).sort('purchase_date', -1))
    
    def save_product_view(self, user_id, product_id, view_data=None):
        """Menyimpan data produk yang dilihat"""
        views = self.get_collection('product_views')
        view_data = view_data or {}
        view_data.update({
            'user_id': user_id,
            'product_id': product_id,
            'view_id': str(uuid.uuid4()),
            'viewed_at': datetime.now()
        })
        return views.insert_one(view_data)
    
    def get_product_views(self, user_id, limit=10):
        """Mendapatkan produk yang pernah dilihat user"""
        views = self.get_collection('product_views')
        return list(views.find({'user_id': user_id}).sort('viewed_at', -1).limit(limit))
    
    def save_user_preference(self, user_id, preference_data):
        """Menyimpan preferensi user"""
        preferences = self.get_collection('user_preferences')
        preference_data['user_id'] = user_id
        preference_data['updated_at'] = datetime.now()
        
        # Update jika sudah ada, insert jika belum ada
        return preferences.update_one(
            {'user_id': user_id},
            {'$set': preference_data},
            upsert=True
        )
    
    def get_user_preferences(self, user_id):
        """Mendapatkan preferensi user"""
        preferences = self.get_collection('user_preferences')
        return preferences.find_one({'user_id': user_id})

    def save_interaction(self, user_id, product_id, interaction_type, interaction_data=None):
        """Menyimpan interaksi user dengan produk"""
        interactions = self.get_collection('user_interactions')
        interaction_data = interaction_data or {}
        interaction_data.update({
            'user_id': user_id,
            'product_id': product_id,
            'interaction_type': interaction_type,
            'interaction_id': str(uuid.uuid4()),
            'interacted_at': datetime.now()
        })
        return interactions.insert_one(interaction_data)

class Neo4jDB:
    """Kelas untuk mengelola koneksi dan operasi Neo4j"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )
    
    def close(self):
        """Menutup koneksi Neo4j"""
        self.driver.close()
    
    def create_user_node(self, user_id, user_data):
        """Membuat node user di Neo4j"""
        with self.driver.session(database=Config.NEO4J_DATABASE) as session:
            session.run("""
                CREATE (u:User {
                    user_id: $user_id,
                    name: $name,
                    email: $email,
                    created_at: datetime()
                })
            """, user_id=user_id, name=user_data.get('name'), email=user_data.get('email'))
    
    def create_product_node(self, product_id, product_data):
        """Membuat node product di Neo4j"""
        with self.driver.session(database=Config.NEO4J_DATABASE) as session:
            session.run("""
                MERGE (p:Product {product_id: $product_id})
                SET p.name = $name,
                    p.category = $category,
                    p.tags = $tags
            """, product_id=product_id, 
                 name=product_data.get('name'), 
                 category=product_data.get('category'),
                 tags=product_data.get('tags', []))
    
    def create_viewed_relationship(self, user_id, product_id):
        """Membuat relasi VIEWED antara user dan product"""
        with self.driver.session(database=Config.NEO4J_DATABASE) as session:
            session.run("""
                MATCH (u:User {user_id: $user_id})
                MATCH (p:Product {product_id: $product_id})
                MERGE (u)-[r:VIEWED {viewed_at: datetime()}]->(p)
                MERGE (u)-[r:IN_CART {added_at: datetime()}]->(p)
            """, user_id=user_id, product_id=product_id)
    
    def create_purchased_relationship(self, user_id, product_id, purchase_data):
        """Membuat relasi PURCHASED antara user dan product"""
        with self.driver.session(database=Config.NEO4J_DATABASE) as session:
            session.run("""
                MATCH (u:User {user_id: $user_id})
                MATCH (p:Product {product_id: $product_id})
                MERGE (u)-[r:PURCHASED {
                    purchase_id: $purchase_id,
                    quantity: $quantity,
                    price: $price,
                    purchased_at: datetime()
                }]->(p)
            """, user_id=user_id, product_id=product_id, 
                 purchase_id=purchase_data.get('purchase_id'),
                 quantity=purchase_data.get('quantity', 1),
                 price=purchase_data.get('price'))
    
    def create_likes_relationship(self, user_id, product_id):
        """Membuat relasi LIKES antara user dan product"""
        with self.driver.session(database=Config.NEO4J_DATABASE) as session:
            session.run("""
                MATCH (u:User {user_id: $user_id})
                MATCH (p:Product {product_id: $product_id})
                MERGE (u)-[r:LIKES {liked_at: datetime()}]->(p)
            """, user_id=user_id, product_id=product_id)
    
    def create_in_cart_relationship(self, user_id, product_id):
        """Membuat relasi IN_CART antara user dan product"""
        with self.driver.session(database=Config.NEO4J_DATABASE) as session:
            session.run("""
                MATCH (u:User {user_id: $user_id})
                MATCH (p:Product {product_id: $product_id})
                MERGE (u)-[r:IN_CART {added_at: datetime()}]->(p)
            """, user_id=user_id, product_id=product_id)
    
    def get_user_recommendations(self, user_id, limit=5):
        """Mendapatkan rekomendasi produk berdasarkan preferensi user"""
        with self.driver.session(database=Config.NEO4J_DATABASE) as session:
            result = session.run("""
                MATCH (u:User {user_id: $user_id})-[r1:VIEWED]->(p1:Product)
                MATCH (p1)<-[r2:VIEWED]-(other:User)
                MATCH (other)-[r3:VIEWED]->(p2:Product)
                WHERE p2 <> p1 AND NOT (u)-[:VIEWED]->(p2)
                RETURN p2.name as product_name, p2.product_id as product_id, 
                       count(r3) as view_count
                ORDER BY view_count DESC
                LIMIT $limit
            """, user_id=user_id, limit=limit)
            return [record.data() for record in result]
    
    def get_similar_products(self, product_id, limit=5):
        """Mendapatkan produk yang mirip berdasarkan user yang sama"""
        with self.driver.session(database=Config.NEO4J_DATABASE) as session:
            result = session.run("""
                MATCH (p1:Product {product_id: $product_id})<-[:VIEWED]-(u:User)-[:VIEWED]->(p2:Product)
                WHERE p2 <> p1
                RETURN p2.name as product_name, p2.product_id as product_id,
                       count(u) as common_users
                ORDER BY common_users DESC
                LIMIT $limit
            """, product_id=product_id, limit=limit)
            return [record.data() for record in result]
    
    def get_frequently_bought_together(self, product_id, limit=5):
        """
        Mendapatkan produk yang sering dibeli bersama dengan produk tertentu.
        Contoh: Orang yang membeli produk A juga membeli produk B.
        """
        with self.driver.session(database=Config.NEO4J_DATABASE) as session:
            result = session.run("""
                MATCH (p1:Product {product_id: $product_id})<-[:PURCHASED]-(u:User)-[:PURCHASED]->(p2:Product)
                WHERE id(p1) < id(p2)
                RETURN p2.product_id AS id, p2.name AS name, p2.image as image, p2.price as price, COUNT(*) AS frequency
                ORDER BY frequency DESC
                LIMIT $limit
            """, product_id=product_id, limit=limit)
            return [dict(record) for record in result]

    def get_content_based_similar_products(self, product_id, limit=5):
        """
        Mendapatkan produk serupa berdasarkan kategori dan tag yang sama.
        """
        with self.driver.session(database=Config.NEO4J_DATABASE) as session:
            result = session.run("""
                MATCH (p1:Product {product_id: $product_id})
                MATCH (p2:Product)
                WHERE p1 <> p2 AND p1.category = p2.category
                WITH p1, p2, 
                     size([tag IN p1.tags WHERE tag IN p2.tags]) AS shared_tags
                WHERE shared_tags > 0
                RETURN p2.product_id AS id, p2.name AS name, p2.image as image, p2.price as price, shared_tags
                ORDER BY shared_tags DESC
                LIMIT $limit
            """, product_id=product_id, limit=limit)
            return [dict(record) for record in result]

    def delete_product_node(self, product_id):
        """Menghapus node produk dan semua relasinya di Neo4j"""
        with self.driver.session(database=Config.NEO4J_DATABASE) as session:
            session.run("""
                MATCH (p:Product {product_id: $product_id})
                DETACH DELETE p
            """, product_id=product_id)

# Instance database
mongodb = MongoDB()
neo4j_db = Neo4jDB() 