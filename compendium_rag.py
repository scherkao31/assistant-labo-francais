"""
Système RAG spécialisé pour le Compendium des analyses belges
Utilise les données JSON des laboratoires belges
"""

import os
import json
import glob
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np
from openai import OpenAI
import chromadb
from chromadb.config import Settings
import tiktoken

@dataclass
class CompendiumAnalysis:
    """Représente une analyse du compendium"""
    titre: str
    code: str
    lien: str
    laboratoire: str
    description: str = ""
    indication: str = ""
    prelevement: str = ""
    technique: str = ""
    reference: str = ""

class CompendiumRAG:
    def __init__(self, openai_api_key: str, data_directory: str = "data/compendium_data"):
        """
        Initialise le système RAG pour le compendium
        
        Args:
            openai_api_key: Clé API OpenAI
            data_directory: Répertoire contenant les données JSON
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.data_directory = data_directory
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        
        # Initialiser ChromaDB
        chroma_path = os.getenv('COMPENDIUM_CHROMA_PATH', './compendium_chroma_db')
        # Sur Render, utiliser un répertoire temporaire si le chemin par défaut n'est pas accessible
        if not os.access(os.path.dirname(chroma_path) or '.', os.W_OK):
            chroma_path = '/tmp/compendium_chroma_db'
        
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Créer ou récupérer la collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="compendium_analyses",
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"Collection compendium initialisée avec {self.collection.count()} analyses")
    
    def load_lab_data(self, filepath: str) -> List[CompendiumAnalysis]:
        """
        Charge les données d'un laboratoire depuis un fichier JSON
        
        Args:
            filepath: Chemin vers le fichier JSON
            
        Returns:
            Liste des analyses
        """
        analyses = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Déterminer le laboratoire depuis le nom du fichier
            filename = os.path.basename(filepath)
            if 'lhub' in filename.lower():
                lab_name = "LHUB-ULB"
            elif 'uza' in filename.lower():
                lab_name = "UZA"
            elif 'citadelle' in filename.lower():
                lab_name = "CHR Citadelle"
            elif 'chu_ulg' in filename.lower():
                lab_name = "CHU ULG"
            else:
                lab_name = "Laboratoire inconnu"
            
            # Traiter chaque analyse
            for item in data:
                if isinstance(item, dict):
                    # Extraire les informations selon la structure
                    titre = item.get('titre', '')
                    code = item.get('code', '')
                    lien = item.get('lien', '')
                    
                    # Extraire les détails supplémentaires s'ils existent
                    description = ""
                    indication = ""
                    prelevement = ""
                    technique = ""
                    reference = ""
                    
                    # Pour les données détaillées UZA
                    if 'analyse' in item:
                        analyse_info = item['analyse']
                        if isinstance(analyse_info, dict):
                            description += f"Service: {analyse_info.get('Service', '')}\n"
                            description += f"Matrice: {analyse_info.get('Matrice', '')}\n"
                    
                    if 'pre_analytique' in item:
                        pre_info = item['pre_analytique']
                        if isinstance(pre_info, dict):
                            prelevement = pre_info.get('type d\'échantillon approprié', '') or pre_info.get('Récipient', '')
                    
                    if 'analytique' in item:
                        analytique_info = item['analytique']
                        if isinstance(analytique_info, dict):
                            technique = analytique_info.get('Méthode analytique', '')
                    
                    if 'post_analytique' in item:
                        post_info = item['post_analytique']
                        if isinstance(post_info, dict):
                            reference = post_info.get('Valeurs de référence', '')
                    
                    # Pour les autres structures
                    if 'description' in item:
                        description = item['description']
                    if 'indication' in item:
                        indication = item['indication']
                    if 'methode' in item:
                        technique = item['methode']
                    if 'types_echantillons' in item:
                        prelevement = item['types_echantillons']
                    
                    if titre and lien:  # Vérifier que les champs essentiels existent
                        analyse = CompendiumAnalysis(
                            titre=titre,
                            code=code,
                            lien=lien,
                            laboratoire=lab_name,
                            description=description,
                            indication=indication,
                            prelevement=prelevement,
                            technique=technique,
                            reference=reference
                        )
                        analyses.append(analyse)
                        
        except Exception as e:
            print(f"Erreur lors du chargement de {filepath}: {e}")
        
        return analyses
    
    def load_all_analyses(self) -> List[CompendiumAnalysis]:
        """
        Charge toutes les analyses depuis tous les fichiers JSON
        
        Returns:
            Liste de toutes les analyses
        """
        analyses = []
        
        # Charger tous les fichiers JSON
        json_files = glob.glob(os.path.join(self.data_directory, "*.json"))
        
        for filepath in json_files:
            print(f"Chargement de {os.path.basename(filepath)}...")
            lab_analyses = self.load_lab_data(filepath)
            analyses.extend(lab_analyses)
            print(f"  {len(lab_analyses)} analyses chargées")
        
        return analyses
    
    def create_search_text(self, analyse: CompendiumAnalysis) -> str:
        """
        Crée le texte de recherche pour une analyse
        
        Args:
            analyse: Analyse à traiter
            
        Returns:
            Texte de recherche
        """
        parts = [
            f"Titre: {analyse.titre}",
            f"Code: {analyse.code}" if analyse.code else "",
            f"Laboratoire: {analyse.laboratoire}",
            f"Description: {analyse.description}" if analyse.description else "",
            f"Indication: {analyse.indication}" if analyse.indication else "",
            f"Prélèvement: {analyse.prelevement}" if analyse.prelevement else "",
            f"Technique: {analyse.technique}" if analyse.technique else "",
            f"Référence: {analyse.reference}" if analyse.reference else "",
        ]
        
        return "\n".join([part for part in parts if part])
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Génère les embeddings pour une liste de textes
        
        Args:
            texts: Liste des textes
            
        Returns:
            Liste des embeddings
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"Erreur lors de la génération des embeddings: {e}")
            return []
    
    def build_database(self):
        """
        Construit la base de données vectorielle du compendium
        """
        print("Chargement des analyses du compendium...")
        analyses = self.load_all_analyses()
        
        if not analyses:
            print("Aucune analyse trouvée!")
            return
        
        # Supprimer l'ancienne collection
        try:
            self.chroma_client.delete_collection("compendium_analyses")
        except:
            pass
        
        # Créer nouvelle collection
        self.collection = self.chroma_client.create_collection(
            name="compendium_analyses",
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"Traitement de {len(analyses)} analyses...")
        
        # Traiter par batches
        batch_size = 50
        for i in range(0, len(analyses), batch_size):
            batch = analyses[i:i + batch_size]
            
            # Préparer les données
            texts = [self.create_search_text(analyse) for analyse in batch]
            embeddings = self.get_embeddings(texts)
            
            if embeddings:
                # Ajouter à ChromaDB
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=[{
                        "titre": analyse.titre,
                        "code": analyse.code,
                        "lien": analyse.lien,
                        "laboratoire": analyse.laboratoire,
                        "description": analyse.description,
                        "indication": analyse.indication,
                        "prelevement": analyse.prelevement,
                        "technique": analyse.technique,
                        "reference": analyse.reference
                    } for analyse in batch],
                    ids=[f"{analyse.laboratoire}_{analyse.titre}_{i+j}" for j, analyse in enumerate(batch)]
                )
                
                print(f"Batch {i//batch_size + 1} ajouté")
        
        print(f"Base de données compendium construite avec {self.collection.count()} analyses")
    
    def search_analyses(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Recherche les analyses pertinentes
        
        Args:
            query: Requête de recherche
            n_results: Nombre de résultats
            
        Returns:
            Liste des analyses pertinentes
        """
        try:
            # Générer l'embedding de la requête
            query_embedding = self.get_embeddings([query])[0]
            
            # Rechercher dans ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Formater les résultats
            analyses = []
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i]
                analyse = {
                    'titre': metadata['titre'],
                    'code': metadata['code'],
                    'lien': metadata['lien'],
                    'laboratoire': metadata['laboratoire'],
                    'description': metadata['description'],
                    'indication': metadata['indication'],
                    'prelevement': metadata['prelevement'],
                    'technique': metadata['technique'],
                    'reference': metadata['reference'],
                    'score': 1 - results['distances'][0][i]  # Convertir distance en score
                }
                analyses.append(analyse)
            
            return analyses
            
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []
    
    def generate_compendium_response(self, query: str, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Génère une réponse basée sur les analyses trouvées
        
        Args:
            query: Question de l'utilisateur
            analyses: Analyses trouvées
            
        Returns:
            Réponse avec liens
        """
        if not analyses:
            return {
                'answer': "Désolé, je n'ai pas trouvé d'analyses correspondant à votre recherche dans le compendium belge.",
                'sources': []
            }
        
        # Préparer le contexte avec plus de détails
        context_text = "\n\n".join([
            f"=== ANALYSE {i+1} ===\n"
            f"Titre: {analyse['titre']}\n"
            f"Laboratoire: {analyse['laboratoire']}\n"
            f"Code: {analyse['code']}\n"
            f"Lien direct: {analyse['lien']}\n"
            f"Description: {analyse['description']}\n"
            f"Indication clinique: {analyse['indication']}\n"
            f"Type de prélèvement: {analyse['prelevement']}\n"
            f"Technique utilisée: {analyse['technique']}\n"
            f"Valeurs de référence: {analyse['reference']}\n"
            f"Score de pertinence: {analyse['score']:.3f}"
            for i, analyse in enumerate(analyses[:5])  # Limiter à 5 analyses
        ])
        
        # Prompt amélioré pour plus de contexte biologique
        prompt = f"""Vous êtes un assistant médical spécialisé dans les analyses de laboratoire belges, avec une expertise approfondie en biologie médicale.

QUESTION DU BIOLOGISTE: {query}

ANALYSES TROUVÉES DANS LES LABORATOIRES BELGES:
{context_text}

INSTRUCTIONS POUR VOTRE RÉPONSE:
1. **Contexte biologique approfondi**: Expliquez l'importance clinique et biologique de l'analyse demandée
2. **Recommandations pratiques**: Donnez des conseils sur le prélèvement, la conservation, les interférences possibles
3. **Interprétation clinique**: Expliquez comment interpréter les résultats et leur signification
4. **Laboratoires disponibles**: Présentez clairement les laboratoires belges qui proposent cette analyse
5. **Liens directs**: Mentionnez que les liens directs vers les laboratoires sont fournis pour plus de détails
6. **Considérations techniques**: Expliquez les méthodes utilisées et leurs avantages/limites

STRUCTURE DE RÉPONSE ATTENDUE:
- Introduction avec contexte biologique
- Présentation des analyses disponibles par laboratoire
- Conseils pratiques pour le biologiste
- Considérations techniques et méthodologiques
- Interprétation clinique

Répondez en français médical professionnel, adapté à un biologiste médical expérimenté."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Vous êtes un assistant médical expert en biologie clinique, spécialisé dans les analyses de laboratoire belges. Votre expertise couvre la biochimie, la microbiologie, l'hématologie, l'immunologie et la biologie moléculaire. Répondez avec un niveau scientifique élevé adapté aux professionnels de santé."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.1
            )
            
            answer = response.choices[0].message.content
            
            # Préparer les sources avec plus d'informations
            sources = []
            for i, analyse in enumerate(analyses[:5]):  # Limiter à 5 liens
                # Créer un titre plus descriptif
                title_with_context = f"{analyse['titre']}"
                if analyse['code']:
                    title_with_context += f" ({analyse['code']})"
                
                sources.append({
                    'title': title_with_context,
                    'lab': analyse['laboratoire'],
                    'url': analyse['lien'],
                    'code': analyse['code'],
                    'description': analyse['description'][:100] + "..." if len(analyse['description']) > 100 else analyse['description'],
                    'prelevement': analyse['prelevement'][:50] + "..." if len(analyse['prelevement']) > 50 else analyse['prelevement'],
                    'technique': analyse['technique'][:50] + "..." if len(analyse['technique']) > 50 else analyse['technique'],
                    'score': round(analyse['score'], 3)
                })
            
            return {
                'answer': answer,
                'sources': sources
            }
            
        except Exception as e:
            print(f"Erreur lors de la génération: {e}")
            return {
                'answer': f"Erreur lors de la génération de la réponse: {str(e)}",
                'sources': []
            }
    
    def ask_compendium(self, query: str) -> Dict[str, Any]:
        """
        Interface principale pour interroger le compendium
        
        Args:
            query: Question de l'utilisateur
            
        Returns:
            Réponse complète avec liens
        """
        print(f"Recherche compendium: {query}")
        
        # Rechercher les analyses pertinentes
        relevant_analyses = self.search_analyses(query, n_results=10)
        
        if not relevant_analyses:
            return {
                'answer': "Je n'ai pas trouvé d'analyses pertinentes dans le compendium belge.",
                'sources': [],
                'query': query
            }
        
        # Générer la réponse
        result = self.generate_compendium_response(query, relevant_analyses)
        result['query'] = query
        
        return result 