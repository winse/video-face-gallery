#!/usr/bin/env python3
"""
Fix all minified HTML files by adding newlines after JavaScript comments.
"""
import os
import re

def fix_html_file(filepath):
    """Fix a single HTML file by adding newlines after JS comments."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file has </script> tag
    if '</script>' not in content:
        return False
    
    # Split at </script> and fix the script section
    parts = content.split('</script>')
    
    fixed_parts = []
    for i, part in enumerate(parts[:-1]):
        script_match = re.search(r'<script>(.*)</script>', part, re.DOTALL)
        if script_match:
            script_content = script_match.group(1)
            # Add newline after each // comment
            script_content = re.sub(r'(//[^\n]*)\n', r'\1\n', script_content)
            # Ensure there's a newline after } and before // comments
            script_content = re.sub(r'(\}[^}])\n*(//)', r'\1\n\2', script_content)
            part = '<script>' + script_content + '</script>'
        fixed_parts.append(part)
    
    fixed_parts.append(parts[-1])  # Last part (after last </script>)
    
    new_content = '</script>'.join(fixed_parts)
    
    # Only write if changed
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    person_dir = 'person_details'
    fixed_count = 0
    
    for filename in os.listdir(person_dir):
        if filename.startswith('person_') and filename.endswith('.html'):
            filepath = os.path.join(person_dir, filename)
            if fix_html_file(filepath):
                fixed_count += 1
                print(f'Fixed: {filename}')
    
    print(f'\nTotal files fixed: {fixed_count}')

if __name__ == '__main__':
    main()
