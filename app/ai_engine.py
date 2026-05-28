import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime
from app.utils import parse_time_to_minutes

def get_gemini_bilingual_suggestion(tasks_data):
    """
    Kullanıcının görev verilerini alır, Gemini API'ye gönderir ve 
    bilingual (TR & EN) analiz ile akıllı sıralama içeren JSON yanıtı döner.
    """
    api_key = os.environ.get('AI_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("[AI ENGINE] API anahtarı bulunamadı. Lütfen .env dosyasında AI_API_KEY değişkenini tanımlayın.")
        return None

    model_name = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    system_prompt = (
        "You are 'Glide AI', an expert time management and productivity assistant. "
        "Your task is to analyze the user's task list, identify any time conflicts or overlaps, "
        "optimize the task order, and assign a priority order index (integer starting from 1) to each task.\n\n"
        "You must respond ONLY with a raw JSON object. Do NOT wrap your response in markdown code blocks like ```json ... ```, "
        "and do NOT include any introductory or explanatory text. The response must be a single, valid JSON object.\n\n"
        "The JSON response MUST follow this exact schema:\n"
        "{\n"
        "  \"ai_evaluation_tr\": \"Türkçe detaylı analiz, zaman çakışması tespiti ve Pomodoro/Eisenhower tabanlı 3 özelleştirilmiş verimlilik tavsiyesi (Markdown formatında).\",\n"
        "  \"ai_evaluation_en\": \"Detailed English analysis, time conflict detection, and 3 personalized productivity tips based on Pomodoro/Eisenhower methodologies (in Markdown format).\",\n"
        "  \"tasks_priority_order\": [\n"
        "    {\n"
        "      \"id\": <task_id_integer>,\n"
        "      \"priority_order\": <optimized_order_integer_starting_from_1>\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    prompt = f"{system_prompt}\n\nUser Task Data:\n{tasks_data}"

    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'), 
            headers=headers, 
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
            
            # Clean possible markdown wrapping if any (just in case)
            raw_text = raw_text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()
            
            parsed_json = json.loads(raw_text)
            return parsed_json
            
    except Exception as e:
        error_msg = str(e)
        if api_key in error_msg:
            error_msg = error_msg.replace(api_key, "MASKED_KEY")
        print(f"[GEMINI API HATA] Yapay zeka motoru çağrılamadı: {error_msg}")
        return None

def generate_local_report(tasks, lang):
    """
    Yerel (offline) raporlama motoru: Yapay zeka olmadığında iki dilde analiz raporu üretir.
    """
    conflicts = []
    for i in range(len(tasks)):
        for j in range(i + 1, len(tasks)):
            t1 = tasks[i]
            t2 = tasks[j]
            if t1.period == t2.period and check_overlap(t1, t2):
                conflicts.append((t1, t2))

    priority_weights = {'High': 3, 'Medium': 2, 'Low': 1}
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            t.period,
            -priority_weights.get(t.priority, 2),
            parse_time_to_minutes(t.start_time)
        )
    )

    report_templates = {
        'en': {
            'title': "### 🧠 AI Planning and Analysis Report\n",
            'evaluation': "🔍 **General Plan Evaluation:**",
            'summary': "You have a total of **{total_tasks}** defined tasks in your list. **{completed_count}** of them are completed.",
            'high': "- 🔥 **High Priority:** {high_count} tasks",
            'medium': "- ⚡ **Medium Priority:** {medium_count} tasks",
            'low': "- 🍃 **Low Priority:** {low_count} tasks\n",
            'overlap_title': "### ⚠️ Time Overlap Analysis",
            'overlap_intro': "Some tasks in your schedule overlap. You cannot be in two places at once! Please review the following conflicts:",
            'overlap_item': "- **Conflict Detected:** [{start1} - {end1}] *\"{title1}\"* conflicts with [{start2} - {end2}] *\"{title2}\"* (in {period} period).",
            'overlap_tip': "\n💡 *Tip: You can update the time slot of the lower-priority task or postpone it to another day.*\n",
            'no_overlap': "🎉 Excellent! No time conflicts detected in your schedule. Your tasks seem well-balanced throughout the day.\n",
            'opt_title': "### 📈 AI-Optimized Schedule",
            'opt_intro': "To maximize your productivity, your tasks have been reordered based on priority, peak energy hours, and periods:",
            'period_headers': {'daily': 'DAILY', 'weekly': 'WEEKLY', 'monthly': 'MONTHLY'},
            'period_header': "\n📅 **{period_name} TASKS:**",
            'task_item': "{idx}. {status_icon} {priority_icon} **[{start} - {end}]** {title} *(Priority: {priority})*",
            'tips_title': "### 💡 Personalized Productivity Tips",
            'tips_high_many': "- ⚠️ You have too many **High Priority** tasks in your daily list. To avoid losing focus, try focusing on at most 2-3 main tasks a day (80/20 rule).",
            'tips_high_good': "- 👍 The number of high-priority tasks is well-balanced. Try to complete these high-priority tasks during the first hours of the day when your energy is highest.",
            'tips_many_tasks': "- 🕒 Your workload seems slightly high. Divide big tasks into smaller sub-tasks to keep up your motivation.",
            'footer': "\n🚀 *Remember: Planning is half of success. AI optimized your plan, now it is time for action!*"
        },
        'es': {
            'title': "### 🧠 Informe de Planificación y Análisis de IA\n",
            'evaluation': "🔍 **Evaluación General del Plan:**",
            'summary': "Tiene un total de **{total_tasks}** tareas definidas en su lista. **{completed_count}** de ellas están completadas.",
            'high': "- 🔥 **Prioridad Alta:** {high_count} tareas",
            'medium': "- ⚡ **Prioridad Media:** {medium_count} tareas",
            'low': "- 🍃 **Prioridad Baja:** {low_count} tareas\n",
            'overlap_title': "### ⚠️ Análisis de Conflicto de Horarios",
            'overlap_intro': "Algunas tareas en su horario se superponen. ¡No puede estar en dos lugares a la vez! Revise los siguientes conflictos:",
            'overlap_item': "- **Conflicto Detectado:** [{start1} - {end1}] *\"{title1}\"* entra en conflicto con [{start2} - {end2}] *\"{title2}\"* (en el periodo {period}).",
            'overlap_tip': "\n💡 *Sugerencia: Puede actualizar el horario de la tarea de menor prioridad o posponerla para otro día.*\n",
            'no_overlap': "🎉 ¡Excelente! No se detectaron conflictos de horarios en su agenda. Sus tareas parecen estar bien distribuidas a lo largo del día.\n",
            'opt_title': "### 📈 Horario Optimizado por IA",
            'opt_intro': "Para maximizar su productividad, sus tareas se han reorganizado según la prioridad, las horas de máxima energía y los periodos:",
            'period_headers': {'daily': 'DIARIAS', 'weekly': 'SEMANALES', 'monthly': 'MENSUALES'},
            'period_header': "\n📅 **TAREAS {period_name}:**",
            'task_item': "{idx}. {status_icon} {priority_icon} **[{start} - {end}]** {title} *(Prioridad: {priority})*",
            'tips_title': "### 💡 Consejos de Productividad Personalizados",
            'tips_high_many': "- ⚠️ Tiene demasiadas tareas de **Prioridad Alta** en su lista diaria. Para evitar perder el enfoque, intente concentrarse en un máximo de 2 o 3 tareas principales al día (regla 80/20).",
            'tips_high_good': "- 👍 El número de tareas de alta prioridad está bien equilibrado. Intente completarlas durante las primeras horas del día, cuando su energía es mayor.",
            'tips_many_tasks': "- 🕒 Su carga de trabajo parece un poco alta. Divida las tareas grandes en subtareas más pequeñas para mantener su motivación.",
            'footer': "\n🚀 *Recuerde: Planificar es la mitad del éxito. ¡La IA ha optimizado su plan, ahora es momento de actuar!*"
        },
        'fr': {
            'title': "### 🧠 Rapport de Planification et d'Analyse de l'IA\n",
            'evaluation': "🔍 **Évaluation Générale du Plan:**",
            'summary': "Vous avez un total de **{total_tasks}** tâches définies dans votre liste. **{completed_count}** d'entre elles sont terminées.",
            'high': "- 🔥 **Priorité Haute:** {high_count} tâches",
            'medium': "- ⚡ **Priorité Moyenne:** {medium_count} tâches",
            'low': "- 🍃 **Priorité Basse:** {low_count} tâches\n",
            'overlap_title': "### ⚠️ Analyse des Conflits de Temps",
            'overlap_intro': "Certaines tâches de votre planning se chevauchent. Vous ne pouvez pas être à deux endroits à la fois ! Veuillez revoir les conflits suivants :",
            'overlap_item': "- **Conflit Détecté:** [{start1} - {end1}] *\"{title1}\"* est en conflit avec [{start2} - {end2}] *\"{title2}\"* (dans la période {period}).",
            'overlap_tip': "\n💡 *Suggéstion: Vous pouvez mettre à jour le créneau horaire de la tâche de moindre priorité ou la reporter à un autre jour.*\n",
            'no_overlap': "🎉 Excellent ! Aucun conflit horaire détecté dans votre planning. Vos tâches semblent bien équilibrées tout au long de la journée.\n",
            'opt_title': "### 📈 Planning Optimisé par l'IA",
            'opt_intro': "Pour maximiser votre productivité, vos tâches ont été réordonnées en fonction de la priorité, des heures de pointe d'énergie et des périodes :",
            'period_headers': {'daily': 'QUOTIDIENNES', 'weekly': 'HEBDOMADAIRES', 'monthly': 'MENSUELLES'},
            'period_header': "\n📅 **TÂCHES {period_name}:**",
            'task_item': "{idx}. {status_icon} {priority_icon} **[{start} - {end}]** {title} *(Priorité: {priority})*",
            'tips_title': "### 💡 Conseils de Productivité Personnalisés",
            'tips_high_many': "- ⚠️ Vous avez trop de tâches de **Priorité Haute** dans votre liste quotidienne. Pour éviter de perdre votre concentration, essayez de vous concentrer sur 2 ou 3 tâches principales par jour au maximum (règle des 80/20).",
            'tips_high_good': "- 👍 Le nombre de tâches hautement prioritaires est bien équilibré. Essayez de les accomplir pendant les premières heures de la journée, lorsque votre énergie est au plus haut.",
            'tips_many_tasks': "- 🕒 Votre charge de travail semble un peu élevée. Divisez les grandes tâches en sous-tâches plus petites pour maintenir votre motivation.",
            'footer': "\n🚀 *Rappelez-vous: Planifier est la moitié du succès. L'IA a optimisé votre planning, maintenant c'est l'heure d'agir !*"
        },
        'ar': {
            'title': "### 🧠 تقرير التخطيط والتحليل بالذكاء الاصطناعي\n",
            'evaluation': "🔍 **تقييم الخطة العام:**",
            'summary': "لديك إجمالي **{total_tasks}** مهام محددة في قائمتك. تم إكمال **{completed_count}** منها.",
            'high': "- 🔥 **أولوية عالية:** {high_count} مهام",
            'medium': "- ⚡ **أولوية متوسطة:** {medium_count} مهام",
            'low': "- 🍃 **أولوية منخفضة:** {low_count} مهام\n",
            'overlap_title': "### ⚠️ تحليل تداخل الأوقات",
            'overlap_intro': "بعض المهام في جدولك تتداخل. لا يمكنك أن تكون في مكانين في وقت واحد! يرجى مراجعة التعارضات التالية:",
            'overlap_item': "- **تم اكتشاف تعارض:** [{start1} - {end1}] *\"{title1}\"* يتعارض مع [{start2} - {end2}] *\"{title2}\"* (في الفترة {period}).",
            'overlap_tip': "\n💡 *نصيحة: يمكنك تحديث وقت المهمة ذات الأولوية المنخفضة أو تأجيلها إلى يوم آخر.*\n",
            'no_overlap': "🎉 ممتاز! لم يتم الكشف عن تعارضات في الأوقات في جدولك. تبدو مهامك متوازنة بشكل جيد طوال اليوم.\n",
            'opt_title': "### 📈 الجدول الزمني المحسن بالذكاء الاصطناعي",
            'opt_intro': "لتحقيق أقصى قدر من الإنتاجية، تم إعادة ترتيب مهامك بناءً على الأولوية وساعات الطاقة القصوى والفترات:",
            'period_headers': {'daily': 'اليومية', 'weekly': 'الأسبوعية', 'monthly': 'الشهرية'},
            'period_header': "\n📅 **مهام {period_name}:**",
            'task_item': "{idx}. {status_icon} {priority_icon} **[{start} - {end}]** {title} *(الأولوية: {priority})*",
            'tips_title': "### 💡 نصائح إنتاجية مخصصة",
            'tips_high_many': "- ⚠️ لديك الكثير من المهام ذات **الأولوية العالية** في قائمتك اليومية. لتجنب تشتت التركيز، حاول التركيز على مهمتين أو ثلاث مهام رئيسية كحد أقصى يوميًا (قاعدة 80/20).",
            'tips_high_good': "- 👍 عدد المهام ذات الأولوية العالية متوازن جيدًا. حاول إكمال هذه المهام ذات الأولوية العالية خلال الساعات الأولى من اليوم عندما تكون طاقتك في أعلى مستوياتها.",
            'tips_many_tasks': "- 🕒 يبدو أن عبء العمل لديك مرتفع قليلاً. قسّم المهام الكبيرة إلى مهام فرعية أصغر للحفاظ على حافزك.",
            'footer': "\n🚀 *تذكر: التخطيط هو نصف النجاح. لقد قام الذكاء الاصطناعي بتحسين خطتك، والآن حان وقت العمل!*"
        },
        'hi': {
            'title': "### 🧠 एआई नियोजन और विश्लेषण रिपोर्ट\n",
            'evaluation': "🔍 **सामान्य योजना मूल्यांकन:**",
            'summary': "आपकी सूची में कुल **{total_tasks}** परिभाषित कार्य हैं। उनमें से **{completed_count}** पूरे हो चुके हैं।",
            'high': "- 🔥 **उच्च प्राथमिकता:** {high_count} कार्य",
            'medium': "- ⚡ **मध्यम प्राथमिकता:** {medium_count} कार्य",
            'low': "- 🍃 **निम्न प्राथमिकता:** {low_count} कार्य\n",
            'overlap_title': "### ⚠️ समय ओवरलैप विश्लेषण",
            'overlap_intro': "आपकी योजना के कुछ कार्य ओवरलैप हो रहे हैं। आप एक समय में दो स्थानों पर नहीं हो सकते! कृपया निम्नलिखित टकरावों की समीक्षा करें:",
            'overlap_item': "- **टकराव का पता चला:** [{start1} - {end1}] *\"{title1}\"* का [{start2} - {end2}] *\"{title2}\"* ({period} अवधि में) के साथ टकराव है।",
            'overlap_tip': "\n💡 *सुझाव: आप कम प्राथमिकता वाले कार्य के समय को बदल सकते हैं या इसे दूसरे दिन के लिए टाल सकते हैं।*\n",
            'no_overlap': "🎉 उत्कृष्ट! आपकी योजना में कोई समय टकराव नहीं पाया गया। आपके कार्य पूरे दिन अच्छी तरह संतुलित लगते हैं।\n",
            'opt_title': "### 📈 एआई-अनुकूलित कार्यक्रम",
            'opt_intro': "आपकी उत्पादकता को अधिकतम करने के लिए, आपके कार्यों को प्राथमिकता, ऊर्जा के स्तर और अवधियों के आधार पर पुनर्व्यवस्थित किया गया है:",
            'period_headers': {'daily': 'दैनिक', 'weekly': 'साप्ताहिक', 'monthly': 'मासिक'},
            'period_header': "\n📅 **{period_name} कार्य:**",
            'task_item': "{idx}. {status_icon} {priority_icon} **[{start} - {end}]** {title} *(प्राथमिकता: {priority})*",
            'tips_title': "### 💡 व्यक्तिगत उत्पादकता युक्तियाँ",
            'tips_high_many': "- ⚠️ आपकी दैनिक सूची में बहुत अधिक **उच्च प्राथमिकता** वाले कार्य हैं। ध्यान भटकने से बचने के लिए, एक दिन में अधिकतम 2-3 मुख्य कार्यों पर ध्यान केंद्रित करने का प्रयास करें (80/20 नियम)।",
            'tips_high_good': "- 👍 उच्च प्राथमिकता वाले कार्यों की संख्या अच्छी तरह संतुलित है। दिन के पहले घंटों के दौरान इन उच्च प्राथमिकता वाले कार्यों को पूरा करने का प्रयास करें जब आपकी ऊर्जा का स्तर उच्चतम हो।",
            'tips_many_tasks': "- 🕒 आपका कार्यभार थोड़ा अधिक लग रहा है। अपनी प्रेरणा बनाए रखने के लिए बड़े कार्यों को छोटे उप-कार्यों में विभाजित करें।",
            'footer': "\n🚀 *याद रखें: योजना बनाना आधी सफलता है। एआई ने आपकी योजना को अनुकूलित किया है, अब कार्रवाई का समय है!*"
        },
        'tr': {
            'title': "### 🧠 Yapay Zeka Planlama ve Analiz Raporu\n",
            'evaluation': "🔍 **Genel Plan Değerlendirmesi:**",
            'summary': "Listenizde toplam **{total_tasks}** adet tanımlı görev bulunmaktadır. Bunların **{completed_count}** tanesi tamamlanmış durumdadır.",
            'high': "- 🔥 **Yüksek Öncelikli:** {high_count} görev",
            'medium': "- ⚡ **Orta Öncelikli:** {medium_count} görev",
            'low': "- 🍃 **Düşük Öncelikli:** {low_count} görev\n",
            'overlap_title': "### ⚠️ Zaman Çakışması Analizi",
            'overlap_intro': "Zamanlama planınızda bazı görevlerin çakıştığı tespit edildi. Aynı anda iki yerde olamazsınız! Lütfen aşağıdaki çakışmaları gözden geçirin:",
            'overlap_item': "- **Çakışma Tespit Edildi:** [{start1} - {end1}] saatlerindeki *\"{title1}\"* ile [{start2} - {end2}] saatlerindeki *\"{title2}\"* ({period} periyodunda) çakışıyor.",
            'overlap_tip': "\n💡 *Öneri: Çakışan görevlerden daha az öncelikli olanın saat aralığını güncelleyebilir veya başka bir güne erteleyebilirsiniz.*\n",
            'no_overlap': "🎉 Harika! Zaman çizelgenizde herhangi bir zaman çakışması tespit edilmedi. Görevleriniz gün içine dengeli dağıtılmış görünüyor.\n",
            'opt_title': "### 📈 Yapay Zeka Tarafından Optimize Edilmiş Sıralama",
            'opt_intro': "Üretkenliğinizi en üst düzeye çıkarmak için görevleriniz öncelik sırasına, enerjinizin en yüksek olacağı saatlere ve periyotlara göre yeniden dizilmiştir:",
            'period_headers': {'daily': 'GÜNLÜK', 'weekly': 'HAFTALIK', 'monthly': 'AYLIK'},
            'period_header': "\n📅 **{period_name} GÖREVLER:**",
            'task_item': "{idx}. {status_icon} {priority_icon} **[{start} - {end}]** {title} *(Öncelik: {priority})*",
            'tips_title': "### 💡 Kişiselleştirilmiş Verimlilik Tavsiyeleri",
            'tips_high_many': "- ⚠️ Günlük listenizde çok fazla **Yüksek Öncelikli** görev var. Odak noktanızın dağılmaması için bir günde en fazla 2-3 ana göreve odaklanmayı deneyin (80/20 kuralı).",
            'tips_high_good': "- 👍 Yüksek öncelikli görev sayınız oldukça dengeli. Günün en enerjik olduğunuz ilk saatlerinde bu yüksek öncelikli görevleri tamamlamaya çalışın.",
            'tips_many_tasks': "- 🕒 Yapılacak iş yükünüz biraz fazla görünüyor. Motivasyonunuzu kaybetmemek için büyük işleri küçük alt görevlere bölerek ilerleyin.",
            'footer': "\n🚀 *Unutmayın: Plan yapmak başarmanın yarısıdır. Yapay zeka planınızı optimize etti, şimdi harekete geçme zamanı!*"
        }
    }

    t = report_templates.get(lang, report_templates['tr'])
    report_lines = []
    
    report_lines.append(t['title'])
    
    # 1. Genel Durum Analizi
    total_tasks = len(tasks)
    high_count = sum(1 for t_item in tasks if t_item.priority == 'High')
    medium_count = sum(1 for t_item in tasks if t_item.priority == 'Medium')
    low_count = sum(1 for t_item in tasks if t_item.priority == 'Low')
    completed_count = sum(1 for t_item in tasks if t_item.is_completed)
    
    report_lines.append(t['evaluation'])
    report_lines.append(t['summary'].format(total_tasks=total_tasks, completed_count=completed_count))
    report_lines.append(t['high'].format(high_count=high_count))
    report_lines.append(t['medium'].format(medium_count=medium_count))
    report_lines.append(t['low'].format(low_count=low_count))
    
    # 2. Çakışma Analizi ve Uyarılar
    report_lines.append(t['overlap_title'])
    if conflicts:
        report_lines.append(t['overlap_intro'])
        for t1, t2 in conflicts:
            period_tr = t1.period
            if lang == 'es':
                period_tr = 'diario' if t1.period == 'daily' else 'semanal' if t1.period == 'weekly' else 'mensual'
            elif lang == 'fr':
                period_tr = 'quotidien' if t1.period == 'daily' else 'hebdomadaire' if t1.period == 'weekly' else 'mensuel'
            elif lang == 'ar':
                period_tr = 'يومي' if t1.period == 'daily' else 'أسبوعي' if t1.period == 'weekly' else 'شهri'
            elif lang == 'hi':
                period_tr = 'दैनिक' if t1.period == 'daily' else 'साप्ताहिक' if t1.period == 'weekly' else 'मासिक'
            elif lang == 'en':
                period_tr = 'daily' if t1.period == 'daily' else 'weekly' if t1.period == 'weekly' else 'monthly'
            
            report_lines.append(t['overlap_item'].format(
                start1=t1.start_time, end1=t1.end_time, title1=t1.title,
                start2=t2.start_time, end2=t2.end_time, title2=t2.title,
                period=period_tr
            ))
        report_lines.append(t['overlap_tip'])
    else:
        report_lines.append(t['no_overlap'])
        
    # 3. AI Akıllı Sıralama Önerisi
    report_lines.append(t['opt_title'])
    report_lines.append(t['opt_intro'])
    
    current_period = None
    for idx, task in enumerate(sorted_tasks, 1):
        if task.period != current_period:
            current_period = task.period
            period_name = t['period_headers'].get(current_period, current_period.upper())
            report_lines.append(t['period_header'].format(period_name=period_name))
        
        status_icon = "✅" if task.is_completed else "⏳"
        priority_icon = "🔴" if task.priority == 'High' else "🟡" if task.priority == 'Medium' else "🟢"
        
        p_name = task.priority
        if lang == 'es':
            p_name = 'Alta' if task.priority == 'High' else 'Media' if task.priority == 'Medium' else 'Baja'
        elif lang == 'fr':
            p_name = 'Haute' if task.priority == 'High' else 'Moyenne' if task.priority == 'Medium' else 'Basse'
        elif lang == 'ar':
            p_name = 'عالية' if task.priority == 'High' else 'متوسطة' if task.priority == 'Medium' else 'منخفضة'
        elif lang == 'hi':
            p_name = 'उच्च' if task.priority == 'High' else 'मध्यम' if task.priority == 'Medium' else 'निम्न'
        elif lang == 'tr':
            p_name = 'Yüksek' if task.priority == 'High' else 'Orta' if task.priority == 'Medium' else 'Düşük'
            
        report_lines.append(t['task_item'].format(
            idx=idx, status_icon=status_icon, priority_icon=priority_icon,
            start=task.start_time, end=task.end_time, title=task.title,
            priority=p_name
        ))
    report_lines.append("")
    
    # 4. Kişiselleştirilmiş Tavsiyeler (Dinamik)
    report_lines.append(t['tips_title'])
    if high_count > 3:
        report_lines.append(t['tips_high_many'])
    else:
        report_lines.append(t['tips_high_good'])
        
    if len(tasks) - completed_count > 6:
        report_lines.append(t['tips_many_tasks'])
        
    report_lines.append(t['footer'])
    
    return "\n".join(report_lines)

