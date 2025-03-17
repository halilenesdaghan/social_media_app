"""
Medya Servisi
-----------
Medya yükleme, saklama ve yönetim işlemleri için servis sınıfı.
"""

import logging
import os
import uuid
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from app.utils.s3 import upload_file_to_s3, delete_file_from_s3, generate_presigned_url
from app.utils.exceptions import NotFoundError, ValidationError, ForbiddenError

# Logger yapılandırması
logger = logging.getLogger(__name__)

class MediaService:
    """
    Medya servisi.
    
    Medya dosyalarını yükler, saklar ve yönetir.
    """
    
    def allowed_file(self, filename):
        """
        Dosya uzantısının izin verilen formatta olup olmadığını kontrol eder.
        
        Args:
            filename (str): Dosya adı
            
        Returns:
            bool: Dosya formatı izin veriliyorsa True, aksi halde False
        """
        if '.' not in filename:
            return False
        
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in current_app.config['ALLOWED_EXTENSIONS']
    
    def upload_file(self, file, user_id, metadata=None):
        """
        Dosya yükler.
        
        Args:
            file: Flask FileStorage objesi
            user_id (str): Yükleyen kullanıcı ID'si
            metadata (dict, optional): İlişkili metadata
            
        Returns:
            dict: Yüklenen dosya bilgileri
            
        Raises:
            ValidationError: Dosya geçersizse
        """
        if not file:
            raise ValidationError("Dosya bulunamadı")
        
        # Dosya formatını kontrol et
        if not self.allowed_file(file.filename):
            raise ValidationError("Geçersiz dosya formatı")
        
        try:
            # Dosya adını güvenli hale getir
            filename = secure_filename(file.filename)
            
            # Benzersiz ad oluştur
            unique_filename = f"{uuid.uuid4()}-{filename}"
            
            # Metadata'yı hazırla
            file_metadata = metadata or {}
            model_type = file_metadata.get('model_type', 'genel')
            
            # Dosya yolunu belirle
            s3_folder = f"uploads/{model_type}/{datetime.now().strftime('%Y/%m/%d')}"
            
            # S3 veya yerel dosya sistemi
            if current_app.config.get('AWS_ACCESS_KEY_ID') and current_app.config.get('S3_BUCKET_NAME'):
                # S3'e yükle
                upload_result = upload_file_to_s3(file, s3_folder, unique_filename)
                file_url = upload_result['url']
                storage_path = upload_result['s3_path']
                storage_type = 's3'
            else:
                # Yerel dosya sistemine yükle
                upload_folder = current_app.config['UPLOAD_FOLDER']
                folder_path = os.path.join(upload_folder, s3_folder)
                
                # Klasörü oluştur
                os.makedirs(folder_path, exist_ok=True)
                
                file_path = os.path.join(folder_path, unique_filename)
                file.save(file_path)
                
                # URL oluştur
                file_url = f"/uploads/{s3_folder}/{unique_filename}"
                storage_path = file_path
                storage_type = 'local'
            
            # Dosya bilgilerini döndür
            return {
                'file_id': str(uuid.uuid4()),
                'original_filename': filename,
                'storage_filename': unique_filename,
                'content_type': file.content_type,
                'file_size': file.content_length if hasattr(file, 'content_length') else None,
                'url': file_url,
                'storage_path': storage_path,
                'storage_type': storage_type,
                'upload_date': datetime.now().isoformat(),
                'uploader_id': user_id,
                'metadata': file_metadata
            }
            
        except Exception as e:
            logger.error(f"Dosya yükleme hatası: {str(e)}")
            raise ValidationError(f"Dosya yüklenemedi: {str(e)}")
    
    def upload_multiple_files(self, files, user_id, metadata=None):
        """
        Birden fazla dosya yükler.
        
        Args:
            files: Flask FileStorage objesi listesi
            user_id (str): Yükleyen kullanıcı ID'si
            metadata (dict, optional): İlişkili metadata
            
        Returns:
            list: Yüklenen dosya bilgileri listesi
        """
        if not files or len(files) == 0:
            raise ValidationError("Dosya bulunamadı")
        
        uploaded_files = []
        
        for file in files:
            try:
                result = self.upload_file(file, user_id, metadata)
                uploaded_files.append(result)
            except ValidationError as e:
                # Hatayı logla ama devam et
                logger.warning(f"Dosya yükleme atlandı ({file.filename}): {str(e)}")
        
        if not uploaded_files:
            raise ValidationError("Hiçbir dosya yüklenemedi")
        
        return uploaded_files
    
    def delete_file(self, file_info, user_id=None):
        """
        Dosya siler.
        
        Args:
            file_info (dict): Dosya bilgileri
            user_id (str, optional): İşlemi yapan kullanıcı ID'si
            
        Returns:
            bool: İşlem başarılıysa True
            
        Raises:
            ForbiddenError: Kullanıcının yetkisi yoksa
            ValidationError: Dosya silinemezse
        """
        # Yetki kontrolü
        if user_id and file_info.get('uploader_id') != user_id:
            # Admin kontrolü eklenebilir
            raise ForbiddenError("Bu dosyayı silme yetkiniz yok")
        
        try:
            # Depolama türüne göre işlem yap
            if file_info.get('storage_type') == 's3':
                # S3'ten sil
                success = delete_file_from_s3(file_info.get('storage_path'))
                if not success:
                    raise ValidationError("Dosya S3'ten silinemedi")
            else:
                # Yerel dosya sisteminden sil
                file_path = file_info.get('storage_path')
                if os.path.exists(file_path):
                    os.remove(file_path)
                else:
                    logger.warning(f"Silinecek dosya bulunamadı: {file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Dosya silme hatası: {str(e)}")
            raise ValidationError(f"Dosya silinemedi: {str(e)}")
    
    def get_file_url(self, file_info, expires=3600):
        """
        Dosya URL'i oluşturur.
        
        Args:
            file_info (dict): Dosya bilgileri
            expires (int, optional): URL'nin geçerlilik süresi (saniye)
            
        Returns:
            str: Dosya URL'i
        """
        if file_info.get('storage_type') == 's3':
            # Ön imzalı S3 URL oluştur
            return generate_presigned_url(file_info.get('storage_path'), expires)
        else:
            # Yerel dosya URL'ini döndür
            return file_info.get('url')

# Servis singleton'ı
media_service = MediaService()