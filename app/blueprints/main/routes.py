import os
from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.blueprints.main import main_bp
from app.extensions import db
from app.models import User

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
        
        # Avatar Resim Yükleme Kontrolü (Bonus Özellik +4 Puan)
        if avatar_file and avatar_file.filename != '':
            if allowed_file(avatar_file.filename):
                # secure_filename ile güvenlik kontrolü yapılıyor
                original_filename = secure_filename(avatar_file.filename)
                ext = original_filename.rsplit('.', 1)[1].lower()
                
                # Kullanıcıya özel benzersiz dosya adı oluşturulması çakışmaları ve güvenlik açıklarını önler
                filename = f"avatar_{current_user.id}_{int(os.path.getmtime(current_app.config['UPLOAD_FOLDER'])) if os.path.exists(current_app.config['UPLOAD_FOLDER']) else 1}.{ext}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                
                avatar_file.save(filepath)
                current_user.avatar = filename
                flash('Profil fotoğrafınız başarıyla güncellendi!', 'success')
            else:
                flash('Desteklenmeyen dosya formatı. İzin verilenler: PNG, JPG, JPEG, GIF', 'danger')
                return redirect(url_for('main.profile'))
                
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
