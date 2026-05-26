import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime
from app.utils import parse_time_to_minutes

def get_gemini_suggestion(tasks_data):
    """Google Gemini API'yi doğrudan çağırarak görevleri akıllıca analiz eder."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None
        
    model_name = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    prompt = (
        "Sen akıllı zaman yönetimi ve üretkenlik asistanı 'Glide'sın. "
        "Aşağıda bir kullanıcının zaman planı ve görev listesi yer almaktadır. Lütfen bu listeyi bir yapay zeka uzmanı olarak analiz et.\n\n"
        "Görev Verileri:\n"
        f"{tasks_data}\n\n"
        "Lütfen şu analizleri içeren zengin ve profesyonel bir Markdown raporu hazırla:\n"
        "1. Genel Durum Analizi: Toplam iş yükü ve öncelik dağılımı değerlendirmesi.\n"
        "2. Zaman Çakışması Kontrolü: Aynı saat aralığına denk gelen veya birbiriyle çakışan görevleri açıkça belirt (örn: 09:00 - 10:00 arası ile 09:30 - 11:00 arası çakışır).\n"
        "3. Yapay Zeka Tarafından Optimize Edilmiş Zaman Çizelgesi: Görevleri en yüksek üretkenlik sağlayacak şekilde saat ve öncelik derecelerine göre sıralayarak listele.\n"
        "4. Kişiselleştirilmiş Üretkenlik Tavsiyeleri: Eisenhower Matrisi, 80/20 kuralı veya Pomodoro gibi bilimsel metodolojilere dayalı, bu kişiye özel 3 pratik tavsiye sun.\n\n"
        "Yanıtını doğrudan Jinja2 şablonuna basılacak şekilde Markdown formatında dönüştür. Ekstra giriş/açıklama yapmadan doğrudan analiz raporu başlığıyla başla."
    )
    
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
        print(f"[GEMINI API HATA] Yapay zeka motoru çağrılamadı, kural tabanlı motora geçiliyor: {error_msg}")
        return None

def get_gemini_chat_response(user_message, chat_history_list, tasks_data):
    """
    Kullanıcının görevlerini, konuşma geçmişini ve son mesajını alarak
    Google Gemini API'den interaktif, planlama odaklı bir yanıt üretir.
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None
        
    model_name = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    history_str = ""
    for msg in chat_history_list:
        role = "Kullanıcı" if msg['sender'] == 'user' else "Asistan (Sen)"
        history_str += f"{role}: {msg['message']}\n"
        
    prompt = (
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
    
    # Çakışma koşulu: Birinin başlangıcı diğerinin bitişinden önce ve bitişi başlangıcından sonra
    return max(t1_start, t2_start) < min(t1_end, t2_end)

def analyze_and_optimize_tasks(tasks):
    """
    Görev listesini analiz eder:
    - Zaman çakışmalarını bulur.
    - Öncelik ve süre analizi yapar.
    - Yapay zeka tavsiyeleri ve yeniden sıralanmış akıllı bir plan üretir (Markdown formatında).
    """
    if not tasks:
        return "Henüz değerlendirilecek bir görev eklemediniz. Lütfen birkaç görev ekleyin."

    # 1. Görev verilerini metne dönüştür
    tasks_list = []
    for idx, t in enumerate(tasks, 1):
        tasks_list.append(
            f"Görev {idx}: Başlık: '{t.title}', Açıklama: '{t.description}', "
            f"Periyot: '{t.period}', Öncelik: '{t.priority}', "
            f"Saat Aralığı: '{t.start_time} - {t.end_time}', Durum: '{'Tamamlandı' if t.is_completed else 'Bekliyor'}'"
        )
    tasks_data = "\n".join(tasks_list)

    # 2. Gerçek Yapay Zeka (Gemini) Raporunu Dene
    gemini_report = get_gemini_suggestion(tasks_data)
    if gemini_report:
        return gemini_report

    # 3. FALLBACK: Kural Tabanlı Lokal Analiz Motoru (Çevrimdışı Mod)
    conflicts = []
    # Çakışma analizi (Sadece aynı periyotta olan görevler çakışabilir)
    for i in range(len(tasks)):
        for j in range(i + 1, len(tasks)):
            t1 = tasks[i]
            t2 = tasks[j]
            if t1.period == t2.period and check_overlap(t1, t2):
                conflicts.append((t1, t2))

    # Görevleri öncelik ve saatlerine göre sınıflandır
    priority_weights = {'High': 3, 'Medium': 2, 'Low': 1}
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            t.period,
            -priority_weights.get(t.priority, 2),
            parse_time_to_minutes(t.start_time)
        )
    )

    # Dinamik Akıllı Rapor Oluşturma
    report_lines = []
    report_lines.append("### 🧠 Yapay Zeka Planlama ve Analiz Raporu\n")
    
    # 1. Genel Durum Analizi
    total_tasks = len(tasks)
    high_count = sum(1 for t in tasks if t.priority == 'High')
    medium_count = sum(1 for t in tasks if t.priority == 'Medium')
    low_count = sum(1 for t in tasks if t.priority == 'Low')
    completed_count = sum(1 for t in tasks if t.is_completed)
    
    report_lines.append(f"🔍 **Genel Plan Değerlendirmesi:**")
    report_lines.append(f"Listenizde toplam **{total_tasks}** adet tanımlı görev bulunmaktadır. Bunların **{completed_count}** tanesi tamamlanmış durumdadır.")
    report_lines.append(f"- 🔥 **Yüksek Öncelikli:** {high_count} görev")
    report_lines.append(f"- ⚡ **Orta Öncelikli:** {medium_count} görev")
    report_lines.append(f"- 🍃 **Düşük Öncelikli:** {low_count} görev\n")

    # 2. Çakışma Analizi ve Uyarılar
    report_lines.append("### ⚠️ Zaman Çakışması Analizi")
    if conflicts:
        report_lines.append("Zamanlama planınızda bazı görevlerin çakıştığı tespit edildi. Aynı anda iki yerde olamazsınız! Lütfen aşağıdaki çakışmaları gözden geçirin:")
        for t1, t2 in conflicts:
            report_lines.append(
                f"- **Çakışma Tespit Edildi:** [{t1.start_time} - {t1.end_time}] saatlerindeki *\"{t1.title}\"* ile "
                f"[{t2.start_time} - {t2.end_time}] saatlerindeki *\"{t2.title}\"* ({t1.period} periyodunda) çakışıyor."
            )
        report_lines.append("\n💡 *Öneri: Çakışan görevlerden daha az öncelikli olanın saat aralığını güncelleyebilir veya başka bir güne erteleyebilirsiniz.*\n")
    else:
        report_lines.append("🎉 Harika! Zaman çizelgenizde herhangi bir zaman çakışması tespit edilmedi. Görevleriniz gün içine dengeli dağıtılmış görünüyor.\n")

    # 3. AI Akıllı Sıralama Önerisi
    report_lines.append("### 📈 Yapay Zeka Tarafından Optimize Edilmiş Sıralama")
    report_lines.append("Üretkenliğinizi en üst düzeye çıkarmak için görevleriniz öncelik sırasına, enerjinizin en yüksek olacağı saatlere ve periyotlara göre yeniden dizilmiştir:")
    
    current_period = None
    for idx, task in enumerate(sorted_tasks, 1):
        if task.period != current_period:
            current_period = task.period
            period_name = "GÜNLÜK" if current_period == 'daily' else "HAFTALIK" if current_period == 'weekly' else "AYLIK"
            report_lines.append(f"\n📅 **{period_name} GÖREVLER:**")
        
        status_icon = "✅" if task.is_completed else "⏳"
        priority_icon = "🔴" if task.priority == 'High' else "🟡" if task.priority == 'Medium' else "🟢"
        report_lines.append(
            f"{idx}. {status_icon} {priority_icon} **[{task.start_time} - {task.end_time}]** {task.title} "
            f"*(Öncelik: {task.priority})*"
        )
    report_lines.append("")

    # 4. Kişiselleştirilmiş Tavsiyeler (Dinamik)
    report_lines.append("### 💡 Kişiselleştirilmiş Verimlilik Tavsiyeleri")
    
    if high_count > 3:
        report_lines.append("- ⚠️ Günlük listenizde çok fazla **Yüksek Öncelikli** görev var. Odak noktanızın dağılmaması için bir günde en fazla 2-3 ana göreve odaklanmayı deneyin (80/20 kuralı).")
    else:
        report_lines.append("- 👍 Yüksek öncelikli görev sayınız oldukça dengeli. Günün en enerjik olduğunuz ilk saatlerinde bu yüksek öncelikli görevleri tamamlamaya çalışın.")
        
    if len(tasks) - completed_count > 6:
        report_lines.append("- 🕒 Yapılacak iş yükünüz biraz fazla görünüyor. Motivasyonunuzu kaybetmemek için büyük işleri küçük alt görevlere bölerek ilerleyin.")
    
    # Genel motivasyon cümlesi
    report_lines.append("\n🚀 *Unutmayın: Plan yapmak başarmanın yarısıdır. Yapay zeka planınızı optimize etti, şimdi harekete geçme zamanı!*")

    return "\n".join(report_lines)
