#!/usr/bin/env python3
"""
Script d'installation automatique pour l'assistant médical français
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """
    Vérifier la version de Python
    """
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou supérieur requis")
        print(f"Version actuelle: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} détecté")
    return True

def install_requirements():
    """
    Installer les dépendances
    """
    print("📦 Installation des dépendances...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        print("✅ Dépendances installées")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur d'installation: {e}")
        print("Sortie d'erreur:")
        print(e.stderr)
        return False

def create_env_file():
    """
    Créer le fichier .env
    """
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  Le fichier .env existe déjà")
        return True
    
    print("🔧 Création du fichier .env...")
    
    openai_key = input("🔑 Entrez votre clé API OpenAI: ").strip()
    
    if not openai_key:
        print("❌ Clé API OpenAI requise")
        return False
    
    env_content = f"""OPENAI_API_KEY={openai_key}
FLASK_DEBUG=True
FLASK_PORT=5000
SECRET_KEY=medical-assistant-secret-key-change-in-production
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Fichier .env créé")
        return True
    except Exception as e:
        print(f"❌ Erreur création .env: {e}")
        return False

def verify_data_files():
    """
    Vérifier les fichiers de données
    """
    print("📁 Vérification des données...")
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("❌ Dossier 'data' introuvable")
        return False
    
    md_files = list(data_dir.glob("*.md"))
    if not md_files:
        print("❌ Aucun fichier .md trouvé dans 'data'")
        return False
    
    print(f"✅ {len(md_files)} fichiers de données trouvés:")
    for f in md_files:
        print(f"  - {f.name}")
    
    return True

def initialize_database():
    """
    Initialiser la base de données
    """
    print("🗄️  Initialisation de la base de données...")
    
    try:
        subprocess.run([
            sys.executable, "setup_database.py"
        ], check=True, capture_output=True, text=True)
        print("✅ Base de données initialisée")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur initialisation base de données: {e}")
        print("Sortie d'erreur:")
        print(e.stderr)
        return False

def run_tests():
    """
    Lancer les tests
    """
    print("🧪 Lancement des tests...")
    
    try:
        subprocess.run([
            sys.executable, "test_system.py"
        ], check=True, capture_output=True, text=True)
        print("✅ Tests réussis")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur tests: {e}")
        print("Sortie d'erreur:")
        print(e.stderr)
        return False

def main():
    """
    Installation complète
    """
    print("🚀 Installation de l'Assistant Médical Français")
    print("=" * 60)
    
    steps = [
        ("Vérification Python", check_python_version),
        ("Installation dépendances", install_requirements),
        ("Configuration .env", create_env_file),
        ("Vérification données", verify_data_files),
        ("Initialisation base de données", initialize_database),
        ("Tests du système", run_tests)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ Échec: {step_name}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Installation terminée avec succès!")
    print()
    print("📍 Prochaines étapes:")
    print("1. Lancez l'application: python app.py")
    print("2. Ouvrez votre navigateur: http://localhost:5000")
    print("3. Posez vos questions en français!")
    print()
    print("🔧 Commandes utiles:")
    print("- Reconstruire la base de données: python setup_database.py")
    print("- Tester le système: python test_system.py")
    print("- Lancer l'application: python app.py")

if __name__ == "__main__":
    main() 