# Assistant PME (StockPilot) 

Assistant PME est une solution d'intelligence artificielle conçue pour aider les petites et moyennes entreprises à optimiser leur gestion de stocks et l'analyse de leurs données.

## L'Idée

L'objectif est de démocratiser l'accès à l'analyse de données pour les gestionnaires de PME. Plutôt que de naviguer dans des tableaux complexes, l'utilisateur interagit avec un **Assistant IA** via un chat pour :
- Poser des questions sur ses stocks ("Quel est le produit le plus cher ?").
- Visualiser des tendances ("Affiche un graphique des ventes").
- Détecter des anomalies (Ruptures de stock, marges faibles).

## Méthodologie & Architecture

Le projet repose sur une architecture moderne séparant clairement l'interface utilisateur de la logique d'analyse.

### 1. Intelligence Artificielle & NLP
Le cœur du système utilise des modèles de langage (LLM) avancés (via **Groq / Llama3**) pour comprendre le langage naturel.
- **Pipeline NLP** : Chaque message utilisateur est analysé pour extraire l'intention (`SEARCH_PRODUCT`, `GET_STATS`, `PLOT_CHART`) et les entités (noms de produits, dates, métriques).
- **Traduction SQL** : L'IA ne requête pas directement la base ; elle structure la demande que le backend traduit en requêtes SQL optimisées et sécurisées via SQLAlchemy.

### 2. Traitement des Données (ETL)
- **Ingestion Flexible** : Les utilisateurs peuvent uploader leurs fichiers Excel/CSV.
- **Normalisation** : Un moteur interne (Pandas) nettoie et mappe automatiquement les colonnes (ex: `prix_unitaire` -> `unit_price`) vers notre schéma de base de données unifié.

### 3. Stack Technique
- **Frontend** : [Next.js](https://nextjs.org/) (React) + Tailwind CSS pour une interface réactive et moderne. Utilisation de WebSockets pour une communication temps réel.
- **Backend** : [FastAPI](https://fastapi.tiangolo.com/) (Python) pour la performance asynchrone.
- **Base de Données** : PostgreSQL (Production) / SQLite (Dev) avec SQLAlchemy.
- **Déploiement** : Configuration optimisée pour Vercel (Monorepo).

## Installation & Déploiement

### Pré-requis
- Node.js 18+
- Python 3.10+
- Clés API (Groq, OpenAI ou Google Gemini)

### Lancement Local
1.  **Cloner le projet**
    ```bash
    git clone https://github.com/Mawandu/Assistant-PME.git
    cd Assistant-PME
    ```

2.  **Backend**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```

3.  **Frontend**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## 🔒 Sécurité
- Isolation des données par session (`X-Client-ID`).
- Chiffrement des tokens et données sensibles.
- Pas de stockage persistant des fichiers bruts après analyse.
