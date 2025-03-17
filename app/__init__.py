"""
Flask Uygulama İnit Dosyası
--------------------------
Flask uygulamasını ve API blueprint'lerini başlatır.
"""

import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app.config import active_config
from app.middleware.error_handler import register_error_handlers
from app.utils.dynamodb import initialize_dynamodb

# Logger yapılandırması
def configure_logging(app):
    """Uygulama log yapılandırmasını ayarlar"""
    log_level = getattr(logging, app.config['LOG_LEVEL'], logging.INFO)
    
    # Kök logger'ı yapılandır
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Flask ve Werkzeug logger'larını yapılandır
    logging.getLogger('flask').setLevel(log_level)
    logging.getLogger('werkzeug').setLevel(log_level)
    
    app.logger.setLevel(log_level)
    app.logger.info('Logging configured')

def register_extensions(app):
    """Flask extension'larını kaydet"""
    # CORS yapılandırması
    CORS(app)
    
    # JWT yapılandırması
    JWTManager(app)
    
    # DynamoDB bağlantısını başlat
    initialize_dynamodb(app)
    
    # Upload klasörünü oluştur (varsa)
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

def register_blueprints(app):
    """API blueprint'lerini kaydet"""
    from app.api.auth import auth_bp
    from app.api.user import user_bp
    from app.api.forum import forum_bp
    from app.api.comment import comment_bp
    from app.api.poll import poll_bp
    from app.api.group import group_bp
    from app.api.media import media_bp
    
    # Blueprint'leri API prefix ile kaydet
    prefix = app.config['API_PREFIX']
    app.register_blueprint(auth_bp, url_prefix=f"{prefix}/auth")
    app.register_blueprint(user_bp, url_prefix=f"{prefix}/users")
    app.register_blueprint(forum_bp, url_prefix=f"{prefix}/forums")
    app.register_blueprint(comment_bp, url_prefix=f"{prefix}/comments")
    app.register_blueprint(poll_bp, url_prefix=f"{prefix}/polls")
    app.register_blueprint(group_bp, url_prefix=f"{prefix}/groups")
    app.register_blueprint(media_bp, url_prefix=f"{prefix}/media")

def create_app(config=active_config):
    """Ana uygulama factory fonksiyonu"""
    app = Flask(__name__)
    
    # Konfigürasyonu yükle
    app.config.from_object(config)
    
    # Log yapılandırması
    configure_logging(app)
    
    # Extension'ları kaydet
    register_extensions(app)
    
    # Blueprint'leri kaydet
    register_blueprints(app)
    
    # Hata işleyicileri kaydet
    register_error_handlers(app)
    
    # Health check endpoint
    @app.route(f"{app.config['API_PREFIX']}/health")
    def health_check():
        return {"status": "OK", "message": "Server is running"}
    
    app.logger.info(f"Application initialized with {app.config['FLASK_ENV']} configuration")
    
    return app