import re
import os

def get_clean_msgid(lines):
    msgid_lines = []
    in_msgid = False
    for line in lines:
        if line.startswith('msgid'):
            in_msgid = True
            msgid_lines.append(line[5:].strip())
        elif line.startswith('msgstr'):
            in_msgid = False
        elif in_msgid:
            msgid_lines.append(line.strip())
    
    clean_parts = []
    for part in msgid_lines:
        if part.startswith('"') and part.endswith('"'):
            part = part[1:-1]
        part = part.replace('\\"', '"').replace('\\\\', '\\')
        clean_parts.append(part)
    return "".join(clean_parts)

def fix_po_file(filepath, translations):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = re.split(r'\n\n', content)
    updated_entries = []

    for entry in entries:
        entry_stripped = entry.strip()
        if not entry_stripped:
            updated_entries.append(entry)
            continue

        if 'msgid' in entry_stripped and not entry_stripped.startswith('#~'):
            lines = entry_stripped.split('\n')
            
            msgid_val = get_clean_msgid(lines)
            
            if msgid_val in translations:
                # Remove "#, fuzzy" line if it exists
                lines = [l for l in lines if 'fuzzy' not in l]
                
                # Re-locate msgstr after removing fuzzy
                msgstr_start_idx = -1
                for idx, line in enumerate(lines):
                    if line.startswith('msgstr'):
                        msgstr_start_idx = idx
                        break
                
                # Replace msgstr
                new_val = translations[msgid_val]
                new_val_escaped = new_val.replace('"', '\\"')
                
                lines = lines[:msgstr_start_idx]
                lines.append(f'msgstr "{new_val_escaped}"')
                
                entry_stripped = '\n'.join(lines)
        
        updated_entries.append(entry_stripped)

    new_content = '\n\n'.join(updated_entries)
    if not new_content.endswith('\n'):
        new_content += '\n'

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {os.path.basename(filepath)} successfully!")

