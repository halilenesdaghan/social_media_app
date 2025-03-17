"""
Grup Veri Modeli
--------------
Grup verisinin DynamoDB modeli.
"""

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute, 
    ListAttribute, MapAttribute, NumberAttribute
)
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from app.models.base import BaseModel, generate_uuid
from datetime import datetime


class GroupNameIndex(GlobalSecondaryIndex):
    """
    Grup adı için Global Secondary Index (GSI).
    Grup adına göre hızlı arama sağlar.
    """
    
    class Meta:
        index_name = 'group-name-index'
        read_capacity_units = 5
        write_capacity_units = 5
        projection = AllProjection()
    
    grup_adi = UnicodeAttribute(hash_key=True)


class GroupMember(MapAttribute):
    """
    Grup üyeliği için map attribute.
    
    Attributes:
        kullanici_id (UnicodeAttribute): Üye kullanıcının ID'si
        rol (UnicodeAttribute): Kullanıcının gruptaki rolü (uye, moderator, yonetici)
        katilma_tarihi (UTCDateTimeAttribute): Gruba katılma tarihi
        durum (UnicodeAttribute): Üyelik durumu (aktif, beklemede, engellendi)
    """
    kullanici_id = UnicodeAttribute()
    rol = UnicodeAttribute(default='uye')
    katilma_tarihi = UTCDateTimeAttribute(default=datetime.now)
    durum = UnicodeAttribute(default='aktif')


class GroupModel(BaseModel):
    """
    Grup DynamoDB modeli.
    
    Attributes:
        group_id (UnicodeAttribute): Grup ID'si (primary key)
        grup_adi (UnicodeAttribute): Grup adı
        aciklama (UnicodeAttribute): Grup açıklaması
        olusturulma_tarihi (UTCDateTimeAttribute): Grup oluşturulma tarihi
        olusturan_id (UnicodeAttribute): Grubu oluşturan kullanıcının ID'si
        logo_url (UnicodeAttribute): Grup logo URL'si
        kapak_resmi_url (UnicodeAttribute): Grup kapak resmi URL'si
        gizlilik (UnicodeAttribute): Grup gizlilik ayarı (acik, kapali, gizli)
        kategoriler (ListAttribute): Grup kategorileri
        uyeler (ListAttribute): Grup üyeleri
        uye_sayisi (NumberAttribute): Grup üye sayısı
    """
    
    class Meta:
        table_name = 'Groups'
    
    # Birincil anahtar
    group_id = UnicodeAttribute(hash_key=True, default=lambda: f"grp_{generate_uuid()}")
    
    # Indeksler
    group_name_index = GroupNameIndex()
    
    # Grup bilgileri
    grup_adi = UnicodeAttribute()
    aciklama = UnicodeAttribute(null=True)
    olusturulma_tarihi = UTCDateTimeAttribute(default=datetime.now)
    olusturan_id = UnicodeAttribute()
    logo_url = UnicodeAttribute(null=True)
    kapak_resmi_url = UnicodeAttribute(null=True)
    gizlilik = UnicodeAttribute(default='acik')
    kategoriler = ListAttribute(default=list)
    uyeler = ListAttribute(of=GroupMember, default=list)
    uye_sayisi = NumberAttribute(default=1)  # Grup oluşturan kişi otomatik olarak üye olur
    
    def add_member(self, kullanici_id, rol='uye', durum='aktif'):
        """
        Gruba yeni bir üye ekler.
        
        Args:
            kullanici_id (str): Eklenecek kullanıcının ID'si
            rol (str, optional): Kullanıcının rolü (varsayılan: 'uye')
            durum (str, optional): Üyelik durumu (varsayılan: 'aktif')
            
        Returns:
            bool: İşlemin başarılı olup olmadığı
        """
        # Kullanıcının zaten üye olup olmadığını kontrol et
        for uye in self.uyeler:
            if uye.kullanici_id == kullanici_id:
                # Kullanıcı zaten üye, durumunu güncelle
                uye.rol = rol
                uye.durum = durum
                self.save()
                return True
        
        # Yeni üye ekle
        yeni_uye = GroupMember(
            kullanici_id=kullanici_id,
            rol=rol,
            katilma_tarihi=datetime.now(),
            durum=durum
        )
        self.uyeler.append(yeni_uye)
        
        # Aktif üye sayısını artır (eğer durum aktifse)
        if durum == 'aktif':
            self.uye_sayisi += 1
        
        self.save()
        return True
    
    def remove_member(self, kullanici_id):
        """
        Gruptan bir üyeyi çıkarır.
        
        Args:
            kullanici_id (str): Çıkarılacak kullanıcının ID'si
            
        Returns:
            bool: İşlemin başarılı olup olmadığı
        """
        # Kullanıcının grup oluşturucu olup olmadığını kontrol et
        if kullanici_id == self.olusturan_id:
            return False  # Grup oluşturucusu gruptan çıkarılamaz
        
        # Kullanıcıyı bul ve çıkar
        for i, uye in enumerate(self.uyeler):
            if uye.kullanici_id == kullanici_id:
                # Eğer üyelik aktifse, üye sayısını azalt
                if uye.durum == 'aktif':
                    self.uye_sayisi -= 1
                
                # Üyeyi listeden çıkar
                self.uyeler.pop(i)
                self.save()
                return True
        
        return False  # Kullanıcı bulunamadı
    
    def update_member_role(self, kullanici_id, yeni_rol):
        """
        Bir üyenin rolünü günceller.
        
        Args:
            kullanici_id (str): Rolü güncellenecek kullanıcının ID'si
            yeni_rol (str): Yeni rol (uye, moderator, yonetici)
            
        Returns:
            bool: İşlemin başarılı olup olmadığı
        """
        for uye in self.uyeler:
            if uye.kullanici_id == kullanici_id:
                uye.rol = yeni_rol
                self.save()
                return True
        
        return False  # Kullanıcı bulunamadı
    
    def get_members(self, durum='aktif'):
        """
        Belirli bir durumdaki grup üyelerini döndürür.
        
        Args:
            durum (str, optional): Üyelik durumu (varsayılan: 'aktif')
            
        Returns:
            list: Üye listesi
        """
        return [uye for uye in self.uyeler if uye.durum == durum]
    
    def is_member(self, kullanici_id):
        """
        Kullanıcının grup üyesi olup olmadığını kontrol eder.
        
        Args:
            kullanici_id (str): Kontrol edilecek kullanıcının ID'si
            
        Returns:
            bool: Kullanıcı aktif bir üyeyse True, değilse False
        """
        for uye in self.uyeler:
            if uye.kullanici_id == kullanici_id and uye.durum == 'aktif':
                return True
        return False
    
    def get_member_role(self, kullanici_id):
        """
        Kullanıcının gruptaki rolünü döndürür.
        
        Args:
            kullanici_id (str): Rolü sorgulanacak kullanıcının ID'si
            
        Returns:
            str: Kullanıcının rolü (kullanıcı aktif üye değilse None)
        """
        for uye in self.uyeler:
            if uye.kullanici_id == kullanici_id and uye.durum == 'aktif':
                return uye.rol
        return None
    
    def to_dict(self):
        """
        Grup verisini sözlük olarak döndürür.
        
        Returns:
            dict: Grup verisi
        """
        data = super().to_dict()
        
        # Üyeleri JSON serileştirilebilir formata dönüştür
        data['uyeler'] = [uye.as_dict() for uye in self.uyeler]
        
        return data