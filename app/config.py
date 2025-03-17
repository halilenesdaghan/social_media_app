"""
Uygulama Konfigürasyon Dosyası
------------------------------
Tüm uygulama ayarlarını ve çevre değişkenlerini yönetir.
"""

import os
from datetime import timedelta

# .env dosyasını yükle
from dotenv import load_dotenv
load_dotenv()

class Config:
    """Ana konfigürasyon sınıfı"""
    
    # Flask ayarları
    SECRET_KEY = os.getenv('SECRET_KEY', 'gelistirme-icin-gizli-anahtar')
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    API_PREFIX = os.getenv('API_PREFIX', '/api')
    
    # JWT ayarları
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400)))
    
    # AWS ayarları
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'eu-central-1')
    
    # DynamoDB ayarları
    DYNAMODB_HOST = os.getenv('DYNAMODB_HOST', 'http://localhost:8000')
    DYNAMODB_ENDPOINT = os.getenv('DYNAMODB_ENDPOINT')
    
    # S3 ayarları (medya depolama)
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'social-media-uploads')
    S3_REGION = os.getenv('S3_REGION', AWS_DEFAULT_REGION)
    S3_URL = os.getenv('S3_URL', f'https://{S3_BUCKET_NAME}.s3.amazonaws.com/')
    
    # Redis ayarları (önbellek için)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Logging ayarları
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Upload kısıtlamaları
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # Maksimum 10MB yükleme
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')


class DevelopmentConfig(Config):
    """Geliştirme ortamı konfigürasyonu"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Test ortamı konfigürasyonu"""
    TESTING = True
    DEBUG = True
    # Test için memory-based DynamoDB veya test endpoint'i
    DYNAMODB_ENDPOINT = 'http://localhost:8000'
    # Test için geçici S3 bucket
    S3_BUCKET_NAME = 'test-social-media-uploads'


class ProductionConfig(Config):
    """Üretim ortamı konfigürasyonu"""
    DEBUG = False
    # Üretimde yerel DynamoDB endpoint'i kullanılmamalı
    DYNAMODB_ENDPOINT = None


# Konfigürasyon sözlüğü
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

# Aktif konfigürasyonu belirle
active_config = config_by_name[os.getenv('FLASK_ENV', 'development')]