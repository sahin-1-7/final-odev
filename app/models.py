from datetime import datetime
from flask_login import UserMixin
from app.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey, Text

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(256), nullable=False)
    avatar: Mapped[str] = mapped_column(String(200), default='default_avatar.png', nullable=False)
    last_reset_request_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # İlişkiler (Kullanıcı silindiğinde görevleri de silinir)
    tasks: Mapped[list["Task"]] = relationship('Task', backref='owner', lazy=True, cascade="all, delete-orphan")
    suggestions: Mapped[list["AISuggestion"]] = relationship('AISuggestion', backref='owner', lazy=True, cascade="all, delete-orphan")
    chat_history: Mapped[list["ChatHistory"]] = relationship('ChatHistory', backref='owner', lazy=True, cascade="all, delete-orphan")

    @property
    def api_key(self):
        """Kullanıcı için kriptografik olarak imzalanmış ve doğrulanabilir benzersiz bir API anahtarı üretir."""
        from itsdangerous import URLSafeTimedSerializer as Serializer
        from flask import current_app
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})


class Task(db.Model):
    __tablename__ = 'tasks'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    period: Mapped[str] = mapped_column(String(20), default="daily", nullable=False)      # 'daily', 'weekly', 'monthly'
    priority: Mapped[str] = mapped_column(String(20), default="Medium", nullable=False)    # 'Low', 'Medium', 'High'
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)                     # HH:MM formatı
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)                       # HH:MM formatı
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    priority_order: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    
    # Kullanıcı ilişkisi
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

    @property
    def is_failed(self):
        """Görevin süresi geçmiş ve hala tamamlanmamışsa True döner (Yapılamadı)."""
        if self.is_completed:
            return False
        from datetime import datetime
        from app.utils import parse_time_to_minutes
        
        now_str = datetime.now().strftime("%H:%M")
        now_min = parse_time_to_minutes(now_str)
        end_min = parse_time_to_minutes(self.end_time)
        return now_min > end_min


class AISuggestion(db.Model):
    __tablename__ = 'ai_suggestions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    suggestion_text: Mapped[str] = mapped_column(Text, nullable=False)
    ai_evaluation_tr: Mapped[str] = mapped_column(Text, nullable=True)
    ai_evaluation_en: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Kullanıcı ilişkisi
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

    @property
    def localized_text(self):
        try:
            from flask_babel import get_locale
            lang = str(get_locale())
        except Exception:
            lang = 'tr'
            
        if lang == 'en':
            return self.ai_evaluation_en or self.suggestion_text
        return self.ai_evaluation_tr or self.suggestion_text

class ChatHistory(db.Model):
    __tablename__ = 'chat_histories'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sender: Mapped[str] = mapped_column(String(10), nullable=False) # 'user' veya 'ai'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Kullanıcı ilişkisi
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)


class DeveloperEmail(db.Model):
    __tablename__ = 'developer_emails'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str] = mapped_column(String(120), nullable=False)
    recipient: Mapped[str] = mapped_column(String(120), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    html: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
