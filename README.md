# Assistant Médical Français - MVP

## 🧪 Description
Assistant intelligent pour biologiste médical en laboratoire clinique, utilisant un système RAG (Retrieval Augmented Generation) pour répondre aux questions cliniques et administratives en français.

## 🚀 Installation

1. Clonez le projet et naviguez dans le dossier
2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurez votre clé API OpenAI :
```bash
cp .env.example .env
# Éditez .env et ajoutez votre clé OpenAI
```

4. Initialisez la base de données vectorielle :
```bash
python setup_database.py
```

5. Lancez l'application :
```bash
python app.py
```

## 🎯 Utilisation
- Accédez à `http://localhost:5000`
- Posez vos questions en français dans le champ de saisie
- L'assistant répondra en citant ses sources

## 📁 Structure
- `data/` : Documents synthétiques en français
- `app.py` : Application Flask principale
- `rag_system.py` : Système RAG avec embeddings
- `templates/` : Interface web
- `static/` : CSS et JavaScript

## 🔧 Fonctionnalités
- Questions/réponses en français
- Citations des sources
- Interface simple et intuitive
- Données synthétiques réalistes 