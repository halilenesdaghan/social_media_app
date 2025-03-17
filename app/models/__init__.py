"""
Veri Modelleri Paketi
------------------
DynamoDB modelleri ve veri şemalarını içerir.
"""

from app.models.user import UserModel
from app.models.forum import ForumModel
from app.models.comment import CommentModel
from app.models.poll import PollModel, PollOption, PollVote
from app.models.group import GroupModel, GroupMember
from app.models.base import BaseModel, generate_uuid

def setup_model_associations():
    """
    Tüm modellerin ilişkilerini yapılandırır.
    Bu fonksiyon, uygulamanın başlangıcında çağrılmalıdır.
    """
    # İlişkiler burada kurulur (eğer gerekirse)
    # DynamoDB NoSQL olduğu için ilişkiler daha çok kod tarafında yönetilir

def setup_models(app):
    """
    Tüm modelleri uygulama konfigurasyon değerleriyle yapılandırır.
    
    Args:
        app: Flask uygulaması veya konfigurasyon nesnesi
    """
    models = [
        BaseModel,
        UserModel,
        ForumModel,
        CommentModel, 
        PollModel,
        GroupModel
    ]
    
    for model in models:
        if hasattr(model, 'setup_meta'):
            model.setup_meta(app)

__all__ = [
    'UserModel',
    'ForumModel',
    'CommentModel',
    'PollModel',
    'PollOption',
    'PollVote',
    'GroupModel',
    'GroupMember',
    'BaseModel',
    'generate_uuid',
    'setup_model_associations',
    'setup_models'
]