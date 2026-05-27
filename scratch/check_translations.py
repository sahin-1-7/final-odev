import re
import os

def check_po_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = re.split(r'\n\n', content)
    empty_or_fuzzy = []
    for idx, entry in enumerate(entries):
        entry_stripped = entry.strip()
        if not entry_stripped:
            continue
        if 'msgid' in entry_stripped:
            is_obsolete = entry_stripped.startswith('#~')
            if not is_obsolete:
                lines = entry_stripped.split('\n')
                fuzzy = any('fuzzy' in l for l in lines)
                
                empty_msgstr = False
                for i, line in enumerate(lines):
                    if line.startswith('msgstr'):
                        if line == 'msgstr ""':
                            if i == len(lines) - 1:
                                empty_msgstr = True
                            elif not any(l.strip().startswith('"') for l in lines[i+1:]):
                                empty_msgstr = True
                
                if fuzzy or empty_msgstr:
                    # extract msgid
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
                    msgid = " ".join(msgid_lines).replace('"', '')
                    empty_or_fuzzy.append((msgid, "Fuzzy" if fuzzy else "Empty"))
    return empty_or_fuzzy

if __name__ == "__main__":
    import os
    for lang in ['es', 'fr']:
        po_path = f"app/translations/{lang}/LC_MESSAGES/messages.po"
        if os.path.exists(po_path):
            issues = check_po_file(po_path)
            print(f"=================== LANGUAGE: {lang} - {len(issues)} issues ===================")
            for idx, (msgid, issue_type) in enumerate(issues, 1):
                print(f"{idx}. [{issue_type}]: '{msgid}'")
