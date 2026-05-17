"""
Shared fixtures and configuration for HomeIQ test suite.

Set environment variables before running:
  DATABASE_URL   — Supabase connection string
  API_URL        — Live backend URL (e.g. https://eloquent-optimism-...railway.app)
  FRONTEND_URL   — Live frontend URL (e.g. https://homeiq.ie)  [optional]

Or copy tests/.env.test.example to tests/.env.test and fill in values.
"""

import os
import pytest
import psycopg2
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env.test")

API_URL      = os.environ.get("API_URL",      "https://eloquent-optimism-production-350a.up.railway.app")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://homeiq.ie")
DATABASE_URL = os.environ.get("DATABASE_URL", "")


@pytest.fixture(scope="session")
def api():
    """Base URL for the live backend API."""
    return API_URL.rstrip("/")


@pytest.fixture(scope="session")
def db():
    """Direct DB connection — used for data-layer checks."""
    if not DATABASE_URL:
        pytest.skip("DATABASE_URL not set")
    conn = psycopg2.connect(DATABASE_URL)
    yield conn
    conn.close()


def get(api_url, path, **params):
    """GET helper with a consistent timeout."""
    r = requests.get(f"{api_url}{path}", params=params, timeout=15)
    return r
