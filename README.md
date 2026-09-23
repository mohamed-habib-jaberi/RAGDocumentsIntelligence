# 01 — Architecture et initialisation de RAG Document Intelligence

Cette première étape pose le socle du projet. Aucun serveur ni pipeline RAG n'est encore implémenté : l'objectif est de créer un environnement Python reproductible et de séparer la configuration sensible du code source.

## Architecture cible

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

Les étapes suivantes implémenteront progressivement ces composants. À ce stade, seuls les contrats d'environnement sont définis.

## Prérequis

- Python 3.8 ou supérieur
- Conda ou Miniconda (recommandé pour isoler les dépendances)

## Créer l'environnement Python

```bash
conda create -n rag-document-intelligence python=3.8
conda activate rag-document-intelligence
pip install -r requirements.txt
```

`requirements.txt` fixe les versions de FastAPI, Uvicorn et du support d'upload. Cela évite que deux développeurs installent des versions incompatibles.

## Configurer les variables d'environnement

```bash
cp .env.example .env
```

Le fichier `.env` est local et ne doit jamais être ajouté à Git. Il contiendra notamment la clé API du fournisseur LLM. Le modèle `.env.example`, lui, est versionné afin que chaque développeur connaisse les variables attendues sans exposer de secret.

```env
APP_NAME="RAG Document Intelligence"
APP_VERSION="0.1"
OPENAI_API_KEY=""
```

## Principes retenus

- **Configuration hors du code** : les secrets et paramètres propres à une machine passent par `.env`.
- **Versions verrouillées** : les bibliothèques sont épinglées pour rendre l'environnement reproductible.
- **Évolution incrémentale** : chaque branche numérotée ajoute une responsabilité précise au projet.

## Guide d'installation hérité de `mini-rag` (`tut-001`)

Cette section conserve l'intégralité des instructions du README d'origine. Les noms d'environnement ci-dessous sont historiques ; pour ce dépôt, préférer `rag-document-intelligence` comme indiqué plus haut.

# mini-rag

This is a minimal implementation of the RAG model for question answering.

## Requirements

- Python 3.8 or later

#### Install Python using MiniConda

1) Download and install MiniConda from [here](https://docs.anaconda.com/free/miniconda/#quick-command-line-install)
2) Create a new environment using the following command:

```bash
$ conda create -n mini-rag python=3.8
```

3) Activate the environment:

```bash
$ conda activate mini-rag
```

### (Optional) Setup you command line interface for better readability

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

## Installation

### Install the required packages

```bash
$ pip install -r requirements.txt
```

### Setup the environment variables

```bash
$ cp .env.example .env
```

Set your environment variables in the `.env` file. Like `OPENAI_API_KEY` value.
