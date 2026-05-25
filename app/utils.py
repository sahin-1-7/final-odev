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
