# 🚀 Déploiement sur Render avec PostgreSQL

## 📋 Prérequis

- Compte Render (gratuit)
- Dépôt GitHub avec votre code
- Clé API OpenAI

## 🐘 Étape 1: Créer la Base de Données PostgreSQL

### Via l'Interface Render:

1. **Connectez-vous à Render** → https://render.com
2. **Créez une nouvelle base de données**:
   - Cliquez sur "New" → "PostgreSQL"
   - **Name**: `assistant-medical-db`
   - **Database**: `assistant_medical`
   - **User**: `assistant_user`
   - **Region**: `Oregon` (ou `Frankfurt` pour l'Europe)
   - **Plan**: `Free` (1GB - suffisant pour les métadonnées)

3. **Notez les informations de connexion**:
   - **Internal Database URL**: `postgresql://...` (utilisé automatiquement)
   - **External Database URL**: Pour les connexions externes

### Via render.yaml (Recommandé):

Le fichier `render.yaml` créera automatiquement la base de données avec votre service web.

## 🌐 Étape 2: Déployer le Service Web

### Méthode 1: Via render.yaml (Automatique)

1. **Poussez le code sur GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Connectez Render à votre dépôt**:
   - Render Dashboard → "New" → "Blueprint"
   - Sélectionnez votre dépôt GitHub
   - Render détectera automatiquement le `render.yaml`

3. **Configurez les variables d'environnement**:
   - `OPENAI_API_KEY`: Votre clé API OpenAI
   - Les autres variables sont déjà configurées dans `render.yaml`

### Méthode 2: Configuration Manuelle

1. **Créez un nouveau service web**:
   - "New" → "Web Service"
   - Connectez votre dépôt GitHub
   - **Name**: `assistant-medical-belge`
   - **Environment**: `Python 3`
   - **Region**: `Oregon`
   - **Branch**: `main`

2. **Configurez les commandes**:
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && python init_render_db.py
     ```
   - **Start Command**: 
     ```bash
     python app.py
     ```

3. **Variables d'environnement**:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   FLASK_ENV=production
   FLASK_DEBUG=False
   RENDER=true
   PORT=10000
   ```

4. **Connectez la base de données**:
   - Dans les paramètres du service web
   - Section "Environment" → "Add from Database"
   - Sélectionnez votre base PostgreSQL
   - Cela ajoute automatiquement `DATABASE_URL`

## 🔧 Étape 3: Configuration Avancée

### Health Check

L'endpoint `/api/health` est configuré pour vérifier:
- État de l'application
- Connexion à la base de données
- Nombre de documents chargés

### Scaling

Pour une utilisation en production:
- Changez le plan de `free` à `starter` ou plus
- Ajustez `minInstances` et `maxInstances` selon vos besoins

### Monitoring

Render fournit automatiquement:
- Logs en temps réel
- Métriques de performance
- Alertes de santé

## 🛠️ Étape 4: Vérification du Déploiement

1. **Vérifiez les logs de build**:
   - Recherchez les messages de construction de base de données
   - Confirmez que PostgreSQL est initialisé

2. **Testez l'application**:
   ```bash
   curl https://your-app-name.onrender.com/api/health
   ```

3. **Vérifiez la base de données**:
   - Connectez-vous à PostgreSQL via l'interface Render
   - Vérifiez que les tables sont créées

## 🐛 Dépannage

### Problèmes Courants

1. **Erreur de build - OpenAI API Key**:
   - Vérifiez que `OPENAI_API_KEY` est défini
   - Assurez-vous que la clé est valide

2. **Erreur de connexion PostgreSQL**:
   - Vérifiez que la base de données est démarrée
   - Confirmez que `DATABASE_URL` est automatiquement ajouté

3. **Timeout de build**:
   - Les embeddings peuvent prendre du temps
   - Augmentez le timeout de build si nécessaire

4. **Erreur de mémoire**:
   - Le plan gratuit a des limites de mémoire
   - Considérez un upgrade pour de gros datasets

### Logs Utiles

```bash
# Vérifier les logs de build
# Dans l'interface Render → Service → Logs → Build

# Vérifier les logs d'exécution
# Dans l'interface Render → Service → Logs → Deploy
```

## 🔄 Mise à Jour

Pour mettre à jour votre déploiement:

1. **Poussez les changements**:
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```

2. **Redéploiement automatique**:
   - Render redéploie automatiquement
   - Les bases de données existantes sont préservées

## 💡 Conseils d'Optimisation

### Performance

1. **Utilisez les index PostgreSQL**:
   - Les index sont créés automatiquement
   - Optimisent les recherches de métadonnées

2. **Cache des embeddings**:
   - ChromaDB gère le cache automatiquement
   - PostgreSQL stocke les métadonnées persistantes

3. **Monitoring**:
   - Surveillez l'utilisation mémoire
   - Optimisez les requêtes si nécessaire

### Sécurité

1. **Variables d'environnement**:
   - Ne jamais commiter les clés API
   - Utilisez l'interface Render pour les secrets

2. **Base de données**:
   - Connexions automatiquement sécurisées
   - Backups automatiques avec Render

## 📊 Architecture Finale

```
User Request
    ↓
Render Web Service (Flask)
    ↓
ChromaDB (Embeddings) + PostgreSQL (Metadata)
    ↓
OpenAI API (Embeddings & Completion)
    ↓
Response to User
```

## 🎯 Avantages de cette Architecture

- **Persistance**: PostgreSQL survit aux redéploiements
- **Performance**: ChromaDB pour les recherches vectorielles
- **Scalabilité**: Render gère l'auto-scaling
- **Maintenance**: Backups automatiques
- **Coût**: Plan gratuit suffisant pour commencer

## 🚀 Prêt pour la Production

Une fois déployé, votre assistant médical belge sera:
- ✅ Accessible 24/7
- ✅ Avec base de données persistante
- ✅ Backups automatiques
- ✅ Monitoring intégré
- ✅ SSL/HTTPS automatique
- ✅ Domaine personnalisable

Votre application sera accessible à: `https://your-app-name.onrender.com` 