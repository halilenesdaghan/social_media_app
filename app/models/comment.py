"""
Yorum Veri Modeli
---------------
Yorum verisinin DynamoDB modeli.
"""

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute, 
    ListAttribute, NumberAttribute
)
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from app.models.base import BaseModel, generate_uuid
from datetime import datetime


class ForumCommentsIndex(GlobalSecondaryIndex):
    """
    Forum yorumları için Global Secondary Index (GSI).
    Belirli bir foruma ait yorumları hızlıca bulmak için kullanılır.
    """
    
    class Meta:
        index_name = 'forum-comments-index'
        read_capacity_units = 5
        write_capacity_units = 5
        projection = AllProjection()
    
    forum_id = UnicodeAttribute(hash_key=True)
    acilis_tarihi = UTCDateTimeAttribute(range_key=True)


class UserCommentsIndex(GlobalSecondaryIndex):
    """
    Kullanıcı yorumları için Global Secondary Index (GSI).
    Belirli bir kullanıcının yorumlarını hızlıca bulmak için kullanılır.
    """
    
    class Meta:
        index_name = 'user-comments-index'
        read_capacity_units = 5
        write_capacity_units = 5
        projection = AllProjection()
    
    acan_kisi_id = UnicodeAttribute(hash_key=True)
    acilis_tarihi = UTCDateTimeAttribute(range_key=True)


class ParentCommentIndex(GlobalSecondaryIndex):
    """
    Üst yoruma bağlı yanıtlar için Global Secondary Index (GSI).
    Bir yoruma verilen yanıtları hızlıca bulmak için kullanılır.
    """
    
    class Meta:
        index_name = 'parent-comment-index'
        read_capacity_units = 5
        write_capacity_units = 5
        projection = AllProjection()
    
    ust_yorum_id = UnicodeAttribute(hash_key=True)
    acilis_tarihi = UTCDateTimeAttribute(range_key=True)


class CommentModel(BaseModel):
    """
    Yorum DynamoDB modeli.
    
    Attributes:
        comment_id (UnicodeAttribute): Yorum ID'si (primary key)
        forum_id (UnicodeAttribute): Yorumun ait olduğu forumun ID'si
        acan_kisi_id (UnicodeAttribute): Yorumu yapan kullanıcının ID'si
        icerik (UnicodeAttribute): Yorum içeriği
        acilis_tarihi (UTCDateTimeAttribute): Yorum açılış tarihi
        foto_urls (ListAttribute): Yorum resimlerinin URL'leri
        begeni_sayisi (NumberAttribute): Beğeni sayısı
        begenmeme_sayisi (NumberAttribute): Beğenmeme sayısı
        ust_yorum_id (UnicodeAttribute): Üst yorumun ID'si (yanıt ise)
    """
    
    class Meta:
        table_name = 'Comments'
    
    # Birincil anahtar
    comment_id = UnicodeAttribute(hash_key=True, default=lambda: f"cmt_{generate_uuid()}")
    
    # Indeksler
    forum_comments_index = ForumCommentsIndex()
    user_comments_index = UserCommentsIndex()
    parent_comment_index = ParentCommentIndex()
    
    # Yorum bilgileri
    forum_id = UnicodeAttribute()
    acan_kisi_id = UnicodeAttribute()
    icerik = UnicodeAttribute()
    acilis_tarihi = UTCDateTimeAttribute(default=datetime.now)
    foto_urls = ListAttribute(default=list)
    begeni_sayisi = NumberAttribute(default=0)
    begenmeme_sayisi = NumberAttribute(default=0)
    ust_yorum_id = UnicodeAttribute(null=True)
    
    def add_like(self):
        """
        Yorum beğeni sayısını artırır.
        """
        self.begeni_sayisi += 1
        self.save()
    
    def remove_like(self):
        """
        Yorum beğeni sayısını azaltır.
        """
        if self.begeni_sayisi > 0:
            self.begeni_sayisi -= 1
            self.save()
    
    def add_dislike(self):
        """
        Yorum beğenmeme sayısını artırır.
        """
        self.begenmeme_sayisi += 1
        self.save()
    
    def remove_dislike(self):
        """
        Yorum beğenmeme sayısını azaltır.
        """
        if self.begenmeme_sayisi > 0:
            self.begenmeme_sayisi -= 1
            self.save()
    
    def add_photo(self, photo_url):
        """
        Yoruma yeni bir fotoğraf ekler.
        
        Args:
            photo_url (str): Fotoğraf URL'si
        """
        if photo_url not in self.foto_urls:
            self.foto_urls.append(photo_url)
            self.save()
    
    def is_reply(self):
        """
        Yorumun bir yanıt olup olmadığını kontrol eder.
        
        Returns:
            bool: Yorumun bir yanıt olup olmadığı
        """
        return self.ust_yorum_id is not None
    
    def to_dict(self):
        """
        Yorum verisini sözlük olarak döndürür.
        
        Returns:
            dict: Yorum verisi
        """
        return super().to_dict()