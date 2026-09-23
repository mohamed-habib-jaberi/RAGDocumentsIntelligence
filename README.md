# 02 — Foundation API de RAG Document Intelligence

RAG Document Intelligence est un système RAG (*Retrieval-Augmented Generation*) destiné aux questions-réponses fondées sur des documents. Cette étape introduit la première API HTTP ; les étapes suivantes ajouteront l'import de documents, les embeddings, la recherche sémantique et la génération de réponses.

## 1. Architecture cible

```text
Client HTTP
    │
    ▼
FastAPI (API du projet)
    ├── LLM : génération de réponses
    ├── Embeddings : représentation vectorielle des textes
    ├── MongoDB : projets, fichiers et chunks
    └── Base vectorielle : recherche sémantique
```

## 2. Prérequis

- Python 3.8 ou supérieur ;
- Conda ou [Miniconda](https://docs.anaconda.com/free/miniconda/#quick-command-line-install), recommandé pour isoler les dépendances.

## 3. Créer et activer l'environnement Python

```bash
conda create -n rag-document-intelligence python=3.8
conda activate rag-document-intelligence
```

Optionnellement, rendre l'invite de commande plus lisible :

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

## 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

Les versions sont verrouillées afin que tous les développeurs utilisent des dépendances compatibles. FastAPI définit les routes, Uvicorn exécute l'application et `python-multipart` prépare les futurs uploads de fichiers.

## 5. Configurer l'environnement

```bash
cp .env.example .env
```

Le fichier `.env` est local et ignoré par Git. Il doit contenir les secrets, tandis que `.env.example` documente les variables attendues sans exposer de clé.

```env
APP_NAME="RAG Document Intelligence"
APP_VERSION="0.1"
OPENAI_API_KEY=""
```

## 6. Démarrer l'API FastAPI

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Vérifier le premier endpoint :

```bash
curl http://127.0.0.1:8000/welcome
```

Cet endpoint confirme que le serveur est disponible avant l'ajout des routes métier.

## 7. Tester avec Postman

Importer `assets/rag-document-intelligence.postman_collection.json`, définir la variable `api` sur `http://127.0.0.1:8000`, puis exécuter la requête `Welcome endpoint`.

## Principes du projet

- **Configuration hors du code** : secrets et paramètres de machine sont conservés dans `.env`.
- **Versions verrouillées** : l'environnement est reproductible.
- **Évolution incrémentale** : chaque branche numérotée ajoute une responsabilité précise.
