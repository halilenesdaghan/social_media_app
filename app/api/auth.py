"""
Kimlik Doğrulama API
------------------
Kullanıcı kaydı, girişi ve kimlik doğrulama işlemleri için API endpoints.
"""

from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate
from app.services.auth_service import auth_service
from app.utils.responses import success_response, error_response, created_response
from app.middleware.validation import validate_schema
from app.middleware.auth import authenticate
from app.utils.exceptions import AuthError, ValidationError

# Blueprint tanımla
auth_bp = Blueprint('auth', __name__)

# Şemalar
class RegisterSchema(Schema):
    """Kullanıcı kaydı şeması"""
    email = fields.Email(required=True, error_messages={'required': 'E-posta gereklidir'})
    username = fields.Str(required=True, validate=validate.Length(min=3, max=30), error_messages={'required': 'Kullanıcı adı gereklidir'})
    password = fields.Str(required=True, validate=validate.Length(min=6), error_messages={'required': 'Şifre gereklidir'})
    cinsiyet = fields.Str(validate=validate.OneOf(['Erkek', 'Kadın', 'Diğer']))
    universite = fields.Str()

class LoginSchema(Schema):
    """Kullanıcı girişi şeması"""
    email = fields.Email(required=True, error_messages={'required': 'E-posta gereklidir'})
    password = fields.Str(required=True, error_messages={'required': 'Şifre gereklidir'})

class PasswordChangeSchema(Schema):
    """Şifre değiştirme şeması"""
    current_password = fields.Str(required=True, error_messages={'required': 'Mevcut şifre gereklidir'})
    new_password = fields.Str(required=True, validate=validate.Length(min=6), error_messages={'required': 'Yeni şifre gereklidir'})

class ForgotPasswordSchema(Schema):
    """Şifre sıfırlama isteği şeması"""
    email = fields.Email(required=True, error_messages={'required': 'E-posta gereklidir'})

class ResetPasswordSchema(Schema):
    """Şifre sıfırlama şeması"""
    reset_token = fields.Str(required=True, error_messages={'required': 'Sıfırlama token gereklidir'})
    new_password = fields.Str(required=True, validate=validate.Length(min=6), error_messages={'required': 'Yeni şifre gereklidir'})

# Routes
@auth_bp.route('/register', methods=['POST'])
@validate_schema(RegisterSchema())
def register():
    """
    Yeni kullanıcı kaydı yapar.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Kullanıcı kaydı
        result = auth_service.register(data)
        
        return created_response(result, "Kullanıcı başarıyla kaydedildi")
    
    except AuthError as e:
        return error_response(e.message, e.status_code)
    
    except ValidationError as e:
        return error_response(e.message, e.status_code, e.errors)
    
    except Exception as e:
        return error_response(str(e), 500)

@auth_bp.route('/login', methods=['POST'])
@validate_schema(LoginSchema())
def login():
    """
    Kullanıcı girişi yapar.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Kullanıcı girişi
        result = auth_service.login(data['email'], data['password'])
        
        return success_response(result, "Giriş başarılı")
    
    except AuthError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@auth_bp.route('/me', methods=['GET'])
@authenticate
def me():
    """
    Mevcut kullanıcı bilgilerini getirir.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    user = g.user
    return success_response(user.to_dict(), "Kullanıcı bilgileri getirildi")

@auth_bp.route('/refresh-token', methods=['POST'])
@authenticate
def refresh_token():
    """
    Token yeniler.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Token yenile
        token = auth_service.refresh_token(user_id)
        
        return success_response({'token': token}, "Token yenilendi")
    
    except AuthError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@auth_bp.route('/change-password', methods=['POST'])
@authenticate
@validate_schema(PasswordChangeSchema())
def change_password():
    """
    Kullanıcı şifresini değiştirir.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Mevcut kullanıcı ID'si
        user_id = g.user.user_id
        
        # Şifre değiştir
        auth_service.change_password(
            user_id, 
            data['current_password'], 
            data['new_password']
        )
        
        return success_response(None, "Şifre başarıyla değiştirildi")
    
    except AuthError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)

@auth_bp.route('/forgot-password', methods=['POST'])
@validate_schema(ForgotPasswordSchema())
def forgot_password():
    """
    Şifre sıfırlama isteği gönderir.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Şifre sıfırlama isteği
        result = auth_service.forgot_password(data['email'])
        
        return success_response(result, "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi")
    
    except Exception as e:
        # Güvenlik için, e-posta bulunamasa bile aynı mesajı döndür
        return success_response(None, "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi")

@auth_bp.route('/reset-password', methods=['POST'])
@validate_schema(ResetPasswordSchema())
def reset_password():
    """
    Şifre sıfırlar.
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    try:
        # Şema tarafından doğrulanmış veriler
        data = request.validated_data
        
        # Şifre sıfırla
        auth_service.reset_password(
            data['reset_token'], 
            data['new_password']
        )
        
        return success_response(None, "Şifre başarıyla sıfırlandı")
    
    except AuthError as e:
        return error_response(e.message, e.status_code)
    
    except Exception as e:
        return error_response(str(e), 500)