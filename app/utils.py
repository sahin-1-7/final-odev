import os
from flask import render_template, url_for, current_app
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask_mail import Message
from app.extensions import mail

def parse_time_to_minutes(time_str):
    """'HH:MM' formatındaki saati gece yarısından itibaren dakikaya çevirir."""
    try:
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    except Exception:
        return 0

def get_reset_token(user, expires_sec=900):
    """itsdangerous ile 15 dakika geçerli güvenli şifre sıfırlama token'ı üretir."""
    s = Serializer(current_app.config['SECRET_KEY'])
    return s.dumps({'user_id': user.id})

def verify_reset_token(token, expires_sec=900):
    """Token'ı doğrular ve ilgili kullanıcı nesnesini döner."""
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        from app.models import User
        user_id = s.loads(token, max_age=expires_sec)['user_id']
        return User.query.get(user_id)
    except Exception:
        return None

def send_reset_email(user):
    """Kullanıcıya şifre sıfırlama e-postası gönderir."""
    token = get_reset_token(user)
    msg = Message('Zaman ve Görev Yöneticisi - Şifre Sıfırlama Talebi',
                  recipients=[user.email])
    
    # E-posta içeriği
    reset_url = url_for('auth.reset_token', token=token, _external=True)
    msg.body = f'''Şifrenizi sıfırlamak için lütfen aşağıdaki bağlantıya tıklayın:
{reset_url}

Bu istek sizin tarafınızdan yapılmadıysa lütfen bu e-postayı dikkate almayın.
Giriş bilgileriniz güvendedir.
'''
    msg.html = render_template('auth/reset_email.html', user=user, reset_url=reset_url)
    
    try:
        mail.send(msg)
    except Exception as e:
        # SMTP ayarları yapılmamışsa hata vermemesi için yakalıyoruz ve konsola/terminale linki yazdırıyoruz
        print(f"\n[POSTA SİSTEMİ HATA] E-posta gönderilemedi: {e}")
        print("\n" + "="*50)
        print("=== ŞİFRE SIFIRLAMA BAĞLANTISI (GELİŞTİRİCİ KONSOLU) ===")
        print(reset_url)
        print("="*50 + "\n")

import uuid
from PIL import Image

def save_secure_avatar(avatar_file, upload_folder, user_id):
    """
    Siber güvenlik penetrasyon testlerinden sorunsuz geçecek şekilde
    profil fotoğrafını doğrular, temizler, yeniden boyutlandırır/kodlar ve kaydeder.
    """
    filename = avatar_file.filename
    if not filename or '.' not in filename:
        return None, "Geçersiz dosya adı."
        
    ext = filename.rsplit('.', 1)[1].lower()
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    if ext not in ALLOWED_EXTENSIONS:
        return None, "Desteklenmeyen dosya formatı. İzin verilenler: PNG, JPG, JPEG, GIF"
        
    # 1. Kriptografik olarak güvenli rastgele ve benzersiz yeni dosya adı (UUIDv4)
    secure_name = f"avatar_{user_id}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_folder, secure_name)
    
    try:
        # 2. Dosya işaretçisini sıfırla ve Pillow ile doğrula
        avatar_file.seek(0)
        img = Image.open(avatar_file)
        
        # 3. Dosya formatının doğruluğunu Pillow ile teyit et
        img_format = img.format.lower()
        valid_formats = {'png', 'jpeg', 'gif', 'jpg'}
        if img_format not in valid_formats:
            return None, "Dosya içeriği geçerli bir resim formatında değil."
            
        # 4. EXIF ve Zararlı Kod Temizleme (Sanitization)
        # Resmi temiz kanallara sahip yeni bir resme dönüştürüp kaydederek
        # EXIF veya comment satırlarına gizlenmiş zararlı scriptleri yok ediyoruz.
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
            
        # Avatar için resmi 400x400 pikselliğe orantılı düşürüyoruz (DoS koruması ve optimizasyon)
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        
        # Dosya yazma işlemini gerçekleştiriyoruz
        os.makedirs(upload_folder, exist_ok=True)
        img.save(filepath, format=img.format)
        
        return secure_name, None
        
    except Exception as e:
        # Hata durumunda dosya içeriğinin bozuk veya manipüle edilmiş olduğunu varsayıyoruz
        return None, "Dosya içeriği doğrulanamadı. Bozuk veya zararlı içerik algılandı."

