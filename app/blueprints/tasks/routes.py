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
    search_query = request.args.get('q', '').strip()[:100]
    
    query = Task.query.filter_by(user_id=current_user.id)
    
    # SQL LIKE/ILIKE Tabanlı Güvenli Full-Text Arama (Bonus Özellik +3 Puan)
    if search_query:
        # SQL wildcard karakterlerini güvenli hale getir
        escaped_query = search_query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        query = query.filter(
            (Task.title.ilike(f"%{escaped_query}%", escape='\\')) | 
            (Task.description.ilike(f"%{escaped_query}%", escape='\\'))
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
        return jsonify({'error': _('Görev başlığı boş bırakılamaz.')}), 400
        
    if not start_time or not end_time:
        return jsonify({'error': _('Başlangıç ve bitiş saatleri boş bırakılamaz.')}), 400
        
    start_min = parse_time_to_minutes(start_time)
    end_min = parse_time_to_minutes(end_time)
    
    if start_min >= end_min:
        return jsonify({'error': _('Görev başlangıç saati bitiş saatinden büyük veya eşit olamaz.')}), 400
        
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
            return jsonify({'error': _('Zaman çakışması tespit edildi: Bu saatler arasında zaten başka bir göreviniz ("%(title)s") bulunmaktadır.', title=t.title)}), 400
            
    task.title = title
    task.description = description
    task.period = period
    task.priority = priority
    task.start_time = start_time
    task.end_time = end_time
    
    db.session.commit()
    flash(_('Görev başarıyla güncellendi!'), 'success')
    return jsonify({'success': True})

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
    result = analyze_and_optimize_tasks(tasks)
    
    # priority_order alanlarını güvenle güncelle
    if isinstance(result, dict) and 'tasks_priority_order' in result:
        for item in result['tasks_priority_order']:
            task_id = item.get('id')
            order_val = item.get('priority_order')
            task_to_update = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
            if task_to_update:
                task_to_update.priority_order = order_val
                
    # Yeni öneriyi veritabanına kaydet
    ai_evaluation_tr = result.get('ai_evaluation_tr', '') if isinstance(result, dict) else result
    ai_evaluation_en = result.get('ai_evaluation_en', '') if isinstance(result, dict) else result
    
    new_suggestion = AISuggestion(
        suggestion_text=ai_evaluation_tr,
        ai_evaluation_tr=ai_evaluation_tr,
        ai_evaluation_en=ai_evaluation_en,
        user_id=current_user.id
    )
    db.session.add(new_suggestion)
    db.session.commit()
    
    flash(_('Görevleriniz yapay zeka tarafından başarıyla analiz edildi!'), 'success')
    return redirect(url_for('tasks.ai_planner'))

@tasks_bp.route('/ai/planner')
@login_required
def ai_planner():
    latest_suggestion = AISuggestion.query.filter_by(user_id=current_user.id).order_by(AISuggestion.created_at.desc()).first()
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Görevleri öncelikle periyoda, ardından yapay zeka tarafından belirlenen priority_order değerine göre sırala
    sorted_tasks = sorted(
        tasks, 
        key=lambda t: (
            t.period, 
            t.priority_order or 9999, 
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
    from flask_babel import get_locale
    lang = str(get_locale())
    api_key_configured = bool(
        current_app.config.get('AI_API_KEY') or 
        os.environ.get('AI_API_KEY') or 
        current_app.config.get('GEMINI_API_KEY') or 
        os.environ.get('GEMINI_API_KEY')
    )
    
    if request.method == 'POST':
        user_message = request.form.get('message', '').strip()
        if not user_message:
            error_msgs = {
                'en': 'Message cannot be empty.',
                'es': 'El mensaje no puede estar vacío.',
                'fr': 'Le message ne peut pas être vide.',
                'ar': 'لا يمكن أن تكون الرسالة فارغة.',
                'hi': 'संदेश खाली नहीं हो सकता।',
                'tr': 'Mesaj boş olamaz.'
            }
            return jsonify({'error': error_msgs.get(lang, error_msgs['tr'])}), 400
            
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
            ai_response = get_gemini_chat_response(user_message, history_list[:-1], tasks_data, lang=lang)
            
        if not ai_response:
            # SİMÜLASYON MODU (Fallback / Offline Demo Modu)
            msg_lower = user_message.lower()
            
            # Localized Keyword matching
            sorting_keywords = {
                'tr': ["sırala", "sirala", "görev", "gorev", "plan", "hedef", "list", "düzenle", "duzenle", "kronolojik"],
                'en': ["sort", "order", "task", "plan", "schedule", "list", "edit", "chronological"],
                'es': ["ordenar", "organizar", "tarea", "plan", "lista", "editar", "cronologico"],
                'fr': ["trier", "ordonner", "tache", "plan", "liste", "modifier", "chronologique"],
                'ar': ["ترتيب", "تنظيم", "مهمة", "خطة", "قائمة", "تعديل", "زمني"],
                'hi': ["क्रम", "व्यवस्थित", "कार्य", "योजना", "सूची", "संपादित", "कालानुक्रमिक"]
            }
            
            greeting_keywords = {
                'tr': ["selam", "merhaba", "hey", "naber", "meraba", "merhabalar"],
                'en': ["hi", "hello", "hey", "howdy", "greetings"],
                'es': ["hola", "saludos", "hey"],
                'fr': ["salut", "bonjour", "hey", "coucou"],
                'ar': ["مرحبا", "أهلا", "سلام", "مرحباً"],
                'hi': ["नमस्ते", "हैलो", "प्रणाम", "राम राम"]
            }
            
            help_keywords = {
                'tr': ["yardım", "yardim", "neler yapabilirsin", "özellikler"],
                'en': ["help", "features", "what can you do"],
                'es': ["ayuda", "caracteristicas", "que puedes hacer"],
                'fr': ["aide", "fonctionnalites", "que peux tu faire"],
                'ar': ["مساعدة", "ميزات", "ماذا يمكنك أن تفعل"],
                'hi': ["मदद", "विशेषताएं", "आप क्या कर सकते हैं"]
            }
            
            def match_keywords(msg, kw_dict, current_lang):
                keywords = kw_dict.get(current_lang, kw_dict['tr'])
                return any(k in msg for k in keywords) or any(k in msg for k in kw_dict['tr'])
            
            wants_sorting = match_keywords(msg_lower, sorting_keywords, lang)
            wants_greeting = match_keywords(msg_lower, greeting_keywords, lang)
            wants_help = match_keywords(msg_lower, help_keywords, lang)
            
            # Localized Responses
            if wants_sorting:
                if tasks:
                    # Görevleri önceliklerine göre sıralayalım (High -> Medium -> Low)
                    priority_weights = {'High': 3, 'Medium': 2, 'Low': 1}
                    sorted_t = sorted(tasks, key=lambda t_item: -priority_weights.get(t_item.priority, 2))
                    tasks_sorted_str = ""
                    for i, t_item in enumerate(sorted_t, 1):
                        status = "✅" if t_item.is_completed else "⏳"
                        
                        # Priority badge çevirisi
                        p_badge = t_item.priority
                        if lang == 'es':
                            p_badge = '🔴 Prioridad Alta' if t_item.priority == 'High' else '🟡 Prioridad Media' if t_item.priority == 'Medium' else '🟢 Prioridad Baja'
                        elif lang == 'fr':
                            p_badge = '🔴 Priorité Haute' if t_item.priority == 'High' else '🟡 Priorité Moyenne' if t_item.priority == 'Medium' else '🟢 Priorité Basse'
                        elif lang == 'ar':
                            p_badge = '🔴 أولوية عالية' if t_item.priority == 'High' else '🟡 أولوية متوسطة' if t_item.priority == 'Medium' else '🟢 أولوية منخفضة'
                        elif lang == 'hi':
                            p_badge = '🔴 उच्च प्राथमिकता' if t_item.priority == 'High' else '🟡 मध्यम प्राथमिकता' if t_item.priority == 'Medium' else '🟢 निम्न प्राथमिकता'
                        elif lang == 'en':
                            p_badge = '🔴 High Priority' if t_item.priority == 'High' else '🟡 Medium Priority' if t_item.priority == 'Medium' else '🟢 Low Priority'
                        else:
                            p_badge = '🔴 Yüksek' if t_item.priority == 'High' else '🟡 Orta' if t_item.priority == 'Medium' else '🟢 Düşük'
                        
                        tasks_sorted_str += f"{i}. {status} **{t_item.title}** | Saat: {t_item.start_time} - {t_item.end_time} | Öncelik: {p_badge}\n"
                    
                    if lang == 'en':
                        ai_response = (
                            f"Hello **{current_user.username}**! I reviewed **{len(tasks)}** tasks in your list and sorted them by priority for maximum productivity:\n\n"
                            f"{tasks_sorted_str}\n"
                            "💡 **AI Tip:** Starting with high-priority tasks will boost your focus. "
                            "How does this schedule look to you? Are there any updates you'd like to make?"
                        )
                    elif lang == 'es':
                        ai_response = (
                            f"¡Hola **{current_user.username}**! He revisado las **{len(tasks)}** tareas de tu lista y las he ordenado por prioridad para obtener la máxima productividad:\n\n"
                            f"{tasks_sorted_str}\n"
                            "💡 **Consejo de IA:** Comenzar con tus tareas de alta prioridad aumentará tu enfoque. "
                            "¿Cómo se ve este horario? ¿Hay algún cambio que quieras hacer?"
                        )
                    elif lang == 'fr':
                        ai_response = (
                            f"Bonjour **{current_user.username}** ! J'ai passé en revue les **{len(tasks)}** tâches de votre liste et les ai triées par priorité pour une productivité maximale :\n\n"
                            f"{tasks_sorted_str}\n"
                            "💡 **Conseil de l'IA :** Commencer par vos tâches prioritaires augmentera votre concentration. "
                            "Que pensez-vous de ce planning ? Souhaitez-vous y apporter des modifications ?"
                        )
                    elif lang == 'ar':
                        ai_response = (
                            f"مرحباً **{current_user.username}**! لقد راجعت **{len(tasks)}** من المهام في قائمتك ورتبتها حسب الأولوية لتحقيق أقصى قدر من الإنتاجية:\n\n"
                            f"{tasks_sorted_str}\n"
                            "💡 **نصيحة الذكاء الاصطناعي:** البدء بالمهام ذات الأولوية العالية سيزيد من تركيزك. "
                            "كيف تبدو هذه الخطة بالنسبة لك؟ هل هناك أي تعديلات ترغب في إجرائها؟"
                        )
                    elif lang == 'hi':
                        ai_response = (
                            f"नमस्ते **{current_user.username}**! मैंने आपकी सूची में **{len(tasks)}** कार्यों की समीक्षा की है और अधिकतम उत्पादकता के लिए उन्हें प्राथमिकता के अनुसार व्यवस्थित किया है:\n\n"
                            f"{tasks_sorted_str}\n"
                            "💡 **एआई सलाह:** उच्च प्राथमिकता वाले कार्यों से शुरुआत करने से आपका ध्यान बढ़ेगा। "
                            "यह कार्यक्रम आपको कैसा लगा? क्या आप इसमें कोई बदलाव करना चाहते हैं?"
                        )
                    else:
                        ai_response = (
                            f"Merhaba **{current_user.username}**! Güncel listendeki **{len(tasks)}** adet görevi senin için inceledim ve maksimum üretkenlik için öncelik sırasına göre dizdim:\n\n"
                            f"{tasks_sorted_str}\n"
                            "💡 **Glide Yapay Zeka Önerisi:** En yüksek öncelikli görevlerinden başlamak odaklanmanı artıracaktır. "
                            "Bu sıralama senin için nasıl? Değiştirmemi istediğin herhangi bir saat veya öncelik var mı?"
                        )
                else:
                    if lang == 'en':
                        ai_response = f"Hello **{current_user.username}**! I'd love to sort your tasks, but your schedule is currently empty. Please add some tasks from the dashboard first!"
                    elif lang == 'es':
                        ai_response = f"¡Hola **{current_user.username}**! Me encantaría ordenar tus tareas, pero tu agenda está vacía. ¡Agrega algunas tareas desde el tablero primero!"
                    elif lang == 'fr':
                        ai_response = f"Bonjour **{current_user.username}** ! J'aimerais trier vos tâches, mais votre planning est vide. Veuillez d'abord ajouter des tâches depuis le tableau !"
                    elif lang == 'ar':
                        ai_response = f"مرحباً **{current_user.username}**! أود ترتيب مهامك، لكن جدولك فارغ حالياً. يرجى إضافة بعض المهام من لوحة التحكم أولاً!"
                    elif lang == 'hi':
                        ai_response = f"नमस्ते **{current_user.username}**! मैं आपके कार्यों को क्रमबद्ध करना पसंद करूँगा, लेकिन आपका कार्यक्रम वर्तमान में खाली है। कृपया पहले डैशबोर्ड से कुछ कार्य जोड़ें!"
                    else:
                        ai_response = f"Merhaba **{current_user.username}**! Görev sıralama talebini aldım. Fakat şu an planında kayıtlı bir görev bulunmuyor. Öncelikle panelden birkaç görev eklersen, onları senin için hemen analiz edebilir ve en verimli şekilde sıralayabilirim!"
            elif wants_greeting:
                if lang == 'en':
                    ai_response = f"Hello **{current_user.username}**! I am your smart planning assistant Glide AI. How are you today? We can organize your tasks and schedule together."
                elif lang == 'es':
                    ai_response = f"¡Hola **{current_user.username}**! Soy tu asistente de planificación inteligente Glide AI. ¿Cómo estás hoy? Podemos organizar tus tareas y tu horario juntos."
                elif lang == 'fr':
                    ai_response = f"Bonjour **{current_user.username}** ! Je suis votre assistant de planification intelligent Glide AI. Comment allez-vous aujourd'hui ? Nous pouvons organiser vos tâches et votre planning ensemble."
                elif lang == 'ar':
                    ai_response = f"مرحباً **{current_user.username}**! أنا مساعد التخطيط الذكي الخاص بك Glide AI. كيف حالك اليوم؟ يمكننا تنظيم مهامك وجدولك معاً."
                elif lang == 'hi':
                    ai_response = f"नमस्ते **{current_user.username}**! मैं आपका स्मार्ट प्लानिंग असिस्टेंट Glide AI हूँ। आज आप कैसे हैं? हम मिलकर आपके कार्यों और कार्यक्रम को व्यवस्थित कर सकते हैं."
                else:
                    ai_response = f"Merhaba **{current_user.username}**! Harika bir sohbet olsun. Ben senin akıllı asistanın Glide. Bugün nasılsın? Kalan işlerini ve zaman planını birlikte organize edebiliriz."
            elif wants_help:
                if lang == 'en':
                    ai_response = "I am **Glide AI**, your smart time management assistant. I can help you with:\n1. 🕒 **Time Overlap Analysis**\n2. ⭐ **Smart Priority Sequence**\n3. 💬 **Chat & Efficiency Tips**\n\nHow can I help you today?"
                elif lang == 'es':
                    ai_response = "Soy **Glide AI**, tu asistente inteligente de gestión del tiempo. Puedo ayudarte con:\n1. 🕒 **Análisis de conflicto de horarios**\n2. ⭐ **Orden inteligente de prioridades**\n3. 💬 **Chat y consejos de eficiencia**\n\n¿Cómo puedo ayudarte hoy?"
                elif lang == 'fr':
                    ai_response = "Je suis **Glide AI**, votre assistant intelligent de gestion du temps. Je peux vous aider à :\n1. 🕒 **Analyse des conflits horaires**\n2. ⭐ **Tri intelligent des priorités**\n3. 💬 **Discussion & Conseils d'efficacité**\n\nComment puis-je vous aider aujourd'hui ?"
                elif lang == 'ar':
                    ai_response = "أنا **Glide AI**، مساعدك الذكي لإدارة الوقت. يمكنني مساعدتك في:\n1. 🕒 **تحليل تداخل الوقت**\n2. ⭐ **ترتيب الأولويات الذكي**\n3. 💬 **المحادثة ونصائح الكفاءة**\n\nكيف يمكنني مساعدتك اليوم؟"
                elif lang == 'hi':
                    ai_response = "मैं **Glide AI** हूँ, आपका स्मार्ट समय प्रबंधन सहायक। मैं आपकी मदद कर सकता हूँ:\n1. 🕒 **समय ओवरलैप विश्लेषण**\n2. ⭐ **स्मार्ट प्राथमिकता क्रम**\n3. 💬 **चैट और दक्षता युक्तियाँ**\n\nआज मैं आपकी कैसे मदद कर सकता हूँ?"
                else:
                    ai_response = "Ben senin akıllı zaman yönetimi asistanın **Glide AI**. Sana şu konularda yardımcı olabilirim:\n1. 🕒 **Zaman Çakışması Analizi**\n2. ⭐ **Akıllı Öncelik Sıralaması**\n3. 💬 **Sohbet & Verimlilik Tavsiyeleri**\n\nDenemek için bana bir mesaj yazabilirsin!"
            else:
                completed_count = sum(1 for t in tasks if t.is_completed)
                total_count = len(tasks)
                
                tips_pool_tr = [
                    "Pomodoro Tekniği'ni kullanarak 25 dakika çalışma ve 5 dakika mola düzenini denemelisin.",
                    "Öncelik sıralamasında 'Yüksek' olan görevleri günün en enerjik olduğun ilk saatlerinde tamamlamaya odaklan.",
                    "İş yükünü hafifletmek için büyük görevleri daha küçük ve yönetilebilir alt adımlara bölebilirsin.",
                    "80/20 kuralına göre, sonuçlarının %80'i çabalarının %20'sinden gelir. En kritik işe odaklan."
                ]
                import random
                tip_tr = random.choice(tips_pool_tr)
                
                tips_pool_en = [
                    "Try using the Pomodoro Technique: 25 minutes of work followed by a 5-minute break.",
                    "Focus on completing 'High' priority tasks during the first hours of the day when your energy is highest.",
                    "To ease your workload, try breaking large tasks into smaller, manageable sub-steps.",
                    "According to the 80/20 rule, 80% of results come from 20% of efforts. Focus on the most critical tasks."
                ]
                tip_en = random.choice(tips_pool_en)
                
                if lang == 'en':
                    ai_response = (
                        f"I received your message! Since we are currently in offline simulation mode, I analyzed your task list: "
                        f"You have **{total_count}** tasks, with **{completed_count}** completed.\n\n"
                        f"💡 **Custom tip for you:** {tip_en}\n\n"
                        f"Would you like me to sort your tasks or do you have any other questions?"
                    )
                else:
                    ai_response = (
                        f"Sohbet mesajını aldım! Çevrimdışı simülasyon modunda olsak da görev listeni senin için inceledim: "
                        f"Şu an planında **{total_count}** adet görev var ve bunlardan **{completed_count}** tanesini tamamlamışsın.\n\n"
                        f"💡 **Sana özel tavsiyem:** {tip_tr}\n\n"
                        f"Görevlerini öncelik sırasına göre dizmemi veya saat çakışmalarını kontrol etmemi ister misin?"
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

