"""
Forum Veri Modeli
---------------
Forum verisinin DynamoDB modeli.
"""

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute, 
    ListAttribute, MapAttribute, NumberAttribute
)
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection, LocalSecondaryIndex
from app.models.base import BaseModel, generate_uuid
from datetime import datetime


class UserForumIndex(GlobalSecondaryIndex):
    """
    Kullanıcı forum ilişkisi için Global Secondary Index (GSI).
    Kullanıcı ID'sine göre forum aramalarını hızlandırır.
    """
    
    class Meta:
        index_name = 'user-forum-index'
        read_capacity_units = 5
        write_capacity_units = 5
        projection = AllProjection()
    
    acan_kisi_id = UnicodeAttribute(hash_key=True)
    acilis_tarihi = UTCDateTimeAttribute(range_key=True)


class UniversiteKategoriIndex(GlobalSecondaryIndex):
    """
    Üniversite ve kategori için Global Secondary Index (GSI).
    Üniversite ve kategoriye göre forum aramalarını hızlandırır.
    """
    
    class Meta:
        index_name = 'universite-kategori-index'
        read_capacity_units = 5
        write_capacity_units = 5
        projection = AllProjection()
    
    universite = UnicodeAttribute(hash_key=True)
    kategori = UnicodeAttribute(range_key=True)


class AcilisTarihiIndex(LocalSecondaryIndex):
    """
    Açılış tarihine göre sıralama için Local Secondary Index (LSI).
    """
    
    class Meta:
        index_name = 'acilis-tarihi-index'
        read_capacity_units = 5
        write_capacity_units = 5
        projection = AllProjection()
    
    forum_id = UnicodeAttribute(hash_key=True)
    acilis_tarihi = UTCDateTimeAttribute(range_key=True)


class ForumModel(BaseModel):
    """
    Forum DynamoDB modeli.
    
    Attributes:
        forum_id (UnicodeAttribute): Forum ID'si (primary key)
        baslik (UnicodeAttribute): Forum başlığı
        aciklama (UnicodeAttribute): Forum açıklaması
        acilis_tarihi (UTCDateTimeAttribute): Forum açılış tarihi
        acan_kisi_id (UnicodeAttribute): Forumu açan kullanıcının ID'si
        foto_urls (ListAttribute): Forum resimleri URL'leri
        yorum_ids (ListAttribute): Forum yorumlarının ID'leri
        begeni_sayisi (NumberAttribute): Beğeni sayısı
        begenmeme_sayisi (NumberAttribute): Beğenmeme sayısı
        universite (UnicodeAttribute): Forum açan kişinin üniversitesi
        kategori (UnicodeAttribute): Forum kategorisi
    """
    
    class Meta:
        table_name = 'Forums'
    
    # Birincil anahtar
    forum_id = UnicodeAttribute(hash_key=True, default=lambda: f"frm_{generate_uuid()}")
    
    # Indeksler
    user_forum_index = UserForumIndex()
    universite_kategori_index = UniversiteKategoriIndex()
    acilis_tarihi_index = AcilisTarihiIndex()
    
    # Forum bilgileri
    baslik = UnicodeAttribute()
    aciklama = UnicodeAttribute(null=True)
    acilis_tarihi = UTCDateTimeAttribute(default=datetime.now)
    acan_kisi_id = UnicodeAttribute()
    foto_urls = ListAttribute(default=list)
    yorum_ids = ListAttribute(default=list)
    begeni_sayisi = NumberAttribute(default=0)
    begenmeme_sayisi = NumberAttribute(default=0)
    universite = UnicodeAttribute(null=True)
    kategori = UnicodeAttribute(null=True)
    
    def add_comment(self, comment_id):
        """
        Foruma yeni bir yorum ekler.
        
        Args:
            comment_id (str): Yorum ID'si
        """
        if comment_id not in self.yorum_ids:
            self.yorum_ids.append(comment_id)
            self.save()
    
    def add_like(self):
        """
        Forum beğeni sayısını artırır.
        """
        self.begeni_sayisi += 1
        self.save()
    
    def remove_like(self):
        """
        Forum beğeni sayısını azaltır.
        """
        if self.begeni_sayisi > 0:
            self.begeni_sayisi -= 1
            self.save()
    
    def add_dislike(self):
        """
        Forum beğenmeme sayısını artırır.
        """
        self.begenmeme_sayisi += 1
        self.save()
    
    def remove_dislike(self):
        """
        Forum beğenmeme sayısını azaltır.
        """
        if self.begenmeme_sayisi > 0:
            self.begenmeme_sayisi -= 1
            self.save()
    
    def add_photo(self, photo_url):
        """
        Foruma yeni bir fotoğraf ekler.
        
        Args:
            photo_url (str): Fotoğraf URL'si
        """
        if photo_url not in self.foto_urls:
            self.foto_urls.append(photo_url)
            self.save()
    
    def to_dict(self):
        """
        Forum verisini sözlük olarak döndürür.
        
        Returns:
            dict: Forum verisi
        """
        return super().to_dict()