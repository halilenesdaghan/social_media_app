"""
Kimlik Doğrulama API Testleri
---------------------------
Kimlik doğrulama API endpoint'leri için birim testleri.
"""

import json
import pytest
from app.utils.auth import generate_token

@pytest.fixture
def auth_headers():
    # Test kullanıcısı için token oluştur
    token = generate_token("test_user_id")
    return {
        "Authorization": f"Bearer {token}"
    }

def test_register_success(client):
    """Başarılı kullanıcı kaydı testi"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "Password123"
        }
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert "user" in data["data"]
    assert "token" in data["data"]

def test_login_success(client):
    """Başarılı kullanıcı girişi testi"""
    # Önce kullanıcı oluştur
    client.post(
        "/api/auth/register",
        json={
            "email": "login_test@example.com",
            "username": "logintest",
            "password": "Password123"
        }
    )
    
    # Giriş yap
    response = client.post(
        "/api/auth/login",
        json={
            "email": "login_test@example.com",
            "password": "Password123"
        }
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert "user" in data["data"]
    assert "token" in data["data"]

def test_me_authenticated(client, auth_headers):
    """Kimliği doğrulanmış kullanıcı için 'me' endpoint testi"""
    response = client.get(
        "/api/auth/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"