"""Define Flower settings for local execution and Docker containers."""

import os

from dotenv import dotenv_values


# Docker injects settings through process environment variables, while local
# execution reads src/.env. Environment variables take precedence when both
# sources define the same setting.
file_config = dotenv_values(".env")
flower_password = os.getenv(
    "CELERY_FLOWER_PASSWORD",
    file_config.get("CELERY_FLOWER_PASSWORD"),
)

# Flower configuration
port = 5555
max_tasks = 10000
# db = 'flower.db'  # SQLite database for persistent storage
auto_refresh = True

# Authentication is optional for local development. Configure a strong
# CELERY_FLOWER_PASSWORD before exposing Flower outside the local machine.
if flower_password:
    basic_auth = [f"admin:{flower_password}"]
