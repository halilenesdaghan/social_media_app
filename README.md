# Twitter Benzeri Sosyal Medya Platformu

Bu proje, Python ve DynamoDB kullanarak geliştirilen, Twitter benzeri bir sosyal medya platformunun backend uygulamasıdır. Kullanıcılar düşüncelerini paylaşabilir, yorum yapabilir, anket oluşturabilir ve gruplara katılabilirler.

## Özellikler

- **Kullanıcı Yönetimi**: Kayıt, giriş, profil düzenleme
- **Forum Paylaşımları**: Düşünce paylaşımı, yorum yapma, beğeni/beğenmeme
- **Yorumlar**: İç içe yorumlar, beğeni/beğenmeme
- **Anketler**: Anket oluşturma ve oylama
- **Gruplar**: Grup oluşturma ve üyelik
- **Medya Yükleme**: Fotoğraf yükleme desteği (S3 veya yerel depolama)
- **API**: RESTful API ile frontend uygulamaları için destek

## Teknolojiler

- **Backend**: Python 3.8+
- **Web Framework**: Flask
- **Veritabanı**: Amazon DynamoDB
- **Kimlik Doğrulama**: JWT (JSON Web Tokens)
- **Depolama**: AWS S3 (opsiyonel)
- **API**: RESTful API
- **Doğrulama**: Marshmallow ile veri doğrulama
- **Dokümantasyon**: Swagger/OpenAPI

## Kurulum

### Ön Koşullar

- Python 3.8 veya üstü
- pip (Python paket yöneticisi)
- virtualenv (önerilen)
- AWS hesabı (DynamoDB ve S3 için, yerel geliştirme için opsiyonel)
- DynamoDB Local (yerel geliştirme için)

### Adımlar

1. **Projeyi klonlayın**

   ```bash
   git clone https://github.com/username/social-media-app.git
   cd social-media-app
   ```

2. **Sanal ortam oluşturun ve etkinleştirin**

   ```bash
   python -m venv venv
   # Windows için
   venv\Scripts\activate
   # macOS/Linux için
   source venv/bin/activate
   ```

3. **Bağımlılıkları yükleyin**

   ```bash
   pip install -r requirements.txt
   ```

4. **Ortam değişkenlerini yapılandırın**

   `.env.example` dosyasını `.env` olarak kopyalayın ve değişkenleri yapılandırın:

   ```bash
   cp .env.example .env
   # .env dosyasını düzenleyin
   ```

5. **DynamoDB Local'i başlatın (yerel geliştirme için)**

   ```bash
   # DynamoDB Local'i indirin
   mkdir -p dynamodb-local
   cd dynamodb-local
   wget https://d1ni2b6xgvw0s0.cloudfront.net/dynamodb_local_latest.tar.gz
   tar -xzf dynamodb_local_latest.tar.gz
   
   # DynamoDB Local'i başlatın
   java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb
   ```

6. **Veritabanı tablolarını oluşturun**

   ```bash
   python migrations/create_tables.py
   ```

7. **Örnek veriler oluşturun (opsiyonel)**

   ```bash
   python migrations/seed_data.py
   ```

8. **Uygulamayı başlatın**

   ```bash
   python run.py
   ```

   Uygulama varsayılan olarak `http://localhost:5000` adresinde çalışacaktır.

### Docker ile Kurulum (Opsiyonel)

Docker kullanmak istiyorsanız:

```bash
docker-compose up -d
```

## API Endpoints

Ana API endpoint'leri şunlardır:

### Kimlik Doğrulama

- `POST /api/auth/register` - Kullanıcı kaydı
- `POST /api/auth/login` - Kullanıcı girişi
- `GET /api/auth/me` - Mevcut kullanıcı bilgileri
- `POST /api/auth/refresh-token` - Token yenileme
- `POST /api/auth/change-password` - Şifre değiştirme
- `POST /api/auth/forgot-password` - Şifre sıfırlama isteği
- `POST /api/auth/reset-password` - Şifre sıfırlama

### Kullanıcılar

- `GET /api/users/<user_id>` - Kullanıcı bilgilerini getir
- `PUT /api/users/profile` - Profil güncelle
- `DELETE /api/users/account` - Hesabı sil
- `GET /api/users/forums` - Kullanıcının forumlarını getir
- `GET /api/users/comments` - Kullanıcının yorumlarını getir
- `GET /api/users/polls` - Kullanıcının anketlerini getir
- `GET /api/users/groups` - Kullanıcının gruplarını getir

### Forumlar

- `GET /api/forums` - Tüm forumları getir
- `POST /api/forums` - Yeni forum oluştur
- `GET /api/forums/<forum_id>` - Forum bilgilerini getir
- `PUT /api/forums/<forum_id>` - Forum güncelle
- `DELETE /api/forums/<forum_id>` - Forum sil
- `GET /api/forums/<forum_id>/comments` - Forum yorumlarını getir
- `POST /api/forums/<forum_id>/react` - Foruma reaksiyon ver

### Yorumlar

- `POST /api/comments` - Yeni yorum oluştur
- `GET /api/comments/<comment_id>` - Yorum bilgilerini getir
- `PUT /api/comments/<comment_id>` - Yorum güncelle
- `DELETE /api/comments/<comment_id>` - Yorum sil
- `GET /api/comments/<comment_id>/replies` - Yorum yanıtlarını getir
- `POST /api/comments/<comment_id>/react` - Yoruma reaksiyon ver

### Anketler

- `GET /api/polls` - Tüm anketleri getir
- `POST /api/polls` - Yeni anket oluştur
- `GET /api/polls/<poll_id>` - Anket bilgilerini getir
- `PUT /api/polls/<poll_id>` - Anket güncelle
- `DELETE /api/polls/<poll_id>` - Anket sil
- `POST /api/polls/<poll_id>/vote` - Ankete oy ver
- `GET /api/polls/<poll_id>/results` - Anket sonuçlarını getir

### Medya

- `POST /api/media/upload` - Dosya yükle
- `POST /api/media/upload-multiple` - Çoklu dosya yükle
- `POST /api/media/delete` - Dosya sil
- `POST /api/media/url` - Dosya URL'i oluştur

## Proje Yapısı

```
social_media_app/
│
├── app/                  # Ana uygulama
│   ├── api/              # API endpoints
│   ├── models/           # Veri modelleri
│   ├── services/         # İş mantığı servisleri
│   ├── middleware/       # Middleware'ler
│   └── utils/            # Yardımcı araçlar
│
├── migrations/           # Veritabanı migration scriptleri
├── tests/                # Testler
├── uploads/              # Yerel dosya yüklemeleri
├── .env                  # Ortam değişkenleri
└── run.py                # Uygulama çalıştırma dosyası
```

## Geliştirme

### Kod Stilleri ve Formatları

Proje, PEP 8 kod stil kurallarını takip eder. Kodunuzu gönderirken, lütfen bu kurallara uyun:

```bash
# Kod formatını kontrol et
flake8 app tests

# Kodu formatla
black app tests
```

### Testler

Testleri çalıştırmak için:

```bash
pytest
```

## Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.

## İletişim

Sorularınız veya geri bildirimleriniz için [email@example.com](mailto:email@example.com) adresine e-posta gönderin.