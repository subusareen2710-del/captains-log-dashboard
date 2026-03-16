#!/usr/bin/env python3
"""
Pre-deploy validator — run this before every git push.
Catches the class of bugs that have broken the site (temporal dead zones,
missing IDs, broken function references, etc.)
Usage: python3 validate.py
"""

import re, sys, subprocess, tempfile, os

FILES = {
    'subanshu-dashboard.html': {
        'must_contain': [
            ('Firebase config',         'AIzaSy'),
            ('Lock screen HTML',        'id="lock-screen"'),
            ('Lock screen JS',          'async function submitLock()'),
            ('Theme toggle HTML',       'id="theme-toggle"'),
            ('Theme toggle JS',         'function toggleTheme()'),
            ('initTheme light default', "saved !== 'dark'"),
            ('Tab nav HTML',            'class="tab-nav"'),
            ('switchTab JS',            'function switchTab('),
            ('Firebase save fn',        'function save('),
            ('Firebase load fn',        'function load('),
            ('Today tab section',       'id="tab-today"'),
            ('Training tab section',    'id="tab-training"'),
            ('Portfolio tab section',   'id="tab-portfolio"'),
            ('Log tab section',         'id="tab-log"'),
        ],
        'must_not_contain': [
            ('Old initTheme (dark)',     "if (saved === 'light')"),
            ('Undefined reference',      'undefined is not'),
        ],
        'js_order_checks': [
            # (thing that must come BEFORE, thing that must come AFTER)
        ],
    },
    'training-hub.html': {
        'must_contain': [
            ('Firebase config',           'AIzaSy'),
            ('Theme toggle HTML',         'id="theme-toggle"'),
            ('Theme toggle JS',           'function toggleTheme()'),
            ('initTheme light default',   "saved !== 'dark'"),
            ('videoNotes declared',       'let videoNotes = {}'),
            ('renderAll called after',    'renderAll();'),
            ('renderVideoRow fn',         'function renderVideoRow('),
            ('toggleVideoNote JS',        'function toggleVideoNote('),
            ('saveVideoNote JS',          'function saveVideoNote('),
            ('renderAllNotes JS',         'function renderAllNotes()'),
            ('All-notes body HTML',       'id="all-notes-body"'),
            ('Per-video toggle btn HTML', 'class="vn-toggle-btn'),
            ('CURRICULUM defined',        'const CURRICULUM = {'),
        ],
        'must_not_contain': [
            ('Old initTheme (dark)',     "if (saved === 'light')"),
            ('Global notes-area HTML',   'id="notes-area"'),
        ],
        'js_order_checks': [
            # videoNotes must be declared BEFORE the renderAll() init call
            # Check by comparing character positions in the file
            ('videoNotes declaration BEFORE renderAll() init',
             'let videoNotes = {}',
             'renderAll();'),
        ],
    },
}

errors = []
warnings = []

for filename, rules in FILES.items():
    path = f'/tmp/captains-log-update/{filename}'
    try:
        content = open(path).read()
    except FileNotFoundError:
        errors.append(f'[{filename}] FILE NOT FOUND')
        continue

    print(f'\n── {filename} ({content.count(chr(10))} lines) ──')

    # Must-contain checks
    for name, needle in rules.get('must_contain', []):
        if needle not in content:
            errors.append(f'[{filename}] MISSING: {name}  (needle: {needle!r})')
            print(f'  ❌ MISSING: {name}')
        else:
            print(f'  ✅ {name}')

    # Must-not-contain checks
    for name, needle in rules.get('must_not_contain', []):
        if needle in content:
            errors.append(f'[{filename}] FORBIDDEN: {name}  (needle: {needle!r})')
            print(f'  ❌ FORBIDDEN found: {name}')
        else:
            print(f'  ✅ (not present) {name}')

    # Order checks — thing A must appear before thing B (by character position)
    for check_name, thing_a, thing_b in rules.get('js_order_checks', []):
        pos_a = content.find(thing_a)
        pos_b = content.rfind(thing_b)   # last occurrence (the init call, not internal ones)
        if pos_a == -1:
            errors.append(f'[{filename}] ORDER: cannot find "{thing_a}"')
            print(f'  ❌ ORDER: {check_name} — "{thing_a}" not found')
        elif pos_b == -1:
            errors.append(f'[{filename}] ORDER: cannot find "{thing_b}"')
            print(f'  ❌ ORDER: {check_name} — "{thing_b}" not found')
        elif pos_a > pos_b:
            errors.append(f'[{filename}] ORDER ERROR: {check_name} (A at {pos_a}, B at {pos_b})')
            print(f'  ❌ ORDER: {check_name}')
        else:
            print(f'  ✅ ORDER: {check_name}')

    # JS syntax check via Node (catches literal newlines in strings, etc.)
    script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    for i, block in enumerate(script_blocks):
        # Brace balance
        opens  = block.count('{')
        closes = block.count('}')
        if abs(opens - closes) > 5:
            warnings.append(f'[{filename}] Script block {i+1}: brace mismatch ({opens} open, {closes} close)')
            print(f'  ⚠️  Script block {i+1} brace imbalance: {opens}{{ vs {closes}}}')
        # Node syntax check
        try:
            with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as tf:
                tf.write(block)
                tf_name = tf.name
            result = subprocess.run(['node', '--check', tf_name],
                                    capture_output=True, text=True)
            os.unlink(tf_name)
            if result.returncode != 0:
                err_line = result.stderr.split('\n')[1] if '\n' in result.stderr else result.stderr
                errors.append(f'[{filename}] JS SYNTAX ERROR in script block {i+1}: {err_line.strip()}')
                print(f'  ❌ JS syntax error in script block {i+1}: {err_line.strip()}')
            else:
                print(f'  ✅ JS syntax OK (script block {i+1})')
        except FileNotFoundError:
            pass  # node not installed — skip silently

print('\n' + '─'*50)
if errors:
    print(f'\n🚨 {len(errors)} ERROR(S) — DO NOT DEPLOY:\n')
    for e in errors:
        print(f'   • {e}')
    sys.exit(1)
elif warnings:
    print(f'\n⚠️  {len(warnings)} warning(s) — review before deploying:')
    for w in warnings:
        print(f'   • {w}')
    print('\n✅ No blocking errors — OK to deploy (check warnings)')
    sys.exit(0)
else:
    print('\n✅ All checks passed — safe to deploy.')
    sys.exit(0)
