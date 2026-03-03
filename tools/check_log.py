with open('processing.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for line in lines[-80:]:
        print(line.strip())
