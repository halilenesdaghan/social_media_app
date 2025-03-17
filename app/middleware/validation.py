"""
Hata İşleme Middleware
--------------------
Flask uygulaması için merkezi hata işleme fonksiyonları.
"""

import logging
from pynamodb.exceptions import DoesNotExist
from flask import jsonify
from werkzeug.exceptions import HTTPException
from app.utils.exceptions import ApiError, AuthError, NotFoundError, ValidationError, ForbiddenError

# Logger yapılandırması
logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """
    Uygulamaya hata işleyicileri kaydeder.
    
    Args:
        app: Flask uygulaması
    """
    
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        """
        Özel API hatalarını işler.
        
        Args:
            error (ApiError): API hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = error.to_dict()
        logger.error(f"API Error: {error.message}", exc_info=True)
        return jsonify(response), error.status_code
    
    @app.errorhandler(AuthError)
    def handle_auth_error(error):
        """
        Kimlik doğrulama hatalarını işler.
        
        Args:
            error (AuthError): Kimlik doğrulama hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = error.to_dict()
        logger.error(f"Auth Error: {error.message}")
        return jsonify(response), error.status_code
    
    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error):
        """
        Bulunamadı hatalarını işler.
        
        Args:
            error (NotFoundError): Bulunamadı hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = error.to_dict()
        logger.info(f"Not Found Error: {error.message}")
        return jsonify(response), error.status_code
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """
        Doğrulama hatalarını işler.
        
        Args:
            error (ValidationError): Doğrulama hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = error.to_dict()
        logger.info(f"Validation Error: {error.message}")
        return jsonify(response), error.status_code
    
    @app.errorhandler(ForbiddenError)
    def handle_forbidden_error(error):
        """
        Yasaklı erişim hatalarını işler.
        
        Args:
            error (ForbiddenError): Yasaklı erişim hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = error.to_dict()
        logger.warning(f"Forbidden Error: {error.message}")
        return jsonify(response), error.status_code
    
    @app.errorhandler(DoesNotExist)
    def handle_does_not_exist(error):
        """
        DynamoDB öğe bulunamadı hatalarını işler.
        
        Args:
            error (DoesNotExist): DynamoDB bulunamadı hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = {
            'status': 'error',
            'message': 'İstenen kaynak bulunamadı'
        }
        return jsonify(response), 404
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """
        HTTP hatalarını işler.
        
        Args:
            error (HTTPException): HTTP hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = {
            'status': 'error',
            'message': error.description
        }
        logger.error(f"HTTP Exception: {error}")
        return jsonify(response), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """
        Genel istisnaları işler.
        
        Args:
            error (Exception): Genel istisna
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        # Beklenmeyen hataları günlüğe kaydet
        logger.exception(f"Unhandled Exception: {str(error)}")
        
        # Hata mesajını kullanıcıya gösterme (güvenlik)
        response = {
            'status': 'error',
            'message': 'Sunucu hatası oluştu'
        }
        
        # Debug modunda ise hata detaylarını da gönder
        if app.debug:
            response['error'] = str(error)
            response['traceback'] = str(error.__traceback__)
        
        return jsonify(response), 500