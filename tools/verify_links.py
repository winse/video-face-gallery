import re
with open('person_details/person_0000.html', 'r', encoding='utf-8') as f:
    content = f.read()

matches = re.findall(r'href="([^"]+2026[^"]+\.mp4)"', content)
print("Video links found:")
for m in matches[:5]:
    print(f"  {m}")
