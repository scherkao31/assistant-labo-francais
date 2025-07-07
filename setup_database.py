#!/usr/bin/env python3
"""
Script pour initialiser la base de données vectorielle
"""

import os
from dotenv import load_dotenv
from rag_system import RAGSystem

def main():
    """
    Initialise la base de données vectorielle avec les documents
    """
    # Charger les variables d'environnement
    load_dotenv()
    
    # Vérifier la clé API
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Erreur: OPENAI_API_KEY n'est pas défini")
        print("Créez un fichier .env avec votre clé API OpenAI")
        return
    
    print("🚀 Initialisation de la base de données vectorielle...")
    
    # Créer le système RAG
    rag_system = RAGSystem(openai_api_key=openai_api_key)
    
    # Vérifier que le dossier data existe
    if not os.path.exists("data"):
        print("❌ Erreur: Le dossier 'data' n'existe pas")
        return
    
    # Lister les fichiers
    md_files = [f for f in os.listdir("data") if f.endswith(".md")]
    if not md_files:
        print("❌ Erreur: Aucun fichier .md trouvé dans le dossier 'data'")
        return
    
    print(f"📁 Fichiers trouvés: {', '.join(md_files)}")
    
    # Construire la base de données
    try:
        rag_system.build_database()
        print("✅ Base de données vectorielle créée avec succès!")
        print("Vous pouvez maintenant lancer l'application avec: python app.py")
        
    except Exception as e:
        print(f"❌ Erreur lors de la construction: {e}")

if __name__ == "__main__":
    main() 