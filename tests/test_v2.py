#!/usr/bin/env python
"""Test v2 features"""
import sys
import os
import subprocess
import traceback

print("=" * 60)
print("Testing v2 Features")
print("=" * 60)

# Test 1: Check regenerate_html.py can be imported
print("\n1. Testing regenerate_html.py import...")
try:
    # Just check syntax
    with open('regenerate_html.py', 'r', encoding='utf-8') as f:
        code = f.read()
    compile(code, 'regenerate_html.py', 'exec')
    print("   OK: Syntax check passed")
except SyntaxError as e:
    print(f"   ERROR: Syntax error at line {e.lineno}: {e.msg}")
    sys.exit(1)
except Exception as e:
    print(f"   ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Check tags.html exists
print("\n2. Testing tags.html...")
if os.path.exists('tags.html'):
    print("   OK: tags.html exists")
else:
    print("   ERROR: tags.html not found")

# Test 3: Check tags.json exists
print("\n3. Testing tags.json...")
if os.path.exists('tags.json'):
    with open('tags.json', 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"   OK: tags.json exists ({len(content)} bytes)")
else:
    print("   ERROR: tags.json not found")

# Test 4: Try running regenerate_html.py
print("\n4. Running regenerate_html.py...")
try:
    result = subprocess.run(
        [sys.executable, 'regenerate_html.py'],
        capture_output=True,
        text=True,
        timeout=180
    )
    print(f"   Return code: {result.returncode}")
    if result.stdout:
        for line in result.stdout.strip().split('\n'):
            print(f"   {line}")
    if result.stderr:
        print(f"   STDERR: {result.stderr[:500]}")
    if result.returncode != 0:
        print("   ERROR: regenerate_html.py failed")
except subprocess.TimeoutExpired:
    print("   ERROR: Timeout")
except Exception as e:
    print(f"   ERROR: {e}")
    traceback.print_exc()

# Test 5: Check generated files
print("\n5. Checking generated files...")
if os.path.exists('index.html'):
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    if 'data-theme' in content:
        print("   OK: index.html has dark theme support")
    else:
        print("   WARNING: index.html missing dark theme")
else:
    print("   ERROR: index.html not found")

if os.path.exists('person_details'):
    html_files = [f for f in os.listdir('person_details') if f.endswith('.html')]
    print(f"   OK: person_details has {len(html_files)} HTML files")
else:
    print("   ERROR: person_details directory not found")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
