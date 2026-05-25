from flask import jsonify, request
from flask_login import current_user
from app.blueprints.api import api_bp
from app.models import Task
from app.extensions import db

@api_bp.route('/v1/tasks', methods=['GET'])
def get_tasks():
    """Kullanıcının görev listesini JSON formatında döner."""
    if not current_user.is_authenticated:
        return jsonify({
            'error': 'Unauthorized', 
            'message': 'Lütfen bu servis için oturum açın veya geçerli bir kimlik bilgisi sağlayın.'
        }), 401
        
    tasks = Task.query.filter_by(user_id=current_user.id).all()
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
            'created_at': task.created_at.isoformat()
        })
        
    return jsonify({
        'success': True,
        'count': len(task_list),
        'tasks': task_list
    }), 200

@api_bp.route('/v1/tasks', methods=['POST'])
def create_task():
    """Kullanıcı için yeni bir görevi JSON verisiyle oluşturur."""
    if not current_user.is_authenticated:
        return jsonify({
            'error': 'Unauthorized', 
            'message': 'Görev oluşturabilmek için lütfen giriş yapın.'
        }), 401
        
    # JSON verisini çek
    data = request.get_json() or {}
    
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    period = data.get('period', 'daily')
    priority = data.get('priority', 'Medium')
    start_time = data.get('start_time', '09:00')
    end_time = data.get('end_time', '10:00')
    
    if not title:
        return jsonify({
            'error': 'Bad Request',
            'message': 'Görev başlığı (title) zorunludur.'
        }), 400
        
    new_task = Task(
        title=title,
        description=description,
        period=period,
        priority=priority,
        start_time=start_time,
        end_time=end_time,
        user_id=current_user.id
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Görev başarıyla oluşturuldu.',
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
