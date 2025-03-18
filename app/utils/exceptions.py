"""
Özel İstisna Sınıfları
--------------------
Uygulama genelinde kullanılan özel istisna sınıfları.
"""

class ApiError(Exception):
    """
    API hatası için özel istisna sınıfı.
    
    Attributes:
        status_code (int): HTTP durum kodu
        message (str): Hata mesajı
        errors (list/dict): Hata detayları (isteğe bağlı)
    """
    
    def __init__(self, status_code, message, errors=None):
        """
        ApiError istisnasını başlat.
        
        Args:
            status_code (int): HTTP durum kodu
            message (str): Hata mesajı
            errors (list/dict, optional): Hata detayları
        """
        self.status_code = status_code
        self.message = message
        self.errors = errors
        super().__init__(self.message)
    
    def to_dict(self):
        """
        İstisnayı sözlük olarak döndür.
        
        Returns:
            dict: İstisnanın sözlük gösterimi
        """
        error_dict = {
            'status': 'error',
            'message': self.message,
        }
        
        if self.errors:
            error_dict['errors'] = self.errors
            
        return error_dict


class AuthError(ApiError):
    """
    Kimlik doğrulama hatası için özel istisna sınıfı.
    """
    
    def __init__(self, message="Kimlik doğrulama hatası", errors=None):
        """
        AuthError istisnasını başlat.
        
        Args:
            message (str, optional): Hata mesajı
            errors (list/dict, optional): Hata detayları
        """
        super().__init__(401, message, errors)


class ForbiddenError(ApiError):
    """
    Yasaklı erişim hatası için özel istisna sınıfı.
    """
    
    def __init__(self, message="Bu işlem için yetkiniz bulunmamaktadır", errors=None):
        """
        ForbiddenError istisnasını başlat.
        
        Args:
            message (str, optional): Hata mesajı
            errors (list/dict, optional): Hata detayları
        """
        super().__init__(403, message, errors)


class NotFoundError(ApiError):
    """
    Kaynak bulunamadı hatası için özel istisna sınıfı.
    """
    
    def __init__(self, message="İstenen kaynak bulunamadı", errors=None):
        """
        NotFoundError istisnasını başlat.
        
        Args:
            message (str, optional): Hata mesajı
            errors (list/dict, optional): Hata detayları
        """
        super().__init__(404, message, errors)


class ValidationError(ApiError):
    """
    Doğrulama hatası için özel istisna sınıfı.
    """
    
    def __init__(self, message="Doğrulama hatası", errors=None):
        """
        ValidationError istisnasını başlat.
        
        Args:
            message (str, optional): Hata mesajı
            errors (list/dict, optional): Hata detayları
        """
        super().__init__(400, message, errors)


class ConflictError(ApiError):
    """
    Çakışma hatası için özel istisna sınıfı.
    """
    
    def __init__(self, message="Kaynak çakışması", errors=None):
        """
        ConflictError istisnasını başlat.
        
        Args:
            message (str, optional): Hata mesajı
            errors (list/dict, optional): Hata detayları
        """
        super().__init__(409, message, errors)