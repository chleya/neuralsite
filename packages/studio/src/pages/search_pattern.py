import os

os.chdir(r'C:\Users\Administrator\.openclaw\workspace\neuralsite\packages\studio\src\pages')
files = ['DashboardPage.tsx', 'DataImportPage.tsx', 'LoginPage.tsx', 'PhotoBrowser.tsx', 'ProjectDetailPage.tsx']

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        for i, line in enumerate(file, 1):
            if '}>' in line:
                print(f'{f}:{i}: {repr(line[-50:])}')
