"""
Kimlik Doğrulama Servisi
----------------------
Kullanıcı kimlik doğrulama ve yetkilendirme işlemleri için iş mantığı.
"""

import logging
from datetime import datetime, timedelta
from pynamodb.exceptions import DoesNotExist
from pynamodb.indexes import Index
from app.models.user import UserModel
from app.utils.auth import hash_password, check_password, generate_token
from app.utils.exceptions import AuthError, ValidationError, NotFoundError
from flask import current_app
import uuid

# Logger yapılandırması
logger = logging.getLogger(__name__)

class AuthService:
    """
    Kimlik doğrulama servisi.
    
    Kullanıcı kaydı, girişi, token üretimi gibi işlemleri yönetir.
    """
    
    def register(self, user_data):
        """
        Yeni kullanıcı kaydı yapar.
        
        Args:
            user_data (dict): Kullanıcı verileri
            
        Returns:
            dict: Oluşturulan kullanıcı bilgileri ve token
            
        Raises:
            ValidationError: Gerekli alanlar eksikse veya geçersizse
            AuthError: E-posta veya kullanıcı adı zaten kullanılıyorsa
        """
        # Gerekli alanları doğrula
        required_fields = ['email', 'username', 'password']
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                raise ValidationError(f"{field} alanı zorunludur")
        
        # E-posta ve kullanıcı adı benzersizliğini kontrol et
        try:
            # E-posta kontrolü
            for user in UserModel.email_index.query(user_data['email']):
                raise AuthError("Bu e-posta adresi zaten kullanılıyor")
                
            # Kullanıcı adı kontrolü
            for user in UserModel.username_index.query(user_data['username']):
                raise AuthError("Bu kullanıcı adı zaten kullanılıyor")
        
        except DoesNotExist:
            # İstisna oluşmazsa, bu e-posta veya kullanıcı adı kullanılabilir
            pass
        
        try:
            # Yeni kullanıcı oluştur
            user = UserModel(
                user_id=f"usr_{uuid.uuid4()}",
                email=user_data['email'],
                username=user_data['username'],
                password_hash=hash_password(user_data['password']),
                cinsiyet=user_data.get('cinsiyet'),
                kayit_tarihi=datetime.now(),
                universite=user_data.get('universite'),
                role='user',  # Varsayılan rol
                son_giris_tarihi=datetime.now()
            )
            
            user.save()
            logger.info(f"Yeni kullanıcı kaydedildi: {user.user_id}")
            
            # Kullanıcı verilerinden hassas bilgileri temizle
            user_dict = user.to_dict()
            
            # Token oluştur
            token = generate_token(user.user_id)
            
            return {
                'user': user_dict,
                'token': token
            }
            
        except Exception as e:
            logger.error(f"Kullanıcı kaydı sırasında hata: {str(e)}")
            raise ValidationError("Kullanıcı kaydı yapılamadı")
    
    def login(self, email, password):
        """
        Kullanıcı girişi yapar.
        
        Args:
            email (str): Kullanıcı e-postası
            password (str): Kullanıcı şifresi
            
        Returns:
            dict: Kullanıcı bilgileri ve token
            
        Raises:
            AuthError: Kimlik bilgileri geçersizse
        """
        try:
            # E-posta ile kullanıcıyı bul
            for user in UserModel.email_index.query(email):
                # Şifreyi kontrol et
                if check_password(password, user.password_hash):
                    # Kullanıcı aktif mi kontrol et
                    if not user.is_active:
                        raise AuthError("Hesabınız devre dışı bırakılmış")
                    
                    # Son giriş tarihini güncelle
                    user.son_giris_tarihi = datetime.now()
                    user.save()
                    
                    # Kullanıcı verilerinden hassas bilgileri temizle
                    user_dict = user.to_dict()
                    
                    # Token oluştur
                    token = generate_token(user.user_id)
                    
                    return {
                        'user': user_dict,
                        'token': token
                    }
                else:
                    raise AuthError("Geçersiz e-posta veya şifre")
            
            # Döngüden çıkılırsa, kullanıcı bulunamadı demektir
            raise AuthError("Geçersiz e-posta veya şifre")
            
        except DoesNotExist:
            # Kullanıcı bulunamadı
            raise AuthError("Geçersiz e-posta veya şifre")
    
    def refresh_token(self, user_id):
        """
        Yeni bir token oluşturur.
        
        Args:
            user_id (str): Kullanıcı ID'si
            
        Returns:
            str: Yeni token
            
        Raises:
            NotFoundError: Kullanıcı bulunamazsa
        """
        try:
            # Kullanıcıyı kontrol et
            user = UserModel.get(user_id)
            
            # Kullanıcı aktif mi kontrol et
            if not user.is_active:
                raise AuthError("Hesabınız devre dışı bırakılmış")
            
            # Yeni token oluştur
            token = generate_token(user.user_id)
            
            return token
            
        except DoesNotExist:
            raise NotFoundError("Kullanıcı bulunamadı")
    
    def change_password(self, user_id, current_password, new_password):
        """
        Kullanıcı şifresini değiştirir.
        
        Args:
            user_id (str): Kullanıcı ID'si
            current_password (str): Mevcut şifre
            new_password (str): Yeni şifre
            
        Returns:
            bool: İşlem başarılıysa True
            
        Raises:
            AuthError: Mevcut şifre geçersizse
            NotFoundError: Kullanıcı bulunamazsa
        """
        try:
            # Kullanıcıyı bul
            user = UserModel.get(user_id)
            
            # Mevcut şifreyi kontrol et
            if not check_password(current_password, user.password_hash):
                raise AuthError("Mevcut şifre geçersiz")
            
            # Yeni şifreyi ayarla
            user.password_hash = hash_password(new_password)
            user.save()
            
            logger.info(f"Kullanıcının şifresi değiştirildi: {user_id}")
            
            return True
            
        except DoesNotExist:
            raise NotFoundError("Kullanıcı bulunamadı")
    
    def forgot_password(self, email):
        """
        Şifre sıfırlama işlemini başlatır.
        
        Args:
            email (str): Kullanıcı e-postası
            
        Returns:
            bool: İşlem başarılıysa True
            
        Note:
            Gerçek uygulamada, şifre sıfırlama e-postası gönderilir.
            Bu örnek implementasyonda sadece token oluşturulup döndürülür.
        """
        try:
            # E-posta ile kullanıcıyı bul
            user_found = False
            reset_token = None
            
            for user in UserModel.email_index.query(email):
                user_found = True
                
                # Şifre sıfırlama token'ı oluştur (1 saat geçerli)
                reset_token = generate_token(
                    user.user_id,
                    expires_delta=timedelta(hours=1)
                )
                
                logger.info(f"Şifre sıfırlama token'ı oluşturuldu: {user.user_id}")
                
                # Gerçek uygulamada, buraya e-posta gönderme kodu eklenir
                # send_password_reset_email(user.email, reset_token)
                
                break
            
            # Güvenlik için, kullanıcı bulunamasa bile başarılı yanıt döndür
            return {
                'success': True,
                'token': reset_token if current_app.debug else None  # Sadece debug modunda token döndür
            }
            
        except Exception as e:
            logger.error(f"Şifre sıfırlama hatası: {str(e)}")
            
            # Güvenlik için, hata olsa bile başarılı yanıt döndür
            return {'success': True}
    
    def reset_password(self, reset_token, new_password):
        """
        Şifreyi sıfırlar.
        
        Args:
            reset_token (str): Şifre sıfırlama token'ı
            new_password (str): Yeni şifre
            
        Returns:
            bool: İşlem başarılıysa True
            
        Raises:
            AuthError: Token geçersizse veya süresi dolmuşsa
        """
        try:
            # Token'ı doğrula
            import jwt
            
            try:
                payload = jwt.decode(
                    reset_token,
                    current_app.config['JWT_SECRET_KEY'],
                    algorithms=['HS256']
                )
            except jwt.ExpiredSignatureError:
                raise AuthError("Şifre sıfırlama bağlantısının süresi dolmuş")
            except jwt.InvalidTokenError:
                raise AuthError("Geçersiz şifre sıfırlama bağlantısı")
            
            # Kullanıcı ID'sini al
            user_id = payload.get('sub')
            
            if not user_id:
                raise AuthError("Geçersiz token")
            
            # Kullanıcıyı bul
            user = UserModel.get(user_id)
            
            # Yeni şifreyi ayarla
            user.password_hash = hash_password(new_password)
            user.save()
            
            logger.info(f"Kullanıcı şifresi sıfırlandı: {user_id}")
            
            return True
            
        except DoesNotExist:
            raise AuthError("Geçersiz şifre sıfırlama bağlantısı")

# Servis singleton'ı
auth_service = AuthService()