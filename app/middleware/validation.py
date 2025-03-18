"""
Doğrulama Middleware
------------------
API isteklerini doğrulamak için middleware fonksiyonları.
"""

import re
import uuid
from functools import wraps
from flask import request, jsonify, g
from app.utils.exceptions import ValidationError
from app.utils.responses import error_response

def validate_schema(schema):
    """
    İstek verilerini belirtilen şemaya göre doğrular.
    
    Args:
        schema: Marshmallow şeması
        
    Returns:
        function: Decorator fonksiyonu
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Form veya JSON verileri
            is_json = request.is_json
            
            if is_json:
                data = request.json
            else:
                data = request.form.to_dict()
            
            # Şema ile doğrula
            errors = schema.validate(data)
            
            if errors:
                return error_response("Doğrulama hatası", 400, errors)
            
            # Doğrulanmış verileri çıkart
            validated_data = schema.dump(schema.load(data))
            
            # Verileri request nesnesine ekle
            request.validated_data = validated_data
            
            return f(*args, **kwargs)
        
        return wrapper
    
    return decorator

def validate_path_param(param_name, validator_func):
    """
    URL yol parametresini doğrular.
    
    Args:
        param_name (str): Parametre adı
        validator_func (function): Doğrulama fonksiyonu
        
    Returns:
        function: Decorator fonksiyonu
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if param_name in kwargs:
                value = kwargs[param_name]
                
                if not validator_func(value):
                    return error_response(f"Geçersiz {param_name} parametresi", 400)
            
            return f(*args, **kwargs)
        
        return wrapper
    
    return decorator

def validate_query_params(validators):
    """
    Sorgu parametrelerini doğrular.
    
    Args:
        validators (dict): Parametre adı ve doğrulama fonksiyonu eşleşmeleri
        
    Returns:
        function: Decorator fonksiyonu
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            for param_name, validator_func in validators.items():
                if param_name in request.args:
                    value = request.args.get(param_name)
                    
                    if not validator_func(value):
                        return error_response(f"Geçersiz {param_name} parametre değeri", 400)
            
            return f(*args, **kwargs)
        
        return wrapper
    
    return decorator

# Doğrulama yardımcı fonksiyonları
def is_uuid(value):
    """
    Değerin geçerli bir UUID olup olmadığını kontrol eder.
    
    Args:
        value (str): Kontrol edilecek değer
        
    Returns:
        bool: Değer geçerli bir UUID ise True, değilse False
    """
    try:
        uuid_obj = uuid.UUID(str(value))
        return str(uuid_obj) == value or value.startswith(('usr_', 'frm_', 'cmt_', 'grp_', 'pol_', 'med_'))
    except (ValueError, AttributeError):
        return False

def is_positive_integer(value):
    """
    Değerin pozitif bir tamsayı olup olmadığını kontrol eder.
    
    Args:
        value: Kontrol edilecek değer
        
    Returns:
        bool: Değer pozitif bir tamsayı ise True, değilse False
    """
    try:
        num = int(value)
        return num > 0
    except (ValueError, TypeError):
        return False

def is_boolean(value):
    """
    Değerin boolean olarak değerlendirilebilirliğini kontrol eder.
    
    Args:
        value: Kontrol edilecek değer
        
    Returns:
        bool: Değer boolean olarak değerlendirilebilir ise True, değilse False
    
    Note:
        "true", "false", "1", "0", True, False değerleri kabul edilir.
    """
    if isinstance(value, bool):
        return True
    
    if isinstance(value, str):
        lower_value = value.lower()
        if lower_value in ('true', 'false', '1', '0'):
            return True
    
    if isinstance(value, (int, float)):
        if value in (0, 1):
            return True
    
    return False

def is_email(value):
    """
    Değerin geçerli bir e-posta adresi olup olmadığını kontrol eder.
    
    Args:
        value (str): Kontrol edilecek değer
        
    Returns:
        bool: Değer geçerli bir e-posta adresi ise True, değilse False
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not isinstance(value, str):
        return False
    return bool(re.match(email_pattern, value))

def is_url(value):
    """
    Değerin geçerli bir URL olup olmadığını kontrol eder.
    
    Args:
        value (str): Kontrol edilecek değer
        
    Returns:
        bool: Değer geçerli bir URL ise True, değilse False
    """
    url_pattern = r'^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([\/\w .-]*)*\/?$'
    if not isinstance(value, str):
        return False
    return bool(re.match(url_pattern, value))