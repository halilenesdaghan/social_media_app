"""
Kullanıcı Veri Modeli
-------------------
Kullanıcı verisinin DynamoDB modeli.
"""

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute, 
    ListAttribute, MapAttribute, NumberAttribute
)
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from app.models.base import BaseModel, generate_uuid
from app.utils.auth import hash_password, check_password


class EmailIndex(GlobalSecondaryIndex):
    """
    E-posta için Global Secondary Index (GSI).
    E-posta ile hızlı kullanıcı araması sağlar.
    """
    
    class Meta:
        index_name = 'email-index'
        read_capacity_units = 5
        write_capacity_units = 5
        projection = AllProjection()
    
    email = UnicodeAttribute(hash_key=True)


class UsernameIndex(GlobalSecondaryIndex):
    """
    Kullanıcı adı için Global Secondary Index (GSI).
    Kullanıcı adı ile hızlı kullanıcı araması sağlar.
    """
    
    class Meta:
        index_name = 'username-index'
        read_capacity_units = 5
        write_capacity_units = 5
        projection = AllProjection()
    
    username = UnicodeAttribute(hash_key=True)


class UserModel(BaseModel):
    """
    Kullanıcı DynamoDB modeli.
    
    Attributes:
        user_id (UnicodeAttribute): Kullanıcı ID'si (primary key)
        email (UnicodeAttribute): E-posta adresi (unique)
        username (UnicodeAttribute): Kullanıcı adı (unique)
        password_hash (UnicodeAttribute): Şifre hash'i
        cinsiyet (UnicodeAttribute): Cinsiyet (Erkek, Kadın, Diğer)
        kayit_tarihi (UTCDateTimeAttribute): Kayıt tarihi
        universite (UnicodeAttribute): Okuduğu üniversite
        role (UnicodeAttribute): Kullanıcı rolü (user, moderator, admin)
        son_giris_tarihi (UTCDateTimeAttribute): Son giriş tarihi
        profil_resmi_url (UnicodeAttribute): Profil resmi URL'si
        grup_ids (ListAttribute): Üye olduğu grupların ID'leri
        forum_ids (ListAttribute): Açtığı forumların ID'leri
        anket_ids (ListAttribute): Açtığı anketlerin ID'leri
    """
    
    class Meta:
        table_name = 'Users'
    
    # Birincil anahtar
    user_id = UnicodeAttribute(hash_key=True, default=lambda: f"usr_{generate_uuid()}")
    
    # Global Secondary Indexes
    email_index = EmailIndex()
    username_index = UsernameIndex()
    
    # Kullanıcı bilgileri
    email = UnicodeAttribute()
    username = UnicodeAttribute()
    password_hash = UnicodeAttribute()
    cinsiyet = UnicodeAttribute(null=True)
    kayit_tarihi = UTCDateTimeAttribute()
    universite = UnicodeAttribute(null=True)
    role = UnicodeAttribute(default='user')
    son_giris_tarihi = UTCDateTimeAttribute(null=True)
    profil_resmi_url = UnicodeAttribute(null=True)
    
    # İlişkili veriler (NoSQL yaklaşımı)
    grup_ids = ListAttribute(default=list)
    forum_ids = ListAttribute(default=list)
    anket_ids = ListAttribute(default=list)
    
    def set_password(self, password):
        """
        Kullanıcı şifresini ayarlar (hash'leyerek).
        
        Args:
            password (str): Ham şifre
        """
        self.password_hash = hash_password(password)
    
    def check_password(self, password):
        """
        Verilen şifrenin kullanıcı şifresiyle eşleşip eşleşmediğini kontrol eder.
        
        Args:
            password (str): Kontrol edilecek şifre
        
        Returns:
            bool: Şifreler eşleşiyorsa True, aksi halde False
        """
        return check_password(password, self.password_hash)
    
    def add_forum(self, forum_id):
        """
        Kullanıcının forum listesine yeni bir forum ekler.
        
        Args:
            forum_id (str): Forum ID'si
        """
        if forum_id not in self.forum_ids:
            self.forum_ids.append(forum_id)
            self.save()
    
    def add_group(self, group_id):
        """
        Kullanıcının grup listesine yeni bir grup ekler.
        
        Args:
            group_id (str): Grup ID'si
        """
        if group_id not in self.grup_ids:
            self.grup_ids.append(group_id)
            self.save()
    
    def add_poll(self, poll_id):
        """
        Kullanıcının anket listesine yeni bir anket ekler.
        
        Args:
            poll_id (str): Anket ID'si
        """
        if poll_id not in self.anket_ids:
            self.anket_ids.append(poll_id)
            self.save()
    
    def to_dict(self):
        """
        Kullanıcı verisini sözlük olarak döndürür (hassas veriler olmadan).
        
        Returns:
            dict: Kullanıcı verisi
        """
        data = super().to_dict()
        
        # Hassas alanları kaldır
        data.pop('password_hash', None)
        
        return data