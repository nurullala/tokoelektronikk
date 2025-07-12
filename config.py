import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Konfigurasi aplikasi"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    MONGODB_DB = os.getenv('MONGODB_DB', 'tokoelektronik')
    
    # Neo4j Configuration
    NEO4J_URI = 'bolt://127.0.0.1:7687'
    NEO4J_USER = 'neo4j'
    NEO4J_PASSWORD = 'Aku12345678'
    NEO4J_DATABASE = 'neo4j'
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour 