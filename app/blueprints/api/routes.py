from flask import jsonify, request
from flask_login import current_user
from flask_babel import gettext as _
from app.blueprints.api import api_bp
from app.models import Task, User
from app.extensions import db

def get_authenticated_user():
    """
    Tarayıcı oturumunu (session) veya HTTP X-API-KEY başlığını doğrular ve ilişkili kullanıcıyı döner.
    Kimlik doğrulama başarısız olursa None döner.
    """
    if current_user.is_authenticated:
        return current_user
        
    api_key = request.headers.get('X-API-KEY')
    if api_key:
        from itsdangerous import URLSafeTimedSerializer as Serializer
        from flask import current_app
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(api_key)
            user_id = data.get('user_id')
            if user_id:
                user = User.query.get(user_id)
                if user:
                    return user
        except Exception:
            pass
            
    return None

@api_bp.route('/v1/tasks', methods=['GET'])
def get_tasks():
    """Kullanıcının görev listesini gelişmiş JSON formatında döner."""
    user = get_authenticated_user()
    if not user:
        return jsonify({
            'error': 'Unauthorized', 
            'message': _('Lütfen bu servis için geçerli bir oturum açın veya X-API-KEY başlığı sağlayın.')
        }), 401
        
    # BOLA/IDOR Zafiyeti Önleme: Görevler sadece sorgulayan kullanıcının ID'sine göre filtrelenir
    tasks = Task.query.filter_by(user_id=user.id).all()
    
    # En son AI planlama önerisini/raporunu getir (3. gündeki raporlar)
    from app.models import AISuggestion
    latest_suggestion = AISuggestion.query.filter_by(user_id=user.id).order_by(AISuggestion.created_at.desc()).first()
    
    ai_evaluation_tr = latest_suggestion.ai_evaluation_tr if latest_suggestion else None
    ai_evaluation_en = latest_suggestion.ai_evaluation_en if latest_suggestion else None
    
    task_list = []
    for task in tasks:
        task_list.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'period': task.period,
            'priority': task.priority,
            'start_time': task.start_time,
            'end_time': task.end_time,
            'is_completed': task.is_completed,
            'created_at': task.created_at.isoformat(),
            'priority_order': task.priority_order,
            'ai_evaluation_tr': ai_evaluation_tr,
            'ai_evaluation_en': ai_evaluation_en
        })
        
    return jsonify({
        'success': True,
        'count': len(task_list),
        'tasks': task_list
    }), 200

@api_bp.route('/v1/tasks', methods=['POST'])
def create_task():
    """Kullanıcı için yeni bir görevi JSON verisiyle oluşturur (Girdi Doğrulamalı)."""
    user = get_authenticated_user()
    if not user:
        return jsonify({
            'error': 'Unauthorized', 
            'message': _('Görev oluşturabilmek için lütfen geçerli bir oturum açın veya X-API-KEY başlığı sağlayın.')
        }), 401
        
    # JSON verisini çek
    data = request.get_json() or {}
    
    title = data.get('title', '').strip() if data.get('title') else ''
    description = data.get('description', '').strip() if data.get('description') else ''
    period = data.get('period', 'daily')
    priority = data.get('priority', 'Medium')
    start_time = data.get('start_time', '').strip() if data.get('start_time') else ''
    end_time = data.get('end_time', '').strip() if data.get('end_time') else ''
    
    # 1. Girdi Validasyonu: Zorunlu Alan Kontrolleri
    if not title:
        return jsonify({
            'error': 'Bad Request',
            'message': _('Görev başlığı (title) zorunludur.')
        }), 400
        
    if not start_time or not end_time:
        return jsonify({
            'error': 'Bad Request',
            'message': _('Başlangıç saati (start_time) ve bitiş saati (end_time) zorunludur.')
        }), 400
        
    # 2. Girdi Validasyonu: Saat formatı (HH:MM)
    import re
    time_regex = re.compile(r'^(?:[01]\d|2[0-3]):[0-5]\d$')
    if not time_regex.match(start_time) or not time_regex.match(end_time):
        return jsonify({
            'error': 'Bad Request',
            'message': _('Saat formatı geçersizdir. Lütfen HH:MM formatında (örn: 09:00) gönderin.')
        }), 400
        
    # 3. Girdi Validasyonu: Değer Kontrolleri (Enums)
    if period not in ['daily', 'weekly', 'monthly']:
        return jsonify({
            'error': 'Bad Request',
            'message': _('Geçersiz periyot (period) değeri. İzin verilenler: daily, weekly, monthly.')
        }), 400
        
    if priority not in ['Low', 'Medium', 'High']:
        return jsonify({
            'error': 'Bad Request',
            'message': _('Geçersiz öncelik (priority) değeri. İzin verilenler: Low, Medium, High.')
        }), 400
        
    # 4. Girdi Validasyonu: Başlangıç/Bitiş Karşılaştırması
    from app.utils import parse_time_to_minutes
    start_min = parse_time_to_minutes(start_time)
    end_min = parse_time_to_minutes(end_time)
    
    if start_min >= end_min:
        return jsonify({
            'error': 'Bad Request',
            'message': _('Görev başlangıç saati bitiş saatinden büyük veya eşit olamaz.')
        }), 400
        
    # 5. Zaman Çakışması Kontrolü (BOLA/IDOR önlenerek sadece bu kullanıcının görevleri kontrol edilir)
    existing_tasks = Task.query.filter_by(user_id=user.id, period=period).all()
    for t in existing_tasks:
        t_start = parse_time_to_minutes(t.start_time)
        t_end = parse_time_to_minutes(t.end_time)
        if max(start_min, t_start) < min(end_min, t_end):
            return jsonify({
                'error': 'Bad Request',
                'message': _('Zaman çakışması tespit edildi: Bu saatler arasında zaten başka bir göreviniz ("%(title)s") bulunmaktadır.', title=t.title)
            }), 400
            
    # Validasyonlardan başarıyla geçti, görevi veritabanına ekle
    new_task = Task(
        title=title,
        description=description,
        period=period,
        priority=priority,
        start_time=start_time,
        end_time=end_time,
        user_id=user.id
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': _('Görev başarıyla oluşturuldu.'),
        'task': {
            'id': new_task.id,
            'title': new_task.title,
            'description': new_task.description,
            'period': new_task.period,
            'priority': new_task.priority,
            'start_time': new_task.start_time,
            'end_time': new_task.end_time,
            'is_completed': new_task.is_completed,
            'created_at': new_task.created_at.isoformat()
        }
    }), 201
