from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel

# Eklenti örneklerini tanımla (Circular Dependency engellemek için)
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
babel = Babel()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bu sayfaya erişmek için lütfen giriş yapın.'
login_manager.login_message_category = 'warning'
