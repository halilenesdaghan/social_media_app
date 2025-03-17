"""
Uygulama Başlatma Dosyası
------------------------
Flask uygulamasını başlatır ve çalıştırır.
"""

import os
from app import create_app

# Uygulama örneğini oluştur
app = create_app()

if __name__ == '__main__':
    # Eğer doğrudan çalıştırılırsa, geliştirme sunucusunu başlat
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    
    # Debug modunda çalıştır (sadece geliştirme ortamında)
    debug = app.config.get('DEBUG', False)
    
    app.run(host=host, port=port, debug=debug)