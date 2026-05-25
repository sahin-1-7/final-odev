from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.blueprints.tasks import tasks_bp
from app.extensions import db
from app.models import Task, AISuggestion
from app.ai_engine import analyze_and_optimize_tasks, parse_time_to_minutes

@tasks_bp.route('/dashboard')
@login_required
def dashboard():
    # Filtreler ve Arama Parametreleri
    period_filter = request.args.get('period', 'all')
    priority_filter = request.args.get('priority', 'all')
    search_query = request.args.get('q', '').strip()
    
    query = Task.query.filter_by(user_id=current_user.id)
    
    # SQL LIKE Tabanlı Full-Text Arama (Bonus Özellik +3 Puan)
    if search_query:
        query = query.filter(
            (Task.title.like(f"%{search_query}%")) | 
            (Task.description.like(f"%{search_query}%"))
        )
    
    if period_filter != 'all':
        query = query.filter_by(period=period_filter)
    if priority_filter != 'all':
        query = query.filter_by(priority=priority_filter)
        
    # Görevleri başlangıç saatine göre sıralayarak al
    tasks = query.order_by(Task.start_time).all()
    
    # En son AI planlama önerisini getir
    latest_suggestion = AISuggestion.query.filter_by(user_id=current_user.id).order_by(AISuggestion.created_at.desc()).first()
    
    return render_template(
        'tasks/dashboard.html', 
        tasks=tasks, 
        period_filter=period_filter, 
        priority_filter=priority_filter, 
        search_query=search_query,
        latest_suggestion=latest_suggestion
    )

@tasks_bp.route('/add', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    period = request.form.get('period', 'daily')
    priority = request.form.get('priority', 'Medium')
    start_time = request.form.get('start_time', '09:00')
    end_time = request.form.get('end_time', '10:00')
    
    if not title:
        flash('Görev başlığı boş bırakılamaz.', 'danger')
        return redirect(url_for('tasks.dashboard'))
        
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
    
    flash('Görev başarıyla eklendi!', 'success')
    return redirect(url_for('tasks.dashboard'))

@tasks_bp.route('/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.is_completed = not task.is_completed
    db.session.commit()
    
    status_str = "tamamlandı" if task.is_completed else "tamamlanmadı"
    flash(f'"{task.title}" görevi {status_str} olarak işaretlendi.', 'success')
    return redirect(url_for('tasks.dashboard'))

@tasks_bp.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    
    flash(f'"{task.title}" görevi başarıyla silindi.', 'success')
    return redirect(url_for('tasks.dashboard'))

@tasks_bp.route('/ai/optimize', methods=['POST'])
@login_required
def ai_optimize():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    if not tasks:
        flash('Yapay zeka analizi için en az bir görev tanımlamış olmalısınız.', 'warning')
        return redirect(url_for('tasks.dashboard'))
        
    # AI analizi ve optimizasyon motorunu çalıştır
    result_text = analyze_and_optimize_tasks(tasks)
    
    # Yeni öneriyi veritabanına kaydet
    new_suggestion = AISuggestion(suggestion_text=result_text, user_id=current_user.id)
    db.session.add(new_suggestion)
    db.session.commit()
    
    flash('Görevleriniz yapay zeka tarafından başarıyla analiz edildi!', 'success')
    return redirect(url_for('tasks.ai_planner'))

@tasks_bp.route('/ai/planner')
@login_required
def ai_planner():
    latest_suggestion = AISuggestion.query.filter_by(user_id=current_user.id).order_by(AISuggestion.created_at.desc()).first()
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Yapay zekanın önerdiği öncelik sıralaması
    priority_weights = {'High': 3, 'Medium': 2, 'Low': 1}
    sorted_tasks = sorted(
        tasks, 
        key=lambda t: (
            t.period, 
            -priority_weights.get(t.priority, 2), 
            parse_time_to_minutes(t.start_time)
        )
    )
    
    return render_template(
        'tasks/ai_planner.html', 
        suggestion=latest_suggestion, 
        tasks=sorted_tasks
    )
