"""
Medya API
-------
Medya yükleme, listeleme ve yönetimi için API endpoints.
"""

from flask import Blueprint, request, jsonify, g, current_app, send_from_directory
from marshmallow import Schema, fields, validate
from app.services.media_service import media_service
from app.utils.responses import success_response, error_response, list_response, created_response, deleted_response
from app.middleware.validation import validate_schema, validate_path_param, validate_query_params, is_uuid, is_positive_integer
from app.middleware.auth import authenticate
from app.utils.exceptions import NotFoundError, ValidationError, ForbiddenError
import os

# Blueprint tanımla
media_bp = Blueprint('media', __name__)

# Şemalar
class MediaUploadMetadataSchema(Schema):
    """Medya yükleme metadata şeması"""
    model_type = fields.Str(validate=validate.OneOf(['genel', 'forum', 'comment', 'user', 'group', 'poll']))
    model_id = fields.Str()
    description = fields.Str()

class MediaDeleteSchema(Schema):
    """Medya silme şeması"""
    storage_path = fields.Str(required=True, error_messages={'required': 'Depolama yolu zorunludur'})
    storage_type = fields.Str(required=True, validate=validate.OneOf(['s3', 'local']), error_messages={'required': 'Depolama türü zorunludur'})
    uploader_id = fields.Str(required=True, error_messages={'required': 'Yükleyen kullanıcı ID zorunludur'})

class MediaUrlSchema(Schema):
    """Medya URL şeması"""
    storage_path = fields.Str(required=True, error_messages={'required': 'Depolama yolu zorunludur'})
    storage_type = fields.Str(required=True, validate=validate.OneOf(['s3', 'local']), error_messages={'required': 'Depolama türü zorunludur'})
    expires = fields.Int(missing=3600)  # Varsayılan 1 saat

# Routes
@media_bp.route('/upload', methods=['POST'])
@authenticate
def upload_file():
    """
    Dosya yükler.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Dosya kontrolü
        if 'file' not in request.files:
            return error_response("Dosya bulunamadı", 400)
        
        file = request.files['file']
        if file.filename == '':
            return error_response("Dosya seçilmedi", 400)
        
        # Metadata
        metadata = {}
        
        # Form verilerinden metadata oluştur
        if request.form:
            schema = MediaUploadMetadataSchema()
            metadata = schema.load(request.form.to_dict())
        
        # Dosyayı yükle
        result = media_service.upload_file(file, g.user.user_id, metadata)
        
        return created_response(result, "Dosya başarıyla yüklendi")
    
    except ValidationError as e:
        return error_response(e.message, 400, e.errors if hasattr(e, 'errors') else None)
    
    except Exception as e:
        return error_response(str(e), 500)

@media_bp.route('/upload-multiple', methods=['POST'])
@authenticate
def upload_multiple_files():
    """
    Birden fazla dosya yükler.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Dosya kontrolü
        if 'files' not in request.files:
            return error_response("Dosya bulunamadı", 400)
        
        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return error_response("Dosya seçilmedi", 400)
        
        # Dosya sayısı kontrolü
        max_files = current_app.config.get('MAX_UPLOAD_FILES', 10)
        if len(files) > max_files:
            return error_response(f"En fazla {max_files} dosya yükleyebilirsiniz", 400)
        
        # Metadata
        metadata = {}
        
        # Form verilerinden metadata oluştur
        if request.form:
            schema = MediaUploadMetadataSchema()
            metadata = schema.load(request.form.to_dict())
        
        # Dosyaları yükle
        results = media_service.upload_multiple_files(files, g.user.user_id, metadata)
        
        return created_response(results, "Dosyalar başarıyla yüklendi")
    
    except ValidationError as e:
        return error_response(e.message, 400, e.errors if hasattr(e, 'errors') else None)
    
    except Exception as e:
        return error_response(str(e), 500)

