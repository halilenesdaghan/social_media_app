"""
Hata İşleme Middleware
--------------------
Flask uygulaması için merkezi hata işleme fonksiyonları.
"""

import logging
from pynamodb.exceptions import DoesNotExist, PynamoDBConnectionError
from flask import jsonify
from werkzeug.exceptions import HTTPException
from app.utils.exceptions import ApiError, AuthError, NotFoundError, ValidationError, ForbiddenError, ConflictError

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
    
    @app.errorhandler(ConflictError)
    def handle_conflict_error(error):
        """
        Çakışma hatalarını işler.
        
        Args:
            error (ConflictError): Çakışma hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = error.to_dict()
        logger.warning(f"Conflict Error: {error.message}")
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
    
    @app.errorhandler(PynamoDBConnectionError)
    def handle_dynamodb_connection_error(error):
        """
        DynamoDB bağlantı hatalarını işler.
        
        Args:
            error (PynamoDBConnectionError): DynamoDB bağlantı hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        logger.error(f"DynamoDB Connection Error: {str(error)}")
        response = {
            'status': 'error',
            'message': 'Veritabanı bağlantı hatası'
        }
        return jsonify(response), 500
    
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
    
    @app.errorhandler(404)
    def handle_404(error):
        """
        404 (Bulunamadı) hatalarını işler.
        
        Args:
            error: 404 hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = {
            'status': 'error',
            'message': 'İstenen kaynak bulunamadı'
        }
        return jsonify(response), 404
    
    @app.errorhandler(405)
    def handle_405(error):
        """
        405 (İzin Verilmeyen Metod) hatalarını işler.
        
        Args:
            error: 405 hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = {
            'status': 'error',
            'message': 'Bu endpoint için istek metodu desteklenmiyor'
        }
        return jsonify(response), 405
    
    @app.errorhandler(400)
    def handle_400(error):
        """
        400 (Hatalı İstek) hatalarını işler.
        
        Args:
            error: 400 hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = {
            'status': 'error',
            'message': 'Hatalı istek'
        }
        return jsonify(response), 400
    
    @app.errorhandler(401)
    def handle_401(error):
        """
        401 (Yetkisiz) hatalarını işler.
        
        Args:
            error: 401 hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = {
            'status': 'error',
            'message': 'Kimlik doğrulama gerekiyor'
        }
        return jsonify(response), 401
    
    @app.errorhandler(403)
    def handle_403(error):
        """
        403 (Yasaklı) hatalarını işler.
        
        Args:
            error: 403 hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        response = {
            'status': 'error',
            'message': 'Bu işlem için yetkiniz bulunmamaktadır'
        }
        return jsonify(response), 403
    
    @app.errorhandler(500)
    def handle_500(error):
        """
        500 (Sunucu Hatası) hatalarını işler.
        
        Args:
            error: 500 hatası
            
        Returns:
            tuple: Hata yanıtı ve HTTP durum kodu
        """
        logger.error(f"Server Error: {str(error)}")
        response = {
            'status': 'error',
            'message': 'Sunucu hatası oluştu'
        }
        return jsonify(response), 500
    
    logger.info("Error handlers registered successfully")