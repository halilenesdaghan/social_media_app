"""
Grup Servisi
----------
Grup oluşturma, yönetme ve üyelik işlemleri için servis sınıfı.
"""

import logging
from datetime import datetime
from pynamodb.exceptions import DoesNotExist
from app.models.group import GroupModel, GroupMember
from app.models.user import UserModel
from app.utils.exceptions import NotFoundError, ValidationError, ForbiddenError
import uuid

# Logger yapılandırması
logger = logging.getLogger(__name__)

class GroupService:
    """
    Grup servisi.
    
    Grup oluşturma, listeleme, üyelik ve yönetme işlemlerini gerçekleştirir.
    """
    
    def create_group(self, user_id, group_data):
        """
        Yeni grup oluşturur.
        
        Args:
            user_id (str): Grubu oluşturan kullanıcı ID'si
            group_data (dict): Grup verileri
            
        Returns:
            dict: Oluşturulan grup bilgileri
            
        Raises:
            ValidationError: Grup verileri geçersizse
            NotFoundError: Kullanıcı bulunamazsa
        """
        try:
            # Kullanıcıyı kontrol et
            user = UserModel.get(user_id)
            
            if not user.is_active:
                raise NotFoundError("Kullanıcı bulunamadı")
            
            # Gerekli alanları doğrula
            if 'grup_adi' not in group_data or not group_data['grup_adi']:
                raise ValidationError("Grup adı zorunludur")
            
            # Grup adı benzersiz mi kontrol et
            for group in GroupModel.scan(
                GroupModel.grup_adi == group_data['grup_adi'],
                GroupModel.is_active == True
            ):
                raise ValidationError("Bu grup adı zaten kullanılıyor")
            
            # Grup oluştur
            group = GroupModel(
                group_id=f"grp_{uuid.uuid4()}",
                grup_adi=group_data['grup_adi'],
                aciklama=group_data.get('aciklama', ''),
                olusturulma_tarihi=datetime.now(),
                olusturan_id=user_id,
                logo_url=group_data.get('logo_url'),
                kapak_resmi_url=group_data.get('kapak_resmi_url'),
                gizlilik=group_data.get('gizlilik', 'acik'),
                kategoriler=group_data.get('kategoriler', [])
            )
            
            # Oluşturan kişiyi yönetici olarak ekle
            kurucu_uye = GroupMember(
                kullanici_id=user_id,
                rol='yonetici',
                katilma_tarihi=datetime.now(),
                durum='aktif'
            )
            
            group.uyeler = [kurucu_uye]
            group.uye_sayisi = 1
            
            group.save()
            logger.info(f"Yeni grup oluşturuldu: {group.group_id} (Kullanıcı: {user_id})")
            
            # Kullanıcının grup listesini güncelle
            user.add_group(group.group_id)
            
            return group.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Kullanıcı bulunamadı")
        except Exception as e:
            logger.error(f"Grup oluşturma hatası: {str(e)}")
            if isinstance(e, (ValidationError, NotFoundError)):
                raise
            raise ValidationError("Grup oluşturulamadı")
    
    def get_group_by_id(self, group_id):
        """
        ID'ye göre grup getirir.
        
        Args:
            group_id (str): Grup ID'si
            
        Returns:
            dict: Grup bilgileri
            
        Raises:
            NotFoundError: Grup bulunamazsa
        """
        try:
            group = GroupModel.get(group_id)
            
            if not group.is_active:
                raise NotFoundError("Grup bulunamadı")
            
            return group.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Grup bulunamadı")
    
    def update_group(self, group_id, user_id, update_data):
        """
        Grup bilgilerini günceller.
        
        Args:
            group_id (str): Grup ID'si
            user_id (str): İşlemi yapan kullanıcı ID'si
            update_data (dict): Güncellenecek veriler
            
        Returns:
            dict: Güncellenmiş grup bilgileri
            
        Raises:
            NotFoundError: Grup bulunamazsa
            ForbiddenError: Kullanıcının yetkisi yoksa
            ValidationError: Güncellenecek veriler geçersizse
        """
        try:
            group = GroupModel.get(group_id)
            
            if not group.is_active:
                raise NotFoundError("Grup bulunamadı")
            
            # Yetki kontrolü
            has_permission = False
            
            # Grup kurucusu mu?
            if group.olusturan_id == user_id:
                has_permission = True
            else:
                # Grup yöneticisi mi?
                for uye in group.uyeler:
                    if uye.kullanici_id == user_id and uye.rol == 'yonetici' and uye.durum == 'aktif':
                        has_permission = True
                        break
                
                # Admin mi?
                if not has_permission:
                    try:
                        user = UserModel.get(user_id)
                        if user.role == 'admin':
                            has_permission = True
                    except:
                        pass
            
            if not has_permission:
                raise ForbiddenError("Bu grubu düzenleme yetkiniz yok")
            
            # Güncellenebilir alanlar
            update_fields = [
                'grup_adi', 
                'aciklama', 
                'logo_url', 
                'kapak_resmi_url', 
                'gizlilik', 
                'kategoriler'
            ]
            
            # Alanları güncelle
            updated = False
            for field in update_fields:
                if field in update_data and update_data[field] is not None:
                    # Grup adı değiştiriliyorsa benzersizliği kontrol et
                    if field == 'grup_adi' and update_data[field] != group.grup_adi:
                        for existing_group in GroupModel.scan(
                            GroupModel.grup_adi == update_data[field],
                            GroupModel.is_active == True
                        ):
                            raise ValidationError("Bu grup adı zaten kullanılıyor")
                    
                    setattr(group, field, update_data[field])
                    updated = True
            
            if updated:
                group.save()
                logger.info(f"Grup güncellendi: {group_id}")
            
            return group.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Grup bulunamadı")
    
    def delete_group(self, group_id, user_id):
        """
        Grubu siler (soft delete).
        
        Args:
            group_id (str): Grup ID'si
            user_id (str): İşlemi yapan kullanıcı ID'si
            
        Returns:
            bool: İşlem başarılıysa True
            
        Raises:
            NotFoundError: Grup bulunamazsa
            ForbiddenError: Kullanıcının yetkisi yoksa
        """
        try:
            group = GroupModel.get(group_id)
            
            if not group.is_active:
                raise NotFoundError("Grup bulunamadı")
            
            # Yetki kontrolü
            if group.olusturan_id != user_id:
                # Admin mi?
                user = UserModel.get(user_id)
                if user.role != 'admin':
                    raise ForbiddenError("Bu grubu silme yetkiniz yok")
            
            # Grubu devre dışı bırak (soft delete)
            group.soft_delete()
            
            logger.info(f"Grup silindi: {group_id}")
            
            return True
            
        except DoesNotExist:
            raise NotFoundError("Grup bulunamadı")
    
    def join_group(self, group_id, user_id):
        """
        Gruba üye olur.
        
        Args:
            group_id (str): Grup ID'si
            user_id (str): Kullanıcı ID'si
            
        Returns:
            dict: Güncellenmiş grup üyelik bilgileri
            
        Raises:
            NotFoundError: Grup bulunamazsa
            ValidationError: Kullanıcı zaten grup üyesiyse
        """
        try:
            group = GroupModel.get(group_id)
            
            if not group.is_active:
                raise NotFoundError("Grup bulunamadı")
            
            # Kullanıcı zaten üye mi kontrol et
            for uye in group.uyeler:
                if uye.kullanici_id == user_id:
                    if uye.durum == 'aktif':
                        raise ValidationError("Zaten grup üyesisiniz")
                    elif uye.durum == 'beklemede':
                        raise ValidationError("Üyelik başvurunuz onay bekliyor")
                    elif uye.durum == 'engellendi':
                        raise ValidationError("Bu gruba katılmanız engellendi")
            
            # Üyelik durumunu belirle
            durum = 'aktif'
            if group.gizlilik == 'kapali':
                durum = 'beklemede'
            
            # Kullanıcıyı üye olarak ekle
            yeni_uye = GroupMember(
                kullanici_id=user_id,
                rol='uye',
                katilma_tarihi=datetime.now(),
                durum=durum
            )
            
            group.uyeler.append(yeni_uye)
            
            # Aktif üye sayısını güncelle
            if durum == 'aktif':
                group.uye_sayisi += 1
            
            group.save()
            
            # Kullanıcının grup listesini güncelle
            user = UserModel.get(user_id)
            user.add_group(group_id)
            
            return {
                'status': 'success',
                'message': 'Gruba başarıyla katıldınız' if durum == 'aktif' else 'Üyelik başvurunuz onay bekliyor',
                'membership_status': durum
            }
            
        except DoesNotExist:
            raise NotFoundError("Grup bulunamadı")
    
    def leave_group(self, group_id, user_id):
        """
        Gruptan ayrılır.
        
        Args:
            group_id (str): Grup ID'si
            user_id (str): Kullanıcı ID'si
            
        Returns:
            bool: İşlem başarılıysa True
            
        Raises:
            NotFoundError: Grup bulunamazsa
            ValidationError: Kullanıcı grup üyesi değilse
            ForbiddenError: Kullanıcı grup kurucusuysa (kurucu gruptan ayrılamaz)
        """
        try:
            group = GroupModel.get(group_id)
            
            if not group.is_active:
                raise NotFoundError("Grup bulunamadı")
            
            # Grup kurucusu mu kontrol et
            if group.olusturan_id == user_id:
                raise ForbiddenError("Grup kurucusu gruptan ayrılamaz")
            
            # Kullanıcı üye mi kontrol et
            uye_index = None
            for i, uye in enumerate(group.uyeler):
                if uye.kullanici_id == user_id:
                    uye_index = i
                    break
            
            if uye_index is None:
                raise ValidationError("Bu grubun üyesi değilsiniz")
            
            # Üyeliği kaldır
            uye = group.uyeler.pop(uye_index)
            
            # Aktif üye sayısını güncelle
            if uye.durum == 'aktif':
                group.uye_sayisi = max(1, group.uye_sayisi - 1)
            
            group.save()
            
            return True
            
        except DoesNotExist:
            raise NotFoundError("Grup bulunamadı")
    
    def update_member_role(self, group_id, user_id, target_user_id, new_role):
        """
        Grup üyesinin rolünü günceller.
        
        Args:
            group_id (str): Grup ID'si
            user_id (str): İşlemi yapan kullanıcı ID'si
            target_user_id (str): Rolü değiştirilecek kullanıcı ID'si
            new_role (str): Yeni rol ('uye', 'moderator', 'yonetici')
            
        Returns:
            dict: Güncellenmiş üyelik bilgileri
            
        Raises:
            NotFoundError: Grup veya kullanıcı bulunamazsa
            ForbiddenError: Kullanıcının yetkisi yoksa
            ValidationError: Rol geçersizse
        """
        if new_role not in ['uye', 'moderator', 'yonetici']:
            raise ValidationError("Geçersiz rol")
        
        try:
            group = GroupModel.get(group_id)
            
            if not group.is_active:
                raise NotFoundError("Grup bulunamadı")
            
            # Yetki kontrolü
            has_permission = False
            
            # Grup kurucusu mu?
            if group.olusturan_id == user_id:
                has_permission = True
            else:
                # Grup yöneticisi mi?
                for uye in group.uyeler:
                    if uye.kullanici_id == user_id and uye.rol == 'yonetici' and uye.durum == 'aktif':
                        has_permission = True
                        break
            
            if not has_permission:
                raise ForbiddenError("Üyelerin rollerini değiştirme yetkiniz yok")
            
            # Hedef kullanıcı üye mi kontrol et
            target_member = None
            for uye in group.uyeler:
                if uye.kullanici_id == target_user_id:
                    target_member = uye
                    break
            
            if target_member is None:
                raise NotFoundError("Kullanıcı bu grubun üyesi değil")
            
            # Aktif üye mi kontrol et
            if target_member.durum != 'aktif':
                raise ValidationError("Sadece aktif üyelerin rolleri değiştirilebilir")
            
            # Grup kurucusunun rolü değiştirilemez
            if target_user_id == group.olusturan_id:
                raise ForbiddenError("Grup kurucusunun rolü değiştirilemez")
            
            # Rolü güncelle
            target_member.rol = new_role
            group.save()
            
            return {
                'status': 'success',
                'user_id': target_user_id,
                'role': new_role
            }
            
        except DoesNotExist:
            raise NotFoundError("Grup bulunamadı")
    
    def approve_membership(self, group_id, user_id, target_user_id, approve=True):
        """
        Grup üyelik başvurusunu onaylar veya reddeder.
        
        Args:
            group_id (str): Grup ID'si
            user_id (str): İşlemi yapan kullanıcı ID'si
            target_user_id (str): Üyelik başvurusu onaylanacak/reddedilecek kullanıcı ID'si
            approve (bool, optional): True ise onaylar, False ise reddeder
            
        Returns:
            dict: Güncellenmiş üyelik bilgileri
            
        Raises:
            NotFoundError: Grup veya kullanıcı bulunamazsa
            ForbiddenError: Kullanıcının yetkisi yoksa
            ValidationError: Üyelik durumu uygun değilse
        """
        try:
            group = GroupModel.get(group_id)
            
            if not group.is_active:
                raise NotFoundError("Grup bulunamadı")
            
            # Yetki kontrolü
            has_permission = False
            
            # Grup kurucusu mu?
            if group.olusturan_id == user_id:
                has_permission = True
            else:
                # Grup yöneticisi mi?
                for uye in group.uyeler:
                    if uye.kullanici_id == user_id and uye.rol in ['yonetici', 'moderator'] and uye.durum == 'aktif':
                        has_permission = True
                        break
            
            if not has_permission:
                raise ForbiddenError("Üyelik başvurularını yönetme yetkiniz yok")
            
            # Hedef kullanıcı üye mi kontrol et
            target_member = None
            for uye in group.uyeler:
                if uye.kullanici_id == target_user_id:
                    target_member = uye
                    break
            
            if target_member is None:
                raise NotFoundError("Kullanıcı bu gruba başvurmamış")
            
            # Beklemede durumunda mı kontrol et
            if target_member.durum != 'beklemede':
                raise ValidationError("Bu kullanıcının onay bekleyen bir başvurusu yok")
            
            # Üyeliği güncelle
            if approve:
                target_member.durum = 'aktif'
                group.uye_sayisi += 1
                message = "Üyelik başvurusu onaylandı"
            else:
                # Üyeliği kaldır
                group.uyeler = [uye for uye in group.uyeler if uye.kullanici_id != target_user_id]
                message = "Üyelik başvurusu reddedildi"
            
            group.save()
            
            return {
                'status': 'success',
                'message': message
            }
            
        except DoesNotExist:
            raise NotFoundError("Grup bulunamadı")
    
    def get_group_members(self, group_id, page=1, per_page=20, status=None, role=None):
        """
        Grup üyelerini getirir.
        
        Args:
            group_id (str): Grup ID'si
            page (int, optional): Sayfa numarası
            per_page (int, optional): Sayfa başına üye sayısı
            status (str, optional): Üyelik durumu filtresi ('aktif', 'beklemede', 'engellendi')
            role (str, optional): Rol filtresi ('uye', 'moderator', 'yonetici')
            
        Returns:
            dict: Üyeler ve meta bilgiler
            
        Raises:
            NotFoundError: Grup bulunamazsa
        """
        try:
            group = GroupModel.get(group_id)
            
            if not group.is_active:
                raise NotFoundError("Grup bulunamadı")
            
            # Filtreleme ve sayfalama
            filtered_members = []
            
            for uye in group.uyeler:
                # Durum filtresi
                if status and uye.durum != status:
                    continue
                
                # Rol filtresi
                if role and uye.rol != role:
                    continue
                
                filtered_members.append(uye)
            
            # Toplam sayı
            total_count = len(filtered_members)
            
            # Sayfalama
            start_index = (page - 1) * per_page
            end_index = min(start_index + per_page, total_count)
            
            paged_members = filtered_members[start_index:end_index]
            
            # Üye detaylarını al
            member_details = []
            for uye in paged_members:
                try:
                    user = UserModel.get(uye.kullanici_id)
                    member_details.append({
                        'user_id': uye.kullanici_id,
                        'username': user.username,
                        'profil_resmi_url': user.profil_resmi_url,
                        'rol': uye.rol,
                        'durum': uye.durum,
                        'katilma_tarihi': uye.katilma_tarihi.isoformat() if uye.katilma_tarihi else None
                    })
                except DoesNotExist:
                    # Kullanıcı bulunamadıysa atlayalım
                    continue
            
            return {
                'members': member_details,
                'meta': {
                    'total': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            }
            
        except DoesNotExist:
            raise NotFoundError("Grup bulunamadı")
    
    def get_all_groups(self, page=1, per_page=10, search=None, kategoriler=None):
        """
        Tüm grupları getirir.
        
        Args:
            page (int, optional): Sayfa numarası
            per_page (int, optional): Sayfa başına grup sayısı
            search (str, optional): Arama metni
            kategoriler (list, optional): Kategori filtresi
            
        Returns:
            dict: Gruplar ve meta bilgiler
        """
        # Filtreleme koşulları
        def match_filters(group):
            # Aktif mi kontrol et
            if not group.is_active:
                return False
            
            # Arama filtresi
            if search:
                search_lower = search.lower()
                if (search_lower not in group.grup_adi.lower() and 
                    (not group.aciklama or search_lower not in group.aciklama.lower())):
                    return False
            
            # Kategori filtresi
            if kategoriler:
                if not any(kat in group.kategoriler for kat in kategoriler):
                    return False
            
            return True
        
        try:
            # Tüm grupları getir
            groups = []
            total_count = 0
            
            for group in GroupModel.scan():
                if match_filters(group):
                    total_count += 1
                    
                    # Sayfalama kontrolü
                    if total_count > (page - 1) * per_page and total_count <= page * per_page:
                        groups.append(group.to_dict())
            
            return {
                'groups': groups,
                'meta': {
                    'total': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            }
        
        except Exception as e:
            logger.error(f"Grupları getirme hatası: {str(e)}")
            # Hata durumunda boş liste döndür
            return {
                'groups': [],
                'meta': {
                    'total': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                }
            }

# Servis singleton'ı
group_service = GroupService()