@media_bp.route('/delete', methods=['POST'])
@authenticate
@validate_schema(MediaDeleteSchema())
def delete_file():
    """
    Dosya siler.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Şema tarafından doğrulanmış veriler
        file_info = request.validated_data
        
        # Dosyayı sil
        media_service.delete_file(file_info, g.user.user_id)
        
        return deleted_response("Dosya başarıyla silindi")
    
    except ForbiddenError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, 400, e.errors if hasattr(e, 'errors') else None)
    
    except Exception as e:
        return error_response(str(e), 500)

@media_bp.route('/url', methods=['POST'])
@authenticate
@validate_schema(MediaUrlSchema())
def get_file_url():
    """
    Dosya URL'i oluşturur.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Şema tarafından doğrulanmış veriler
        file_info = request.validated_data
        
        # URL oluştur
        url = media_service.get_file_url(file_info, file_info.get('expires', 3600))
        
        return success_response({"url": url}, "Dosya URL'i oluşturuldu")
    
    except ValidationError as e:
        return error_response(e.message, 400, e.errors if hasattr(e, 'errors') else None)
    
    except Exception as e:
        return error_response(str(e), 500)

@media_bp.route('/uploads/<path:filename>', methods=['GET'])
def serve_upload(filename):
    """
    Yerel disk üzerindeki dosyaları servis eder.
    
    Args:
        filename (str): Dosya adı/yolu
        
    Returns:
        file: Dosya içeriği
    """
    try:
        # Güvenlik kontrolü: Path traversal saldırılarını önlemek için
        if '..' in filename or filename.startswith('/'):
            return error_response("Geçersiz dosya yolu", 400)
        
        # Uploads klasöründen dosyayı gönder
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    
    except Exception as e:
        return error_response(f"Dosya bulunamadı: {str(e)}", 404)

@media_bp.route('/by-model/<model_type>/<model_id>', methods=['GET'])
@authenticate
@validate_path_param('model_id', is_uuid)
def get_media_by_model(model_type, model_id):
    """
    Belirli bir modele ait medya dosyalarını getirir.
    
    Args:
        model_type (str): Model türü (forum, comment, user, group, poll)
        model_id (str): Model ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Model türü kontrolü
        valid_model_types = ['genel', 'forum', 'comment', 'user', 'group', 'poll']
        if model_type not in valid_model_types:
            return error_response(f"Geçersiz model türü. Geçerli türler: {', '.join(valid_model_types)}", 400)
        
        # Metadata ile dosyaları listeleme fonksiyonu (Bu servis fonksiyonu eklenmeli)
        # Şu an için örnek yanıt dönüyoruz
        media_files = []  # media_service.get_media_by_model(model_type, model_id)
        
        return success_response(media_files, f"{model_type.capitalize()} modeline ait medya dosyaları getirildi")
    
    except ValidationError as e:
        return error_response(e.message, 400, e.errors if hasattr(e, 'errors') else None)
    
    except Exception as e:
        return error_response(str(e), 500)

@media_bp.route('/user/<user_id>', methods=['GET'])
@validate_path_param('user_id', is_uuid)
@validate_query_params({
    'page': is_positive_integer,
    'per_page': is_positive_integer
})
def get_user_media(user_id):
    """
    Kullanıcının yüklediği medya dosyalarını getirir.
    
    Args:
        user_id (str): Kullanıcı ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Sorgu parametreleri
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        model_type = request.args.get('model_type')
        
        # Bu fonksiyon media_service içinde tanımlanmalı
        # Şu an için örnek yanıt dönüyoruz
        result = {
            'media': [],
            'meta': {
                'total': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            }
        }  # media_service.get_user_media(user_id, page, per_page, model_type)
        
        return list_response(
            result['media'],
            result['meta']['total'],
            result['meta']['page'],
            result['meta']['per_page'],
            "Kullanıcı medya dosyaları başarıyla getirildi"
        )
    
    except ValidationError as e:
        return error_response(e.message, 400, e.errors if hasattr(e, 'errors') else None)
    
    except Exception as e:
        return error_response(str(e), 500)