import re
import os

def find_empty_translations(po_path):
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by double newlines to find PO blocks
    blocks = re.split(r'\n\n', content)
    empty_blocks = []
    
    for block in blocks:
        block = block.strip()
        if not block or block.startswith('#~'):
            continue
        
        # Check if it has msgid and msgstr ""
        lines = block.split('\n')
        msgid_lines = []
        msgstr_lines = []
        in_msgid = False
        in_msgstr = False
        fuzzy = any('fuzzy' in l for l in lines)
        
        for line in lines:
            line_str = line.strip()
            if line_str.startswith('msgid'):
                in_msgid = True
                in_msgstr = False
                msgid_lines.append(line_str[5:].strip())
            elif line_str.startswith('msgstr'):
                in_msgid = False
                in_msgstr = True
                msgstr_lines.append(line_str[6:].strip())
            elif line_str.startswith('"'):
                if in_msgid:
                    msgid_lines.append(line_str)
                elif in_msgstr:
                    msgstr_lines.append(line_str)
        
        msgid = "".join(msgid_lines).replace('"', '')
        msgstr = "".join(msgstr_lines).replace('"', '')
        
        if not msgid: # header
            continue
            
        if not msgstr or fuzzy:
            empty_blocks.append((msgid, "Fuzzy" if fuzzy else "Empty"))
            
    return empty_blocks

if __name__ == "__main__":
    for lang in ['tr', 'en', 'es', 'fr', 'hi', 'ar']:
        po_path = f"app/translations/{lang}/LC_MESSAGES/messages.po"
        if os.path.exists(po_path):
            issues = find_empty_translations(po_path)
            print(f"=== {lang} has {len(issues)} empty/fuzzy translations ===")
            for i, (msgid, kind) in enumerate(issues, 1):
                print(f"  {i}. [{kind}] msgid: '{msgid}'")
