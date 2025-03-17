"""
Temel Model Sınıfı
----------------
Tüm model sınıfları için temel sınıf.
"""

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute
)
from datetime import datetime
import uuid
from flask import current_app


class BaseModel(Model):
    """
    Tüm DynamoDB modellerinin temel sınıfı.
    
    Bu sınıf, temel alanlar ve yardımcı metodlar sağlar.
    """
    
    # Meta verileri bir subclass tarafından override edilmelidir
    class Meta:
        table_name = None  # Her alt sınıf kendi tablo adını belirlemelidir
        region = None  # Flask uygulaması başlatıldığında doldurulacak
        host = None  # Yerel geliştirme için (isteğe bağlı)
    
    # Oluşturma ve güncelleme tarihleri
    created_at = UTCDateTimeAttribute(default=datetime.now)
    updated_at = UTCDateTimeAttribute(default=datetime.now)
    
    # Aktif durumu (soft delete için)
    is_active = BooleanAttribute(default=True)
    
    def save(self, conditional_operator=None, **expected_values):
        """
        Kaydı kaydederken updated_at alanını günceller.
        
        Args:
            conditional_operator: Koşullu işlemler için operatör
            expected_values: Koşullu işlemler için beklenen değerler
        """
        self.updated_at = datetime.now()
        super().save(conditional_operator, **expected_values)
    
    def update(self, actions=None, condition=None, **kwargs):
        """
        Kaydı güncellerken updated_at alanını günceller.
        
        Args:
            actions: Güncelleme eylemleri listesi
            condition: Güncelleme koşulu
        """
        if actions is None:
            actions = []
        
        # updated_at alanını güncelle
        from pynamodb.models import Update
        actions.append(
            Update(self.updated_at, datetime.now())
        )
        
        super().update(actions=actions, condition=condition)
    
    def soft_delete(self):
        """
        Kaydı soft-delete yapar (is_active=False).
        """
        from pynamodb.models import Update
        actions = [
            Update(self.is_active, False),
            Update(self.updated_at, datetime.now())
        ]
        self.update(actions=actions)
    
    def to_dict(self):
        """
        Modeli sözlük olarak döndürür.
        
        Returns:
            dict: Model verilerinin sözlük gösterimi
        """
        attributes = {}
        for name, attr in self.get_attributes().items():
            if name not in ['Meta'] and hasattr(self, name):
                value = getattr(self, name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                attributes[name] = value
        return attributes
    
    @classmethod
    def setup_meta(cls, app):
        """
        Meta verilerini ayarlar.
        
        Args:
            app: Flask uygulaması
        """
        cls.Meta.region = app.config['AWS_DEFAULT_REGION']
        
        # Yerel geliştirme için host belirtilmişse ayarla
        if app.config['DYNAMODB_ENDPOINT']:
            cls.Meta.host = app.config['DYNAMODB_ENDPOINT']


def generate_uuid():
    """
    Benzersiz UUID oluşturur.
    
    Returns:
        str: UUID
    """
    return str(uuid.uuid4())