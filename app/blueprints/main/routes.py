import os
from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.blueprints.main import main_bp
from app.extensions import db
from app.models import User
from app.utils import save_secure_avatar

def allowed_file(filename):
    """Dosya uzantısının izin verilen listede olup olmadığını kontrol eder."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@main_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.dashboard'))
    return render_template('main/index.html')

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        avatar_file = request.files.get('avatar')
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not username or not email:
            flash('Kullanıcı adı ve e-posta alanları zorunludur.', 'danger')
            return redirect(url_for('main.profile'))
            
        # Başka bir kullanıcının bilgileriyle çakışma kontrolü
        existing_user = User.query.filter(((User.username == username) | (User.email == email)) & (User.id != current_user.id)).first()
        if existing_user:
            if existing_user.username == username:
                flash('Bu kullanıcı adı zaten başka bir kullanıcı tarafından alınmış.', 'danger')
            else:
                flash('Bu e-posta adresi zaten başka bir kullanıcı tarafından kayıt edilmiş.', 'danger')
            return redirect(url_for('main.profile'))
            
        # Profil bilgilerini güncelle
        current_user.username = username
        current_user.email = email
        
        # Şifre Değiştirme Mantığı
        if new_password:
            if len(new_password) < 6:
                flash('Yeni şifre en az 6 karakter olmalıdır.', 'danger')
                return redirect(url_for('main.profile'))
            if new_password != confirm_password:
                flash('Girdiğiniz şifreler birbiriyle uyuşmuyor.', 'danger')
                return redirect(url_for('main.profile'))
                
            from werkzeug.security import generate_password_hash
            current_user.password = generate_password_hash(new_password, method='scrypt')
            flash('Şifreniz başarıyla güncellendi!', 'success')
        
        # Avatar Resim Yükleme Kontrolü (Güvenlik Odaklı +4 Puan)
        if avatar_file and avatar_file.filename != '':
            # Güvenli kaydetme ve doğrulama fonksiyonunu çağırıyoruz
            filename, error = save_secure_avatar(
                avatar_file=avatar_file,
                upload_folder=current_app.config['UPLOAD_FOLDER'],
                user_id=current_user.id
            )
            
            if error:
                flash(error, 'danger')
                return redirect(url_for('main.profile'))
                
            # Eğer yükleme başarılıysa ve kullanıcının eski avatarı varsayılandan farklıysa eskiyi temizliyoruz
            if current_user.avatar and current_user.avatar != 'default_avatar.png':
                old_avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.avatar)
                if os.path.exists(old_avatar_path):
                    try:
                        os.remove(old_avatar_path)
                    except Exception:
                        pass # Silme sırasında oluşabilecek bir kilitlenme hatası işlemi durdurmamalı
                        
            current_user.avatar = filename
            flash('Profil fotoğrafınız başarıyla güncellendi!', 'success')
                
        db.session.commit()
        flash('Profil bilgileriniz başarıyla güncellendi!', 'success')
        return redirect(url_for('main.profile'))
        
    return render_template('main/profile.html')

# Global Hata Yönetimi (Error Handlers)
@main_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('main/errors.html', error_code=404, error_message="Aradığınız sayfa bulunamadı."), 404

@main_bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('main/errors.html', error_code=500, error_message="Sunucu tarafında beklenmedik bir hata oluştu."), 500