def get_gemini_chat_response(user_message, chat_history_list, tasks_data, lang='tr'):
    """
    Kullanıcının görevlerini, konuşma geçmişini ve son mesajını alarak
    Google Gemini API'den interaktif, planlama odaklı bir yanıt üretir.
    """
    api_key = os.environ.get('AI_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None
        
    model_name = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    history_str = ""
    for msg in chat_history_list:
        role = "Kullanıcı" if msg['sender'] == 'user' else "Asistan (Sen)"
        history_str += f"{role}: {msg['message']}\n"
        
    prompts = {
        'en': (
            "You are 'Glide', an intelligent time management and productivity assistant. "
            "You converse in a friendly, goal-oriented manner to help the user optimize their daily schedule.\n\n"
            f"User's Current Task List:\n{tasks_data}\n\n"
            f"Conversation History:\n{history_str}\n"
            f"User's Last Message: {user_message}\n\n"
            "Please analyze their plan, answer questions, or reorder tasks based on this message in English. "
            "If they request time, period, or priority updates, or want to shift tasks based on energy, "
            "provide an optimized schedule and ask for their approval.\n"
            "Always end your message with a guided, polite question to keep the conversation going. "
            "Use Markdown formatting. Prefer a conversational, natural English language."
        ),
        'es': (
            "Eres 'Glide', un asistente inteligente de gestión del tiempo y productividad. "
            "Conversas de manera amistosa y orientada a los objetivos para ayudar al usuario a optimizar su horario diario.\n\n"
            f"Lista de tareas actuales del usuario:\n{tasks_data}\n\n"
            f"Historial de conversación:\n{history_str}\n"
            f"Último mensaje del usuario: {user_message}\n\n"
            "Analiza su plan, responde preguntas o reorganiza tareas según este mensaje en español. "
            "Si solicitan actualizaciones de tiempo, periodo o prioridad, o desean cambiar tareas según la energía, "
            "proporciona un horario optimizado y solicita su aprobación.\n"
            "Termina siempre tu mensaje con una pregunta guiada y educada para mantener la conversación. "
            "Usa el formato Markdown. Prefiere un lenguaje de conversación natural en español."
        ),
        'fr': (
            "Vous êtes 'Glide', un assistant intelligent de gestion du temps et de productivité. "
            "Vous discutez de manière amicale et axée sur les objectifs pour aider l'utilisateur à optimiser son planning quotidien.\n\n"
            f"Liste des tâches actuelles de l'utilisateur :\n{tasks_data}\n\n"
            f"Historique de la conversation :\n{history_str}\n"
            f"Dernier message de l'utilisateur : {user_message}\n\n"
            "Veuillez analyser son plan, répondre aux questions ou réordonner les tâches en fonction de ce message en français. "
            "S'ils demandent des mises à jour de temps, de période ou de priorité, ou s'ils souhaitent déplacer des tâches en fonction de l'énergie, "
            "fournissez un planning optimisé et demandez leur approbation.\n"
            "Terminez toujours votre message par une question guidée et polie pour poursuivre la conversation. "
            "Utilisez le format Markdown. Préférez un langage conversationnel naturel en français."
        ),
        'ar': (
            "أنت 'Glide'، مساعد ذكي لإدارة الوقت والإنتاجية. "
            "تتحدث بطريقة ودية وموجهة نحو الأهداف لمساعدة المستخدم على تحسين جدوله اليومي.\n\n"
            f"قائمة المهام الحالية للمستخدم:\n{tasks_data}\n\n"
            f"سجل المحادثة:\n{history_str}\n"
            f"آخر رسالة للمستخدم: {user_message}\n\n"
            "يرجى تحليل خطتهم، أو الإجابة على الأسئلة، أو إعادة ترتيب المهام بناءً على هذه الرسالة باللغة العربية. "
            "إذا طلبوا تحديثات الوقت أو الفترة أو الأولوية، أو أرادوا تحويل المهام بناءً على الطاقة، "
            "فقدم جدولاً زمنياً محسناً واطلب موافقتهم.\n"
            "أنهِ رسالتك دائماً بسؤال موجه ومهذب لمواصلة المحادثة. "
            "استخدم تنسيق Markdown. يفضل استخدام لغة حوار طبيعية باللغة العربية."
        ),
        'hi': (
            "आप 'Glide' हैं, एक बुद्धिमान समय प्रबंधन और उत्पादकता सहायक। "
            "आप उपयोगकर्ता के दैनिक कार्यक्रम को अनुकूलित करने में मदद करने के लिए एक दोस्ताना, लक्ष्य-उन्मुख तरीके से बातचीत करते हैं।\n\n"
            f"उपयोगकर्ता की वर्तमान कार्य सूची:\n{tasks_data}\n\n"
            f"बातचीत का इतिहास:\n{history_str}\n"
            f"उपयोगकर्ता का अंतिम संदेश: {user_message}\n\n"
            "कृपया इस संदेश के आधार पर हिंदी में उनकी योजना का विश्लेषण करें, प्रश्नों के उत्तर दें या कार्यों को पुनर्व्यवस्थित करें। "
            "यदि वे समय, अवधि या प्राथमिकता अपडेट का अनुरोध करते हैं, या ऊर्जा के आधार पर कार्यों को स्थानांतरित करना चाहते हैं, "
            "तो एक अनुकूलित कार्यक्रम प्रदान करें और उनकी स्वीकृति मांगें।\n"
            "बातचीत को जारी रखने के लिए हमेशा अपने संदेश के अंत में एक निर्देशित, विनम्र प्रश्न पूछें। "
            "Markdown स्वरूपण का उपयोग करें। बातचीत की स्वाभाविक हिंदी भाषा को प्राथमिकता दें।"
        ),
        'tr': (
            "Sen akıllı zaman yönetimi ve verimlilik asistanı 'Glide'sın. "
            "Kullanıcı ile dost canlısı ve çözüm odaklı konuşarak onun günlük planını optimize etmesine yardımcı oluyorsun.\n\n"
            f"Kullanıcının Güncel Görev Listesi:\n{tasks_data}\n\n"
            f"Konuşma Geçmişiniz:\n{history_str}\n"
            f"Kullanıcının Son Mesajı: {user_message}\n\n"
            "Lütfen bu son mesaja göre kullanıcının planını analiz et, sorularını yanıtla veya görevlerini sırala. "
            "Eğer kullanıcı saat, periyot veya öncelik değişikliği gibi taleplerde bulunuyorsa veya enerjisine göre işleri kaydırmanı istiyorsa, "
            "ona optimize edilmiş bir zaman çizelgesi sun ve bunu onaylayıp onaylamadığını sor.\n"
            "Mesajının sonunda her zaman konuşmayı devam ettirecek yönlendirici ve nazik bir soru sor. "
            "Markdown biçimlendirmesi kullan. Çok uzun olmayan, akıcı ve doğal bir konuşma dili tercih et."
        )
    }
    
    prompt = prompts.get(lang, prompts['tr'])
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'), 
            headers=headers, 
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        error_msg = str(e)
        if api_key in error_msg:
            error_msg = error_msg.replace(api_key, "MASKED_KEY")
        print(f"[GEMINI CHAT HATA] Sohbet motoru çağrılamadı: {error_msg}")
        return None

def check_overlap(task1, task2):
    """İki görevin saat aralıklarının çakışıp çakışmadığını kontrol eder."""
    t1_start = parse_time_to_minutes(task1.start_time)
    t1_end = parse_time_to_minutes(task1.end_time)
    t2_start = parse_time_to_minutes(task2.start_time)
    t2_end = parse_time_to_minutes(task2.end_time)
    return max(t1_start, t2_start) < min(t1_end, t2_end)

def analyze_and_optimize_tasks(tasks):
    """
    Görev listesini analiz eder:
    - Zaman çakışmalarını bulur.
    - Öncelik ve süre analizi yapar.
    - Yapay zeka tavsiyeleri ve yeniden sıralanmış akıllı bir plan üretir (Bilingual Dict formatında).
    """
    if not tasks:
        return {
            "ai_evaluation_tr": "Henüz değerlendirilecek bir görev eklemediniz. Lütfen birkaç görev ekleyin.",
            "ai_evaluation_en": "You have not added any tasks to evaluate yet. Please add some tasks.",
            "tasks_priority_order": []
        }

    # 1. Görev verilerini metne dönüştür
    tasks_list = []
    for idx, t in enumerate(tasks, 1):
        status = 'Completed' if t.is_completed else 'Pending'
        tasks_list.append(
            f"Task {idx}: ID: {t.id}, Title: '{t.title}', Description: '{t.description}', "
            f"Period: '{t.period}', Priority: '{t.priority}', "
            f"Time Interval: '{t.start_time} - {t.end_time}', Status: '{status}'"
        )
    tasks_data = "\n".join(tasks_list)

    # 2. Gerçek Yapay Zeka (Gemini) Raporunu Dene (İki dilli şema ile)
    gemini_result = get_gemini_bilingual_suggestion(tasks_data)
    if gemini_result and isinstance(gemini_result, dict) and 'ai_evaluation_tr' in gemini_result and 'ai_evaluation_en' in gemini_result:
        return gemini_result

    # 3. FALLBACK: Kural Tabanlı Lokal Analiz Motoru (Çevrimdışı Mod - Çift dilli)
    report_tr = generate_local_report(tasks, 'tr')
    report_en = generate_local_report(tasks, 'en')

    priority_weights = {'High': 3, 'Medium': 2, 'Low': 1}
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            t.period,
            -priority_weights.get(t.priority, 2),
            parse_time_to_minutes(t.start_time)
        )
    )

    tasks_priority_order = []
    for idx, t in enumerate(sorted_tasks, 1):
        tasks_priority_order.append({
            "id": t.id,
            "priority_order": idx
        })

    return {
        "ai_evaluation_tr": report_tr,
        "ai_evaluation_en": report_en,
        "tasks_priority_order": tasks_priority_order
    }
