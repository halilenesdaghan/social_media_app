"""
Anket Veri Modeli
---------------
Anket verisinin DynamoDB modeli.
"""

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute, 
    ListAttribute, MapAttribute, NumberAttribute, JSONAttribute
)
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from app.models.base import BaseModel, generate_uuid
from datetime import datetime


class UserPollsIndex(GlobalSecondaryIndex):
    """
    Kullanıcı anketleri için Global Secondary Index (GSI).
    Belirli bir kullanıcının anketlerini hızlıca bulmak için kullanılır.
    """
    
    class Meta:
        index_name = 'user-polls-index'
        read_capacity_units = 5
        write_capacity_units = 5
        projection = AllProjection()
    
    acan_kisi_id = UnicodeAttribute(hash_key=True)
    acilis_tarihi = UTCDateTimeAttribute(range_key=True)


class PollOption(MapAttribute):
    """
    Anket seçeneği için map attribute.
    
    Attributes:
        option_id (UnicodeAttribute): Seçenek ID'si
        metin (UnicodeAttribute): Seçenek metni
        oy_sayisi (NumberAttribute): Seçeneğin oy sayısı
    """
    option_id = UnicodeAttribute()
    metin = UnicodeAttribute()
    oy_sayisi = NumberAttribute(default=0)


class PollVote(MapAttribute):
    """
    Anket oyları için map attribute.
    
    Attributes:
        kullanici_id (UnicodeAttribute): Oy veren kullanıcının ID'si
        secenek_id (UnicodeAttribute): Oy verilen seçeneğin ID'si
        tarih (UTCDateTimeAttribute): Oy verme tarihi
    """
    kullanici_id = UnicodeAttribute()
    secenek_id = UnicodeAttribute()
    tarih = UTCDateTimeAttribute(default=datetime.now)


class PollModel(BaseModel):
    """
    Anket DynamoDB modeli.
    
    Attributes:
        poll_id (UnicodeAttribute): Anket ID'si (primary key)
        baslik (UnicodeAttribute): Anket başlığı
        aciklama (UnicodeAttribute): Anket açıklaması
        acilis_tarihi (UTCDateTimeAttribute): Anket açılış tarihi
        bitis_tarihi (UTCDateTimeAttribute): Anket bitiş tarihi
        acan_kisi_id (UnicodeAttribute): Anketi açan kullanıcının ID'si
        secenekler (ListAttribute): Anket seçenekleri listesi
        oylar (ListAttribute): Anket oyları listesi
        universite (UnicodeAttribute): Anket açan kişinin üniversitesi
        kategori (UnicodeAttribute): Anket kategorisi
    """
    
    class Meta:
        table_name = 'Polls'
    
    # Birincil anahtar
    poll_id = UnicodeAttribute(hash_key=True, default=lambda: f"pol_{generate_uuid()}")
    
    # Indeksler
    user_polls_index = UserPollsIndex()
    
    # Anket bilgileri
    baslik = UnicodeAttribute()
    aciklama = UnicodeAttribute(null=True)
    acilis_tarihi = UTCDateTimeAttribute(default=datetime.now)
    bitis_tarihi = UTCDateTimeAttribute(null=True)
    acan_kisi_id = UnicodeAttribute()
    secenekler = ListAttribute(of=PollOption, default=list)
    oylar = ListAttribute(of=PollVote, default=list)
    universite = UnicodeAttribute(null=True)
    kategori = UnicodeAttribute(null=True)
    
    def add_option(self, metin):
        """
        Ankete yeni bir seçenek ekler.
        
        Args:
            metin (str): Seçenek metni
            
        Returns:
            str: Eklenen seçeneğin ID'si
        """
        option_id = generate_uuid()
        option = PollOption(
            option_id=option_id,
            metin=metin,
            oy_sayisi=0
        )
        self.secenekler.append(option)
        self.save()
        return option_id
    
    def add_vote(self, kullanici_id, secenek_id):
        """
        Ankete oy ekler. Eğer kullanıcı daha önce oy vermişse, oyunu günceller.
        
        Args:
            kullanici_id (str): Oy veren kullanıcının ID'si
            secenek_id (str): Oy verilen seçeneğin ID'si
            
        Returns:
            bool: İşlemin başarılı olup olmadığı
        """
        # Seçeneğin var olduğunu kontrol et
        secenek_varmi = False
        for secenek in self.secenekler:
            if secenek.option_id == secenek_id:
                secenek_varmi = True
                break
        
        if not secenek_varmi:
            return False
        
        # Kullanıcının daha önce oy verip vermediğini kontrol et
        eski_oy = None
        for i, oy in enumerate(self.oylar):
            if oy.kullanici_id == kullanici_id:
                eski_oy = oy
                eski_secenek_id = oy.secenek_id
                self.oylar.pop(i)
                break
        
        # Eğer önceki oy varsa, seçeneğin oy sayısını azalt
        if eski_oy:
            for secenek in self.secenekler:
                if secenek.option_id == eski_secenek_id:
                    secenek.oy_sayisi -= 1
                    break
        
        # Yeni oy ekle
        yeni_oy = PollVote(
            kullanici_id=kullanici_id,
            secenek_id=secenek_id,
            tarih=datetime.now()
        )
        self.oylar.append(yeni_oy)
        
        # Seçeneğin oy sayısını artır
        for secenek in self.secenekler:
            if secenek.option_id == secenek_id:
                secenek.oy_sayisi += 1
                break
        
        self.save()
        return True
    
    def get_results(self):
        """
        Anket sonuçlarını döndürür.
        
        Returns:
            list: Seçenekler ve oy sayıları
        """
        results = []
        for secenek in self.secenekler:
            results.append({
                'option_id': secenek.option_id,
                'metin': secenek.metin,
                'oy_sayisi': secenek.oy_sayisi
            })
        return results
    
    def is_active(self):
        """
        Anketin aktif olup olmadığını kontrol eder.
        
        Returns:
            bool: Anket aktifse True, değilse False
        """
        # Bitiş tarihi belirtilmemişse anket aktiftir
        if not self.bitis_tarihi:
            return True
        
        # Bitiş tarihi geçmişse anket aktif değildir
        return datetime.now() < self.bitis_tarihi
    
    def to_dict(self):
        """
        Anket verisini sözlük olarak döndürür.
        
        Returns:
            dict: Anket verisi
        """
        data = super().to_dict()
        
        # Seçenekleri ve oyları JSON serileştirilebilir formata dönüştür
        data['secenekler'] = [secenek.as_dict() for secenek in self.secenekler]
        data['oylar'] = [oy.as_dict() for oy in self.oylar]
        data['aktif'] = self.is_active()
        
        return data