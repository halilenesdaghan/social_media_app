"""
Kimlik Doğrulama Middleware
--------------------------
JWT bazlı kimlik doğrulama için Flask middleware fonksiyonları.
"""

import jwt
from functools import wraps
from flask import request, current_app, g
from app.utils.exceptions import AuthError, ForbiddenError, NotFoundError
from app.models.user import UserModel


def get_token_from_header():
    """
    İstek başlıklarından Bearer token'ı alır.
    
    Returns:
        str: JWT token
        
    Raises:
        AuthError: Token bulunamazsa veya geçersiz formattaysa
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        raise AuthError('Authorization header gerekli')
    
    parts = auth_header.split()
    
    if parts[0].lower() != 'bearer':
        raise AuthError('Authorization header "Bearer" ile başlamalı')
    
    if len(parts) == 1:
        raise AuthError('Token eksik')
    
    if len(parts) > 2:
        raise AuthError('Authorization header geçersiz formatta')
    
    return parts[1]


def decode_jwt_token(token):
    """
    JWT token'ı doğrular ve içeriğini döndürür.
    
    Args:
        token (str): JWT token
        
    Returns:
        dict: Token içeriği
        
    Raises:
        AuthError: Token geçersizse veya süresi dolmuşsa
    """
    try:
        # Token'ı doğrula
        decoded = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        
        return decoded
    
    except jwt.ExpiredSignatureError:
        raise AuthError('Token süresi dolmuş')
    
    except jwt.InvalidTokenError:
        raise AuthError('Geçersiz token')


def authenticate(f):
    """
    Kimlik doğrulama decorator'ı.
    
    Kullanıcının kimliğini doğrular ve kullanıcı bilgilerini g.user'a ekler.
    
    Args:
        f: Decore edilecek fonksiyon
        
    Returns:
        function: Wrapped fonksiyon
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        # İstek başlıklarından token'ı al
        token = get_token_from_header()
        
        # Token'ı doğrula
        payload = decode_jwt_token(token)
        
        # Kullanıcı ID'sini al
        user_id = payload.get('sub')
        
        if not user_id:
            raise AuthError('Geçersiz token: Kullanıcı kimliği bulunamadı')
        
        try:
            # Kullanıcıyı bul
            user = UserModel.get(user_id)
            
            # Kullanıcının aktif olup olmadığını kontrol et
            if not user.is_active:
                raise AuthError('Hesabınız devre dışı bırakılmış')
            
            # Kullanıcı bilgilerini g'ye ekle
            g.user = user
            g.user_id = user_id
            
            # Son giriş zamanını güncelle (isteğe bağlı)
            # user.update_last_login()
            
        except UserModel.DoesNotExist:
            raise AuthError('Kullanıcı bulunamadı')
        
        return f(*args, **kwargs)
    
    return wrapper


def authorize(required_roles):
    """
    Yetkilendirme decorator'ı.
    
    Kullanıcının belirtilen rollere sahip olup olmadığını kontrol eder.
    authenticate decorator'ından sonra kullanılmalıdır.
    
    Args:
        required_roles (str/list): Gerekli rol(ler)
        
    Returns:
        function: Decorator fonksiyonu
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Önce kimlik doğrulama yapılmış olmalı
            if not hasattr(g, 'user'):
                raise AuthError('Yetkilendirme için kimlik doğrulama gerekli')
            
            # required_roles string ise listeye çevir
            roles = [required_roles] if isinstance(required_roles, str) else required_roles
            
            # Kullanıcının rolünü kontrol et
            if g.user.role not in roles:
                raise ForbiddenError('Bu işlem için yetkiniz bulunmamaktadır')
            
            return f(*args, **kwargs)
        
        return wrapper
    
    return decorator


def get_current_user():
    """
    Mevcut kimliği doğrulanmış kullanıcıyı döndürür.
    
    Returns:
        UserModel: Kimliği doğrulanmış kullanıcı
        
    Raises:
        AuthError: Kimliği doğrulanmış kullanıcı yoksa
    """
    if not hasattr(g, 'user'):
        raise AuthError('Kimliği doğrulanmış kullanıcı bulunamadı')
    
    return g.user