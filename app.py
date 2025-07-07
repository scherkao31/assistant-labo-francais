#!/usr/bin/env python3
"""
Application Flask pour l'assistant médical français
"""

import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from rag_system import RAGSystem

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Initialiser le système RAG
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("❌ Erreur: OPENAI_API_KEY n'est pas défini")
    print("Créez un fichier .env avec votre clé API OpenAI")
    exit(1)

rag_system = RAGSystem(openai_api_key=openai_api_key)

@app.route('/')
def index():
    """
    Page d'accueil
    """
    return render_template('index.html')

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """
    Endpoint pour poser une question
    """
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'error': 'Question manquante',
                'success': False
            }), 400
        
        question = data['question'].strip()
        
        if not question:
            return jsonify({
                'error': 'Question vide',
                'success': False
            }), 400
        
        # Traiter la question
        result = rag_system.ask_question(question)
        
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'sources': result['sources'],
            'query': result['query']
        })
        
    except Exception as e:
        print(f"Erreur lors du traitement: {e}")
        return jsonify({
            'error': f'Erreur serveur: {str(e)}',
            'success': False
        }), 500

@app.route('/api/health')
def health_check():
    """
    Vérification de l'état de l'application
    """
    try:
        # Vérifier la base de données
        doc_count = rag_system.collection.count()
        
        return jsonify({
            'status': 'healthy',
            'database_documents': doc_count,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/sources')
def get_sources():
    """
    Récupère la liste des sources disponibles
    """
    try:
        # Récupérer les métadonnées uniques
        result = rag_system.collection.get()
        
        sources = {}
        for metadata in result['metadatas']:
            filename = metadata['filename']
            title = metadata['title']
            if filename not in sources:
                sources[filename] = {
                    'filename': filename,
                    'title': title,
                    'chunk_count': 0
                }
            sources[filename]['chunk_count'] += 1
        
        return jsonify({
            'success': True,
            'sources': list(sources.values())
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.errorhandler(404)
def not_found(error):
    """
    Gestion des erreurs 404
    """
    return jsonify({
        'error': 'Endpoint non trouvé',
        'success': False
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """
    Gestion des erreurs 500
    """
    return jsonify({
        'error': 'Erreur interne du serveur',
        'success': False
    }), 500

if __name__ == '__main__':
    # Vérifier que la base de données existe
    try:
        doc_count = rag_system.collection.count()
        if doc_count == 0:
            print("⚠️  Base de données vide, construction automatique...")
            print("🚀 Initialisation de la base de données vectorielle...")
            
            # Vérifier que le dossier data existe
            if not os.path.exists("data"):
                print("❌ Erreur: Le dossier 'data' n'existe pas")
            else:
                # Lister les fichiers
                md_files = [f for f in os.listdir("data") if f.endswith(".md")]
                if not md_files:
                    print("❌ Erreur: Aucun fichier .md trouvé dans le dossier 'data'")
                else:
                    print(f"📁 Fichiers trouvés: {', '.join(md_files)}")
                    # Construire la base de données
                    rag_system.build_database()
                    print("✅ Base de données vectorielle créée avec succès!")
        else:
            print(f"✅ Base de données chargée avec {doc_count} documents")
    except Exception as e:
        print(f"❌ Erreur de base de données: {e}")
        print("Tentative de construction de la base de données...")
        try:
            rag_system.build_database()
            print("✅ Base de données vectorielle créée avec succès!")
        except Exception as build_error:
            print(f"❌ Erreur lors de la construction: {build_error}")
    
    # Lancer l'application
    port = int(os.getenv('PORT', os.getenv('FLASK_PORT', 5000)))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"🚀 Démarrage de l'assistant médical français")
    print(f"📍 Accès: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 