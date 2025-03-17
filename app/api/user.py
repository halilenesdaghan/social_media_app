"""
Kullanıcı API
-----------
Kullanıcı profil yönetimi ve ilgili işlemler için API endpoints.
"""

from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate
from app.services.user_service import user_service
from app.utils.responses import success_response, error_response, list_response, updated_response, deleted_response
from app.middleware.validation import validate_schema, validate_path_param, validate_query_params, is_uuid, is_positive_integer
from app.middleware.auth import authenticate, authorize
from app.utils.exceptions import NotFoundError, ValidationError, ForbiddenError

# Blueprint tanımla
user_bp = Blueprint('user', __name__)

# Şemalar
class UserUpdateSchema(Schema):
    """Kullanıcı güncelleme şeması"""
    username = fields.Str(validate=validate.Length(min=3, max=30))
    password = fields.Str(validate=validate.Length(min=6))
    cinsiyet = fields.Str(validate=validate.OneOf(['Erkek', 'Kadın', 'Diğer']))
    universite = fields.Str()
    profil_resmi_url = fields.Url()

class UserListQuerySchema(Schema):
    """Kullanıcı listesi sorgu şeması"""
    page = fields.Int(validate=validate.Range(min=1), missing=1)
    per_page = fields.Int(validate=validate.Range(min=1, max=100), missing=10)
    search = fields.Str()

# Routes
@user_bp.route('/<user_id>', methods=['GET'])
@validate_path_param('user_id', is_uuid)
def get_user(user_id):
    """
    Kullanıcı bilgilerini getirir.
    
    Args:
        user_id (str): Kullanıcı ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Kullanıcıyı getir
        user = user_service.get_user_by_id(user_id)
        
        return success_response(user, "Kullanıcı bilgileri getirildi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@user_bp.route('/by-username/<username>', methods=['GET'])
def get_user_by_username(username):
    """
    Kullanıcı adına göre kullanıcı bilgilerini getirir.
    
    Args:
        username (str): Kullanıcı adı
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Kullanıcıyı getir
        user = user_service.get_user_by_username(username)
        
        return success_response(user, "Kullanıcı bilgileri getirildi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@user_bp.route('/profile', methods=['PUT'])
@authenticate
@validate_schema(UserUpdateSchema())
def update_profile():
    """
    Mevcut kullanıcının profil bilgilerini günceller.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Profil güncelle
        updated_user = user_service.update_user(user_id, data)
        
        return updated_response(updated_user, "Profil başarıyla güncellendi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@user_bp.route('/account', methods=['DELETE'])
@authenticate
def delete_account():
    """
    Kullanıcı hesabını siler.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Hesabı sil
        user_service.delete_user(user_id)
        
        return deleted_response("Hesabınız başarıyla silindi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@user_bp.route('/forums', methods=['GET'])
@authenticate
@validate_query_params({
    'page': is_positive_integer,
    'per_page': is_positive_integer
})
def get_my_forums():
    """
    Mevcut kullanıcının forumlarını getirir.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Sorgu parametreleri
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Forumları getir
        result = user_service.get_user_forums(user_id, page, per_page)
        
        return list_response(
            result['forums'],
            result['meta']['total'],
            result['meta']['page'],
            result['meta']['per_page'],
            "Forumlarınız başarıyla getirildi"
        )
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@user_bp.route('/<user_id>/forums', methods=['GET'])
@validate_path_param('user_id', is_uuid)
@validate_query_params({
    'page': is_positive_integer,
    'per_page': is_positive_integer
})
def get_user_forums(user_id):
    """
    Belirli bir kullanıcının forumlarını getirir.
    
    Args:
        user_id (str): Kullanıcı ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Sorgu parametreleri
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Forumları getir
        result = user_service.get_user_forums(user_id, page, per_page)
        
        return list_response(
            result['forums'],
            result['meta']['total'],
            result['meta']['page'],
            result['meta']['per_page'],
            "Kullanıcı forumları başarıyla getirildi"
        )
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@user_bp.route('/comments', methods=['GET'])
@authenticate
@validate_query_params({
    'page': is_positive_integer,
    'per_page': is_positive_integer
})
def get_my_comments():
    """
    Mevcut kullanıcının yorumlarını getirir.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Sorgu parametreleri
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Yorumları getir
        result = user_service.get_user_comments(user_id, page, per_page)
        
        return list_response(
            result['comments'],
            result['meta']['total'],
            result['meta']['page'],
            result['meta']['per_page'],
            "Yorumlarınız başarıyla getirildi"
        )
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@user_bp.route('/<user_id>/comments', methods=['GET'])
@validate_path_param('user_id', is_uuid)
@validate_query_params({
    'page': is_positive_integer,
    'per_page': is_positive_integer
})
def get_user_comments(user_id):
    """
    Belirli bir kullanıcının yorumlarını getirir.
    
    Args:
        user_id (str): Kullanıcı ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Sorgu parametreleri
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Yorumları getir
        result = user_service.get_user_comments(user_id, page, per_page)
        
        return list_response(
            result['comments'],
            result['meta']['total'],
            result['meta']['page'],
            result['meta']['per_page'],
            "Kullanıcı yorumları başarıyla getirildi"
        )
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@user_bp.route('/polls', methods=['GET'])
@authenticate
@validate_query_params({
    'page': is_positive_integer,
    'per_page': is_positive_integer
})
def get_my_polls():
    """
    Mevcut kullanıcının anketlerini getirir.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Sorgu parametreleri
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Anketleri getir
        result = user_service.get_user_polls(user_id, page, per_page)
        
        return list_response(
            result['polls'],
            result['meta']['total'],
            result['meta']['page'],
            result['meta']['per_page'],
            "Anketleriniz başarıyla getirildi"
        )
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@user_bp.route('/groups', methods=['GET'])
@authenticate
def get_my_groups():
    """
    Mevcut kullanıcının gruplarını getirir.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Grupları getir
        groups = user_service.get_user_groups(user_id)
        
        return success_response(groups, "Gruplarınız başarıyla getirildi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)