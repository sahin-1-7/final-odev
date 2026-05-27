import re
import os

def check_specific_msgids(filepath, msgids_to_check):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = re.split(r'\n\n', content)
    results = {}
    for entry in entries:
        entry_stripped = entry.strip()
        if not entry_stripped:
            continue
        if 'msgid' in entry_stripped:
            is_obsolete = entry_stripped.startswith('#~')
            if not is_obsolete:
                lines = entry_stripped.split('\n')
                
                # Get clean msgid
                msgid_lines = []
                in_msgid = False
                msgstr_line = ""
                for line in lines:
                    if line.startswith('msgid'):
                        in_msgid = True
                        msgid_lines.append(line[5:].strip())
                    elif line.startswith('msgstr'):
                        in_msgid = False
                        msgstr_line = line[7:].strip()
                    elif in_msgid:
                        msgid_lines.append(line.strip())
                
                clean_parts = []
                for part in msgid_lines:
                    if part.startswith('"') and part.endswith('"'):
                        part = part[1:-1]
                    part = part.replace('\\"', '"').replace('\\\\', '\\')
                    clean_parts.append(part)
                msgid_val = "".join(clean_parts)
                
                if msgid_val in msgids_to_check:
                    fuzzy = any('fuzzy' in l for l in lines)
                    results[msgid_val] = {
                        'translation': msgstr_line,
                        'fuzzy': fuzzy,
                        'raw': entry_stripped
                    }
    return results

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    msgids = [
        "Yapay Zeka Analizi",
        "Görev çakışmalarını tespit edin, önceliklerinize göre optimize edilmiş programınızı yapay zeka ile hemen oluşturun.",
        "Planı Optimize Et"
    ]
    for lang in ['ar', 'en', 'es', 'fr', 'hi', 'tr']:
        po_path = f"app/translations/{lang}/LC_MESSAGES/messages.po"
        if os.path.exists(po_path):
            print(f"=================== LANGUAGE: {lang} ===================")
            res = check_specific_msgids(po_path, msgids)
            for m in msgids:
                if m in res:
                    print(f"'{m}':")
                    print(f"  Translation: {res[m]['translation']}")
                    print(f"  Fuzzy: {res[m]['fuzzy']}")
                else:
                    print(f"'{m}': NOT FOUND IN PO FILE")
