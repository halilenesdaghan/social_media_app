"""
Servis Paketi
----------
Uygulama iş mantığını içeren servis modüllerini içerir.
Her servis, ilgili işlemler için singleton olarak çalışır.
"""

from app.services.auth_service import auth_service
from app.services.user_service import user_service
from app.services.forum_service import forum_service
from app.services.comment_service import comment_service
from app.services.poll_service import poll_service
from app.services.group_service import group_service
from app.services.media_service import media_service

# Servis registry
services = {
    'auth': auth_service,
    'user': user_service,
    'forum': forum_service,
    'comment': comment_service,
    'poll': poll_service,
    'group': group_service,
    'media': media_service
}

def get_service(service_name):
    """
    İsme göre servis nesnesini döndürür.
    
    Args:
        service_name (str): Servis adı
        
    Returns:
        object: Servis nesnesi
        
    Raises:
        KeyError: Servis bulunamazsa
    """
    if service_name not in services:
        raise KeyError(f"Service not found: {service_name}")
    
    return services[service_name]

__all__ = [
    'auth_service',
    'user_service',
    'forum_service',
    'comment_service',
    'poll_service',
    'group_service',
    'media_service',
    'get_service'
]