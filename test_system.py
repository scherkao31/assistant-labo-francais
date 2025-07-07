#!/usr/bin/env python3
"""
Script de test pour vérifier le fonctionnement du système RAG
"""

import os
import sys
from dotenv import load_dotenv
from rag_system import RAGSystem

def test_system():
    """
    Test du système RAG
    """
    print("🧪 Test du système RAG médical français")
    print("=" * 50)
    
    # Charger les variables d'environnement
    load_dotenv()
    
    # Vérifier la clé API
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Erreur: OPENAI_API_KEY n'est pas défini")
        return False
    
    try:
        # Initialiser le système RAG
        print("🔧 Initialisation du système RAG...")
        rag_system = RAGSystem(openai_api_key=openai_api_key)
        
        # Vérifier la base de données
        doc_count = rag_system.collection.count()
        print(f"📊 Base de données: {doc_count} documents")
        
        if doc_count == 0:
            print("⚠️  Base de données vide, construction en cours...")
            rag_system.build_database()
            doc_count = rag_system.collection.count()
            print(f"📊 Base de données construite: {doc_count} documents")
        
        # Questions de test
        test_questions = [
            "Comment interpréter une sérologie CMV ?",
            "Quels sont les délais pour un hémogramme ?",
            "Que faire si un médecin demande les résultats d'un autre patient ?",
            "Quelles sont les valeurs normales de créatinine ?",
            "Procédure d'urgence pour le paludisme"
        ]
        
        print("\n🤔 Test des questions...")
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- Question {i}/5 ---")
            print(f"Q: {question}")
            
            result = rag_system.ask_question(question)
            
            if result['sources']:
                print(f"✅ Réponse générée ({len(result['sources'])} sources)")
                print(f"📝 Longueur: {len(result['answer'])} caractères")
                print(f"🔗 Sources: {[s['title'] for s in result['sources'][:2]]}")
            else:
                print("❌ Aucune source trouvée")
        
        print("\n" + "=" * 50)
        print("✅ Test terminé avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_components():
    """
    Test des composants individuels
    """
    print("\n🔍 Test des composants...")
    
    # Test d'import
    try:
        from rag_system import RAGSystem, Document
        print("✅ Import RAGSystem: OK")
    except ImportError as e:
        print(f"❌ Import RAGSystem: {e}")
        return False
    
    # Test des données
    if os.path.exists("data"):
        md_files = [f for f in os.listdir("data") if f.endswith(".md")]
        print(f"✅ Données: {len(md_files)} fichiers markdown")
        for f in md_files:
            print(f"  - {f}")
    else:
        print("❌ Dossier 'data' introuvable")
        return False
    
    # Test des dépendances
    try:
        import openai
        import chromadb
        import tiktoken
        print("✅ Dépendances: OK")
    except ImportError as e:
        print(f"❌ Dépendances: {e}")
        return False
    
    return True

def main():
    """
    Fonction principale
    """
    print("🚀 Test de l'assistant médical français")
    print("Version: MVP 1.0")
    print("=" * 50)
    
    # Test des composants
    if not test_components():
        print("❌ Échec du test des composants")
        sys.exit(1)
    
    # Test du système
    if not test_system():
        print("❌ Échec du test du système")
        sys.exit(1)
    
    print("\n🎉 Tous les tests sont passés!")
    print("🌐 Vous pouvez maintenant lancer l'application: python app.py")

if __name__ == "__main__":
    main() 