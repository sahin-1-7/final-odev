import os
import re
from datetime import datetime
from app.utils import parse_time_to_minutes

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
