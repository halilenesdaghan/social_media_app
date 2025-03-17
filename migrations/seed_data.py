"""
Örnek Veri Oluşturma Scripti
--------------------------
Geliştirme ve test için örnek veriler oluşturur.
"""

import os
import sys
import logging
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import uuid

# Ana uygulamanın Python yoluna ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import UserModel
from app.models.forum import ForumModel
from app.models.comment import CommentModel
from app.models.poll import PollModel, PollOption
from app.models.group import GroupModel, GroupMember
from app.utils.auth import hash_password

# .env dosyasını yükle
load_dotenv()

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def setup_models(app_config):
    """
    Model sınıflarını konfigüre eder.
    
    Args:
        app_config: Uygulama konfigürasyonu
    """
    # Meta verilerini ayarla
    models = [UserModel, ForumModel, CommentModel, PollModel, GroupModel]
    
    for model in models:
        model.Meta.region = app_config.get('AWS_DEFAULT_REGION', 'eu-central-1')
        
        # Yerel DynamoDB host ayarlanmışsa, kullan
        if app_config.get('DYNAMODB_ENDPOINT'):
            model.Meta.host = app_config.get('DYNAMODB_ENDPOINT')

def create_sample_users(count=10):
    """
    Örnek kullanıcılar oluşturur.
    
    Args:
        count (int): Oluşturulacak kullanıcı sayısı
        
    Returns:
        list: Oluşturulan kullanıcıların ID'leri
    """
    logger.info(f"{count} örnek kullanıcı oluşturuluyor...")
    
    # Üniversite örnekleri
    universiteler = [
        "İstanbul Teknik Üniversitesi",
        "Boğaziçi Üniversitesi",
        "Orta Doğu Teknik Üniversitesi",
        "Ankara Üniversitesi",
        "Ege Üniversitesi",
        "Hacettepe Üniversitesi",
        "Sabancı Üniversitesi",
        "Koç Üniversitesi",
        "Bilkent Üniversitesi",
        "Gazi Üniversitesi"
    ]
    
    cinsiyet_secenekleri = ["Erkek", "Kadın", "Diğer"]
    
    user_ids = []
    
    # Admin kullanıcı
    admin_user = UserModel(
        user_id=f"usr_{uuid.uuid4()}",
        email="admin@example.com",
        username="admin",
        password_hash=hash_password("admin123"),
        cinsiyet=random.choice(cinsiyet_secenekleri),
        kayit_tarihi=datetime.now() - timedelta(days=random.randint(1, 365)),
        universite=random.choice(universiteler),
        role="admin",
        son_giris_tarihi=datetime.now()
    )
    admin_user.save()
    user_ids.append(admin_user.user_id)
    
    # Normal kullanıcılar
    for i in range(1, count):
        user = UserModel(
            user_id=f"usr_{uuid.uuid4()}",
            email=f"user{i}@example.com",
            username=f"user{i}",
            password_hash=hash_password(f"password{i}"),
            cinsiyet=random.choice(cinsiyet_secenekleri),
            kayit_tarihi=datetime.now() - timedelta(days=random.randint(1, 365)),
            universite=random.choice(universiteler),
            role="user",
            son_giris_tarihi=datetime.now() - timedelta(days=random.randint(0, 30))
        )
        user.save()
        user_ids.append(user.user_id)
    
    logger.info(f"{len(user_ids)} kullanıcı oluşturuldu.")
    return user_ids

