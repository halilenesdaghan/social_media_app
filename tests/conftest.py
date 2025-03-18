"""
Pytest Konfigürasyonu
-------------------
Tüm test dosyaları için ortak fixture'lar ve konfigürasyon.
"""

import os
import sys
import pytest
from dotenv import load_dotenv

# Ana uygulamanın Python yoluna ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# .env dosyasını yükle
load_dotenv()

# Uygulama oluşturma
@pytest.fixture
def app():
    from app import create_app
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()