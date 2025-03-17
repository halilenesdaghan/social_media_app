"""
Kullanıcı Servisi
---------------
Kullanıcı bilgilerini ve hesap yönetimi işlemlerini gerçekleştirir.
"""

import logging
from datetime import datetime
from pynamodb.exceptions import DoesNotExist
from app.models.user import UserModel
from app.models.forum import ForumModel
from app.models.comment import CommentModel
from app.models.poll import PollModel
from app.models.group import GroupModel
from app.utils.exceptions import NotFoundError, ValidationError, ForbiddenError
from app.utils.auth import hash_password

# Logger yapılandırması
logger = logging.getLogger(__name__)

class UserService:
    """
    Kullanıcı servisi.
    
    Kullanıcı bilgilerini yönetir, kullanıcı forumlarını, yorumlarını ve anketlerini getirir.
    """
    
    def get_user_by_id(self, user_id):
        """
        ID'ye göre kullanıcı getirir.
        
        Args:
            user_id (str): Kullanıcı ID'si
            
        Returns:
            dict: Kullanıcı bilgileri
            
        Raises:
            NotFoundError: Kullanıcı bulunamazsa
        """
        try:
            user = UserModel.get(user_id)
            
            if not user.is_active:
                raise NotFoundError("Kullanıcı bulunamadı")
            
            return user.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Kullanıcı bulunamadı")
    
    def get_user_by_username(self, username):
        """
        Kullanıcı adına göre kullanıcı getirir.
        
        Args:
            username (str): Kullanıcı adı
            
        Returns:
            dict: Kullanıcı bilgileri
            
        Raises:
            NotFoundError: Kullanıcı bulunamazsa
        """
        try:
            # Kullanıcı adı indeksinde ara
            for user in UserModel.username_index.query(username):
                if user.is_active:
                    return user.to_dict()
            
            # Kullanıcı bulunamazsa
            raise NotFoundError("Kullanıcı bulunamadı")
            
        except Exception:
            raise NotFoundError("Kullanıcı bulunamadı")
    
    def update_user(self, user_id, update_data):
        """
        Kullanıcı bilgilerini günceller.
        
        Args:
            user_id (str): Kullanıcı ID'si
            update_data (dict): Güncellenecek veriler
            
        Returns:
            dict: Güncellenmiş kullanıcı bilgileri
            
        Raises:
            NotFoundError: Kullanıcı bulunamazsa
            ValidationError: Güncellenecek veriler geçersizse
        """
        try:
            user = UserModel.get(user_id)
            
            if not user.is_active:
                raise NotFoundError("Kullanıcı bulunamadı")
            
            # Güvenlik: Hassas alanların güncellenmesini engelle
            # (password_hash, role, is_active)
            safe_update_fields = [
                'username', 'cinsiyet', 'universite', 'profil_resmi_url'
            ]
            
            for field in safe_update_fields:
                if field in update_data and update_data[field] is not None:
                    # Kullanıcı adı değiştiriliyorsa benzersizliği kontrol et
                    if field == 'username' and update_data[field] != user.username:
                        try:
                            for existing_user in UserModel.username_index.query(update_data[field]):
                                raise ValidationError("Bu kullanıcı adı zaten kullanılıyor")
                        except DoesNotExist:
                            pass
                    
                    # Alanı güncelle
                    setattr(user, field, update_data[field])
            
            # Şifre güncelleme (ayrı işlenir)
            if 'password' in update_data and update_data['password']:
                user.password_hash = hash_password(update_data['password'])
            
            # Değişiklikleri kaydet
            user.save()
            
            logger.info(f"Kullanıcı güncellendi: {user_id}")
            
            return user.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Kullanıcı bulunamadı")
    
    def delete_user(self, user_id):
        """
        Kullanıcıyı siler (soft delete).
        
        Args:
            user_id (str): Kullanıcı ID'si
            
        Returns:
            bool: İşlem başarılıysa True
            
        Raises:
            NotFoundError: Kullanıcı bulunamazsa
        """
        try:
            user = UserModel.get(user_id)
            
            # Kullanıcıyı devre dışı bırak (soft delete)
            user.soft_delete()
            
            logger.info(f"Kullanıcı silindi: {user_id}")
            
            return True
            
        except DoesNotExist:
            raise NotFoundError("Kullanıcı bulunamadı")
    
    def get_user_forums(self, user_id, page=1, per_page=10):
        """
        Kullanıcının forumlarını getirir.
        
        Args:
            user_id (str): Kullanıcı ID'si
            page (int, optional): Sayfa numarası
            per_page (int, optional): Sayfa başına forum sayısı
            
        Returns:
            dict: Forumlar ve meta bilgiler
            
        Raises:
            NotFoundError: Kullanıcı bulunamazsa
        """
        try:
            # Kullanıcıyı kontrol et
            user = UserModel.get(user_id)
            
            if not user.is_active:
                raise NotFoundError("Kullanıcı bulunamadı")
            
            # Kullanıcının forumlarını getir
            forum_list = []
            total_count = 0
            
            # For döngüsü içinde sayfalama yapıyoruz (DynamoDB'de offset/limit olmadığı için)
            for forum in ForumModel.user_forum_index.query(
                user_id,
                scan_index_forward=False  # Açılış tarihine göre azalan sıralama
            ):
                if forum.is_active:
                    total_count += 1
                    
                    # Sayfalama kontrolü
                    if total_count > (page - 1) * per_page and total_count <= page * per_page:
                        forum_list.append(forum.to_dict())
            
            return {
                'forums': forum_list,
                'meta': {
                    'total': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            }
            
        except DoesNotExist:
            raise NotFoundError("Kullanıcı bulunamadı")
    
    def get_user_comments(self, user_id, page=1, per_page=10):
        """
        Kullanıcının yorumlarını getirir.
        
        Args:
            user_id (str): Kullanıcı ID'si
            page (int, optional): Sayfa numarası
            per_page (int, optional): Sayfa başına yorum sayısı
            
        Returns:
            dict: Yorumlar ve meta bilgiler
            
        Raises:
            NotFoundError: Kullanıcı bulunamazsa
        """
        try:
            # Kullanıcıyı kontrol et
            user = UserModel.get(user_id)
            
            if not user.is_active:
                raise NotFoundError("Kullanıcı bulunamadı")
            
            # Kullanıcının yorumlarını getir
            comment_list = []
            total_count = 0
            
            # For döngüsü içinde sayfalama yapıyoruz (DynamoDB'de offset/limit olmadığı için)
            for comment in CommentModel.user_comments_index.query(
                user_id,
                scan_index_forward=False  # Açılış tarihine göre azalan sıralama
            ):
                if comment.is_active:
                    total_count += 1
                    
                    # Sayfalama kontrolü
                    if total_count > (page - 1) * per_page and total_count <= page * per_page:
                        comment_list.append(comment.to_dict())
            
            return {
                'comments': comment_list,
                'meta': {
                    'total': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            }
            
        except DoesNotExist:
            raise NotFoundError("Kullanıcı bulunamadı")
    
    def get_user_polls(self, user_id, page=1, per_page=10):
        """
        Kullanıcının anketlerini getirir.
        
        Args:
            user_id (str): Kullanıcı ID'si
            page (int, optional): Sayfa numarası
            per_page (int, optional): Sayfa başına anket sayısı
            
        Returns:
            dict: Anketler ve meta bilgiler
            
        Raises:
            NotFoundError: Kullanıcı bulunamazsa
        """
        try:
            # Kullanıcıyı kontrol et
            user = UserModel.get(user_id)
            
            if not user.is_active:
                raise NotFoundError("Kullanıcı bulunamadı")
            
            # Kullanıcının anketlerini getir
            poll_list = []
            total_count = 0
            
            # For döngüsü içinde sayfalama yapıyoruz (DynamoDB'de offset/limit olmadığı için)
            for poll in PollModel.user_polls_index.query(
                user_id,
                scan_index_forward=False  # Açılış tarihine göre azalan sıralama
            ):
                if poll.is_active:
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
            
        except DoesNotExist:
            raise NotFoundError("Kullanıcı bulunamadı")
    
    def get_user_groups(self, user_id):
        """
        Kullanıcının üye olduğu grupları getirir.
        
        Args:
            user_id (str): Kullanıcı ID'si
            
        Returns:
            list: Gruplar listesi
            
        Raises:
            NotFoundError: Kullanıcı bulunamazsa
        """
        try:
            # Kullanıcıyı kontrol et
            user = UserModel.get(user_id)
            
            if not user.is_active:
                raise NotFoundError("Kullanıcı bulunamadı")
            
            # Kullanıcının gruplarını getir (kullanıcı-grup ilişkisi group model'da tutulur)
            # Tüm grupları tarayarak kullanıcının olduklarını buluyoruz
            # Not: Gerçek uygulamada, bu işlem daha verimli yapılabilir
            groups = []
            
            # DynamoDB'nin scan işlemini kullan (verimlilik için ikincil bir dizin kullanılabilir)
            for group in GroupModel.scan(consistent_read=True):
                if group.is_active:
                    for member in group.uyeler:
                        if member.kullanici_id == user_id and member.durum == 'aktif':
                            group_data = group.to_dict()
                            # Üyelik rolünü ekle
                            group_data['uyelik_rolu'] = member.rol
                            groups.append(group_data)
                            break
            
            return groups
            
        except DoesNotExist:
            raise NotFoundError("Kullanıcı bulunamadı")

# Servis singleton'ı
user_service = UserService()