def create_sample_groups(user_ids, count=5):
    """
    Örnek gruplar oluşturur.
    
    Args:
        user_ids (list): Kullanıcı ID'leri
        count (int): Oluşturulacak grup sayısı
        
    Returns:
        list: Oluşturulan grupların ID'leri
    """
    logger.info(f"{count} örnek grup oluşturuluyor...")
    
    # Grup kategorileri
    kategoriler = [
        ["Teknoloji", "Yazılım", "Bilişim"],
        ["Spor", "Fitness", "Sağlık"],
        ["Sanat", "Müzik", "Edebiyat"],
        ["Bilim", "Akademi", "Eğitim"],
        ["Oyun", "E-Spor", "Eğlence"]
    ]
    
    gizlilik_secenekleri = ["acik", "kapali", "gizli"]
    
    group_ids = []
    
    for i in range(count):
        # Rastgele bir grup sahibi seç
        olusturan_id = random.choice(user_ids)
        
        # Rastgele kategori seç
        kategori_listesi = random.choice(kategoriler)
        
        # Grup oluştur
        group = GroupModel(
            group_id=f"grp_{uuid.uuid4()}",
            grup_adi=f"Örnek Grup {i+1}",
            aciklama=f"Bu, örnek bir grup açıklamasıdır. Grup #{i+1}",
            olusturulma_tarihi=datetime.now() - timedelta(days=random.randint(1, 180)),
            olusturan_id=olusturan_id,
            gizlilik=random.choice(gizlilik_secenekleri),
            kategoriler=kategori_listesi,
            uye_sayisi=0
        )
        
        # Grup üyeleri ekle
        uyeler = []
        
        # Oluşturan kullanıcı
        uyeler.append(GroupMember(
            kullanici_id=olusturan_id,
            rol="yonetici",
            katilma_tarihi=group.olusturulma_tarihi,
            durum="aktif"
        ))
        
        # Rastgele üyeler
        uye_sayisi = random.randint(3, min(15, len(user_ids)))
        for _ in range(uye_sayisi):
            uye_id = random.choice(user_ids)
            
            # Kullanıcı zaten eklenmişse atla
            if any(uye.kullanici_id == uye_id for uye in uyeler):
                continue
            
            # Kullanıcıyı ekle
            rol = random.choices(
                ["uye", "moderator"],
                weights=[0.8, 0.2],
                k=1
            )[0]
            
            katilma_tarihi = group.olusturulma_tarihi + timedelta(days=random.randint(1, 30))
            
            uyeler.append(GroupMember(
                kullanici_id=uye_id,
                rol=rol,
                katilma_tarihi=katilma_tarihi,
                durum="aktif"
            ))
        
        group.uyeler = uyeler
        group.uye_sayisi = len(uyeler)
        group.save()
        
        group_ids.append(group.group_id)
    
    logger.info(f"{len(group_ids)} grup oluşturuldu.")
    return group_ids

def create_sample_forums(user_ids, count=20):
    """
    Örnek forumlar oluşturur.
    
    Args:
        user_ids (list): Kullanıcı ID'leri
        count (int): Oluşturulacak forum sayısı
        
    Returns:
        list: Oluşturulan forumların ID'leri
    """
    logger.info(f"{count} örnek forum oluşturuluyor...")
    
    # Forum kategorileri
    kategoriler = [
        "Genel", "Teknoloji", "Spor", "Sanat", "Bilim",
        "Eğitim", "Siyaset", "Ekonomi", "Sağlık", "Oyunlar"
    ]
    
    forum_ids = []
    
    for i in range(count):
        # Rastgele bir kullanıcı seç
        user_id = random.choice(user_ids)
        
        # Kullanıcı bilgilerini al
        try:
            user = UserModel.get(user_id)
            universite = user.universite
        except:
            universite = None
        
        # Forum oluştur
        forum = ForumModel(
            forum_id=f"frm_{uuid.uuid4()}",
            baslik=f"Örnek Forum #{i+1}",
            aciklama=f"Bu, örnek bir forum açıklamasıdır. Forum #{i+1}",
            acilis_tarihi=datetime.now() - timedelta(days=random.randint(1, 90)),
            acan_kisi_id=user_id,
            kategori=random.choice(kategoriler),
            universite=universite,
            begeni_sayisi=random.randint(0, 100),
            begenmeme_sayisi=random.randint(0, 20)
        )
        forum.save()
        
        forum_ids.append(forum.forum_id)
    
    logger.info(f"{len(forum_ids)} forum oluşturuldu.")
    return forum_ids

