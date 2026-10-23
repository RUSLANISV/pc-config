"""Настройки сервера из окружения и файла .env."""

import os
from pathlib import Path
from secrets import token_urlsafe

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'test.db'}")
CATALOG_URL = os.getenv("CATALOG_URL", f"sqlite:///{BASE_DIR / 'pc_components_100.db'}")
SECRET_KEY = os.getenv("SECRET_KEY") or token_urlsafe(32)
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://proxy.gen-api.ru/v1")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4.1-mini")
AI_BUILD_MODEL = os.getenv("AI_BUILD_MODEL", "gpt-4.1-mini")
