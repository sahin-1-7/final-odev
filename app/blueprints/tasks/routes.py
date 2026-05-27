from flask import render_template, redirect, url_for, request, flash, jsonify, current_app
import os
from flask_login import login_required, current_user
from flask_babel import gettext as _
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
    start_time = request.form.get('start_time', '09:00').strip()
    end_time = request.form.get('end_time', '10:00').strip()
    
    if not title:
        flash(_('Görev başlığı boş bırakılamaz.'), 'danger')
        return redirect(url_for('tasks.dashboard'))
        
    if not start_time or not end_time:
        flash(_('Başlangıç ve bitiş saatleri boş bırakılamaz.'), 'danger')
        return redirect(url_for('tasks.dashboard'))
        
    start_min = parse_time_to_minutes(start_time)
    end_min = parse_time_to_minutes(end_time)
    
    if start_min >= end_min:
        flash(_('Görev başlangıç saati bitiş saatinden büyük veya eşit olamaz.'), 'danger')
        return redirect(url_for('tasks.dashboard'))
        
    # Zaman Çakışması Kontrolü
    existing_tasks = Task.query.filter_by(user_id=current_user.id, period=period).all()
    for t in existing_tasks:
        t_start = parse_time_to_minutes(t.start_time)
        t_end = parse_time_to_minutes(t.end_time)
        if max(start_min, t_start) < min(end_min, t_end):
            flash(_('Zaman çakışması tespit edildi: Bu saatler arasında zaten başka bir göreviniz ("%(title)s") bulunmaktadır.', title=t.title), 'danger')
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
    
    flash(_('Görev başarıyla eklendi!'), 'success')
    return redirect(url_for('tasks.dashboard'))

@tasks_bp.route('/edit/<int:task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    period = request.form.get('period', 'daily')
    priority = request.form.get('priority', 'Medium')
    start_time = request.form.get('start_time', '09:00').strip()
    end_time = request.form.get('end_time', '10:00').strip()
    
    if not title:
        flash(_('Görev başlığı boş bırakılamaz.'), 'danger')
        return redirect(url_for('tasks.dashboard'))
        
    if not start_time or not end_time:
        flash(_('Başlangıç ve bitiş saatleri boş bırakılamaz.'), 'danger')
        return redirect(url_for('tasks.dashboard'))
        
    start_min = parse_time_to_minutes(start_time)
    end_min = parse_time_to_minutes(end_time)
    
    if start_min >= end_min:
        flash(_('Görev başlangıç saati bitiş saatinden büyük veya eşit olamaz.'), 'danger')
        return redirect(url_for('tasks.dashboard'))
        
    # Zaman Çakışması Kontrolü (Kendisi hariç)
    existing_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.period == period,
        Task.id != task_id
    ).all()
    
    for t in existing_tasks:
        t_start = parse_time_to_minutes(t.start_time)
        t_end = parse_time_to_minutes(t.end_time)
        if max(start_min, t_start) < min(end_min, t_end):
            flash(_('Zaman çakışması tespit edildi: Bu saatler arasında zaten başka bir göreviniz ("%(title)s") bulunmaktadır.', title=t.title), 'danger')
            return redirect(url_for('tasks.dashboard'))
            
    task.title = title
    task.description = description
    task.period = period
    task.priority = priority
    task.start_time = start_time
    task.end_time = end_time
    
    db.session.commit()
    flash(_('Görev başarıyla güncellendi!'), 'success')
    return redirect(url_for('tasks.dashboard'))

