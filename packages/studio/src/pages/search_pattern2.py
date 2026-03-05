import os

os.chdir(r'C:\Users\Administrator\.openclaw\workspace\neuralsite\packages\studio\src\pages')
files = ['DashboardPage.tsx', 'DataImportPage.tsx', 'LoginPage.tsx', 'PhotoBrowser.tsx', 'ProjectDetailPage.tsx']

# Search for pattern where }> appears but should be just > (expression followed by > without closing tag)
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        # Check for }> pattern that is NOT followed by a closing tag
        import re
        # Find all }> followed by whitespace or end of tag
        matches = re.findall(r'\{[^}]+\}[a-zA-Z][^<]*>', content)
        for m in matches:
            print(f'{f}: {repr(m)}')
        
        # Also look for }> at end of line
        for i, line in enumerate(content.split('\n'), 1):
            if re.search(r'\}\s*>$', line) and '</' not in line:
                print(f'{f} line {i}: {repr(line[-40:])}')
