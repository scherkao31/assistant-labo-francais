"""
Configuration de base de données pour l'assistant médical
Supporte ChromaDB local et PostgreSQL pour la production
"""

import os
import chromadb
from chromadb.config import Settings
from urllib.parse import urlparse

def get_database_config():
    """
    Retourne la configuration de base de données selon l'environnement
    """
    # Vérifier si on est sur Render avec PostgreSQL
    database_url = os.getenv('DATABASE_URL')
    is_render = os.getenv('RENDER') == 'true'
    
    if database_url and is_render:
        # Configuration PostgreSQL pour Render
        return get_postgres_config(database_url)
    else:
        # Configuration ChromaDB locale
        return get_local_config()

def get_postgres_config(database_url):
    """
    Configuration PostgreSQL pour la production
    """
    parsed = urlparse(database_url)
    
    # Configuration ChromaDB avec stockage temporaire
    # ChromaDB 0.4.22 ne supporte pas directement PostgreSQL comme backend
    # On utilise le stockage temporaire avec métadonnées en PostgreSQL
    settings = Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
    
    return {
        'type': 'postgres',
        'settings': settings,
        'connection_string': database_url,
        'host': parsed.hostname,
        'port': parsed.port,
        'database': parsed.path[1:] if parsed.path else 'postgres',  # Enlever le '/' initial
        'username': parsed.username,
        'password': parsed.password,
        'temp_chroma_path': '/tmp/chroma_db',
        'temp_compendium_path': '/tmp/compendium_chroma_db'
    }

def get_local_config():
    """
    Configuration locale pour le développement
    """
    chroma_path = os.getenv('CHROMA_DB_PATH', './chroma_db')
    compendium_path = os.getenv('COMPENDIUM_CHROMA_PATH', './compendium_chroma_db')
    
    # Sur Render, utiliser un répertoire temporaire si nécessaire
    if not os.access(os.path.dirname(chroma_path) or '.', os.W_OK):
        chroma_path = '/tmp/chroma_db'
    
    if not os.access(os.path.dirname(compendium_path) or '.', os.W_OK):
        compendium_path = '/tmp/compendium_chroma_db'
    
    settings = Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
    
    return {
        'type': 'local',
        'settings': settings,
        'chroma_path': chroma_path,
        'compendium_path': compendium_path
    }

def create_chroma_client(config, db_type='main'):
    """
    Crée un client ChromaDB selon la configuration
    """
    if config['type'] == 'postgres':
        # Utiliser le stockage temporaire pour ChromaDB
        path = config['temp_chroma_path'] if db_type == 'main' else config['temp_compendium_path']
        return chromadb.PersistentClient(
            path=path,
            settings=config['settings']
        )
    else:
        # Configuration locale
        path = config['chroma_path'] if db_type == 'main' else config['compendium_path']
        return chromadb.PersistentClient(
            path=path,
            settings=config['settings']
        )

def get_postgres_connection():
    """
    Retourne une connexion PostgreSQL pour les opérations personnalisées
    """
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        return None
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        parsed = urlparse(database_url)
        
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:] if parsed.path else 'postgres',
            user=parsed.username,
            password=parsed.password
        )
        return conn
    except Exception as e:
        print(f"Erreur connexion PostgreSQL: {e}")
        return None

def init_postgres_tables():
    """
    Initialise les tables PostgreSQL pour stocker les métadonnées
    """
    conn = get_postgres_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Table pour les métadonnées des documents principaux
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_documents (
                id SERIAL PRIMARY KEY,
                chunk_id VARCHAR(255) UNIQUE NOT NULL,
                filename VARCHAR(255) NOT NULL,
                title TEXT,
                content TEXT,
                embedding_stored BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table pour les analyses du compendium
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compendium_analyses (
                id SERIAL PRIMARY KEY,
                analysis_id VARCHAR(255) UNIQUE NOT NULL,
                titre TEXT NOT NULL,
                code VARCHAR(100),
                lien TEXT,
                laboratoire VARCHAR(255),
                description TEXT,
                indication TEXT,
                prelevement TEXT,
                technique TEXT,
                reference TEXT,
                embedding_stored BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table pour les statistiques et métadonnées système
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metadata (
                id SERIAL PRIMARY KEY,
                key VARCHAR(255) UNIQUE NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index pour les recherches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_filename ON rag_documents(filename)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_chunk_id ON rag_documents(chunk_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_laboratoire ON compendium_analyses(laboratoire)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_titre ON compendium_analyses(titre)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_code ON compendium_analyses(code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_metadata_key ON system_metadata(key)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Tables PostgreSQL initialisées")
        return True
        
    except Exception as e:
        print(f"❌ Erreur initialisation PostgreSQL: {e}")
        if conn:
            conn.close()
        return False

def store_system_metadata(key, value):
    """
    Stocke une métadonnée système en PostgreSQL
    """
    conn = get_postgres_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO system_metadata (key, value, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = CURRENT_TIMESTAMP
        """, (key, value))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur stockage métadonnée: {e}")
        if conn:
            conn.close()
        return False

def get_system_metadata(key):
    """
    Récupère une métadonnée système depuis PostgreSQL
    """
    conn = get_postgres_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_metadata WHERE key = %s", (key,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Erreur récupération métadonnée: {e}")
        if conn:
            conn.close()
        return None 