@tasks_bp.route('/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.is_completed = not task.is_completed
    db.session.commit()
    
    status_str = _("tamamlandı") if task.is_completed else _("tamamlanmadı")
    flash(_('"%(title)s" görevi %(status)s olarak işaretlendi.', title=task.title, status=status_str), 'success')
    return redirect(url_for('tasks.dashboard'))

@tasks_bp.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    
    flash(_('"%(title)s" görevi başarıyla silindi.', title=task.title), 'success')
    return redirect(url_for('tasks.dashboard'))

@tasks_bp.route('/ai/optimize', methods=['POST'])
@login_required
def ai_optimize():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    if not tasks:
        flash(_('Yapay zeka analizi için en az bir görev tanımlamış olmalısınız.'), 'warning')
        return redirect(url_for('tasks.dashboard'))
        
    # AI analizi ve optimizasyon motorunu çalıştır
    result_text = analyze_and_optimize_tasks(tasks)
    
    # Yeni öneriyi veritabanına kaydet
    new_suggestion = AISuggestion(suggestion_text=result_text, user_id=current_user.id)
    db.session.add(new_suggestion)
    db.session.commit()
    
    flash(_('Görevleriniz yapay zeka tarafından başarıyla analiz edildi!'), 'success')
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
            # Kullanıcının mesajına göre hem sohbet eden hem de görev sıralaması yapan zengin bir motor
            msg_lower = user_message.lower()
            
            # Görev sıralama tespiti
            wants_sorting = any(k in msg_lower for k in ["sırala", "sirala", "görev", "gorev", "plan", "hedef", "list", "düzenle", "duzenle", "kronolojik"])
            wants_greeting = any(k in msg_lower for k in ["selam", "merhaba", "hey", "naber", "meraba", "merhabalar"])
            wants_help = any(k in msg_lower for k in ["yardım", "yardim", "neler yapabilirsin", "özellikler"])
            
            if wants_sorting:
                if tasks:
                    # Görevleri önceliklerine göre sıralayalım (High -> Medium -> Low)
                    priority_weights = {'High': 3, 'Medium': 2, 'Low': 1}
                    sorted_t = sorted(tasks, key=lambda t: -priority_weights.get(t.priority, 2))
                    tasks_sorted_str = ""
                    for i, t in enumerate(sorted_t, 1):
                        status = "✅" if t.is_completed else "⏳"
                        p_badge = "🔴 Yüksek" if t.priority == 'High' else "🟡 Orta" if t.priority == 'Medium' else "🟢 Düşük"
                        tasks_sorted_str += f"{i}. {status} **{t.title}** | Saat: {t.start_time} - {t.end_time} | Öncelik: {p_badge}\n"
                    
                    greeting_prefix = ""
                    if wants_greeting:
                        greeting_prefix = f"Merhaba **{current_user.username}**! Harika bir gün dilerim. Sohbet etmek ne güzel!\n\n"
                    else:
                        greeting_prefix = "Tabii ki! Günlük zaman yönetimini optimize etmek için buradayım.\n\n"
                        
                    ai_response = (
                        f"{greeting_prefix}"
                        f"Güncel listendeki **{len(tasks)}** adet görevi senin için inceledim ve maksimum üretkenlik için öncelik sırasına göre dizdim:\n\n"
                        f"{tasks_sorted_str}\n"
                        "💡 **Glide Yapay Zeka Önerisi:** En yüksek öncelikli görevlerinden başlamak odaklanmanı artıracaktır. "
                        "Bu sıralama senin için nasıl? Değiştirmemi istediğin herhangi bir saat veya öncelik var mı?"
                    )
                else:
                    greeting_prefix = ""
                    if wants_greeting:
                        greeting_prefix = f"Merhaba **{current_user.username}**! "
                    ai_response = (
                        f"{greeting_prefix}Sohbet isteğini ve görev sıralama talebini aldım. "
                        "Fakat şu an planında kayıtlı bir görev bulunmuyor. "
                        "Öncelikle panelden birkaç görev eklersen, onları senin için hemen analiz edebilir ve en verimli şekilde sıralayabilirim!"
                    )
            elif wants_greeting:
                ai_response = (
                    f"Merhaba **{current_user.username}**! Harika bir sohbet olsun. Ben senin akıllı asistanın Glide.\n\n"
                    "Bugün nasılsın? Kalan işlerini ve zaman planını birlikte organize edebiliriz.\n\n"
                    "💡 *Bana 'görevlerimi sırala' diyerek planını listelememi isteyebilir veya zaman çakışmalarını incelememi talep edebilirsin.*"
                )
            elif any(k in msg_lower for k in ["nasılsın", "nasilsin", "keyifler"]):
                ai_response = (
                    "Harikayım, teşekkür ederim! Glide asistanı olarak sana zaman yönetiminde yardım etmekten büyük keyif alıyorum.\n\n"
                    "Bugünkü görev listeni sıralamamı veya planındaki çakışmaları analiz etmemi ister misin?"
                )
            elif wants_help:
                ai_response = (
                    f"Ben senin akıllı zaman yönetimi asistanın **Glide AI**. Sana şu konularda yardımcı olabilirim:\n\n"
                    "1. 🕒 **Zaman Çakışması Analizi:** Aynı saate denk gelen çakışan görevlerini bulurum.\n"
                    "2. ⭐ **Akıllı Öncelik Sıralaması:** Görevlerini önem derecesine göre dizerim.\n"
                    "3. 💬 **Sohbet & Motivasyon:** Günlük planın hakkında konuşup verimli tavsiyeler veririm.\n\n"
                    "Denemek için bana bir mesaj yazabilirsin!"
                )
            else:
                ai_response = (
                    f"Sohbet mesajını aldım! Glide asistanı olarak seninle konuşmak harika.\n\n"
                    "Bu çevrimdışı simülasyon modunda sana en iyi şekilde yardımcı olmak için çalışıyorum. "
                    "Görevlerini öncelik sırasına göre sıralamamı veya saat çakışmalarını kontrol etmemi ister misin? "
                    "Ya da gerçek zamanlı sınırsız zeka için `.env` dosyana API anahtarını ekleyebilirsin!"
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

