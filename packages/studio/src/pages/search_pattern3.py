import os

os.chdir(r'C:\Users\Administrator\.openclaw\workspace\neuralsite\packages\studio\src\pages')

# Let where } me look for lines appears at the end (no closing tag)
files = ['DashboardPage.tsx', 'DataImportPage.tsx', 'LoginPage.tsx', 'PhotoBrowser.tsx', 'ProjectDetailPage.tsx']

for f in files:
    print(f"=== {f} ===")
    with open(f, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for i, line in enumerate(lines, 1):
            # Check for lines ending with }> without proper closing
            stripped = line.rstrip()
            if stripped.endswith('}>') or stripped.endswith('}> ') or stripped.endswith('}>'):
                print(f"  Line {i}: {repr(stripped[-30:])}")
            # Also check for }> followed by nothing (potential unclosed tag)
            if '}>' in line and '</' not in line.split('}>')[1] if '}>' in line else False:
                print(f"  Line {i} (potential): {repr(line[-40:])}")
