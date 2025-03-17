"""
Yorum API
-------
Yorum oluşturma, listeleme ve yönetimi için API endpoints.
"""

from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate
from app.services.comment_service import comment_service
from app.utils.responses import success_response, error_response, list_response, created_response, updated_response, deleted_response
from app.middleware.validation import validate_schema, validate_path_param, validate_query_params, is_uuid, is_positive_integer
from app.middleware.auth import authenticate, authorize
from app.utils.exceptions import NotFoundError, ValidationError, ForbiddenError

# Blueprint tanımla
comment_bp = Blueprint('comment', __name__)

# Şemalar
class CommentCreateSchema(Schema):
    """Yorum oluşturma şeması"""
    forum_id = fields.Str(required=True, error_messages={'required': 'Forum ID zorunludur'})
    icerik = fields.Str(required=True, error_messages={'required': 'Yorum içeriği zorunludur'})
    foto_urls = fields.List(fields.Url())
    ust_yorum_id = fields.Str()

class CommentUpdateSchema(Schema):
    """Yorum güncelleme şeması"""
    icerik = fields.Str()
    foto_urls = fields.List(fields.Url())

class CommentReactionSchema(Schema):
    """Yorum reaksiyon şeması"""
    reaction_type = fields.Str(required=True, validate=validate.OneOf(['begeni', 'begenmeme']), error_messages={'required': 'Reaksiyon türü gereklidir'})

# Routes
@comment_bp.route('/', methods=['POST'])
@authenticate
@validate_schema(CommentCreateSchema())
def create_comment():
    """
    Yeni yorum oluşturur.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Yorum oluştur
        comment = comment_service.create_comment(user_id, data)
        
        return created_response(comment, "Yorum başarıyla oluşturuldu")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@comment_bp.route('/<comment_id>', methods=['GET'])
@validate_path_param('comment_id', is_uuid)
def get_comment(comment_id):
    """
    Yorum bilgilerini getirir.
    
    Args:
        comment_id (str): Yorum ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Yorumu getir
        comment = comment_service.get_comment_by_id(comment_id)
        
        return success_response(comment, "Yorum başarıyla getirildi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@comment_bp.route('/<comment_id>', methods=['PUT'])
@authenticate
@validate_path_param('comment_id', is_uuid)
@validate_schema(CommentUpdateSchema())
def update_comment(comment_id):
    """
    Yorum bilgilerini günceller.
    
    Args:
        comment_id (str): Yorum ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Yorum güncelle
        comment = comment_service.update_comment(comment_id, user_id, data)
        
        return updated_response(comment, "Yorum başarıyla güncellendi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ForbiddenError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@comment_bp.route('/<comment_id>', methods=['DELETE'])
@authenticate
@validate_path_param('comment_id', is_uuid)
def delete_comment(comment_id):
    """
    Yorumu siler.
    
    Args:
        comment_id (str): Yorum ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Yorum sil
        comment_service.delete_comment(comment_id, user_id)
        
        return deleted_response("Yorum başarıyla silindi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ForbiddenError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@comment_bp.route('/<comment_id>/replies', methods=['GET'])
@validate_path_param('comment_id', is_uuid)
@validate_query_params({
    'page': is_positive_integer,
    'per_page': is_positive_integer
})
def get_comment_replies(comment_id):
    """
    Yorum yanıtlarını getirir.
    
    Args:
        comment_id (str): Yorum ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Sorgu parametreleri
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Yanıtları getir
        result = comment_service.get_comment_replies(comment_id, page, per_page)
        
        return list_response(
            result['replies'],
            result['meta']['total'],
            result['meta']['page'],
            result['meta']['per_page'],
            "Yorum yanıtları başarıyla getirildi"
        )
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@comment_bp.route('/<comment_id>/react', methods=['POST'])
@authenticate
@validate_path_param('comment_id', is_uuid)
@validate_schema(CommentReactionSchema())
def react_to_comment(comment_id):
    """
    Yoruma reaksiyon ekler (beğeni/beğenmeme).
    
    Args:
        comment_id (str): Yorum ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Reaksiyon ekle
        result = comment_service.react_to_comment(
            comment_id, 
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