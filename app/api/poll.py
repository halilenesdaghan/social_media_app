"""
Anket API
-------
Anket oluşturma, listeleme, oylama ve yönetim için API endpoints.
"""

from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate
from app.services.poll_service import poll_service
from app.utils.responses import success_response, error_response, list_response, created_response, updated_response, deleted_response
from app.middleware.validation import validate_schema, validate_path_param, validate_query_params, is_uuid, is_positive_integer, is_boolean
from app.middleware.auth import authenticate, authorize
from app.utils.exceptions import NotFoundError, ValidationError, ForbiddenError

# Blueprint tanımla
poll_bp = Blueprint('poll', __name__)

# Şemalar
class PollCreateSchema(Schema):
    """Anket oluşturma şeması"""
    baslik = fields.Str(required=True, validate=validate.Length(min=3, max=100), error_messages={'required': 'Anket başlığı zorunludur'})
    aciklama = fields.Str()
    secenekler = fields.List(fields.Str(), required=True, validate=validate.Length(min=2), error_messages={'required': 'Anket seçenekleri zorunludur'})
    kategori = fields.Str()
    universite = fields.Str()
    bitis_tarihi = fields.Str()  # ISO 8601 formatında

class PollUpdateSchema(Schema):
    """Anket güncelleme şeması"""
    baslik = fields.Str(validate=validate.Length(min=3, max=100))
    aciklama = fields.Str()
    secenekler = fields.List(fields.Str(), validate=validate.Length(min=2))
    kategori = fields.Str()
    bitis_tarihi = fields.Str()  # ISO 8601 formatında

class PollVoteSchema(Schema):
    """Anket oylama şeması"""
    option_id = fields.Str(required=True, error_messages={'required': 'Seçenek ID zorunludur'})

# Routes
@poll_bp.route('/', methods=['GET'])
@validate_query_params({
    'page': is_positive_integer,
    'per_page': is_positive_integer
})
def get_all_polls():
    """
    Tüm anketleri getirir.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Sorgu parametreleri
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        kategori = request.args.get('kategori')
        universite = request.args.get('universite')
        
        # Aktiflik filtresi
        aktif = None
        if 'aktif' in request.args:
            aktif = is_boolean(request.args.get('aktif'))
        
        # Anketleri getir
        result = poll_service.get_all_polls(
            page=page,
            per_page=per_page,
            kategori=kategori,
            universite=universite,
            aktif=aktif
        )
        
        return list_response(
            result['polls'],
            result['meta']['total'],
            result['meta']['page'],
            result['meta']['per_page'],
            "Anketler başarıyla getirildi"
        )
    
    except Exception as e:
        return error_response(str(e), 500)

@poll_bp.route('/<poll_id>', methods=['GET'])
@validate_path_param('poll_id', is_uuid)
def get_poll(poll_id):
    """
    Anket bilgilerini getirir.
    
    Args:
        poll_id (str): Anket ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Anketi getir
        poll = poll_service.get_poll_by_id(poll_id)
        
        return success_response(poll, "Anket başarıyla getirildi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@poll_bp.route('/', methods=['POST'])
@authenticate
@validate_schema(PollCreateSchema())
def create_poll():
    """
    Yeni anket oluşturur.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Anket oluştur
        poll = poll_service.create_poll(user_id, data)
        
        return created_response(poll, "Anket başarıyla oluşturuldu")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@poll_bp.route('/<poll_id>', methods=['PUT'])
@authenticate
@validate_path_param('poll_id', is_uuid)
@validate_schema(PollUpdateSchema())
def update_poll(poll_id):
    """
    Anket bilgilerini günceller.
    
    Args:
        poll_id (str): Anket ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Anket güncelle
        poll = poll_service.update_poll(poll_id, user_id, data)
        
        return updated_response(poll, "Anket başarıyla güncellendi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ForbiddenError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@poll_bp.route('/<poll_id>', methods=['DELETE'])
@authenticate
@validate_path_param('poll_id', is_uuid)
def delete_poll(poll_id):
    """
    Anketi siler.
    
    Args:
        poll_id (str): Anket ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Anket sil
        poll_service.delete_poll(poll_id, user_id)
        
        return deleted_response("Anket başarıyla silindi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ForbiddenError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@poll_bp.route('/<poll_id>/vote', methods=['POST'])
@authenticate
@validate_path_param('poll_id', is_uuid)
@validate_schema(PollVoteSchema())
def vote_poll(poll_id):
    """
    Ankete oy verir.
    
    Args:
        poll_id (str): Anket ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Ankete oy ver
        result = poll_service.vote_poll(poll_id, user_id, data['option_id'])
        
        return success_response(result, "Oy başarıyla kaydedildi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@poll_bp.route('/<poll_id>/results', methods=['GET'])
@validate_path_param('poll_id', is_uuid)
def get_poll_results(poll_id):
    """
    Anket sonuçlarını getirir.
    
    Args:
        poll_id (str): Anket ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Anket sonuçlarını getir
        results = poll_service.get_poll_results(poll_id)
        
        return success_response(results, "Anket sonuçları başarıyla getirildi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)