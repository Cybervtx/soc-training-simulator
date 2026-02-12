"""
Application configuration for SOC Training Simulator
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class"""
    
    # Flask settings
    FLASK_APP = os.environ.get('FLASK_APP', 'backend/app.py')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database settings
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 5432))
    DB_NAME = os.environ.get('DB_NAME', 'soc_training')
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    
    # Alternative DATABASE_URL format
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    
    @classmethod
    def get_database_uri(cls):
        """Get database URI for SQLAlchemy"""
        if cls.DATABASE_URL:
            return cls.DATABASE_URL
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # AbuseIPDB settings
    ABUSEIPDB_API_KEY = os.environ.get('ABUSEIPDB_API_KEY', '')
    ABUSEIPDB_BASE_URL = os.environ.get('ABUSEIPDB_BASE_URL', 'https://api.abuseipdb.com/api/v2')
    
    # Cache settings
    CACHE_TTL = int(os.environ.get('CACHE_TTL', 86400))  # 24 hours
    CACHE_CLEANUP_INTERVAL = int(os.environ.get('CACHE_CLEANUP_INTERVAL', 3600))  # 1 hour
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 24))
    JWT_REFRESH_TOKEN_EXPIRES_DAYS = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 7))
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Rate limiting (AbuseIPDB free tier: 1,000 requests/day)
    ABUSEIPDB_RATE_LIMIT_DAILY = 1000
    ABUSEIPDB_RATE_LIMIT_REMAINING_WARNING = 100


class DevelopmentConfig(Config):
    """Development configuration"""
    FLASK_ENV = 'development'
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    FLASK_ENV = 'production'
    DEBUG = False
    LOG_LEVEL = 'INFO'


class TestingConfig(Config):
    """Testing configuration"""
    FLASK_ENV = 'testing'
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-jwt-secret-key'


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)
