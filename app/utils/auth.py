"""
Kimlik Doğrulama Yardımcı Fonksiyonları
--------------------------------------
Şifre hash'leme ve doğrulama fonksiyonları.
"""

import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
from flask import current_app


def hash_password(password):
    """
    Şifreyi güvenli bir şekilde hash'ler.
    
    Args:
        password (str): Ham şifre
    
    Returns:
        str: Hash'lenmiş şifre
    """
    # Şifreyi bytes'a dönüştür
    password_bytes = password.encode('utf-8')
    
    # Salt oluştur ve şifreyi hash'le
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Hash'i string olarak döndür
    return hashed.decode('utf-8')


def check_password(password, hashed_password):
    """
    Verilen şifrenin hash ile eşleşip eşleşmediğini kontrol eder.
    
    Args:
        password (str): Kontrol edilecek ham şifre
        hashed_password (str): Karşılaştırılacak hash'lenmiş şifre
    
    Returns:
        bool: Şifreler eşleşiyorsa True, aksi halde False
    """
    # Şifreyi bytes'a dönüştür
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    # Şifreleri karşılaştır
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def generate_token(user_id, expires_delta=None):
    """
    Kullanıcı için JWT token oluşturur.
    
    Args:
        user_id (str): Kullanıcının ID'si
        expires_delta (timedelta, optional): Token'ın geçerlilik süresi
    
    Returns:
        str: JWT token
    """
    # Varsayılan süreyi ayarla
    if expires_delta is None:
        expires_delta = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(days=1))
    
    payload = {
        'exp': datetime.utcnow() + expires_delta,
        'iat': datetime.utcnow(),
        'sub': str(user_id),
        'jti': str(uuid.uuid4())
    }
    
    # JWT token oluştur
    return jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )


def decode_token(token):
    """
    JWT token'ı çözer ve içeriğini döndürür.
    
    Args:
        token (str): JWT token
    
    Returns:
        dict: Token içeriği
    
    Raises:
        jwt.InvalidTokenError: Token geçersizse
        jwt.ExpiredSignatureError: Token süresi dolmuşsa
    """
    return jwt.decode(
        token,
        current_app.config['JWT_SECRET_KEY'],
        algorithms=['HS256']
    )