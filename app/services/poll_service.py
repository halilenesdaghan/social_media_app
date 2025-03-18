"""
Anket Servisi
-----------
Anket oluşturma, listeleme, oylama ve yönetim işlemleri için servis fonksiyonları.
"""

import logging
import uuid
from datetime import datetime
from pynamodb.exceptions import DoesNotExist
from app.models.poll import PollModel, PollOption, PollVote
from app.models.user import UserModel
from app.utils.exceptions import NotFoundError, ValidationError, ForbiddenError

# Logger yapılandırması
logger = logging.getLogger(__name__)

class PollService:
    """
    Anket servisi.
    
    Anket oluşturma, listeleme, güncelleme, silme ve oylama işlemlerini gerçekleştirir.
    """
    
    def create_poll(self, user_id, poll_data):
        """
        Yeni anket oluşturur.
        
        Args:
            user_id (str): Anketi oluşturan kullanıcı ID'si
            poll_data (dict): Anket verileri
            
        Returns:
            dict: Oluşturulan anket bilgileri
            
        Raises:
            ValidationError: Anket verileri geçersizse
            NotFoundError: Kullanıcı bulunamazsa
        """
        try:
            # Kullanıcıyı kontrol et
            user = UserModel.get(user_id)
            
            if not user.is_active:
                raise NotFoundError("Kullanıcı bulunamadı")
            
            # Gerekli alanları doğrula
            if 'baslik' not in poll_data or not poll_data['baslik']:
                raise ValidationError("Anket başlığı zorunludur")
            
            if 'secenekler' not in poll_data or len(poll_data['secenekler']) < 2:
                raise ValidationError("En az iki seçenek gereklidir")
            
            # Bitiş tarihi varsa doğrula
            bitis_tarihi = None
            if 'bitis_tarihi' in poll_data and poll_data['bitis_tarihi']:
                try:
                    bitis_tarihi = datetime.fromisoformat(poll_data['bitis_tarihi'])
                    if bitis_tarihi <= datetime.now():
                        raise ValidationError("Bitiş tarihi gelecekte olmalıdır")
                except ValueError:
                    raise ValidationError("Geçersiz tarih formatı. ISO 8601 formatı kullanın (YYYY-MM-DDTHH:MM:SS)")
            
            # Anket oluştur
            poll = PollModel(
                baslik=poll_data['baslik'],
                aciklama=poll_data.get('aciklama', ''),
                acan_kisi_id=user_id,
                bitis_tarihi=bitis_tarihi,
                universite=poll_data.get('universite', user.universite),
                kategori=poll_data.get('kategori')
            )
            
            # Seçenekleri ekle
            for secenek_metin in poll_data['secenekler']:
                poll.add_option(secenek_metin)
            
            poll.save()
            logger.info(f"Yeni anket oluşturuldu: {poll.poll_id} (Kullanıcı: {user_id})")
            
            # Kullanıcının anket listesini güncelle
            user.add_poll(poll.poll_id)
            
            return poll.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Kullanıcı bulunamadı")
        except Exception as e:
            logger.error(f"Anket oluşturma hatası: {str(e)}")
            if isinstance(e, (ValidationError, NotFoundError)):
                raise
            raise ValidationError("Anket oluşturulamadı")
    
    def get_poll_by_id(self, poll_id):
        """
        ID'ye göre anket getirir.
        
        Args:
            poll_id (str): Anket ID'si
            
        Returns:
            dict: Anket bilgileri
            
        Raises:
            NotFoundError: Anket bulunamazsa
        """
        try:
            poll = PollModel.get(poll_id)
            
            if not poll.is_active:
                raise NotFoundError("Anket bulunamadı")
            
            return poll.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Anket bulunamadı")
    
    def update_poll(self, poll_id, user_id, update_data):
        """
        Anket bilgilerini günceller.
        
        Args:
            poll_id (str): Anket ID'si
            user_id (str): İşlemi yapan kullanıcı ID'si
            update_data (dict): Güncellenecek veriler
            
        Returns:
            dict: Güncellenmiş anket bilgileri
            
        Raises:
            NotFoundError: Anket bulunamazsa
            ForbiddenError: Kullanıcının yetkisi yoksa
            ValidationError: Güncellenecek veriler geçersizse
        """
        try:
            poll = PollModel.get(poll_id)
            
            if not poll.is_active:
                raise NotFoundError("Anket bulunamadı")
            
            # Yetki kontrolü
            if poll.acan_kisi_id != user_id:
                # Admin yetkisi kontrolü eklenebilir
                user = UserModel.get(user_id)
                if user.role != 'admin':
                    raise ForbiddenError("Bu anketi düzenleme yetkiniz yok")
            
            # Güncellenebilir alanlar
            fields_to_update = ['baslik', 'aciklama', 'kategori', 'bitis_tarihi']
            
            # Alanları güncelle
            updated = False
            for field in fields_to_update:
                if field in update_data and update_data[field] is not None:
                    # Bitiş tarihi özel olarak işle
                    if field == 'bitis_tarihi':
                        try:
                            bitis_tarihi = datetime.fromisoformat(update_data[field])
                            setattr(poll, field, bitis_tarihi)
                        except ValueError:
                            raise ValidationError("Geçersiz tarih formatı. ISO 8601 formatı kullanın (YYYY-MM-DDTHH:MM:SS)")
                    else:
                        setattr(poll, field, update_data[field])
                    updated = True
            
            # Seçenekler değiştirilmek isteniyorsa
            if 'secenekler' in update_data and isinstance(update_data['secenekler'], list):
                if len(update_data['secenekler']) < 2:
                    raise ValidationError("En az iki seçenek gereklidir")
                
                # Seçenekleri güncelle
                new_options = []
                for secenek_metin in update_data['secenekler']:
                    new_options.append(PollOption(
                        option_id=str(uuid.uuid4()),
                        metin=secenek_metin,
                        oy_sayisi=0
                    ))
                
                poll.secenekler = new_options
                updated = True
            
            if updated:
                poll.save()
                logger.info(f"Anket güncellendi: {poll_id}")
            
            return poll.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Anket bulunamadı")
    
    def delete_poll(self, poll_id, user_id):
        """
        Anketi siler.
        
        Args:
            poll_id (str): Anket ID'si
            user_id (str): İşlemi yapan kullanıcı ID'si
            
        Returns:
            bool: İşlem başarılıysa True
            
        Raises:
            NotFoundError: Anket bulunamazsa
            ForbiddenError: Kullanıcının yetkisi yoksa
        """
        try:
            poll = PollModel.get(poll_id)
            
            if not poll.is_active:
                raise NotFoundError("Anket bulunamadı")
            
            # Yetki kontrolü
            if poll.acan_kisi_id != user_id:
                # Admin yetkisi kontrolü eklenebilir
                user = UserModel.get(user_id)
                if user.role != 'admin':
                    raise ForbiddenError("Bu anketi silme yetkiniz yok")
            
            # Anketi devre dışı bırak (soft delete)
            poll.soft_delete()
            
            logger.info(f"Anket silindi: {poll_id}")
            
            return True
            
        except DoesNotExist:
            raise NotFoundError("Anket bulunamadı")
    
    def get_all_polls(self, page=1, per_page=10, kategori=None, universite=None, aktif=None):
        """
        Tüm anketleri getirir.
        
        Args:
            page (int, optional): Sayfa numarası
            per_page (int, optional): Sayfa başına anket sayısı
            kategori (str, optional): Kategori filtresi
            universite (str, optional): Üniversite filtresi
            aktif (bool, optional): Aktiflik durumu filtresi
            
        Returns:
            dict: Anketler ve meta bilgiler
        """
        # Filtreleme koşulları
        def match_filters(poll):
            # Aktif mi kontrol et
            if not poll.is_active:
                return False
            
            # Kategori filtresi
            if kategori and poll.kategori != kategori:
                return False
            
            # Üniversite filtresi
            if universite and poll.universite != universite:
                return False
            
            # Aktiflik filtresi (anketi açık mı kapalı mı)
            if aktif is not None:
                is_active_poll = poll.is_active()
                if aktif != is_active_poll:
                    return False
            
            return True
        
        try:
            # Tüm anketleri getir (scan)
            poll_list = []
            total_count = 0
            
            for poll in PollModel.scan():
                if match_filters(poll):
                    total_count += 1
                    
                    # Sayfalama kontrolü
                    if total_count > (page - 1) * per_page and total_count <= page * per_page:
                        poll_list.append(poll.to_dict())
            
            return {
                'polls': poll_list,
                'meta': {
                    'total': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            }
        
        except Exception as e:
            logger.error(f"Anketleri getirme hatası: {str(e)}")
            # Hata durumunda boş liste döndür
            return {
                'polls': [],
                'meta': {
                    'total': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                }
            }
    
    def vote_poll(self, poll_id, user_id, option_id):
        """
        Ankete oy verir.
        
        Args:
            poll_id (str): Anket ID'si
            user_id (str): Oy veren kullanıcı ID'si
            option_id (str): Oy verilen seçeneğin ID'si
            
        Returns:
            dict: Oylama sonucu
            
        Raises:
            NotFoundError: Anket veya seçenek bulunamazsa
            ValidationError: Oylama işlemi geçersizse
        """
        try:
            poll = PollModel.get(poll_id)
            
            if not poll.is_active:
                raise NotFoundError("Anket bulunamadı")
            
            # Anket aktif mi kontrol et
            if not poll.is_active():
                raise ValidationError("Bu anket artık aktif değil")
            
            # Seçenek geçerli mi kontrol et
            option_exists = False
            for option in poll.secenekler:
                if option.option_id == option_id:
                    option_exists = True
                    break
            
            if not option_exists:
                raise NotFoundError("Geçersiz seçenek")
            
            # Oy ekle
            poll.add_vote(user_id, option_id)
            
            # Sonuçları döndür
            return {
                'message': 'Oyunuz kaydedildi',
                'results': poll.get_results()
            }
            
        except DoesNotExist:
            raise NotFoundError("Anket bulunamadı")
    
    def get_poll_results(self, poll_id):
        """
        Anket sonuçlarını getirir.
        
        Args:
            poll_id (str): Anket ID'si
            
        Returns:
            dict: Anket sonuçları
            
        Raises:
            NotFoundError: Anket bulunamazsa
        """
        try:
            poll = PollModel.get(poll_id)
            
            if not poll.is_active:
                raise NotFoundError("Anket bulunamadı")
            
            return {
                'poll': {
                    'poll_id': poll.poll_id,
                    'baslik': poll.baslik,
                    'aciklama': poll.aciklama,
                    'aktif': poll.is_active()
                },
                'results': poll.get_results(),
                'total_votes': sum(option.oy_sayisi for option in poll.secenekler)
            }
            
        except DoesNotExist:
            raise NotFoundError("Anket bulunamadı")

# Servis singleton'ı
poll_service = PollService()