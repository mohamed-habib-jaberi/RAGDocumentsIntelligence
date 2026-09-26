# Qdrant vs PGVector : construire un RAG réellement interchangeable avec Pydantic, SQLAlchemy et FastAPI

> Comment choisir entre une base vectorielle spécialisée et PostgreSQL, puis intégrer les deux derrière un même contrat sans coupler les routes, les contrôleurs ou les tâches Celery à une technologie précise.

Par **Mohamed Habib Jaberi**

## Introduction

Un système RAG — *Retrieval-Augmented Generation* — ne repose pas sur une seule base de données. Dans une architecture complète, nous devons généralement conserver deux catégories d’informations :

1. les données métier, comme les projets, les fichiers, les chunks et les statuts des tâches ;
2. les embeddings, c’est-à-dire les représentations vectorielles utilisées pour retrouver les passages les plus proches d’une question.

Ces deux responsabilités sont différentes. La première relève d’une base de persistance classique telle que MongoDB ou PostgreSQL. La seconde nécessite un moteur capable de calculer efficacement la proximité entre des vecteurs.

Dans notre projet **RAG Document Intelligence**, nous avons rendu ces choix indépendants :

```env
PERSISTENCE_BACKEND="mongodb"   # ou "postgresql"
VECTOR_DB_BACKEND="QDRANT"      # ou "PGVECTOR"
```

Cette séparation permet quatre combinaisons :

| Persistance métier | Base vectorielle | Exemple d’usage |
| --- | --- | --- |
| MongoDB | Qdrant | Architecture historique Mini-RAG |
| MongoDB | PGVector | Documents flexibles, vecteurs dans PostgreSQL |
| PostgreSQL | Qdrant | Données relationnelles, moteur vectoriel spécialisé |
| PostgreSQL | PGVector | Une seule plateforme PostgreSQL à exploiter |

L’objectif de cet article est de comprendre les différences entre **Qdrant** et **PGVector**, puis de montrer comment les intégrer proprement avec **Pydantic Settings**, **SQLAlchemy**, **Alembic** et une architecture découplée.

## 1. Où intervient la base vectorielle dans un pipeline RAG ?

Le flux d’indexation est le suivant :

```text
Document PDF/TXT
      ↓
Extraction du texte
      ↓
Découpage en chunks
      ↓
Modèle d'embedding
      ↓
Vecteurs numériques
      ↓
Qdrant ou PGVector
```

Le flux de recherche suit le chemin inverse :

```text
Question utilisateur
      ↓
Modèle d'embedding
      ↓
Vecteur de la question
      ↓
Recherche de similarité
      ↓
Chunks les plus proches
      ↓
Prompt enrichi
      ↓
LLM et réponse finale
```

Le LLM de génération n’est donc pas la base vectorielle. Le modèle d’embedding transforme les textes et les questions en vecteurs. Qdrant ou PGVector stocke ces vecteurs et recherche les voisins les plus proches. Le LLM intervient ensuite pour construire une réponse à partir des passages récupérés.

La tokenisation existe à l’intérieur des modèles de génération et d’embedding, mais elle n’est pas la responsabilité de Qdrant ou de PGVector.

## 2. Qdrant : une base conçue spécifiquement pour les vecteurs

