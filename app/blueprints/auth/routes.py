from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app.blueprints.auth import auth_bp
from app.extensions import db
from app.models import User
from app.utils import send_reset_email, verify_reset_token

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
        from datetime import datetime
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        
        # Jenerik güvenlik bildirimi (Kullanıcı tespiti saldırılarına karşı koruma)
        success_msg = 'Eğer girdiğiniz e-posta adresi sistemimizde kayıtlı ise, şifre sıfırlama bağlantısı gönderilecektir.'
        
        if user:
            # Hız Sınırlama (Rate Limit) Kontrolü (120 saniye)
            now = datetime.utcnow()
            if user.last_reset_request_at:
                time_diff = (now - user.last_reset_request_at).total_seconds()
                if time_diff < 120:
                    wait_time = int(120 - time_diff)
                    flash(f'Çok hızlı istek gönderdiniz. Lütfen {wait_time} saniye sonra tekrar deneyin.', 'warning')
                    return render_template('auth/reset_request.html')
            
            # İstek zamanını güncelle ve e-postayı gönder
            user.last_reset_request_at = now
            db.session.commit()
            
            send_reset_email(user)
            
        # Kullanıcı kayıtlı olsa da olmasa da dışarıya hep aynı jenerik başarı mesajı dönülür!
        flash(success_msg, 'info')
        return redirect(url_for('auth.login'))
            
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
