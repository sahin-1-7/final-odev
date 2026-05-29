import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'vibe-coding-super-secret-key-12345')
    
    # Veritabanı
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(BASE_DIR, "instance", "task_planner.db").replace('\\', '/')
    
    raw_db_url = os.environ.get('DATABASE_URL')
    if raw_db_url:
        if raw_db_url.startswith("postgres://"):
            raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = raw_db_url
    else:
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # E-posta Konfigürasyonu
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    
    # Dosya Yükleme (Avatar)
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'app', 'static', 'uploads'))
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # Maksimum 2MB avatar
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Flask-Babel Çoklu Dil
    BABEL_DEFAULT_LOCALE = os.environ.get('BABEL_DEFAULT_LOCALE', 'tr')
    BABEL_DEFAULT_TIMEZONE = os.environ.get('BABEL_DEFAULT_TIMEZONE', 'Europe/Istanbul')
