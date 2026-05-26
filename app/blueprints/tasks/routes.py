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
        
        # 3. Gemini API veya Simülasyon Yanıtı Üret
        ai_response = None
        if api_key_configured:
            ai_response = get_gemini_chat_response(user_message, history_list[:-1], tasks_data)
            
        if not ai_response:
            # SİMÜLASYON MODU (Fallback / Offline Demo Modu)
            # Kullanıcının mesajına göre akıllıca ve gerçekçi Türkçe yanıtlar simüle edilir
            msg_lower = user_message.lower()
            if any(k in msg_lower for k in ["selam", "merhaba", "hey", "naber", "meraba"]):
                ai_response = (
                    f"Merhaba **{current_user.username}**! Şu an *Çevrimdışı (Simülasyon)* modunda olsak da sana destek olmaya hazırım.\n\n"
                    "Bugünkü görev listeni analiz etmemi ister misin? Ya da planındaki saat çakışmalarını kontrol edebiliriz. "
                    "Hangisiyle başlayalım?"
                )
            elif any(k in msg_lower for k in ["görev", "sırala", "plan", "iş", "hedef", "list"]):
                if tasks:
                    tasks_sorted_str = ""
                    # Görevleri öncelik sırasına göre sıralayalım
                    priority_weights = {'High': 3, 'Medium': 2, 'Low': 1}
                    sorted_t = sorted(tasks, key=lambda t: -priority_weights.get(t.priority, 2))
                    for i, t in enumerate(sorted_t, 1):
                        status = "✅" if t.is_completed else "⏳"
                        tasks_sorted_str += f"{i}. {status} **{t.title}** *(Öncelik: {t.priority}, Saat: {t.start_time} - {t.end_time})*\n"
                    
                    ai_response = (
                        f"Harika! Güncel listendeki **{len(tasks)}** adet görevi senin için analiz ettim. "
                        "Üretkenliğini en üst düzeye çıkarmak için görevlerini öncelik sırasına göre dizdim:\n\n"
                        f"{tasks_sorted_str}\n"
                        "💡 **Glide Tavsiyesi:** Güne en yüksek öncelikli görevlerinle başlamanı öneririm. "
                        "Bu sıralama senin için uygun mu? Saati değişmesi gereken bir görev var mı?"
                    )
                else:
                    ai_response = (
                        "Güncel planında henüz tanımlı bir görev göremedim. "
                        "Öncelikle panelden birkaç görev (örn: ders çalışmak, toplantı vb.) eklersen, "
                        "onları senin için en verimli şekilde sıralayabilirim."
                    )
            elif any(k in msg_lower for k in ["çakış", "overlap", "saat", "kontrol"]):
                # Zaman çakışması kontrolü
                from app.ai_engine import check_overlap
                conflicts = []
                for i in range(len(tasks)):
                    for j in range(i + 1, len(tasks)):
                        if tasks[i].period == tasks[j].period and check_overlap(tasks[i], tasks[j]):
                            conflicts.append((tasks[i], tasks[j]))
                if conflicts:
                    conflict_str = ""
                    for t1, t2 in conflicts:
                        conflict_str += f"- **Çakışma:** [{t1.start_time}-{t1.end_time}] saatlerindeki *\"{t1.title}\"* ile [{t2.start_time}-{t2.end_time}] saatlerindeki *\"{t2.title}\"* çakışıyor.\n"
                    ai_response = (
                        "Zaman çizelgende yaptığım analizde bazı görevlerinin çakıştığını tespit ettim:\n\n"
                        f"{conflict_str}\n"
                        "💡 *Öneri: Çakışan görevlerden daha az öncelikli olanın saat aralığını güncelleyebiliriz.*"
                    )
                else:
                    ai_response = "🎉 Harika! Zaman planında herhangi bir saat veya görev çakışması tespit edilmedi. Her şey dengeli görünüyor."
            else:
                ai_response = (
                    "Glide yapay zeka asistanı çevrimdışı (simülasyon) modunda çalışıyor. "
                    "Gerçek zamanlı olarak Gemini üretken zekasını deneyimlemek için `.env` dosyanıza kendi API anahtarınızı ekleyebilirsiniz.\n\n"
                    "Şu anki görevlerini öncelik sırasına koymamı veya saat çakışmalarını incelememi ister misin?"
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
    model_name = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
    return render_template('tasks/ai_chat.html', chats=chats, api_configured=api_key_configured, model_name=model_name)


@tasks_bp.route('/ai/chat/clear', methods=['POST'])
@login_required
def ai_chat_clear():
    """
    Kullanıcının sohbet geçmişini veritabanından tamamen siler.
    """
    ChatHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Sohbet geçmişi başarıyla temizlendi.'})

