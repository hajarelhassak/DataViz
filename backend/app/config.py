"""
Configuration de l'application Flask DataViz.
"""

import os
from datetime import timedelta


class Config:
    """Configuration commune à tous les environnements."""

    # ==========================================================
    # FLASK
    # ==========================================================

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dataviz-dev-secret-key-change-in-production",
    )

    DEBUG = (
        os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )

    TESTING = False

    # ==========================================================
    # BASE DE DONNÉES INTERNE DATAVIZ
    # ==========================================================

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///app.db",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==========================================================
    # JWT
    # ==========================================================

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "dataviz-jwt-dev-secret-key-change-in-production",
    )

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # ==========================================================
    # CORS
    # ==========================================================

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "*",
        ).split(",")
        if origin.strip()
    ]

    # ==========================================================
    # RATE LIMITING
    # ==========================================================

    RATELIMIT_DEFAULT = os.getenv(
        "RATELIMIT_DEFAULT",
        "100 per hour",
    )

    RATELIMIT_STORAGE_URL = os.getenv(
        "RATELIMIT_STORAGE_URL",
        "memory://",
    )

    RATELIMIT_ENABLED = True

    # ==========================================================
    # CONNEXIONS BDD CLIENTES
    # ==========================================================

    DB_CONNECT_TIMEOUT_SECONDS = int(
        os.getenv(
            "DB_CONNECT_TIMEOUT",
            "10",
        )
    )

    MAX_ROWS_PER_TABLE_LOAD = int(
        os.getenv(
            "MAX_ROWS_PER_TABLE",
            "50",
        )
    )

    # ==========================================================
    # GEMINI API
    # ==========================================================

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

    GEMINI_MODEL = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.6-flash",
    ).strip()

    AI_REQUEST_TIMEOUT_SECONDS = int(
        os.getenv(
            "AI_REQUEST_TIMEOUT_SECONDS",
            "180",
        )
    )

    AI_MAX_RETRIES = int(
        os.getenv(
            "AI_MAX_RETRIES",
            "2",
        )
    )

    AI_CACHE_ENABLED = (
        os.getenv(
            "AI_CACHE_ENABLED",
            "true",
        ).lower()
        == "true"
    )

    # ==========================================================
    # LOGGING
    # ==========================================================

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO",
    )


class DevelopmentConfig(Config):
    """Configuration de développement."""

    DEBUG = True

    SQLALCHEMY_ECHO = False

    # En développement, on peut analyser davantage de données.
    MAX_ROWS_PER_TABLE_LOAD = int(
        os.getenv(
            "MAX_ROWS_PER_TABLE",
            "100000",
        )
    )

    AI_REQUEST_TIMEOUT_SECONDS = int(
        os.getenv(
            "AI_REQUEST_TIMEOUT_SECONDS",
            "180",
        )
    )


class ProductionConfig(Config):
    """Configuration de production."""

    DEBUG = False

    SQLALCHEMY_ECHO = False

    # ==========================================================
    # SÉCURITÉ
    # ==========================================================

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # ==========================================================
    # LIMITES
    # ==========================================================

    MAX_ROWS_PER_TABLE_LOAD = int(
        os.getenv(
            "MAX_ROWS_PER_TABLE",
            "100000",
        )
    )

    AI_REQUEST_TIMEOUT_SECONDS = int(
        os.getenv(
            "AI_REQUEST_TIMEOUT_SECONDS",
            "30",
        )
    )


class TestingConfig(Config):
    """Configuration de test."""

    TESTING = True

    DEBUG = False

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    SQLALCHEMY_ECHO = False

    AI_REQUEST_TIMEOUT_SECONDS = 5

    RATELIMIT_ENABLED = False


# ==============================================================
# MAPPING DES ENVIRONNEMENTS
# ==============================================================

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}