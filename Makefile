SHELL := /bin/sh

# Resolve the project's named Conda environment to an absolute path so shell
# ordering between pyenv, Conda base, and virtualenv cannot select Python.
# Teams not using Conda can override PYTHON, for example:
# make PYTHON=.venv/bin/python api
CONDA_ENV ?= rag
SANITIZED_ENV := env \
	-u __PYVENV_LAUNCHER__ \
	-u VIRTUAL_ENV \
	-u PYTHONEXECUTABLE \
	-u PYTHONHOME \
	-u PYTHONPATH \
	-u PYENV_VERSION \
	PYTHONNOUSERSITE=1
CONDA_ENV_PREFIX = $(shell $(SANITIZED_ENV) conda env list | awk '$$1 == "$(CONDA_ENV)" {print $$NF; exit}')
PYTHON ?= $(CONDA_ENV_PREFIX)/bin/python
PYTHON_CMD = $(SANITIZED_ENV) $(PYTHON)
SRC_DIR := src
ALEMBIC_DIR := $(SRC_DIR)/models/db_schemes/minirag
COMPOSE := docker compose --project-directory docker -f docker/docker-compose.yml
CELERY_APP := celery_app.celery_app
CELERY_QUEUES := default,file_processing,data_indexing,mail_service_queue
API_PORT ?= 8001
FLOWER_PORT ?= 5555

.DEFAULT_GOAL := help

.PHONY: help check-python install env-local env-docker infra infra-logs migrate api worker beat flower check docker-up docker-logs docker-down docker-reset

help:
	@printf '%s\n' \
	  'Run every target from the repository root (default Conda env: rag):' \
	  '  make check-python  Show and validate the selected Python interpreter' \
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

check-python:
	@cd $(SRC_DIR) && $(PYTHON_CMD) -c \
		'import sys, lzma; print("Python:", sys.executable); print("lzma: OK")'

install: check-python
	cd $(SRC_DIR) && $(PYTHON_CMD) -m pip install -r requirements.txt
	cd $(SRC_DIR) && $(PYTHON_CMD) -m pip check

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

migrate: check-python
	@test -f $(ALEMBIC_DIR)/alembic.ini || \
		(echo 'Missing $(ALEMBIC_DIR)/alembic.ini; follow README section 6.'; exit 1)
	cd $(ALEMBIC_DIR) && $(PYTHON_CMD) -m alembic upgrade head

api: check-python
	cd $(SRC_DIR) && $(PYTHON_CMD) -m uvicorn main:app \
		--reload --host 0.0.0.0 --port $(API_PORT)

worker: check-python
	cd $(SRC_DIR) && $(PYTHON_CMD) -m celery \
		-A $(CELERY_APP) worker \
		--loglevel=INFO \
		--queues=$(CELERY_QUEUES) \
		--pool=solo \
		--concurrency=1

beat: check-python
	cd $(SRC_DIR) && $(PYTHON_CMD) -m celery \
		-A $(CELERY_APP) beat --loglevel=INFO

flower: check-python
	cd $(SRC_DIR) && $(PYTHON_CMD) -m celery \
		-A $(CELERY_APP) flower \
		--conf=flowerconfig.py \
		--port=$(FLOWER_PORT)

check: check-python
	cd $(SRC_DIR) && PYTHONDONTWRITEBYTECODE=1 $(PYTHON_CMD) -m compileall -q .
	cd $(SRC_DIR) && $(PYTHON_CMD) -m pip check
	$(COMPOSE) config --quiet

docker-up: env-docker
	$(COMPOSE) up -d --build

docker-logs:
	$(COMPOSE) logs -f fastapi celery-worker celery-beat flower

docker-down:
	$(COMPOSE) down

docker-reset:
	$(COMPOSE) down -v --remove-orphans