[Qdrant](https://qdrant.tech/documentation/) est une base de données vectorielle spécialisée. Elle expose une API dédiée aux collections, aux points vectoriels, aux payloads et à la recherche par similarité.

Un enregistrement Qdrant contient généralement :

```python
models.Record(
    id=record_id,
    vector=embedding,
    payload={
        "text": chunk_text,
        "metadata": chunk_metadata,
    },
)
```

### Points forts de Qdrant

- moteur spécialisé pour la recherche vectorielle ;
- indexation HNSW intégrée et optimisée ;
- collections et payloads pensés pour les applications de recherche sémantique ;
- filtrage sur les métadonnées ;
- API claire et indépendante de la base métier ;
- déploiement local, Docker ou service distant ;
- évolution indépendante de PostgreSQL.

### Contraintes de Qdrant

- un service supplémentaire doit être déployé, surveillé et sauvegardé ;
- les données métier et les vecteurs résident dans deux systèmes différents ;
- une cohérence transactionnelle globale entre PostgreSQL/MongoDB et Qdrant n’est pas automatique ;
- les équipes doivent maîtriser une technologie opérationnelle supplémentaire.

### Quand choisir Qdrant ?

Qdrant est particulièrement intéressant lorsque la recherche vectorielle constitue une fonction centrale du produit, lorsque le volume de vecteurs devient important ou lorsque l’équipe souhaite faire évoluer le moteur vectoriel indépendamment de la base transactionnelle.

## 3. PGVector : la recherche vectorielle à l’intérieur de PostgreSQL

[PGVector](https://github.com/pgvector/pgvector) est une extension PostgreSQL. Elle ajoute notamment :

- le type `vector(n)` ;
- des opérateurs de distance ;
- la recherche exacte ;
- des index approximatifs HNSW et IVFFlat ;
- la possibilité de combiner SQL relationnel et recherche vectorielle.

Une table vectorielle peut ressembler à ceci :

```sql
CREATE TABLE collection_768_42 (
    id BIGSERIAL PRIMARY KEY,
    record_id TEXT NOT NULL UNIQUE,
    text TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
```

La recherche cosinus s’effectue avec l’opérateur `<=>` :

```sql
SELECT
    text,
    1 - (embedding <=> CAST(:query AS vector)) AS score
FROM collection_768_42
ORDER BY embedding <=> CAST(:query AS vector)
LIMIT :limit;
```

### Points forts de PGVector

- réutilisation de PostgreSQL, de ses sauvegardes et de son monitoring ;
- transactions SQL et contraintes relationnelles ;
- métadonnées stockées en `JSONB` ;
- requêtes SQL combinant filtres métier et distance vectorielle ;
- infrastructure simplifiée pour les équipes déjà équipées de PostgreSQL ;
- migrations versionnées avec Alembic.

### Contraintes de PGVector

- les charges transactionnelles et vectorielles partagent les ressources PostgreSQL ;
- le dimensionnement du serveur demande une attention particulière ;
- les performances dépendent du schéma, des index et des paramètres PostgreSQL ;
- l’isolation et la montée en charge du moteur vectoriel sont moins indépendantes qu’avec un service spécialisé.

### Quand choisir PGVector ?

PGVector convient très bien lorsqu’une application utilise déjà PostgreSQL, souhaite réduire le nombre de services, doit relier fortement les embeddings aux données métier ou conserve un volume vectoriel compatible avec son infrastructure PostgreSQL.

## 4. Comparaison détaillée

| Critère | Qdrant | PGVector |
| --- | --- | --- |
| Nature | Base vectorielle spécialisée | Extension PostgreSQL |
| Modèle principal | Collections, points, payloads | Tables, lignes, colonnes, `vector` |
| Recherche approximative | HNSW natif | HNSW ou IVFFlat |
| Recherche exacte | Oui | Oui |
| Métadonnées | Payload JSON | Colonnes SQL et `JSONB` |
| Transactions avec les données métier | Non, si elles sont dans une autre base | Oui, si elles partagent PostgreSQL |
| Jointures relationnelles | Non SQL | Oui |
| Exploitation | Service supplémentaire | Intégré à PostgreSQL |
| Scalabilité indépendante | Plus naturelle | Liée au cluster PostgreSQL |
| Sauvegarde | Sauvegarde Qdrant dédiée | Outils PostgreSQL existants |
| Cas idéal | Recherche vectorielle intensive et spécialisée | Stack PostgreSQL unifiée |

Il n’existe pas de gagnant universel. Le bon choix dépend du volume, des filtres, des compétences de l’équipe, des contraintes opérationnelles et du niveau d’indépendance recherché.

## 5. Le principe architectural : dépendre d’un contrat, pas d’un fournisseur

Une mauvaise intégration disperse les conditions dans toute l’application :

```python
if backend == "QDRANT":
    ...
elif backend == "PGVECTOR":
    ...
```

Si cette logique apparaît dans les routes, les contrôleurs et les workers, chaque nouveau backend multiplie les changements et les risques de régression.

Notre approche repose sur trois éléments :

1. **Pydantic** valide la configuration ;
2. une **interface commune** définit les capacités attendues ;
3. une **factory centralisée** sélectionne l’adaptateur au démarrage.

```text
Routes / Celery / NLPController
              ↓
      VectorDBInterface
          ↙       ↘
     Qdrant     PGVector
```

Le contrôleur NLP ne connaît jamais le fournisseur concret. Il appelle uniquement des opérations telles que `create_collection`, `insert_many` ou `search_by_vector`.

## 6. Valider le switch avec Pydantic Settings

Le choix du backend est déclaré comme un type littéral :

```python
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    VECTOR_DB_BACKEND: Literal["QDRANT", "PGVECTOR"] = "QDRANT"
    VECTOR_DB_URL: str | None = None
    VECTOR_DB_PATH: str = "qdrant_db"
    VECTOR_DB_DISTANCE_METHOD: Literal["cosine", "dot"] = "cosine"
    VECTOR_DB_PGVECTOR_INDEX_THRESHOLD: int = 100

    POSTGRES_USERNAME: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_MAIN_DATABASE: str | None = None

    @model_validator(mode="after")
    def validate_selected_backends(self):
        if self.VECTOR_DB_BACKEND == "PGVECTOR" and not all(
            (
                self.POSTGRES_USERNAME,
                self.POSTGRES_PASSWORD,
                self.POSTGRES_MAIN_DATABASE,
            )
        ):
            raise ValueError("PostgreSQL credentials are required for PGVector")
        return self

    model_config = SettingsConfigDict(env_file=".env")
```

Cette validation apporte deux garanties :

- une valeur comme `ELASTICSEARCH` est rejetée immédiatement ;
- PGVector ne peut pas être activé sans configuration PostgreSQL complète.

Une erreur de configuration apparaît ainsi au démarrage, avant le traitement d’une requête utilisateur.

## 7. Définir un contrat vectoriel commun

Les deux adaptateurs implémentent la même interface asynchrone :

```python
from abc import ABC, abstractmethod


class VectorDBInterface(ABC):
    @abstractmethod
    async def connect(self): ...

    @abstractmethod
    async def disconnect(self): ...

    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        embedding_size: int,
        do_reset: bool = False,
    ): ...

    @abstractmethod
    async def insert_many(
        self,
        collection_name: str,
        texts: list,
        vectors: list,
        metadata: list | None = None,
        record_ids: list | None = None,
        batch_size: int = 50,
    ): ...

    @abstractmethod
    async def search_by_vector(
        self,
        collection_name: str,
        vector: list,
        limit: int,
    ): ...
```

Ce contrat applique le principe d’inversion de dépendance : les couches métier dépendent d’une abstraction stable, tandis que Qdrant et PGVector restent des détails d’infrastructure.

## 8. Centraliser la création avec une factory

La factory est le seul endroit qui interprète `VECTOR_DB_BACKEND` :

```python
class VectorDBProviderFactory:
    def __init__(self, config):
        self.config = config

    def create(self):
        builders = {
            "QDRANT": self._create_qdrant,
            "PGVECTOR": self._create_pgvector,
        }

        try:
            return builders[self.config.VECTOR_DB_BACKEND]()
        except KeyError as exc:
            raise ValueError(
                f"Unsupported vector database backend: "
                f"{self.config.VECTOR_DB_BACKEND}"
            ) from exc
```

Les routes et les workers n’envoient même pas le nom du fournisseur à `create()`. La factory lit directement la configuration centrale, ce qui empêche deux composants de sélectionner accidentellement des backends différents.

### Construction de Qdrant

```python
def _create_qdrant(self):
    qdrant_url = self.config.VECTOR_DB_URL
    qdrant_path = None

    if not qdrant_url:
        database_dir = Path("assets/database")
        database_dir.mkdir(parents=True, exist_ok=True)
        qdrant_path = str(database_dir / self.config.VECTOR_DB_PATH)

    return QdrantDBProvider(
        db_path=qdrant_path,
        db_url=qdrant_url,
        distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
        default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
    )
```

Lorsque plusieurs processus utilisent le vector store — par exemple FastAPI et Celery — un serveur Qdrant partagé via `VECTOR_DB_URL` est préférable au mode local embarqué.

### Construction de PGVector avec SQLAlchemy async

```python
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine


def _create_pgvector(self):
    url = URL.create(
        drivername="postgresql+asyncpg",
        username=self.config.POSTGRES_USERNAME,
        password=self.config.POSTGRES_PASSWORD,
        host=self.config.POSTGRES_HOST,
        port=self.config.POSTGRES_PORT,
        database=self.config.POSTGRES_MAIN_DATABASE,
    )

    return PGVectorProvider(
        engine=create_async_engine(url),
        distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
        default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
        index_threshold=self.config.VECTOR_DB_PGVECTOR_INDEX_THRESHOLD,
    )
```

`URL.create()` évite de construire manuellement une URL contenant un mot de passe avec des caractères spéciaux. `asyncpg` est utilisé par l’application asynchrone, tandis qu’Alembic peut utiliser son propre driver de migration.

## 9. Implémenter l’adaptateur Qdrant

La connexion peut viser une URL partagée ou un chemin local :

```python
async def connect(self):
    if self.db_url:
        self.client = QdrantClient(url=self.db_url)
    elif self.db_path:
        self.client = QdrantClient(path=self.db_path)
    else:
        raise ValueError("Qdrant requires VECTOR_DB_URL or VECTOR_DB_PATH")
```

Une collection précise la dimension et la métrique :

```python
self.client.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(
        size=embedding_size,
        distance=models.Distance.COSINE,
    ),
)
```

L’insertion en lot conserve le texte et les métadonnées dans le payload :

```python
records = [
    models.Record(
        id=record_id,
        vector=vector,
        payload={"text": text, "metadata": metadata},
    )
    for record_id, vector, text, metadata in zip(
        record_ids, vectors, texts, metadata_items
    )
]

self.client.upload_records(
    collection_name=collection_name,
    records=records,
)
```

Dans une application très chargée, il faut vérifier que le client choisi est réellement non bloquant. Un contrat `async` autour d’un client synchrone ne rend pas automatiquement les appels réseau asynchrones. Selon la version du SDK, on peut utiliser son client asynchrone ou déléguer les appels bloquants à un thread.

## 10. Implémenter PGVector avec SQLAlchemy

L’adaptateur crée une fabrique de sessions asynchrones :

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

self.sessions = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

Avant toute utilisation, il vérifie que l’extension est installée :

```python
async def connect(self):
    async with self.engine.connect() as connection:
        result = await connection.execute(
            sql_text(
                "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            )
        )

        if result.scalar_one_or_none() is None:
            raise RuntimeError(
                "The PostgreSQL vector extension is missing. "
                "Run 'alembic upgrade head'."
            )
```

Les noms de collections sont validés avant toute interpolation dans une requête SQL :

```python
_COLLECTION_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")

@classmethod
def _validate_collection_name(cls, collection_name: str) -> str:
    if not cls._COLLECTION_PATTERN.fullmatch(collection_name):
        raise ValueError(f"Invalid vector collection name: {collection_name}")
    return collection_name
```

Cette précaution est importante : les paramètres SQL protègent les valeurs, mais ils ne peuvent généralement pas remplacer dynamiquement un nom de table ou de colonne.

L’insertion utilise un *upsert* sur `record_id` :

```python
statement = sql_text(
    f'INSERT INTO "{collection_name}" '
    "(record_id, text, embedding, metadata) "
    "VALUES (:record_id, :text, CAST(:embedding AS vector), "
    "CAST(:metadata AS jsonb)) "
    "ON CONFLICT (record_id) DO UPDATE SET "
    "text = EXCLUDED.text, "
    "embedding = EXCLUDED.embedding, "
    "metadata = EXCLUDED.metadata"
)
```

Dans notre implémentation, `record_id` est stocké en texte. Le même adaptateur PGVector peut donc référencer un chunk identifié par un entier PostgreSQL ou par un `ObjectId` MongoDB sérialisé.

## 11. Activer PGVector avec Alembic

PGVector doit exister dans PostgreSQL avant le démarrage de l’adaptateur. Cette évolution d’infrastructure est versionnée avec Alembic :

```python
from alembic import op


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # Les collections peuvent encore dépendre de l'extension.
    # La suppression automatique serait destructive.
    pass
```

La migration s’exécute avec :

```bash
cd src/models/db_schemes/minirag
alembic -c alembic.ini.example upgrade head
alembic -c alembic.ini.example current
```

Dans Docker, l’entrypoint déclenche Alembic lorsque PostgreSQL est utilisé pour la persistance métier **ou** lorsque PGVector est sélectionné :

```bash
if { [ "${PERSISTENCE_BACKEND:-mongodb}" = "postgresql" ] \
  || [ "${VECTOR_DB_BACKEND:-QDRANT}" = "PGVECTOR" ]; } \
  && [ "${RUN_DB_MIGRATIONS:-false}" = "true" ]; then
  alembic upgrade head
fi
```

Cette condition est essentielle pour la combinaison MongoDB + PGVector : même si les documents sont dans MongoDB, PGVector dépend toujours de PostgreSQL et de son extension `vector`.

## 12. Intégrer le backend au cycle de vie FastAPI

Au démarrage, FastAPI construit une seule implémentation :

```python
async def startup_span():
    settings = get_settings()

    factory = VectorDBProviderFactory(config=settings)
    app.vectordb_client = factory.create()
    await app.vectordb_client.connect()
```

À l’arrêt, la ressource est libérée par le même contrat :

```python
async def shutdown_span():
    if getattr(app, "vectordb_client", None) is not None:
        await app.vectordb_client.disconnect()
```

Le même mécanisme est utilisé par les workers Celery afin que l’API et les tâches d’indexation partagent la même configuration.

## 13. Le contrôleur RAG reste indépendant du backend

Le contrôleur reçoit une abstraction, crée les embeddings puis délègue leur stockage :

```python
vectors = self.embedding_client.embed_text(
    text=texts,
    document_type=DocumentTypeEnum.DOCUMENT.value,
)

await self.vectordb_client.create_collection(
    collection_name=collection_name,
    embedding_size=self.embedding_client.embedding_size,
    do_reset=do_reset,
)

await self.vectordb_client.insert_many(
    collection_name=collection_name,
    texts=texts,
    vectors=vectors,
    metadata=metadata,
    record_ids=chunk_ids,
)
```

Pour une recherche :

```python
query_vectors = self.embedding_client.embed_text(
    text=query,
    document_type=DocumentTypeEnum.QUERY.value,
)

documents = await self.vectordb_client.search_by_vector(
    collection_name=collection_name,
    vector=query_vectors[0],
    limit=10,
)
```

Ce code fonctionne sans `if QDRANT` et sans `if PGVECTOR`. C’est le résultat recherché : le métier exprime une intention, et l’infrastructure choisie réalise l’opération.

## 14. Configurer et changer de backend

### Qdrant local ou distant

```env
VECTOR_DB_BACKEND="QDRANT"
VECTOR_DB_URL="http://localhost:6333"
VECTOR_DB_PATH="qdrant_db"
VECTOR_DB_DISTANCE_METHOD="cosine"
```

Dans Docker Compose, l’URL devient généralement :

```env
VECTOR_DB_URL="http://qdrant:6333"
```

### PGVector

```env
VECTOR_DB_BACKEND="PGVECTOR"
VECTOR_DB_DISTANCE_METHOD="cosine"
VECTOR_DB_PGVECTOR_INDEX_THRESHOLD=100

POSTGRES_USERNAME="postgres"
POSTGRES_PASSWORD="change-me"
POSTGRES_HOST="localhost"
POSTGRES_PORT=5400
POSTGRES_MAIN_DATABASE="minirag"
```

Dans Docker Compose :

```env
POSTGRES_HOST="pgvector"
POSTGRES_PORT=5432
```

Après toute modification du flag, il faut redémarrer FastAPI et les workers Celery :

```bash
cd docker
docker compose up -d --force-recreate fastapi celery-worker celery-beat
```

Le changement est volontairement effectué **avant le démarrage**. Ce n’est pas un basculement dynamique à chaque requête.

## 15. Changer de backend ne migre pas les vecteurs

Modifier `VECTOR_DB_BACKEND` sélectionne un autre adaptateur, mais ne copie pas les données.

Si un projet a été indexé dans Qdrant puis que l’on active PGVector :

1. PGVector ne contient encore aucun vecteur pour ce projet ;
2. il faut relancer l’indexation depuis les chunks persistés ;
3. il faut vérifier que le modèle d’embedding et sa dimension sont identiques ;
4. l’ancien index Qdrant doit être conservé jusqu’à validation de la migration.

Une procédure de migration sûre est donc :

```text
Conserver le backend source
        ↓
Activer et préparer le backend cible
        ↓
Réindexer tous les chunks
        ↓
Comparer les résultats de recherche
        ↓
Basculer l'API et les workers
        ↓
Supprimer l'ancien index après validation
```

## 16. Tester le switch

L’endpoint de configuration expose les choix actifs :

```http
GET /api/v1/
```

Réponse attendue :

```json
{
  "app_name": "RAG Document Intelligence",
  "app_version": "0.1",
  "persistence_backend": "postgresql",
  "vector_db_backend": "PGVECTOR"
}
```

Le scénario de validation complet doit couvrir :

1. l’upload d’un document ;
2. son traitement en chunks ;
3. l’indexation du projet ;
4. la consultation des informations de collection ;
5. une recherche sémantique ;
6. une réponse RAG ;
7. le redémarrage avec l’autre backend ;
8. la réindexation et la répétition des mêmes tests.

Il faut également vérifier les quatre combinaisons de persistance et de stockage vectoriel, car les identifiants des chunks peuvent provenir de MongoDB ou de PostgreSQL.

## 17. Comment choisir dans un projet réel ?

Choisissez plutôt **Qdrant** si :

- la recherche vectorielle est une charge majeure ;
- vous voulez faire évoluer le moteur vectoriel séparément ;
- vous avez besoin d’un service spécialisé et de fonctionnalités vectorielles avancées ;
- votre équipe accepte d’exploiter un composant supplémentaire.

Choisissez plutôt **PGVector** si :

- PostgreSQL est déjà au cœur de votre architecture ;
- vous souhaitez réduire la complexité opérationnelle ;
- les jointures SQL et la cohérence transactionnelle sont importantes ;
- le volume et la charge vectorielle restent compatibles avec votre cluster PostgreSQL.

Conservez un contrat interchangeable si :

- le produit est encore en phase d’évolution ;
- vous souhaitez comparer les performances sur vos propres données ;
- vos environnements local, test et production n’ont pas les mêmes contraintes ;
- vous voulez éviter de coupler le métier à un fournisseur.

## 18. Points d’attention pour la production

### Dimension des embeddings

Une collection créée pour 768 dimensions ne peut pas recevoir un vecteur de 1 536 dimensions. Le nom des collections de notre projet inclut la dimension afin d’éviter de mélanger des modèles incompatibles.

### Métrique de distance

La métrique choisie à la création doit rester cohérente avec le modèle et avec l’interprétation du score. Cosine et produit scalaire ne sont pas interchangeables sans comprendre la normalisation des embeddings.

### Indexation

Un index approximatif accélère la recherche, mais ajoute un coût d’écriture et de mémoire. Pour une très petite collection, une recherche exacte peut être suffisante. C’est la raison du seuil `VECTOR_DB_PGVECTOR_INDEX_THRESHOLD`.

### Cohérence

L’écriture du chunk métier et l’écriture de son embedding sont deux opérations. Avec deux services séparés, une stratégie de reprise, d’idempotence ou de réindexation est nécessaire. Même dans PostgreSQL, des transactions distinctes peuvent être utilisées par les couches métier et vectorielle ; il faut donc définir explicitement la garantie attendue.

### Observabilité

Mesurez au minimum :

- le temps de génération des embeddings ;
- le temps d’insertion ;
- la latence de recherche ;
- le nombre de vecteurs ;
- le taux d’erreur ;
- la qualité des résultats sur un jeu de questions connu.

La meilleure base vectorielle n’est pas seulement celle qui répond le plus vite : c’est celle qui offre le meilleur compromis entre qualité, coût, exploitation et évolutivité pour votre contexte.

## Conclusion

Qdrant et PGVector répondent au même besoin général, mais avec deux philosophies différentes. Qdrant est un moteur vectoriel spécialisé et indépendant. PGVector intègre la recherche sémantique dans l’écosystème PostgreSQL.

Le point le plus important de notre implémentation n’est pas le `if` qui sélectionne un fournisseur. C’est la séparation entre :

- la configuration validée par Pydantic ;
- le contrat vectoriel utilisé par l’application ;
- les adaptateurs Qdrant et PGVector ;
- SQLAlchemy et Alembic, confinés à l’infrastructure PostgreSQL ;
- les contrôleurs RAG, qui restent indépendants de la technologie.

Grâce à ce découpage, changer de backend demande une modification dans un seul fichier `.env`, suivie d’un redémarrage et, si nécessaire, d’une réindexation.

## Code source et branche GitHub

L’implémentation complète est disponible dans le dépôt **RAGDocumentsIntelligence**, sur la branche :

- [13c-mongodb-postgresql-switch](https://github.com/mohamed-habib-jaberi/RAGDocumentsIntelligence/tree/13c-mongodb-postgresql-switch)

Fichiers principaux à consulter :

- `src/helpers/config.py` : validation Pydantic et flags ;
- `src/stores/vectordb/VectorDBInterface.py` : contrat commun ;
- `src/stores/vectordb/VectorDBProviderFactory.py` : sélection centralisée ;
- `src/stores/vectordb/providers/QdrantDBProvider.py` : adaptateur Qdrant ;
- `src/stores/vectordb/providers/PGVectorProvider.py` : adaptateur PGVector/SQLAlchemy ;
- `src/models/db_schemes/minirag/alembic/versions/13c000000003_enable_pgvector.py` : migration Alembic ;
- `src/controllers/NLPController.py` : indexation, recherche et RAG sans dépendance au fournisseur.

## Références

- [Documentation Qdrant](https://qdrant.tech/documentation/)
- [Projet PGVector](https://github.com/pgvector/pgvector)
- [SQLAlchemy asyncio](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Alembic](https://alembic.sqlalchemy.org/)

## Contact with me

GitHub · LinkedIn · Kaggle

GitHub - mohamed-habib-jaberi - https://github.com/mohamed-habib-jaberi

LinkedIn - Mohamed Habib JABERI - https://www.linkedin.com/in/mohamed-habib-jaberi-b51706120/

Kaggle - jaberimohamedhabib - https://www.kaggle.com/jaberimohamedhabib

Si cet article vous a aidé, n’hésitez pas à partager votre architecture, vos résultats de benchmark et votre choix entre Qdrant et PGVector.
