"""
Yorum Servisi
-----------
Yorum oluşturma, listeleme ve yönetimi işlemleri için servis fonksiyonları.
"""

import logging
from datetime import datetime
from pynamodb.exceptions import DoesNotExist
from app.models.comment import CommentModel
from app.models.forum import ForumModel
from app.models.user import UserModel
from app.utils.exceptions import NotFoundError, ValidationError, ForbiddenError

# Logger yapılandırması
logger = logging.getLogger(__name__)

class CommentService:
    """
    Yorum servisi.
    
    Yorum oluşturma, listeleme, güncelleme ve silme işlemlerini gerçekleştirir.
    """
    
    def create_comment(self, user_id, comment_data):
        """
        Yeni yorum oluşturur.
        
        Args:
            user_id (str): Yorumu yapan kullanıcı ID'si
            comment_data (dict): Yorum verileri
            
        Returns:
            dict: Oluşturulan yorum bilgileri
            
        Raises:
            ValidationError: Yorum verileri geçersizse
            NotFoundError: Forum veya üst yorum bulunamazsa
        """
        try:
            # Kullanıcıyı kontrol et
            user = UserModel.get(user_id)
            
            if not user.is_active:
                raise NotFoundError("Kullanıcı bulunamadı")
            
            # Gerekli alanları doğrula
            if 'forum_id' not in comment_data or not comment_data['forum_id']:
                raise ValidationError("Forum ID zorunludur")
            
            if 'icerik' not in comment_data or not comment_data['icerik']:
                raise ValidationError("Yorum içeriği zorunludur")
            
            # Forumu kontrol et
            try:
                forum = ForumModel.get(comment_data['forum_id'])
                
                if not forum.is_active:
                    raise NotFoundError("Forum bulunamadı")
            except DoesNotExist:
                raise NotFoundError("Forum bulunamadı")
            
            # Üst yorum varsa kontrol et
            if 'ust_yorum_id' in comment_data and comment_data['ust_yorum_id']:
                try:
                    ust_yorum = CommentModel.get(comment_data['ust_yorum_id'])
                    
                    if not ust_yorum.is_active:
                        raise NotFoundError("Üst yorum bulunamadı")
                    
                    # Üst yorumun aynı foruma ait olduğunu kontrol et
                    if ust_yorum.forum_id != comment_data['forum_id']:
                        raise ValidationError("Üst yorum farklı bir foruma ait")
                except DoesNotExist:
                    raise NotFoundError("Üst yorum bulunamadı")
            
            # Yorum oluştur
            comment = CommentModel(
                forum_id=comment_data['forum_id'],
                acan_kisi_id=user_id,
                icerik=comment_data['icerik'],
                foto_urls=comment_data.get('foto_urls', []),
                ust_yorum_id=comment_data.get('ust_yorum_id')
            )
            
            comment.save()
            logger.info(f"Yeni yorum oluşturuldu: {comment.comment_id} (Kullanıcı: {user_id})")
            
            # Forumun yorum listesine ekle (eğer üst yorum değilse)
            if not comment_data.get('ust_yorum_id'):
                forum.add_comment(comment.comment_id)
            
            return comment.to_dict()
            
        except (DoesNotExist, NotFoundError, ValidationError) as e:
            # Bu hataları olduğu gibi bırak
            raise
        except Exception as e:
            logger.error(f"Yorum oluşturma hatası: {str(e)}")
            raise ValidationError("Yorum oluşturulamadı")
    
    def get_comment_by_id(self, comment_id):
        """
        ID'ye göre yorum getirir.
        
        Args:
            comment_id (str): Yorum ID'si
            
        Returns:
            dict: Yorum bilgileri
            
        Raises:
            NotFoundError: Yorum bulunamazsa
        """
        try:
            comment = CommentModel.get(comment_id)
            
            if not comment.is_active:
                raise NotFoundError("Yorum bulunamadı")
            
            return comment.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Yorum bulunamadı")
    
    def update_comment(self, comment_id, user_id, update_data):
        """
        Yorum bilgilerini günceller.
        
        Args:
            comment_id (str): Yorum ID'si
            user_id (str): İşlemi yapan kullanıcı ID'si
            update_data (dict): Güncellenecek veriler
            
        Returns:
            dict: Güncellenmiş yorum bilgileri
            
        Raises:
            NotFoundError: Yorum bulunamazsa
            ForbiddenError: Kullanıcının yetkisi yoksa
            ValidationError: Güncellenecek veriler geçersizse
        """
        try:
            comment = CommentModel.get(comment_id)
            
            if not comment.is_active:
                raise NotFoundError("Yorum bulunamadı")
            
            # Yetki kontrolü
            if comment.acan_kisi_id != user_id:
                # Admin yetkisi kontrolü eklenebilir
                user = UserModel.get(user_id)
                if user.role != 'admin':
                    raise ForbiddenError("Bu yorumu düzenleme yetkiniz yok")
            
            # Güncelleme yapılacak alanlar
            update_fields = ['icerik', 'foto_urls']
            
            # Alanları güncelle
            updated = False
            for field in update_fields:
                if field in update_data and update_data[field] is not None:
                    setattr(comment, field, update_data[field])
                    updated = True
            
            if updated:
                comment.save()
                logger.info(f"Yorum güncellendi: {comment_id}")
            
            return comment.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Yorum bulunamadı")
    
    def delete_comment(self, comment_id, user_id):
        """
        Yorumu siler.
        
        Args:
            comment_id (str): Yorum ID'si
            user_id (str): İşlemi yapan kullanıcı ID'si
            
        Returns:
            bool: İşlem başarılıysa True
            
        Raises:
            NotFoundError: Yorum bulunamazsa
            ForbiddenError: Kullanıcının yetkisi yoksa
        """
        try:
            comment = CommentModel.get(comment_id)
            
            if not comment.is_active:
                raise NotFoundError("Yorum bulunamadı")
            
            # Yetki kontrolü - Yorum sahibi veya forum sahibi veya admin
            has_permission = False
            
            # Yorum sahibi mi?
            if comment.acan_kisi_id == user_id:
                has_permission = True
            else:
                # Forum sahibi mi?
                try:
                    forum = ForumModel.get(comment.forum_id)
                    if forum.acan_kisi_id == user_id:
                        has_permission = True
                except:
                    pass
                
                # Admin mi?
                if not has_permission:
                    try:
                        user = UserModel.get(user_id)
                        if user.role == 'admin' or user.role == 'moderator':
                            has_permission = True
                    except:
                        pass
            
            if not has_permission:
                raise ForbiddenError("Bu yorumu silme yetkiniz yok")
            
            # Yorumu devre dışı bırak (soft delete)
            comment.soft_delete()
            
            logger.info(f"Yorum silindi: {comment_id}")
            
            return True
            
        except DoesNotExist:
            raise NotFoundError("Yorum bulunamadı")
    
    def get_comment_replies(self, comment_id, page=1, per_page=20):
        """
        Yorumun yanıtlarını getirir.
        
        Args:
            comment_id (str): Yorum ID'si
            page (int, optional): Sayfa numarası
            per_page (int, optional): Sayfa başına yanıt sayısı
            
        Returns:
            dict: Yanıtlar ve meta bilgiler
            
        Raises:
            NotFoundError: Yorum bulunamazsa
        """
        try:
            # Yorumu kontrol et
            comment = CommentModel.get(comment_id)
            
            if not comment.is_active:
                raise NotFoundError("Yorum bulunamadı")
            
            # Yanıtları getir
            replies = []
            total_count = 0
            
            for reply in CommentModel.parent_comment_index.query(
                comment_id,
                scan_index_forward=True  # Açılış tarihine göre artan sıralama
            ):
                if reply.is_active:
                    total_count += 1
                    
                    # Sayfalama kontrolü
                    if total_count > (page - 1) * per_page and total_count <= page * per_page:
                        replies.append(reply.to_dict())
            
            return {
                'replies': replies,
                'meta': {
                    'total': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            }
            
        except DoesNotExist:
            raise NotFoundError("Yorum bulunamadı")
    
    def react_to_comment(self, comment_id, user_id, reaction_type):
        """
        Yoruma reaksiyon ekler (beğeni/beğenmeme).
        
        Args:
            comment_id (str): Yorum ID'si
            user_id (str): Kullanıcı ID'si
            reaction_type (str): Reaksiyon türü ('begeni' veya 'begenmeme')
            
        Returns:
            dict: Güncellenmiş beğeni/beğenmeme sayıları
            
        Raises:
            NotFoundError: Yorum bulunamazsa
            ValidationError: Reaksiyon türü geçersizse
        """
        # DynamoDB'de beğeniler için ayrı tablo kullanılabilir
        # Basitlik için, bu örnekte ayrı bir tepki tablosu oluşturmuyoruz
        # Gerçek uygulamada, kullanıcıların reaksiyonlarını izlemek için ek bir tablo önerilir
        
        if reaction_type not in ['begeni', 'begenmeme']:
            raise ValidationError("Geçersiz reaksiyon türü")
        
        try:
            comment = CommentModel.get(comment_id)
            
            if not comment.is_active:
                raise NotFoundError("Yorum bulunamadı")
            
            # Bu örnekte, kullanıcının daha önce reaksiyon verip vermediğini kontrol etmiyoruz
            # Gerçek uygulamada, kullanıcının reaksiyonu kaydedilmeli ve kontrol edilmelidir
            
            # Reaksiyon ekle
            if reaction_type == 'begeni':
                comment.begeni_sayisi += 1
            else:
                comment.begenmeme_sayisi += 1
            
            comment.save()
            
            return {
                'begeni_sayisi': comment.begeni_sayisi,
                'begenmeme_sayisi': comment.begenmeme_sayisi
            }
            
        except DoesNotExist:
            raise NotFoundError("Yorum bulunamadı")

# Servis singleton'ı
comment_service = CommentService()