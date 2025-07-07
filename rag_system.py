"""
Système RAG pour l'assistant médical français
Utilise OpenAI pour les embeddings et la génération de réponses
"""

import os
import glob
import json
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np
from openai import OpenAI
import chromadb
from chromadb.config import Settings
import tiktoken

@dataclass
class Document:
    """Représente un document avec ses métadonnées"""
    content: str
    filename: str
    title: str
    chunk_id: str

class RAGSystem:
    def __init__(self, openai_api_key: str, data_directory: str = "data"):
        """
        Initialise le système RAG
        
        Args:
            openai_api_key: Clé API OpenAI
            data_directory: Répertoire contenant les documents
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.data_directory = data_directory
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        
        # Initialiser ChromaDB
        chroma_path = os.getenv('CHROMA_DB_PATH', './chroma_db')
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Créer ou récupérer la collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="medical_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"Collection initialisée avec {self.collection.count()} documents")
    
    def chunk_text(self, text: str, max_tokens: int = 500, overlap: int = 50) -> List[str]:
        """
        Découpe le texte en chunks avec overlap
        
        Args:
            text: Texte à découper
            max_tokens: Nombre maximum de tokens par chunk
            overlap: Nombre de tokens de chevauchement
            
        Returns:
            Liste des chunks
        """
        tokens = self.encoding.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), max_tokens - overlap):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            
        return chunks
    
    def load_documents(self) -> List[Document]:
        """
        Charge tous les documents depuis le répertoire data
        
        Returns:
            Liste des documents
        """
        documents = []
        
        # Charger les fichiers markdown
        md_files = glob.glob(os.path.join(self.data_directory, "*.md"))
        
        for filepath in md_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                filename = os.path.basename(filepath)
                title = self._extract_title(content)
                
                # Découper en chunks
                chunks = self.chunk_text(content)
                
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        content=chunk,
                        filename=filename,
                        title=title,
                        chunk_id=f"{filename}_{i}"
                    )
                    documents.append(doc)
                    
            except Exception as e:
                print(f"Erreur lors du chargement de {filepath}: {e}")
        
        return documents
    
    def _extract_title(self, content: str) -> str:
        """
        Extrait le titre depuis le contenu markdown
        
        Args:
            content: Contenu du document
            
        Returns:
            Titre du document
        """
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return "Document sans titre"
    
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
        Construit la base de données vectorielle
        """
        print("Chargement des documents...")
        documents = self.load_documents()
        
        if not documents:
            print("Aucun document trouvé!")
            return
        
        # Supprimer l'ancienne collection
        try:
            self.chroma_client.delete_collection("medical_documents")
        except:
            pass
        
        # Créer nouvelle collection
        self.collection = self.chroma_client.create_collection(
            name="medical_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"Traitement de {len(documents)} chunks...")
        
        # Traiter par batches
        batch_size = 10
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Préparer les données
            texts = [doc.content for doc in batch]
            embeddings = self.get_embeddings(texts)
            
            if embeddings:
                # Ajouter à ChromaDB
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=[{
                        "filename": doc.filename,
                        "title": doc.title,
                        "chunk_id": doc.chunk_id
                    } for doc in batch],
                    ids=[doc.chunk_id for doc in batch]
                )
                
                print(f"Batch {i//batch_size + 1} ajouté")
        
        print(f"Base de données construite avec {self.collection.count()} documents")
    
    def search_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche les documents pertinents
        
        Args:
            query: Requête de recherche
            n_results: Nombre de résultats
            
        Returns:
            Liste des documents pertinents
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
            documents = []
            for i in range(len(results['documents'][0])):
                doc = {
                    'content': results['documents'][0][i],
                    'filename': results['metadatas'][0][i]['filename'],
                    'title': results['metadatas'][0][i]['title'],
                    'score': 1 - results['distances'][0][i]  # Convertir distance en score
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []
    
    def generate_answer(self, query: str, context_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Génère une réponse basée sur les documents de contexte
        
        Args:
            query: Question de l'utilisateur
            context_documents: Documents de contexte
            
        Returns:
            Réponse avec sources
        """
        if not context_documents:
            return {
                'answer': "Désolé, je n'ai pas trouvé d'informations pertinentes dans la base de données.",
                'sources': []
            }
        
        # Préparer le contexte
        context_text = "\n\n".join([
            f"Document: {doc['title']}\n{doc['content']}"
            for doc in context_documents
        ])
        
        # Prompt en français
        prompt = f"""Vous êtes un assistant médical spécialisé pour biologiste en laboratoire clinique.
Répondez UNIQUEMENT en français et basez-vous UNIQUEMENT sur les documents fournis.

Question: {query}

Contexte (documents du laboratoire):
{context_text}

Instructions:
1. Répondez de manière claire et précise en français
2. Utilisez UNIQUEMENT les informations des documents fournis
3. Si l'information n'est pas dans les documents, dites-le clairement
4. Citez vos sources en mentionnant le document pertinent
5. Structurez votre réponse de manière professionnelle
6. Utilisez le vocabulaire médical approprié

Réponse:"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Vous êtes un assistant médical français spécialisé en biologie clinique. Répondez uniquement en français et basez-vous uniquement sur les documents fournis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            answer = response.choices[0].message.content
            
            # Préparer les sources
            sources = []
            for doc in context_documents:
                sources.append({
                    'title': doc['title'],
                    'filename': doc['filename'],
                    'score': round(doc['score'], 3)
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
    
    def ask_question(self, query: str) -> Dict[str, Any]:
        """
        Interface principale pour poser une question
        
        Args:
            query: Question de l'utilisateur
            
        Returns:
            Réponse complète avec sources
        """
        print(f"Question: {query}")
        
        # Rechercher les documents pertinents
        relevant_docs = self.search_documents(query, n_results=5)
        
        if not relevant_docs:
            return {
                'answer': "Je n'ai pas trouvé d'informations pertinentes dans la base de données.",
                'sources': [],
                'query': query
            }
        
        # Générer la réponse
        result = self.generate_answer(query, relevant_docs)
        result['query'] = query
        
        return result 