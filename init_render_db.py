#!/usr/bin/env python3
"""
Script d'initialisation de base de données pour Render
Gère ChromaDB et PostgreSQL selon l'environnement
"""

import os
import sys
import time
from dotenv import load_dotenv
from database_config import get_database_config, create_chroma_client, init_postgres_tables
from rag_system import RAGSystem
from compendium_rag import CompendiumRAG

def check_environment():
    """
    Vérifie l'environnement et les variables nécessaires
    """
    print("🔍 Vérification de l'environnement...")
    
    # Charger les variables d'environnement
    load_dotenv()
    
    # Vérifier la clé API OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Erreur: OPENAI_API_KEY n'est pas défini")
        return None
    
    # Vérifier si on est sur Render
    is_render = os.getenv('RENDER') == 'true'
    database_url = os.getenv('DATABASE_URL')
    
    print(f"🌐 Environnement: {'Render' if is_render else 'Local'}")
    print(f"🗄️  PostgreSQL: {'Disponible' if database_url else 'Non configuré'}")
    
    return {
        'openai_api_key': openai_api_key,
        'is_render': is_render,
        'database_url': database_url
    }

def init_postgres_if_available():
    """
    Initialise PostgreSQL si disponible
    """
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ℹ️  PostgreSQL non configuré, utilisation ChromaDB local")
        return True
    
    print("🐘 Initialisation PostgreSQL...")
    
    # Attendre que PostgreSQL soit disponible (important sur Render)
    max_retries = 30
    for attempt in range(max_retries):
        try:
            success = init_postgres_tables()
            if success:
                print("✅ PostgreSQL initialisé avec succès")
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⏳ Tentative {attempt + 1}/{max_retries} - Attente PostgreSQL...")
                time.sleep(2)
            else:
                print(f"❌ Échec initialisation PostgreSQL après {max_retries} tentatives: {e}")
                return False
    
    return False

def build_main_database(env_config):
    """
    Construit la base de données principale (documents médicaux)
    """
    print("🏗️  Construction de la base de données principale...")
    
    try:
        # Créer le système RAG
        rag_system = RAGSystem(openai_api_key=env_config['openai_api_key'])
        
        # Vérifier si la base existe déjà
        doc_count = rag_system.collection.count()
        if doc_count > 0:
            print(f"✅ Base de données principale déjà construite ({doc_count} documents)")
            return True
        
        # Vérifier les données source
        if not os.path.exists("data"):
            print("❌ Erreur: Le dossier 'data' n'existe pas")
            return False
        
        md_files = [f for f in os.listdir("data") if f.endswith(".md")]
        if not md_files:
            print("❌ Erreur: Aucun fichier .md trouvé dans le dossier 'data'")
            return False
        
        print(f"📁 Fichiers trouvés: {', '.join(md_files)}")
        
        # Construire la base de données
        rag_system.build_database()
        
        final_count = rag_system.collection.count()
        print(f"✅ Base de données principale construite ({final_count} documents)")
        return True
        
    except Exception as e:
        print(f"❌ Erreur construction base principale: {e}")
        return False

def build_compendium_database(env_config):
    """
    Construit la base de données du compendium belge
    """
    print("🏗️  Construction de la base de données compendium...")
    
    try:
        # Créer le système Compendium RAG
        compendium_rag = CompendiumRAG(openai_api_key=env_config['openai_api_key'])
        
        # Vérifier si la base existe déjà
        analysis_count = compendium_rag.collection.count()
        if analysis_count > 0:
            print(f"✅ Base de données compendium déjà construite ({analysis_count} analyses)")
            return True
        
        # Vérifier les données source
        if not os.path.exists("data/compendium_data"):
            print("❌ Erreur: Le dossier 'data/compendium_data' n'existe pas")
            return False
        
        json_files = [f for f in os.listdir("data/compendium_data") if f.endswith(".json")]
        if not json_files:
            print("❌ Erreur: Aucun fichier .json trouvé dans le dossier 'data/compendium_data'")
            return False
        
        print(f"📁 Fichiers compendium trouvés: {', '.join(json_files)}")
        
        # Construire la base de données
        compendium_rag.build_database()
        
        final_count = compendium_rag.collection.count()
        print(f"✅ Base de données compendium construite ({final_count} analyses)")
        return True
        
    except Exception as e:
        print(f"❌ Erreur construction base compendium: {e}")
        return False

def main():
    """
    Point d'entrée principal
    """
    print("🚀 Initialisation des bases de données pour Render")
    print("=" * 60)
    
    # Vérifier l'environnement
    env_config = check_environment()
    if not env_config:
        sys.exit(1)
    
    # Initialiser PostgreSQL si disponible
    if not init_postgres_if_available():
        print("⚠️  Continuer sans PostgreSQL...")
    
    # Construire les bases de données
    success_main = build_main_database(env_config)
    success_compendium = build_compendium_database(env_config)
    
    if success_main and success_compendium:
        print("\n✅ Toutes les bases de données ont été initialisées avec succès!")
        print("🚀 L'application est prête à démarrer")
        sys.exit(0)
    else:
        print("\n❌ Erreur lors de l'initialisation des bases de données")
        sys.exit(1)

if __name__ == "__main__":
    main() 