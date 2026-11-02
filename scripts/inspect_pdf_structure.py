import fitz

doc = fitz.open('report/Laporan_UTS_Komputasi_Paralel_Vicky_Maulana_Romadan_2322105049.pdf')
print(f'Total pages: {len(doc)}')

headings = [
    '1. PENDAHULUAN',
    '2. DESAIN IMPLEMENTASI',
    '3. HASIL PENGUJIAN',
    '4. ANALISIS KRITIS',
    '5. KESIMPULAN',
    '6. DAFTAR PUSTAKA'
]

for i, page in enumerate(doc):
    text = page.get_text()
    found = [h for h in headings if h in text]
    first = text.strip().split('\n')[0] if text.strip() else '(empty)'
    print(f'Page {i+1}: Headings={found} | First Line: {first[:60]}')