def create_sample_comments(user_ids, forum_ids, count=50):
    """
    Örnek yorumlar oluşturur.
    
    Args:
        user_ids (list): Kullanıcı ID'leri
        forum_ids (list): Forum ID'leri
        count (int): Oluşturulacak yorum sayısı
        
    Returns:
        list: Oluşturulan yorumların ID'leri
    """
    logger.info(f"{count} örnek yorum oluşturuluyor...")
    
    comment_ids = []
    
    # Ana yorumlar
    main_comments = []
    
    for i in range(count // 2):  # Yarısı ana yorum
        # Rastgele bir kullanıcı ve forum seç
        user_id = random.choice(user_ids)
        forum_id = random.choice(forum_ids)
        
        # Yorum oluştur
        comment = CommentModel(
            comment_id=f"cmt_{uuid.uuid4()}",
            forum_id=forum_id,
            acan_kisi_id=user_id,
            icerik=f"Bu, #{i+1} numaralı örnek bir yorumdur.",
            acilis_tarihi=datetime.now() - timedelta(days=random.randint(1, 30)),
            begeni_sayisi=random.randint(0, 50),
            begenmeme_sayisi=random.randint(0, 10)
        )
        comment.save()
        
        comment_ids.append(comment.comment_id)
        main_comments.append(comment.comment_id)
        
        # Forumun yorum listesini güncelle
        try:
            forum = ForumModel.get(forum_id)
            forum.add_comment(comment.comment_id)
        except:
            pass
    
    # Yanıtlar
    for i in range(count - len(main_comments)):
        # Rastgele bir kullanıcı ve ana yorum seç
        user_id = random.choice(user_ids)
        parent_comment_id = random.choice(main_comments)
        
        # Ana yorumu bul
        try:
            parent_comment = CommentModel.get(parent_comment_id)
            forum_id = parent_comment.forum_id
        except:
            forum_id = random.choice(forum_ids)
        
        # Yanıt oluştur
        reply = CommentModel(
            comment_id=f"cmt_{uuid.uuid4()}",
            forum_id=forum_id,
            acan_kisi_id=user_id,
            icerik=f"Bu, #{i+1} numaralı örnek bir yanıttır.",
            acilis_tarihi=datetime.now() - timedelta(days=random.randint(0, 30)),
            begeni_sayisi=random.randint(0, 20),
            begenmeme_sayisi=random.randint(0, 5),
            ust_yorum_id=parent_comment_id
        )
        reply.save()
        
        comment_ids.append(reply.comment_id)
    
    logger.info(f"{len(comment_ids)} yorum oluşturuldu.")
    return comment_ids

def create_sample_polls(user_ids, count=10):
    """
    Örnek anketler oluşturur.
    
    Args:
        user_ids (list): Kullanıcı ID'leri
        count (int): Oluşturulacak anket sayısı
        
    Returns:
        list: Oluşturulan anketlerin ID'leri
    """
    logger.info(f"{count} örnek anket oluşturuluyor...")
    
    # Kategoriler
    kategoriler = [
        "Genel", "Teknoloji", "Spor", "Sanat", "Bilim",
        "Eğitim", "Siyaset", "Ekonomi", "Sağlık", "Oyunlar"
    ]
    
    poll_ids = []
    
    for i in range(count):
        # Rastgele bir kullanıcı seç
        user_id = random.choice(user_ids)
        
        # Kullanıcı bilgilerini al
        try:
            user = UserModel.get(user_id)
            universite = user.universite
        except:
            universite = None
        
        # Anket oluştur
        poll = PollModel(
            poll_id=f"pol_{uuid.uuid4()}",
            baslik=f"Örnek Anket #{i+1}",
            aciklama=f"Bu, örnek bir anket açıklamasıdır. Anket #{i+1}",
            acilis_tarihi=datetime.now() - timedelta(days=random.randint(1, 60)),
            acan_kisi_id=user_id,
            kategori=random.choice(kategoriler),
            universite=universite
        )
        
        # Seçenekler ekle
        option_count = random.randint(2, 5)
        options = []
        
        for j in range(option_count):
            option = PollOption(
                option_id=str(uuid.uuid4()),
                metin=f"Seçenek {j+1}",
                oy_sayisi=random.randint(0, 30)
            )
            options.append(option)
        
        poll.secenekler = options
        poll.save()
        
        poll_ids.append(poll.poll_id)
    
    logger.info(f"{len(poll_ids)} anket oluşturuldu.")
    return poll_ids

def main():
    """
    Ana fonksiyon. Örnek verileri oluşturur.
    """
    logger.info("Örnek veri oluşturma işlemi başlatılıyor...")
    
    try:
        # Flask uygulamasını simüle eden konfigürasyon
        app_config = {
            'AWS_DEFAULT_REGION': os.getenv('AWS_DEFAULT_REGION', 'eu-central-1'),
            'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'DYNAMODB_ENDPOINT': os.getenv('DYNAMODB_ENDPOINT')
        }
        
        # Model sınıflarını konfigüre et
        setup_models(app_config)
        
        # Örnek kullanıcılar oluştur
        user_ids = create_sample_users(10)
        
        # Örnek gruplar oluştur
        group_ids = create_sample_groups(user_ids, 5)
        
        # Örnek forumlar oluştur
        forum_ids = create_sample_forums(user_ids, 20)
        
        # Örnek yorumlar oluştur
        comment_ids = create_sample_comments(user_ids, forum_ids, 50)
        
        # Örnek anketler oluştur
        poll_ids = create_sample_polls(user_ids, 10)
        
        logger.info("Tüm örnek veriler başarıyla oluşturuldu.")
        
    except Exception as e:
        logger.error(f"Hata oluştu: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()