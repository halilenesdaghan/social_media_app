"""
Grup API
------
Grup oluşturma, yönetme ve üyelik işlemleri için API endpoints.
"""

from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate
from app.services.group_service import group_service
from app.utils.responses import success_response, error_response, list_response, created_response, updated_response, deleted_response
from app.middleware.validation import validate_schema, validate_path_param, validate_query_params, is_uuid, is_positive_integer
from app.middleware.auth import authenticate, authorize
from app.utils.exceptions import NotFoundError, ValidationError, ForbiddenError

# Blueprint tanımla
group_bp = Blueprint('group', __name__)

# Şemalar
class GroupCreateSchema(Schema):
    """Grup oluşturma şeması"""
    grup_adi = fields.Str(required=True, validate=validate.Length(min=3, max=50), error_messages={'required': 'Grup adı zorunludur'})
    aciklama = fields.Str()
    logo_url = fields.Url()
    kapak_resmi_url = fields.Url()
    gizlilik = fields.Str(validate=validate.OneOf(['acik', 'kapali', 'gizli']))
    kategoriler = fields.List(fields.Str())

class GroupUpdateSchema(Schema):
    """Grup güncelleme şeması"""
    grup_adi = fields.Str(validate=validate.Length(min=3, max=50))
    aciklama = fields.Str()
    logo_url = fields.Url()
    kapak_resmi_url = fields.Url()
    gizlilik = fields.Str(validate=validate.OneOf(['acik', 'kapali', 'gizli']))
    kategoriler = fields.List(fields.Str())

class MemberRoleUpdateSchema(Schema):
    """Üye rolü güncelleme şeması"""
    role = fields.Str(required=True, validate=validate.OneOf(['uye', 'moderator', 'yonetici']), error_messages={'required': 'Rol zorunludur'})

class MembershipApprovalSchema(Schema):
    """Üyelik onaylama şeması"""
    approve = fields.Bool(required=True, error_messages={'required': 'Onay durumu zorunludur'})

# Routes
@group_bp.route('/', methods=['GET'])
@validate_query_params({
    'page': is_positive_integer,
    'per_page': is_positive_integer
})
def get_all_groups():
    """
    Tüm grupları getirir.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Sorgu parametreleri
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search')
        
        # Kategori filtresi
        kategoriler = None
        if 'kategoriler' in request.args:
            kategoriler = request.args.getlist('kategoriler')
        
        # Grupları getir
        result = group_service.get_all_groups(
            page=page,
            per_page=per_page,
            search=search,
            kategoriler=kategoriler
        )
        
        return list_response(
            result['groups'],
            result['meta']['total'],
            result['meta']['page'],
            result['meta']['per_page'],
            "Gruplar başarıyla getirildi"
        )
    
    except Exception as e:
        return error_response(str(e), 500)

@group_bp.route('/<group_id>', methods=['GET'])
@validate_path_param('group_id', is_uuid)
def get_group(group_id):
    """
    Grup bilgilerini getirir.
    
    Args:
        group_id (str): Grup ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Grubu getir
        group = group_service.get_group_by_id(group_id)
        
        return success_response(group, "Grup başarıyla getirildi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@group_bp.route('/', methods=['POST'])
@authenticate
@validate_schema(GroupCreateSchema())
def create_group():
    """
    Yeni grup oluşturur.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Grup oluştur
        group = group_service.create_group(user_id, data)
        
        return created_response(group, "Grup başarıyla oluşturuldu")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@group_bp.route('/<group_id>', methods=['PUT'])
@authenticate
@validate_path_param('group_id', is_uuid)
@validate_schema(GroupUpdateSchema())
def update_group(group_id):
    """
    Grup bilgilerini günceller.
    
    Args:
        group_id (str): Grup ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Grup güncelle
        group = group_service.update_group(group_id, user_id, data)
        
        return updated_response(group, "Grup başarıyla güncellendi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ForbiddenError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@group_bp.route('/<group_id>', methods=['DELETE'])
@authenticate
@validate_path_param('group_id', is_uuid)
def delete_group(group_id):
    """
    Grubu siler.
    
    Args:
        group_id (str): Grup ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Grup sil
        group_service.delete_group(group_id, user_id)
        
        return deleted_response("Grup başarıyla silindi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ForbiddenError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@group_bp.route('/<group_id>/join', methods=['POST'])
@authenticate
@validate_path_param('group_id', is_uuid)
def join_group(group_id):
    """
    Gruba üye olur.
    
    Args:
        group_id (str): Grup ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Gruba katıl
        result = group_service.join_group(group_id, user_id)
        
        return success_response(result, result['message'])
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@group_bp.route('/<group_id>/leave', methods=['POST'])
@authenticate
@validate_path_param('group_id', is_uuid)
def leave_group(group_id):
    """
    Gruptan ayrılır.
    
    Args:
        group_id (str): Grup ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Gruptan ayrıl
        group_service.leave_group(group_id, user_id)
        
        return success_response(None, "Gruptan başarıyla ayrıldınız")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except ForbiddenError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@group_bp.route('/<group_id>/members', methods=['GET'])
@validate_path_param('group_id', is_uuid)
@validate_query_params({
    'page': is_positive_integer,
    'per_page': is_positive_integer
})
def get_group_members(group_id):
    """
    Grup üyelerini getirir.
    
    Args:
        group_id (str): Grup ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Sorgu parametreleri
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status')
        role = request.args.get('role')
        
        # Üyeleri getir
        result = group_service.get_group_members(
            group_id,
            page=page,
            per_page=per_page,
            status=status,
            role=role
        )
        
        return list_response(
            result['members'],
            result['meta']['total'],
            result['meta']['page'],
            result['meta']['per_page'],
            "Grup üyeleri başarıyla getirildi"
        )
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@group_bp.route('/<group_id>/members/<user_id>/role', methods=['PUT'])
@authenticate
@validate_path_param('group_id', is_uuid)
@validate_path_param('user_id', is_uuid)
@validate_schema(MemberRoleUpdateSchema())
def update_member_role(group_id, user_id):
    """
    Grup üyesinin rolünü günceller.
    
    Args:
        group_id (str): Grup ID'si
        user_id (str): Rolü değiştirilecek kullanıcı ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        current_user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Rolü güncelle
        result = group_service.update_member_role(
            group_id,
            current_user_id,
            user_id,
            data['role']
        )
        
        return updated_response(result, "Üye rolü başarıyla güncellendi")
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ForbiddenError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@group_bp.route('/<group_id>/members/<user_id>/approve', methods=['POST'])
@authenticate
@validate_path_param('group_id', is_uuid)
@validate_path_param('user_id', is_uuid)
@validate_schema(MembershipApprovalSchema())
def approve_membership(group_id, user_id):
    """
    Grup üyelik başvurusunu onaylar veya reddeder.
    
    Args:
        group_id (str): Grup ID'si
        user_id (str): Başvurusu onaylanacak/reddedilecek kullanıcı ID'si
        
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        current_user_id = g.user.user_id
        
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Üyelik başvurusunu onayla/reddet
        result = group_service.approve_membership(
            group_id,
            current_user_id,
            user_id,
            data['approve']
        )
        
        return success_response(result, result['message'])
    
    except NotFoundError as e:
        return error_response(e.message, e.status_code)
    
    except ForbiddenError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)