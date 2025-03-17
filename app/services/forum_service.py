"""
Forum Servisi
-----------
Forum yönetimi, forum işlemleri ve ilgili işlemleri gerçekleştirir.
"""

import logging
from datetime import datetime
from pynamodb.exceptions import DoesNotExist
from app.models.forum import ForumModel
from app.models.user import UserModel
from app.models.comment import CommentModel
from app.utils.exceptions import NotFoundError, ValidationError, ForbiddenError

# Logger yapılandırması
logger = logging.getLogger(__name__)

class ForumService:
    """
    Forum servisi.
    
    Forum oluşturma, güncelleme, silme ve listeleme işlemlerini gerçekleştirir.
    """
    
    def create_forum(self, user_id, forum_data):
        """
        Yeni forum oluşturur.
        
        Args:
            user_id (str): Forumu oluşturan kullanıcı ID'si
            forum_data (dict): Forum verileri
            
        Returns:
            dict: Oluşturulan forum bilgileri
            
        Raises:
            ValidationError: Forum verileri geçersizse
            NotFoundError: Kullanıcı bulunamazsa
        """
        try:
            # Kullanıcıyı kontrol et
            user = UserModel.get(user_id)
            
            if not user.is_active:
                raise NotFoundError("Kullanıcı bulunamadı")
            
            # Gerekli alanları doğrula
            if 'baslik' not in forum_data or not forum_data['baslik']:
                raise ValidationError("Forum başlığı zorunludur")
            
            # Forum oluştur
            forum = ForumModel(
                baslik=forum_data['baslik'],
                aciklama=forum_data.get('aciklama', ''),
                acan_kisi_id=user_id,
                foto_urls=forum_data.get('foto_urls', []),
                universite=forum_data.get('universite', user.universite),
                kategori=forum_data.get('kategori')
            )
            
            forum.save()
            logger.info(f"Yeni forum oluşturuldu: {forum.forum_id} (Kullanıcı: {user_id})")
            
            # Kullanıcının forum listesini güncelle
            user.add_forum(forum.forum_id)
            
            return forum.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Kullanıcı bulunamadı")
        except Exception as e:
            logger.error(f"Forum oluşturma hatası: {str(e)}")
            raise ValidationError("Forum oluşturulamadı")
    
    def get_forum_by_id(self, forum_id):
        """
        ID'ye göre forum getirir.
        
        Args:
            forum_id (str): Forum ID'si
            
        Returns:
            dict: Forum bilgileri
            
        Raises:
            NotFoundError: Forum bulunamazsa
        """
        try:
            forum = ForumModel.get(forum_id)
            
            if not forum.is_active:
                raise NotFoundError("Forum bulunamadı")
            
            return forum.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Forum bulunamadı")
    
    def update_forum(self, forum_id, user_id, update_data):
        """
        Forum bilgilerini günceller.
        
        Args:
            forum_id (str): Forum ID'si
            user_id (str): İşlemi yapan kullanıcı ID'si
            update_data (dict): Güncellenecek veriler
            
        Returns:
            dict: Güncellenmiş forum bilgileri
            
        Raises:
            NotFoundError: Forum bulunamazsa
            ForbiddenError: Kullanıcının yetkisi yoksa
            ValidationError: Güncellenecek veriler geçersizse
        """
        try:
            forum = ForumModel.get(forum_id)
            
            if not forum.is_active:
                raise NotFoundError("Forum bulunamadı")
            
            # Yetki kontrolü
            if forum.acan_kisi_id != user_id:
                raise ForbiddenError("Bu forumu düzenleme yetkiniz yok")
            
            # Güncelleme yapılacak alanlar
            update_fields = ['baslik', 'aciklama', 'foto_urls', 'kategori']
            
            # Alanları güncelle
            updated = False
            for field in update_fields:
                if field in update_data and update_data[field] is not None:
                    setattr(forum, field, update_data[field])
                    updated = True
            
            if updated:
                forum.save()
                logger.info(f"Forum güncellendi: {forum_id}")
            
            return forum.to_dict()
            
        except DoesNotExist:
            raise NotFoundError("Forum bulunamadı")
    
    def delete_forum(self, forum_id, user_id):
        """
        Forumu siler.
        
        Args:
            forum_id (str): Forum ID'si
            user_id (str): İşlemi yapan kullanıcı ID'si
            
        Returns:
            bool: İşlem başarılıysa True
            
        Raises:
            NotFoundError: Forum bulunamazsa
            ForbiddenError: Kullanıcının yetkisi yoksa
        """
        try:
            forum = ForumModel.get(forum_id)
            
            if not forum.is_active:
                raise NotFoundError("Forum bulunamadı")
            
            # Yetki kontrolü
            if forum.acan_kisi_id != user_id:
                # Admin yetkisi kontrolü eklenebilir
                user = UserModel.get(user_id)
                if user.role != 'admin':
                    raise ForbiddenError("Bu forumu silme yetkiniz yok")
            
            # Forumu devre dışı bırak (soft delete)
            forum.soft_delete()
            
            logger.info(f"Forum silindi: {forum_id}")
            
            return True
            
        except DoesNotExist:
            raise NotFoundError("Forum bulunamadı")
    
    def get_all_forums(self, page=1, per_page=10, kategori=None, universite=None, search=None):
        """
        Tüm forumları getirir.
        
        Args:
            page (int, optional): Sayfa numarası
            per_page (int, optional): Sayfa başına forum sayısı
            kategori (str, optional): Kategori filtresi
            universite (str, optional): Üniversite filtresi
            search (str, optional): Arama metni
            
        Returns:
            dict: Forumlar ve meta bilgiler
        """
        # Not: DynamoDB'de kompleks sorgulamalar için ikincil dizinler kullanılabilir
        # Ancak, tam metin araması için DynamoDB uygun değildir
        # Gerçek uygulamada, Elasticsearch gibi bir arama motoru kullanılabilir
        
        # Bu implementasyon, tüm verileri getirip filtreleme yapar
        # Büyük veri setleri için uygun değildir
        forum_list = []
        total_count = 0
        
        # Filtreleme koşulları
        def match_filters(forum):
            # Aktif mi kontrol et
            if not forum.is_active:
                return False
            
            # Kategori filtresi
            if kategori and forum.kategori != kategori:
                return False
            
            # Üniversite filtresi
            if universite and forum.universite != universite:
                return False
            
            # Arama filtresi
            if search:
                search_lower = search.lower()
                if (search_lower not in forum.baslik.lower() and 
                    (not forum.aciklama or search_lower not in forum.aciklama.lower())):
                    return False
            
            return True
        
        try:
            # Üniversite ve kategori filtreleri varsa ikincil dizini kullan
            if universite and kategori:
                query_result = ForumModel.universite_kategori_index.query(
                    universite,
                    ForumModel.kategori == kategori
                )
            elif universite:
                query_result = ForumModel.universite_kategori_index.query(universite)
            else:
                # Tüm forumları getir (scan)
                query_result = ForumModel.scan()
            
            # Sonuçları filtrele ve sayfalandır
            for forum in query_result:
                if match_filters(forum):
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
        
        except Exception as e:
            logger.error(f"Forumları getirme hatası: {str(e)}")
            # Hata durumunda boş liste döndür
            return {
                'forums': [],
                'meta': {
                    'total': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                }
            }
    
    def get_forum_comments(self, forum_id, page=1, per_page=20):
        """
        Forum yorumlarını getirir.
        
        Args:
            forum_id (str): Forum ID'si
            page (int, optional): Sayfa numarası
            per_page (int, optional): Sayfa başına yorum sayısı
            
        Returns:
            dict: Yorumlar ve meta bilgiler
            
        Raises:
            NotFoundError: Forum bulunamazsa
        """
        try:
            # Forumu kontrol et
            forum = ForumModel.get(forum_id)
            
            if not forum.is_active:
                raise NotFoundError("Forum bulunamadı")
            
            # Ana yorumları getir (ust_yorum_id=None)
            comment_list = []
            total_count = 0
            
            for comment in CommentModel.forum_comments_index.query(
                forum_id,
                scan_index_forward=False  # Açılış tarihine göre azalan sıralama
            ):
                # Sadece ana yorumları al
                if comment.is_active and comment.ust_yorum_id is None:
                    total_count += 1
                    
                    # Sayfalama kontrolü
                    if total_count > (page - 1) * per_page and total_count <= page * per_page:
                        comment_dict = comment.to_dict()
                        
                        # Her yorum için yanıtları getir
                        replies = []
                        for reply in CommentModel.parent_comment_index.query(
                            comment.comment_id,
                            scan_index_forward=True  # Açılış tarihine göre artan sıralama
                        ):
                            if reply.is_active:
                                replies.append(reply.to_dict())
                        
                        comment_dict['replies'] = replies
                        comment_list.append(comment_dict)
            
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
            raise NotFoundError("Forum bulunamadı")
    
    def react_to_forum(self, forum_id, user_id, reaction_type):
        """
        Foruma reaksiyon ekler (beğeni/beğenmeme).
        
        Args:
            forum_id (str): Forum ID'si
            user_id (str): Kullanıcı ID'si
            reaction_type (str): Reaksiyon türü ('begeni' veya 'begenmeme')
            
        Returns:
            dict: Güncellenmiş beğeni/beğenmeme sayıları
            
        Raises:
            NotFoundError: Forum bulunamazsa
            ValidationError: Reaksiyon türü geçersizse
        """
        # DynamoDB'de beğeniler için ayrı tablo kullanılabilir
        # Basitlik için, bu örnekte ayrı bir tepki tablosu oluşturmuyoruz
        # Gerçek uygulamada, kullanıcıların reaksiyonlarını izlemek için ek bir tablo önerilir
        
        if reaction_type not in ['begeni', 'begenmeme']:
            raise ValidationError("Geçersiz reaksiyon türü")
        
        try:
            forum = ForumModel.get(forum_id)
            
            if not forum.is_active:
                raise NotFoundError("Forum bulunamadı")
            
            # Bu örnekte, kullanıcının daha önce reaksiyon verip vermediğini kontrol etmiyoruz
            # Gerçek uygulamada, kullanıcının reaksiyonu kaydedilmeli ve kontrol edilmelidir
            
            # Reaksiyon ekle
            if reaction_type == 'begeni':
                forum.begeni_sayisi += 1
            else:
                forum.begenmeme_sayisi += 1
            
            forum.save()
            
            return {
                'begeni_sayisi': forum.begeni_sayisi,
                'begenmeme_sayisi': forum.begenmeme_sayisi
            }
            
        except DoesNotExist:
            raise NotFoundError("Forum bulunamadı")

# Servis singleton'ı
forum_service = ForumService()