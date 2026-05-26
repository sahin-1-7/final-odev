from datetime import datetime
from flask_login import UserMixin
from app.extensions import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    avatar = db.Column(db.String(200), default='default_avatar.png', nullable=False)
    last_reset_request_at = db.Column(db.DateTime, nullable=True)
    
    # İlişkiler (Kullanıcı silindiğinde görevleri de silinir)
    tasks = db.relationship('Task', backref='owner', lazy=True, cascade="all, delete-orphan")
    suggestions = db.relationship('AISuggestion', backref='owner', lazy=True, cascade="all, delete-orphan")
    chat_history = db.relationship('ChatHistory', backref='owner', lazy=True, cascade="all, delete-orphan")

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    period = db.Column(db.String(20), default="daily", nullable=False)      # 'daily', 'weekly', 'monthly'
    priority = db.Column(db.String(20), default="Medium", nullable=False)    # 'Low', 'Medium', 'High'
    start_time = db.Column(db.String(5), nullable=False)                     # HH:MM formatı
    end_time = db.Column(db.String(5), nullable=False)                       # HH:MM formatı
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Kullanıcı ilişkisi
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class AISuggestion(db.Model):
    __tablename__ = 'ai_suggestions'
    
    id = db.Column(db.Integer, primary_key=True)
    suggestion_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Kullanıcı ilişkisi
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class ChatHistory(db.Model):
    __tablename__ = 'chat_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(10), nullable=False) # 'user' veya 'ai'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Kullanıcı ilişkisi
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
