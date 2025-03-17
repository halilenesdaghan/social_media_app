"""
DynamoDB Yardımcı Modülü
-----------------------
DynamoDB bağlantı ve işlemlerini yöneten yardımcı fonksiyonlar.
"""

import boto3
import logging
from pynamodb.connection import Connection
from flask import current_app

# Logger yapılandırması
logger = logging.getLogger(__name__)

# Global değişkenler
dynamodb_client = None
dynamodb_resource = None
pynamodb_connection = None

def initialize_dynamodb(app):
    """DynamoDB bağlantısını başlatır"""
    global dynamodb_client, dynamodb_resource, pynamodb_connection
    
    # Bağlantı konfigürasyonu
    config = {
        'region_name': app.config['AWS_DEFAULT_REGION'],
        'aws_access_key_id': app.config['AWS_ACCESS_KEY_ID'],
        'aws_secret_access_key': app.config['AWS_SECRET_ACCESS_KEY'],
    }
    
    # Eğer endpoint belirtilmişse (yerel geliştirme için)
    if app.config['DYNAMODB_ENDPOINT']:
        config['endpoint_url'] = app.config['DYNAMODB_ENDPOINT']
    
    # AWS boto3 client ve resource'ları oluştur
    dynamodb_client = boto3.client('dynamodb', **config)
    dynamodb_resource = boto3.resource('dynamodb', **config)
    
    # PynamoDB bağlantısı
    pynamodb_connection = Connection(**config)
    
    logger.info("DynamoDB connections initialized")


def get_dynamodb_client():
    """DynamoDB client'ını döndürür"""
    global dynamodb_client
    if not dynamodb_client:
        # Uygulama konteksti içinde değilse, bağlantıyı başlat
        initialize_dynamodb(current_app)
    return dynamodb_client


def get_dynamodb_resource():
    """DynamoDB resource'unu döndürür"""
    global dynamodb_resource
    if not dynamodb_resource:
        # Uygulama konteksti içinde değilse, bağlantıyı başlat
        initialize_dynamodb(current_app)
    return dynamodb_resource


def get_pynamodb_connection():
    """PynamoDB bağlantısını döndürür"""
    global pynamodb_connection
    if not pynamodb_connection:
        # Uygulama konteksti içinde değilse, bağlantıyı başlat
        initialize_dynamodb(current_app)
    return pynamodb_connection


def create_tables():
    """
    Tüm DynamoDB tablolarını oluşturur.
    Bu fonksiyon, model sınıflarını içe aktarır ve tabloları oluşturur.
    """
    from app.models.user import UserModel
    from app.models.forum import ForumModel
    from app.models.comment import CommentModel
    from app.models.poll import PollModel
    from app.models.group import GroupModel
    
    # Tabloları oluştur (eğer mevcut değillerse)
    for model in [UserModel, ForumModel, CommentModel, PollModel, GroupModel]:
        if not model.exists():
            logger.info(f"Creating table: {model.Meta.table_name}")
            model.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)


def delete_tables():
    """
    Tüm DynamoDB tablolarını siler.
    DİKKAT: Bu fonksiyon sadece geliştirme ve test ortamlarında kullanılmalıdır!
    """
    from app.models.user import UserModel
    from app.models.forum import ForumModel
    from app.models.comment import CommentModel
    from app.models.poll import PollModel
    from app.models.group import GroupModel
    
    # Tabloları sil (eğer mevcutsa)
    for model in [UserModel, ForumModel, CommentModel, PollModel, GroupModel]:
        if model.exists():
            logger.warning(f"Deleting table: {model.Meta.table_name}")
            model.delete_table()


def generate_id(prefix=''):
    """
    Benzersiz ID oluşturur.
    
    Args:
        prefix (str): ID öneki (örn: 'usr', 'frm', vb.)
        
    Returns:
        str: Benzersiz ID
    """
    import uuid
    
    # UUID oluştur ve öneki ekle (eğer belirtilmişse)
    if prefix:
        return f"{prefix}_{uuid.uuid4()}"
    return str(uuid.uuid4())