if __name__ == "__main__":
    # Define translations for all languages
    all_translations = {
        'en': {
            'Yapay Zeka Analizi': 'AI Analysis',
            'Görev çakışmalarını tespit edin, önceliklerinize göre optimize edilmiş programınızı yapay zeka ile hemen oluşturun.': 'Detect task conflicts and immediately create your optimized schedule with artificial intelligence based on your priorities.',
            'Planı Optimize Et': 'Optimize Plan'
        },
        'es': {
            'Yapay Zeka Analizi': 'Análisis de IA',
            'Görev çakışmalarını tespit edin, önceliklerinize göre optimize edilmiş programınızı yapay zeka ile hemen oluşturun.': 'Detecte conflictos de tareas y genere de inmediato su horario optimizado con inteligencia artificial según sus prioridades.',
            'Planı Optimize Et': 'Optimizar plan',
            'kullanici_adi': 'usuario',
            ' Flask Uygulamasını Sun': 'Servir aplicación Flask',
            'Değişiklikleri Kaydet': 'Guardar cambios',
            'Şu an sunucuda bir Gemini API Anahtarı girilmediği için çevrimdışı simülasyon modu aktiftir. Asistana selam verebilir, planınızı sıralamasını veya çakışmaları bulmasını isteyebilirsiniz. Gerçek üretken yapay zekayı denemek için .env dosyanıza GEMINI_API_KEY ekleyebilirsiniz.': 'Dado que actualmente no hay una clave API de Gemini configurada en el servidor, el modo de simulación sin conexión está activo. Puede saludar al asistente, pedirle que organice su plan o busque conflictos. Para probar la IA generativa real, puede agregar GEMINI_API_KEY a su archivo .env.',
            'Yapay zeka tarafından üretilen zaman analizi ve verimlilik önerileri.': 'Análisis de tiempo y recomendaciones de eficiencia generados por IA.',
            'Tümü': 'Todo',
            '"%(query)s" için arama sonuçları': 'Resultados de búsqueda para "%(query)s"',
            'Aradığınız kriterlere uygun görev bulunamadı': 'No se encontraron tareas que coincidan con sus criterios de búsqueda.',
            'Lütfen arama teriminizi değiştirip tekrar deneyin.': 'Por favor, cambie su término de búsqueda e inténtelo de nuevo.',
            'Bir hata oluştu.': 'Ocurrió un error.',
            'Sunucuyla bağlantı kurulurken hata oluştu.': 'Ocurrió un error al conectar con el servidor.',
            'Zamanınızı': 'Rediseña tu tiempo con',
            'ile Yeniden Şekillendirin': ' '
        },
        'fr': {
            'Yapay Zeka Analizi': 'Analyse de l\'IA',
            'Görev çakışmalarını tespit edin, önceliklerinize göre optimize edilmiş programınızı yapay zeka ile hemen oluşturun.': 'Détectez les conflits de tâches et créez immédiatement votre planning optimisé grâce à l\'intelligence artificielle selon vos priorités.',
            'Planı Optimize Et': 'Optimiser le plan',
            'kullanici_adi': 'nom_d_utilisateur',
            ' Flask Uygulamasını Sun': "Servir l'application Flask",
            'Değişiklikleri Kaydet': 'Enregistrer les modifications',
            'Şu an sunucuda bir Gemini API Anahtarı girilmediği için çevrimdışı simülasyon modu aktiftir. Asistana selam verebilir, planınızı sıralamasını veya çakışmaları bulmasını isteyebilirsiniz. Gerçek üretken yapay zekayı denemek için .env dosyanıza GEMINI_API_KEY ekleyebilirsiniz.': "Comme aucune clé API Gemini n'est actuellement configurée sur le serveur, le mode de simulation hors ligne est actif. Vous pouvez saluer l'assistant, lui demander d'organiser votre plan ou de rechercher des conflits. Pour essayer la véritable IA générative, vous pouvez ajouter GEMINI_API_KEY à votre fichier .env.",
            'Yapay zeka tarafından üretilen zaman analizi ve verimlilik önerileri.': "Analyses de temps et recommandations d'efficacité générées par l'IA.",
            'Tümü': 'Tout',
            '"%(query)s" için arama sonuçları': 'Résultats de recherche pour "%(query)s"',
            'Aradığınız kriterlere uygun görev bulunamadı': "Aucune tâche correspondant à vos critères de recherche n'a été trouvée.",
            'Lütfen arama teriminizi değiştirip tekrar deneyin.': 'Veuillez modifier votre terme de recherche et réessayer.',
            'Bir hata oluştu.': 'Une erreur est survenue.',
            'Sunucuyla bağlantı kurulurken hata oluştu.': 'Une erreur est survenue lors de la connexion au serveur.',
            'Zamanınızı': 'Redessinez votre temps avec',
            'ile Yeniden Şekillendirin': ' '
        },
        'ar': {
            'Yapay Zeka Analizi': 'تحليل الذكاء الاصطناعي',
            'Görev çakışmalarını tespit edin, önceliklerinize göre optimize edilmiş programınızı yapay zeka ile hemen oluşturun.': 'اكتشف تعارضات المهام وأنشئ جدولك المحسن على الفور باستخدام الذكاء الاصطناعي بناءً على أولوياتك.',
            'Planı Optimize Et': 'تحسين الخطة'
        },
        'hi': {
            'Yapay Zeka Analizi': 'एआई विश्लेषण',
            'Görev çakışmalarını tespit edin, önceliklerinize göre optimize edilmiş programınızı yapay zeka ile hemen oluşturun.': 'अपनी प्राथमिकताओं के आधार पर कृत्रिम बुद्धिमत्ता के साथ अपने अनुकूलित कार्यक्रम को तुरंत बनाएं और समय के टकरावों का पता लगाएं।',
            'Planı Optimize Et': 'योजना को अनुकूलित करें'
        }
    }

    for lang, translations in all_translations.items():
        po_path = f"app/translations/{lang}/LC_MESSAGES/messages.po"
        if os.path.exists(po_path):
            fix_po_file(po_path, translations)
