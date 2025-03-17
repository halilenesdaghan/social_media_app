"""
Medya Veri Modeli
----------------
Medya dosyalarının DynamoDB modeli.
"""

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute, 
    ListAttribute, MapAttribute, NumberAttribute, JSONAttribute
)
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from app.models.base import BaseModel, generate_uuid
from datetime import datetime

class UserMediaIndex(GlobalSecondaryIndex):
    """
    Kullanıcı medya ilişkisi için Global Secondary Index (GSI).
    Belirli bir kullanıcının medya dosyalarını hızlıca bulmak için kullanılır.
    """
    
    class Meta:
        index_name = 'user-media-index'
        read_capacity_units = 5
        write_capacity_units = 5
        projection = AllProjection()
    
    yukleyen_id = UnicodeAttribute(hash_key=True)
    yuklenme_tarihi = UTCDateTimeAttribute(range_key=True)


class ModelMediaIndex(GlobalSecondaryIndex):
    """
    Model-medya ilişkisi için Global Secondary Index (GSI).
    Belirli bir modele (forum, yorum, kullanıcı vb.) ait medya dosyalarını 
    hızlıca bulmak için kullanılır.
    """
    
    class Meta:
        index_name = 'model-media-index'
        read_capacity_units = 5
        write_capacity_units = 5
        projection = AllProjection()
    
    ilgili_model = UnicodeAttribute(hash_key=True)
    ilgili_id = UnicodeAttribute(range_key=True)


class MediaModel(BaseModel):
    """
    Medya DynamoDB modeli.
    
    Attributes:
        media_id (UnicodeAttribute): Medya ID'si (primary key)
        dosya_adi (UnicodeAttribute): Depolamada kullanılan dosya adı
        orijinal_dosya_adi (UnicodeAttribute): Dosyanın orijinal adı
        mime_type (UnicodeAttribute): Dosya MIME tipi
        boyut (NumberAttribute): Dosya boyutu (byte)
        dosya_url (UnicodeAttribute): Dosya URL'i
        depolama_yolu (UnicodeAttribute): Depolama yolu (S3 key veya yerel dosya sistemi)
        depolama_tipi (UnicodeAttribute): Depolama tipi ('s3' veya 'local')
        yukleyen_id (UnicodeAttribute): Dosyayı yükleyen kullanıcının ID'si
        yuklenme_tarihi (UTCDateTimeAttribute): Yüklenme tarihi
        ilgili_model (UnicodeAttribute): İlişkili model ('forum', 'comment', 'user' vb.)
        ilgili_id (UnicodeAttribute): İlişkili modelin ID'si
        aciklama (UnicodeAttribute): Dosya açıklaması
        meta_data (JSONAttribute): Ek meta veriler (boyutlar, süre vb.)
    """
    
    class Meta:
        table_name = 'Media'
    
    # Birincil anahtar
    media_id = UnicodeAttribute(hash_key=True, default=lambda: f"med_{generate_uuid()}")
    
    # İndeksler
    user_media_index = UserMediaIndex()
    model_media_index = ModelMediaIndex()
    
    # Dosya bilgileri
    dosya_adi = UnicodeAttribute()
    orijinal_dosya_adi = UnicodeAttribute()
    mime_type = UnicodeAttribute()
    boyut = NumberAttribute(null=True)
    dosya_url = UnicodeAttribute()
    depolama_yolu = UnicodeAttribute()
    depolama_tipi = UnicodeAttribute(default='local')  # 's3' veya 'local'
    
    # İlişki bilgileri
    yukleyen_id = UnicodeAttribute()
    yuklenme_tarihi = UTCDateTimeAttribute(default=datetime.now)
    ilgili_model = UnicodeAttribute(null=True)  # 'forum', 'comment', 'user', 'group', 'poll'
    ilgili_id = UnicodeAttribute(null=True)
    
    # Ek bilgiler
    aciklama = UnicodeAttribute(null=True)
    meta_data = JSONAttribute(null=True)
    
    def is_image(self):
        """
        Dosyanın bir resim olup olmadığını kontrol eder.
        
        Returns:
            bool: Dosya bir resimse True, değilse False
        """
        return self.mime_type.startswith('image/')
    
    def is_document(self):
        """
        Dosyanın bir doküman olup olmadığını kontrol eder.
        
        Returns:
            bool: Dosya bir doküman ise True, değilse False
        """
        document_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain',
            'text/csv'
        ]
        return self.mime_type in document_types
    
    def get_file_extension(self):
        """
        Dosya uzantısını döndürür.
        
        Returns:
            str: Dosya uzantısı
        """
        if '.' in self.orijinal_dosya_adi:
            return self.orijinal_dosya_adi.rsplit('.', 1)[1].lower()
        return ''
    
    def get_file_size_formatted(self):
        """
        Dosya boyutunu okunabilir formatta döndürür (KB, MB, GB).
        
        Returns:
            str: Formatlanmış dosya boyutu
        """
        if self.boyut is None:
            return 'Bilinmiyor'
            
        size_bytes = self.boyut
        
        # Bayt cinsinden boyutu okunabilir birime dönüştür
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                break
            size_bytes /= 1024
            
        return f"{size_bytes:.2f} {unit}"
    
    def to_dict(self):
        """
        Medya verisini sözlük olarak döndürür.
        
        Returns:
            dict: Medya verisi
        """
        data = super().to_dict()
        
        # Ek bilgileri ekle
        data['dosya_boyutu_formatli'] = self.get_file_size_formatted()
        data['dosya_uzantisi'] = self.get_file_extension()
        data['resim_mi'] = self.is_image()
        data['dokuman_mi'] = self.is_document()
        
        return data