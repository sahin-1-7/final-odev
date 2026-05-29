import os
from flask import Flask, request, session
from app.config import Config
from app.extensions import db, migrate, mail, babel, login_manager
from app.models import User

def get_locale():
    # Dil seçimini query parametresinden, session'dan ya da tarayıcı dilinden al
    lang = request.args.get('lang')
    allowed_langs = ['tr', 'en', 'fr', 'es', 'hi', 'ar']
    if lang in allowed_langs:
        try:
            session['lang'] = lang
        except Exception:
            pass
        return lang
    
    try:
        sess_lang = session.get('lang')
    except Exception:
        sess_lang = None
        
    return sess_lang or request.accept_languages.best_match(allowed_langs) or 'tr'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Instance klasörünü oluştur
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Eklentileri uygulamaya bağla
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # Babel dil desteğini başlat
    babel.init_app(app, locale_selector=get_locale)
    
    # LoginManager'ı başlat
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Static uploads ve avatars klasörlerinin varlığından emin ol
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)
    
    # Çeviri dosyalarını pybabel ile otomatik derle
    try:
        from babel.messages.frontend import CommandLineInterface
        CommandLineInterface().run(['pybabel', 'compile', '-d', 'app/translations'])
    except Exception as e:
        app.logger.warning(f"Otomatik çeviri derleme adımı atlandı: {e}")
    
    # Blueprint'leri kaydet
    from app.blueprints.auth import auth_bp
    from app.blueprints.tasks import tasks_bp
    from app.blueprints.api import api_bp
    from app.blueprints.main import main_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(main_bp)
    
    return app
