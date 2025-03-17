"""
Forum API
-------
Forum oluşturma, listeleme ve yönetimi için API endpoints.
"""

from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate
from app.services.forum_service import forum_service
from app.utils.responses import success_response, error_response, list_response, created_response, updated_response, deleted_response
from app.middleware.validation import validate_schema, validate_path_param, validate_query_params, is_uuid, is_positive_integer
from app.middleware.auth import authenticate, authorize
from app.utils.exceptions import NotFoundError, ValidationError, ForbiddenError

# Blueprint tanımla
forum_bp = Blueprint('forum', __name__)

# Şemalar
class ForumCreateSchema(Schema):
    """Forum oluşturma şeması"""
    baslik = fields.Str(required=True, validate=validate.Length(min=3, max=100), error_messages={'required': 'Forum başlığı gereklidir'})
    aciklama = fields.Str()
    foto_urls = fields.List(fields.Url())
    kategori = fields.Str()
    universite = fields.Str()

class ForumUpdateSchema(Schema):
    """Forum güncelleme şeması"""
    baslik = fields.Str(validate=validate.Length(min=3, max=100))
    aciklama = fields.Str()
    foto_urls = fields.List(fields.Url())
    kategori = fields.Str()

class ForumReactionSchema(Schema):
    """Forum reaksiyon şeması"""
    reaction_type = fields.Str(required=True, validate=validate.OneOf(['begeni', 'begenmeme']), error_messages={'required': 'Reaksiyon türü gereklidir'})

# Routes
@forum_bp.route('/', methods=['GET'])
@validate_query_params({
    'page': is_positive_integer,
    'per_page': is_positive_integer
})
def get_all_forums():
    """
    Tüm forumları getirir.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Sorgu parametreleri
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        kategori = request.args.get('kategori')
        universite = request.args.get('universite')
        search = request.args.get('search')
        
        # Forumları getir
        result = forum_service.get_all_forums(
            page=page,
            per_page=per_page,
            kategori=kategori,
            universite=universite,
            search=search
        )
        
        return list_response(
            result['forums'],
            result['meta']['total'],
            result['meta']['page'],
            result['meta']['per_page'],
            "Forumlar başarıyla getirildi"
        )
    
    except Exception as e:
        return error_response(str(e), 500)

@forum_bp.route('/<forum_id>', methods=['GET'])
@validate_path_param('forum_id', is_uuid)
def get_forum(forum_id):
    """
    Forum bilgilerini getirir.
    
    Args:
        forum_id (str): Forum ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Forumu getir
        forum = forum_service.get_forum_by_id(forum_id)
        
        return success_response(forum, "Forum başarıyla getirildi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@forum_bp.route('/', methods=['POST'])
@authenticate
@validate_schema(ForumCreateSchema())
def create_forum():
    """
    Yeni forum oluşturur.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Forum oluştur
        forum = forum_service.create_forum(user_id, data)
        
        return created_response(forum, "Forum başarıyla oluşturuldu")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@forum_bp.route('/<forum_id>', methods=['PUT'])
@authenticate
@validate_path_param('forum_id', is_uuid)
@validate_schema(ForumUpdateSchema())
def update_forum(forum_id):
    """
    Forum bilgilerini günceller.
    
    Args:
        forum_id (str): Forum ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Forum güncelle
        forum = forum_service.update_forum(forum_id, user_id, data)
        
        return updated_response(forum, "Forum başarıyla güncellendi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ForbiddenError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@forum_bp.route('/<forum_id>', methods=['DELETE'])
@authenticate
@validate_path_param('forum_id', is_uuid)
def delete_forum(forum_id):
    """
    Forumu siler.
    
    Args:
        forum_id (str): Forum ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Forum sil
        forum_service.delete_forum(forum_id, user_id)
        
        return deleted_response("Forum başarıyla silindi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ForbiddenError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@forum_bp.route('/<forum_id>/comments', methods=['GET'])
@validate_path_param('forum_id', is_uuid)
@validate_query_params({
    'page': is_positive_integer,
    'per_page': is_positive_integer
})
def get_forum_comments(forum_id):
    """
    Forum yorumlarını getirir.
    
    Args:
        forum_id (str): Forum ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Sorgu parametreleri
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Yorumları getir
        result = forum_service.get_forum_comments(forum_id, page, per_page)
        
        return list_response(
            result['comments'],
            result['meta']['total'],
            result['meta']['page'],
            result['meta']['per_page'],
            "Forum yorumları başarıyla getirildi"
        )
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@forum_bp.route('/<forum_id>/react', methods=['POST'])
@authenticate
@validate_path_param('forum_id', is_uuid)
@validate_schema(ForumReactionSchema())
def react_to_forum(forum_id):
    """
    Foruma reaksiyon ekler (beğeni/beğenmeme).
    
    Args:
        forum_id (str): Forum ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Reaksiyon ekle
        result = forum_service.react_to_forum(
            forum_id, 
            user_id, 
            data['reaction_type']
        )
        
        return success_response(result, "Reaksiyon başarıyla eklendi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)