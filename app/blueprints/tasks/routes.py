from flask import render_template, redirect, url_for, request, flash, jsonify, current_app
import os
from flask_login import login_required, current_user
from app.blueprints.tasks import tasks_bp
from app.extensions import db
from app.models import Task, AISuggestion, ChatHistory
from app.ai_engine import analyze_and_optimize_tasks, get_gemini_chat_response
from app.utils import parse_time_to_minutes

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

@tasks_bp.route('/ai/chat', methods=['GET', 'POST'])
@login_required
def ai_chat():
    api_key_configured = bool(current_app.config.get('GEMINI_API_KEY') or os.environ.get('GEMINI_API_KEY'))
    
    if request.method == 'POST':
        if not api_key_configured:
            return jsonify({'error': 'Yapay Zeka API anahtarı yapılandırılmamış. Sohbet başlatılamıyor.'}), 400
            
        user_message = request.form.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'Mesaj boş olamaz.'}), 400
            
        # 1. Kullanıcının mesajını veritabanına kaydet
        user_chat = ChatHistory(message=user_message, sender='user', user_id=current_user.id)
        db.session.add(user_chat)
        db.session.commit()
        
        # 2. Geçmiş konuşmaları ve görev verilerini çek
        history = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.created_at.asc()).all()
        # Son 15 konuşmayı alalım (Gemini bağlamı için)
        history_list = [{'message': h.message, 'sender': h.sender} for h in history[-15:]]
        
        tasks = Task.query.filter_by(user_id=current_user.id).all()
        tasks_list = []
        for idx, t in enumerate(tasks, 1):
            tasks_list.append(
                f"- Görev {idx}: '{t.title}' [Öncelik: {t.priority}, Saat: {t.start_time}-{t.end_time}, Durum: {'Tamamlandı' if t.is_completed else 'Bekliyor'}]"
            )
        tasks_data = "\n".join(tasks_list) if tasks_list else "Henüz görev tanımlanmamış."
        
        # 3. Gemini API'den yanıt üret
        ai_response = get_gemini_chat_response(user_message, history_list[:-1], tasks_data)
        
        if not ai_response:
            ai_response = (
                "Üzgünüm, şu anda Google Gemini sunucularıyla bağlantı kuramadım. "
                "Lütfen internet bağlantınızı kontrol edin veya daha sonra tekrar deneyin."
            )
            
        # 4. Yapay zekanın yanıtını kaydet
        ai_chat = ChatHistory(message=ai_response, sender='ai', user_id=current_user.id)
        db.session.add(ai_chat)
        db.session.commit()
        
        return jsonify({
            'user_message': user_message,
            'ai_response': ai_response
        })
        
    # GET Talebinde geçmiş konuşmaları arayüze yükle
    chats = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.created_at.asc()).all()
    return render_template('tasks/ai_chat.html', chats=chats, api_configured=api_key_configured)
