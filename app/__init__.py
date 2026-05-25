import os
from flask import Flask, request, session
from app.config import Config
from app.extensions import db, migrate, mail, babel, login_manager
from app.models import User

def get_locale():
    # Dil seçimini query parametresinden, session'dan ya da tarayıcı dilinden al
    lang = request.args.get('lang')
    if lang in ['tr', 'en']:
        session['lang'] = lang
        return lang
    return session.get('lang', request.accept_languages.best_match(['tr', 'en']) or 'tr')

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
    
    # Static uploads klasörünün varlığından emin ol
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
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
