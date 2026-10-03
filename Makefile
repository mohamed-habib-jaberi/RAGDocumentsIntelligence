SHELL := /bin/sh

# Prefer the interpreter from the activated Conda/virtualenv environment. Team
# members can also override it explicitly: make PYTHON=/path/to/python api
PYTHON ?= $(if $(CONDA_PREFIX),$(CONDA_PREFIX)/bin/python,$(if $(VIRTUAL_ENV),$(VIRTUAL_ENV)/bin/python,python3))
SRC_DIR := src
ALEMBIC_DIR := $(SRC_DIR)/models/db_schemes/minirag
COMPOSE := docker compose --project-directory docker -f docker/docker-compose.yml
CELERY_APP := celery_app.celery_app
CELERY_QUEUES := default,file_processing,data_indexing,mail_service_queue

.DEFAULT_GOAL := help

.PHONY: help install env-local env-docker infra infra-logs migrate api worker beat flower check docker-up docker-logs docker-down docker-reset

help:
	@printf '%s\n' \
	  'Run every target from the repository root:' \
	  '  make install       Install and verify Python dependencies' \
	  '  make env-local     Create src/.env if it does not exist' \
	  '  make env-docker    Create Docker .env files if missing' \
	  '  make infra         Start PostgreSQL, RabbitMQ, and Redis' \
	  '  make migrate       Apply PostgreSQL migrations' \
	  '  make api           Start local FastAPI on port 8001' \
	  '  make worker        Start the local Celery worker' \
	  '  make beat          Start the local Celery scheduler' \
	  '  make flower        Start local Flower on port 5555' \
	  '  make check         Validate Python and Docker configuration' \
	  '  make docker-up     Build and start the complete Docker stack' \
	  '  make docker-logs   Follow application and worker logs' \
	  '  make docker-down   Stop the Docker stack' \
	  '  make docker-reset  Stop the stack and delete its volumes'

install:
	cd $(SRC_DIR) && $(PYTHON) -m pip install -r requirements.txt
	cd $(SRC_DIR) && $(PYTHON) -m pip check

env-local:
	@test -f $(SRC_DIR)/.env || cp $(SRC_DIR)/.env.example $(SRC_DIR)/.env

env-docker:
	@for name in app postgres postgres-exporter rabbitmq redis grafana; do \
		test -f docker/env/.env.$$name || \
			cp docker/env/.env.example.$$name docker/env/.env.$$name; \
	done
	@test -f docker/minirag/alembic.ini || \
		cp docker/minirag/alembic.example.ini docker/minirag/alembic.ini

infra:
	$(COMPOSE) up -d rabbitmq redis pgvector

infra-logs:
	$(COMPOSE) logs -f rabbitmq redis pgvector

migrate:
	@test -f $(ALEMBIC_DIR)/alembic.ini || \
		(echo 'Missing $(ALEMBIC_DIR)/alembic.ini; follow README section 6.'; exit 1)
	cd $(ALEMBIC_DIR) && $(PYTHON) -m alembic upgrade head

api:
	cd $(SRC_DIR) && $(PYTHON) -m uvicorn main:app \
		--reload --host 0.0.0.0 --port 8001

worker:
	cd $(SRC_DIR) && $(PYTHON) -m celery \
		-A $(CELERY_APP) worker \
		--loglevel=INFO \
		--queues=$(CELERY_QUEUES) \
		--pool=solo \
		--concurrency=1

beat:
	cd $(SRC_DIR) && $(PYTHON) -m celery \
		-A $(CELERY_APP) beat --loglevel=INFO

flower:
	cd $(SRC_DIR) && $(PYTHON) -m celery \
		-A $(CELERY_APP) flower \
		--conf=flowerconfig.py \
		--port=5555

check:
	cd $(SRC_DIR) && PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m compileall -q .
	cd $(SRC_DIR) && $(PYTHON) -m pip check
	$(COMPOSE) config --quiet

docker-up: env-docker
	$(COMPOSE) up -d --build

docker-logs:
	$(COMPOSE) logs -f fastapi celery-worker celery-beat flower

docker-down:
	$(COMPOSE) down

docker-reset:
	$(COMPOSE) down -v --remove-orphans
