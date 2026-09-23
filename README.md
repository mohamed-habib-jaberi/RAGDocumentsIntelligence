# 06 — Persistance MongoDB de RAG Document Intelligence

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

## 4. Entrer dans le dossier applicatif et installer les dépendances

```bash
cd src
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

## 6. Démarrer MongoDB avec Docker

```bash
cd ../docker
docker compose up -d
cd ../src
```

MongoDB est exposé localement sur le port `27007`. Les données sont stockées dans `docker/mongodb/`, un dossier ignoré par Git.

```env
MONGODB_URL="mongodb://localhost:27007"
MONGODB_DATABASE="rag_document_intelligence"
```

## 7. Charger la configuration et organiser les routes

`main.py` charge `.env` avec `python-dotenv`, puis enregistre les routeurs FastAPI. La première route est placée dans `routes/base.py` sous le préfixe versionné `/api/v1` : cette convention permet d'ajouter de nouvelles versions d'API sans casser les clients existants.

La route `GET /api/v1/` retourne le nom et la version définis dans `.env` : elle confirme donc simultanément que l'API et la configuration sont correctement chargées.

## 8. Démarrer l'API FastAPI

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Vérifier le premier endpoint :

```bash
curl http://127.0.0.1:8000/api/v1/
```

Cet endpoint confirme que le serveur est disponible avant l'ajout des routes métier.

## 9. Importer un document

L'endpoint `POST /api/v1/data/upload/{project_id}` accepte les fichiers TXT et PDF déclarés dans `.env`. Il valide le type MIME et la taille, nettoie le nom fourni par le client, crée un dossier par projet et écrit le fichier de façon asynchrone dans `src/assets/files/`.

```bash
curl -F "file=@document.pdf" http://127.0.0.1:8000/api/v1/data/upload/demo-project
```

Les documents importés ne sont pas versionnés : `src/assets/.gitignore` protège les données d'exécution.

## 10. Traiter un document importé

Après l'import, appeler `POST /api/v1/data/process/{project_id}` avec l'identifiant retourné par l'endpoint d'upload. Le contrôleur lit un fichier TXT ou PDF, préserve les métadonnées de source et produit des chunks avec recouvrement. Ces chunks serviront à l'indexation vectorielle dans l'étape suivante.

```json
{
  "file_id": "identifiant-retourné-par-upload.pdf",
  "chunk_size": 500,
  "overlap_size": 50
}
```

`chunk_size` définit la taille maximale d'un fragment et `overlap_size` répète une partie du fragment précédent pour conserver le contexte entre deux chunks.

## 11. Persister les projets et chunks

Lors du premier upload, un projet est créé dans la collection MongoDB `projects`. Lors du traitement, les chunks sont insérés par lots dans `chunks` avec leur texte, leurs métadonnées, leur ordre et l'identifiant MongoDB du projet. Avec `do_reset: true`, les chunks précédents du projet sont supprimés avant la nouvelle insertion.

## 12. Tester avec Postman

Importer `assets/rag-document-intelligence.postman_collection.json`, définir la variable `api` sur `http://127.0.0.1:8000`, puis exécuter les requêtes dans l'ordre : `API configuration endpoint`, `Upload document`, puis `Process document`.

## Principes du projet

- **Configuration hors du code** : secrets et paramètres de machine sont conservés dans `.env`.
- **Versions verrouillées** : l'environnement est reproductible.
- **Évolution incrémentale** : chaque branche numérotée ajoute une responsabilité précise.
