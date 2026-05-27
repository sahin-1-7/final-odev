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
    es_translations = {
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
    }
    
    fr_translations = {
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
    }

    fix_po_file("app/translations/es/LC_MESSAGES/messages.po", es_translations)
    fix_po_file("app/translations/fr/LC_MESSAGES/messages.po", fr_translations)
