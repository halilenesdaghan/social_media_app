"""
AWS S3 Yardımcı Fonksiyonları
--------------------------
S3 medya yükleme ve yönetim fonksiyonları.
"""

import uuid
import logging
import boto3
from botocore.exceptions import ClientError
from flask import current_app
import os

# Logger tanımı
logger = logging.getLogger(__name__)

def get_s3_client():
    """
    S3 client'ı döndürür.
    
    Returns:
        boto3.client: S3 client
    """
    s3_client = boto3.client(
        's3',
        region_name=current_app.config['S3_REGION'],
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
    )
    return s3_client


def upload_file_to_s3(file, folder='uploads', custom_filename=None):
    """
    Dosyayı S3'e yükler.
    
    Args:
        file (FileStorage): Flask dosya objesi
        folder (str, optional): S3 klasör yolu
        custom_filename (str, optional): Özel dosya adı
    
    Returns:
        dict: Yükleme bilgileri
    
    Raises:
        Exception: Yükleme sırasında hata oluşursa
    """
    try:
        s3_client = get_s3_client()
        bucket_name = current_app.config['S3_BUCKET_NAME']
        
        # Dosya adını ve uzantısını ayır
        if custom_filename:
            filename = custom_filename
        else:
            # Orijinal dosya adını koru ama benzersiz hale getir
            _, file_extension = os.path.splitext(file.filename)
            unique_id = str(uuid.uuid4())
            filename = f"{unique_id}{file_extension}"
        
        # S3'teki tam yolu oluştur
        s3_path = f"{folder}/{filename}"
        
        # Dosyayı S3'e yükle
        s3_client.upload_fileobj(
            file,
            bucket_name,
            s3_path,
            ExtraArgs={
                "ContentType": file.content_type  # MIME tipini ayarla
            }
        )
        
        # URL'yi oluştur
        file_url = f"{current_app.config['S3_URL']}{s3_path}"
        
        return {
            'filename': filename,
            'original_filename': file.filename,
            'content_type': file.content_type,
            's3_path': s3_path,
            'url': file_url,
            'bucket': bucket_name
        }
    
    except ClientError as e:
        logger.error(f"S3 upload failed: {e}")
        raise Exception(f"File upload to S3 failed: {str(e)}")


def delete_file_from_s3(s3_path):
    """
    S3'ten dosya siler.
    
    Args:
        s3_path (str): S3'teki dosya yolu
    
    Returns:
        bool: Başarılı ise True, değilse False
    """
    try:
        s3_client = get_s3_client()
        bucket_name = current_app.config['S3_BUCKET_NAME']
        
        # Dosyayı sil
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=s3_path
        )
        
        return True
    
    except ClientError as e:
        logger.error(f"S3 delete failed: {e}")
        return False


def generate_presigned_url(s3_path, expiration=3600):
    """
    S3 dosyası için ön imzalı URL oluşturur.
    
    Args:
        s3_path (str): S3'teki dosya yolu
        expiration (int, optional): URL'nin geçerlilik süresi (saniye)
    
    Returns:
        str: Ön imzalı URL
    """
    try:
        s3_client = get_s3_client()
        bucket_name = current_app.config['S3_BUCKET_NAME']
        
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': s3_path
            },
            ExpiresIn=expiration
        )
        
        return response
    
    except ClientError as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        return None