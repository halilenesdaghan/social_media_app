"""
API Yanıt Yardımcıları
--------------------
Tutarlı API yanıtları oluşturmak için yardımcı fonksiyonlar.
"""

import math
from flask import jsonify


def success_response(data=None, message="İşlem başarılı", status_code=200, meta=None):
    """
    Başarılı API yanıtı oluşturur.
    
    Args:
        data (any, optional): Yanıt verileri
        message (str, optional): Başarı mesajı
        status_code (int, optional): HTTP durum kodu
        meta (dict, optional): Meta veriler
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    response = {
        "status": "success",
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    if meta:
        response["meta"] = meta
        
    return jsonify(response), status_code


def error_response(message="Bir hata oluştu", status_code=400, errors=None):
    """
    Hata API yanıtı oluşturur.
    
    Args:
        message (str, optional): Hata mesajı
        status_code (int, optional): HTTP durum kodu
        errors (list/dict, optional): Hata detayları
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    response = {
        "status": "error",
        "message": message
    }
    
    if errors:
        response["errors"] = errors
        
    return jsonify(response), status_code


def pagination_meta(page, per_page, total_items):
    """
    Sayfalama meta verilerini oluşturur.
    
    Args:
        page (int): Mevcut sayfa numarası
        per_page (int): Sayfa başına öğe sayısı
        total_items (int): Toplam öğe sayısı
    
    Returns:
        dict: Sayfalama meta verileri
    """
    # Toplam sayfa sayısını hesapla
    total_pages = math.ceil(total_items / per_page) if per_page > 0 else 0
    
    return {
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


def list_response(items, total_items, page=1, per_page=10, message="Liste başarıyla getirildi"):
    """
    Liste yanıtı oluşturur (sayfalama ile).
    
    Args:
        items (list): Öğe listesi
        total_items (int): Toplam öğe sayısı
        page (int, optional): Mevcut sayfa numarası
        per_page (int, optional): Sayfa başına öğe sayısı
        message (str, optional): Başarı mesajı
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    meta = pagination_meta(page, per_page, total_items)
    return success_response(items, message, 200, meta)


def created_response(data, message="Kayıt başarıyla oluşturuldu"):
    """
    Oluşturma işlemi için başarılı yanıt.
    
    Args:
        data (any): Oluşturulan kayıt
        message (str, optional): Başarı mesajı
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    return success_response(data, message, 201)


def updated_response(data, message="Kayıt başarıyla güncellendi"):
    """
    Güncelleme işlemi için başarılı yanıt.
    
    Args:
        data (any): Güncellenen kayıt
        message (str, optional): Başarı mesajı
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    return success_response(data, message, 200)


def deleted_response(message="Kayıt başarıyla silindi"):
    """
    Silme işlemi için başarılı yanıt.
    
    Args:
        message (str, optional): Başarı mesajı
    
    Returns:
        tuple: Yanıt ve HTTP durum kodu
    """
    return success_response(None, message, 200)