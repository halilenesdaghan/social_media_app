"""
DynamoDB Tabloları Oluşturma Scripti
----------------------------------
Uygulama için gerekli DynamoDB tablolarını oluşturur.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Ana uygulamanın Python yoluna ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import UserModel
from app.models.forum import ForumModel
from app.models.comment import CommentModel
from app.models.poll import PollModel
from app.models.group import GroupModel
from app.utils.dynamodb import initialize_dynamodb, create_tables

# .env dosyasını yükle
load_dotenv()

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def setup_models(app_config):
    """
    Model sınıflarını konfigüre eder.
    
    Args:
        app_config: Uygulama konfigürasyonu
    """
    # Meta verilerini ayarla
    models = [UserModel, ForumModel, CommentModel, PollModel, GroupModel]
    
    for model in models:
        model.Meta.region = app_config.get('AWS_DEFAULT_REGION', 'eu-central-1')
        
        # Yerel DynamoDB host ayarlanmışsa, kullan
        if app_config.get('DYNAMODB_ENDPOINT'):
            model.Meta.host = app_config.get('DYNAMODB_ENDPOINT')

def main():
    """
    Ana fonksiyon. DynamoDB tablolarını oluşturur.
    """
    logger.info("DynamoDB tablolarını oluşturma işlemi başlatılıyor...")
    
    try:
        # Flask uygulamasını simüle eden konfigürasyon
        app_config = {
            'AWS_DEFAULT_REGION': os.getenv('AWS_DEFAULT_REGION', 'eu-central-1'),
            'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'DYNAMODB_ENDPOINT': os.getenv('DYNAMODB_ENDPOINT')
        }
        
        # Model sınıflarını konfigüre et
        setup_models(app_config)
        
        # Tabloları oluştur
        logger.info("Tablolar oluşturuluyor...")
        
        # UserModel
        if not UserModel.exists():
            logger.info(f"Tablo oluşturuluyor: {UserModel.Meta.table_name}")
            UserModel.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
        else:
            logger.info(f"Tablo zaten mevcut: {UserModel.Meta.table_name}")
        
        # ForumModel
        if not ForumModel.exists():
            logger.info(f"Tablo oluşturuluyor: {ForumModel.Meta.table_name}")
            ForumModel.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
        else:
            logger.info(f"Tablo zaten mevcut: {ForumModel.Meta.table_name}")
        
        # CommentModel
        if not CommentModel.exists():
            logger.info(f"Tablo oluşturuluyor: {CommentModel.Meta.table_name}")
            CommentModel.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
        else:
            logger.info(f"Tablo zaten mevcut: {CommentModel.Meta.table_name}")
        
        # PollModel
        if not PollModel.exists():
            logger.info(f"Tablo oluşturuluyor: {PollModel.Meta.table_name}")
            PollModel.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
        else:
            logger.info(f"Tablo zaten mevcut: {PollModel.Meta.table_name}")
        
        # GroupModel
        if not GroupModel.exists():
            logger.info(f"Tablo oluşturuluyor: {GroupModel.Meta.table_name}")
            GroupModel.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
        else:
            logger.info(f"Tablo zaten mevcut: {GroupModel.Meta.table_name}")
        
        logger.info("Tüm tablolar başarıyla oluşturuldu.")
        
    except Exception as e:
        logger.error(f"Hata oluştu: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()