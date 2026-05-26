"""Test configuration."""

import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_demo.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
