from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask_mail import Message

from app.blueprints.auth import auth_bp
from app.extensions import db, mail
from app.models import User

def get_reset_token(user, expires_sec=900):
    """itsdangerous ile 15 dakika geçerli güvenli şifre sıfırlama token'ı üretir."""
    s = Serializer(current_app.config['SECRET_KEY'])
    return s.dumps({'user_id': user.id})

def verify_reset_token(token, expires_sec=900):
    """Token'ı doğrular ve ilgili kullanıcı nesnesini döner."""
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token, max_age=expires_sec)['user_id']
    except Exception:
        return None
    return User.query.get(user_id)

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

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not email or not password:
            flash('Tüm alanların doldurulması zorunludur.', 'danger')
            return render_template('auth/register.html')
            
        # Kullanıcı adı veya e-posta benzersizlik kontrolü
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                flash('Bu kullanıcı adı zaten alınmış.', 'danger')
            else:
                flash('Bu e-posta adresi zaten kayıtlı.', 'danger')
            return render_template('auth/register.html')
            
        # Şifre hashleme ve kaydetme
        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Kayıt başarıyla tamamlandı! Artık giriş yapabilirsiniz.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Tekrar hoş geldiniz, {username}!', 'success')
            return redirect(url_for('tasks.dashboard'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        if user:
            send_reset_email(user)
            flash('Şifre sıfırlama talimatları e-posta adresinize gönderildi.', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('Bu e-posta adresiyle kayıtlı bir kullanıcı bulunamadı.', 'warning')
            
    return render_template('auth/reset_request.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('tasks.dashboard'))
        
    user = verify_reset_token(token)
    if not user:
        flash('Geçersiz veya süresi dolmuş sıfırlama bağlantısı.', 'danger')
        return redirect(url_for('auth.reset_request'))
        
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        if not password:
            flash('Yeni şifre boş olamaz.', 'danger')
            return render_template('auth/reset_token.html')
            
        hashed_password = generate_password_hash(password, method='scrypt')
        user.password = hashed_password
        db.session.commit()
        
        flash('Şifreniz başarıyla güncellendi! Yeni şifrenizle giriş yapabilirsiniz.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_token.html')
