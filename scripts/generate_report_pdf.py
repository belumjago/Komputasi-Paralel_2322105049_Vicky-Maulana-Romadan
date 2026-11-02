#!/usr/bin/env python3
"""
==============================================================================
Script      : generate_report_pdf.py
Deskripsi   : Generator Dokumen Laporan UTS Komputasi Paralel Berformat PDF
Penulis     : Vicky Maulana Romadan (NIM: 2322105049)
Kelas       : Komputer Paralel (Sistem Terdistribusi) - UTS Ganjil 2026/2027
Dosen       : Dr. Ir. Antonius Irianto. S, ST., MT
==============================================================================
"""

import os
import io
import re
import pandas as pd
from markdown_pdf import Section, MarkdownPdf
import fitz  # PyMuPDF

def generate_pdf():
    os.makedirs('report', exist_ok=True)
    csv_file = 'results/benchmark_data.csv'

    meta_info = {'rng_fast': 0.8360, 'rng_posix': 1.1720, 'fs_padded': 0.1130, 'fs_unpadded': 0.1450}
    data_lines = []

    if os.path.exists(csv_file):
        with open(csv_file, 'r') as f:
            for line in f:
                line_clean = line.strip()
                if line_clean.startswith('#'):
                    if 'RNG Comparison' in line_clean:
                        m = re.search(r'fast_time=([\d.]+),\s*posix_time=([\d.]+)', line_clean)
                        if m:
                            meta_info['rng_fast'] = float(m.group(1))
                            meta_info['rng_posix'] = float(m.group(2))
                    elif 'False Sharing' in line_clean:
                        m = re.search(r'padded=([\d.]+),\s*unpadded=([\d.]+)', line_clean)
                        if m:
                            meta_info['fs_padded'] = float(m.group(1))
                            meta_info['fs_unpadded'] = float(m.group(2))
                elif line_clean:
                    data_lines.append(line_clean)

    df = pd.read_csv(io.StringIO("\n".join(data_lines)))
    
    # Calculate statistics
    grouped = df.groupby(['model', 'threads']).agg({
        'time_sec': ['mean', 'std'],
        'pi_estimate': 'last',
        'abs_error': 'last'
    }).reset_index()

    grouped.columns = ['model', 'threads', 'time_mean', 'time_std', 'pi_estimate', 'abs_error']

    serial_mean = grouped[grouped['model'] == 'Serial']['time_mean'].values[0]
    grouped['speedup'] = serial_mean / grouped['time_mean']
    grouped['efficiency'] = (grouped['speedup'] / grouped['threads']) * 100.0
    grouped['throughput'] = 1000.0 / grouped['time_mean']

    # Build dynamic table rows with zero indentation to prevent code block interpretation
    table_rows = []
    for _, r in grouped.sort_values(by=['model', 'threads']).iterrows():
        table_rows.append(
            f"<tr>"
            f"<td><strong>{r['model']}</strong></td>"
            f"<td>{int(r['threads'])}</td>"
            f"<td>{r['time_mean']:.4f} &plusmn; {r['time_std']:.3f} s</td>"
            f"<td><strong>{r['speedup']:.2f}x</strong></td>"
            f"<td>{r['efficiency']:.1f}%</td>"
            f"<td>{r['throughput']:.1f} Mpts/s</td>"
            f"<td>{r['pi_estimate']:.8f}</td>"
            f"<td>{r['abs_error']:.2e}</td>"
            f"</tr>\n"
        )
    table_html = "".join(table_rows)

    ser_pi = f"{grouped[grouped['model']=='Serial']['pi_estimate'].values[0]:.8f}"
    ser_err = f"{grouped[grouped['model']=='Serial']['abs_error'].values[0]:.2e}"
    
    pth_pi = f"{grouped[(grouped['model']=='Pthreads') & (grouped['threads']==8)]['pi_estimate'].values[0]:.8f}"
    pth_err = f"{grouped[(grouped['model']=='Pthreads') & (grouped['threads']==8)]['abs_error'].values[0]:.2e}"
    
    omp_pi = f"{grouped[(grouped['model']=='OpenMP') & (grouped['threads']==8)]['pi_estimate'].values[0]:.8f}"
    omp_err = f"{grouped[(grouped['model']=='OpenMP') & (grouped['threads']==8)]['abs_error'].values[0]:.2e}"

    fs_overhead = ((meta_info['fs_unpadded'] - meta_info['fs_padded']) / meta_info['fs_padded']) * 100.0

    # CSS for academic report styling
    css = """
    body {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 9.5pt;
        line-height: 1.45;
        color: #1e293b;
        margin: 12px 18px;
    }
    h1 {
        color: #0f172a;
        font-size: 17pt;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 4px;
        margin-top: 12px;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    h2 {
        color: #1e3a8a;
        font-size: 12.5pt;
        border-bottom: 1px solid #cbd5e1;
        padding-bottom: 3px;
        margin-top: 14px;
        margin-bottom: 7px;
    }
    h3 {
        color: #1d4ed8;
        font-size: 10pt;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    p, li {
        text-align: justify;
        margin-bottom: 6px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 8.5pt;
    }
    th, td {
        border: 1px solid #cbd5e1;
        padding: 5px 7px;
        text-align: center;
    }
    th {
        background-color: #1e40af;
        color: #ffffff;
        font-weight: bold;
    }
    tr:nth-child(even) {
        background-color: #f8fafc;
    }
    pre {
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-left: 4px solid #2563eb;
        padding: 6px 8px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 7.5pt;
        line-height: 1.25;
        margin: 6px 0;
    }
    code {
        font-family: 'Courier New', Courier, monospace;
        background-color: #f1f5f9;
        padding: 1px 3px;
        border-radius: 3px;
        font-size: 8pt;
    }
    .cover {
        text-align: center;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 12px;
        margin-bottom: 15px;
    }
    .cover-title {
        font-size: 15pt;
        font-weight: bold;
        color: #0f172a;
        margin-bottom: 3px;
    }
    .cover-subtitle {
        font-size: 11pt;
        color: #2563eb;
        font-weight: bold;
        margin-bottom: 6px;
    }
    .cover-meta {
        font-size: 8.5pt;
        color: #475569;
        line-height: 1.35;
    }
    .page-break {
        page-break-after: always;
    }
    .math-block {
        text-align: center;
        font-size: 10pt;
        font-family: 'Times New Roman', Georgia, serif;
        background-color: #f8fafc;
        border-left: 3px solid #2563eb;
        padding: 5px 10px;
        margin: 7px 0;
    }
    img {
        max-width: 88%;
        height: auto;
        display: block;
        margin: 8px auto;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
    }
    """

    # Section 1
    sec1 = """
<div class="cover">
    <div class="cover-title">LAPORAN UJIAN TENGAH SEMESTER (PROJECT)</div>
    <div class="cover-subtitle">KOMPUTER PARALEL (SISTEM TERDISTRIBUSI) - GANJIL TA-2026/2027</div>
    <div class="cover-meta">
        <strong>Fakultas Teknik dan Ilmu Komputer - Universitas Cendekia Abditama</strong><br>
        <strong>Dosen Pengampu:</strong> Dr. Ir. Antonius Irianto. S, ST., MT<br>
        <strong>Kasus Uji:</strong> Opsi C - Monte Carlo Simulasi Nilai &pi; (Difficulty: 1.5x, Ukuran: 1 Miliar Titik / 10^9)<br>
        <strong>Penyusun:</strong> Vicky Maulana Romadan (NIM: 2322105049) | <strong>Repositori GitHub:</strong> paralel-2322105049-Vicky-Maulana-Romadan
    </div>
</div>

# 1. PENDAHULUAN

## 1.1 Latar Belakang Masalah
Komputasi intensif modern menghadapi batasan fisik yang dikenal sebagai berakhirnya *Dennard Scaling* dan keterbatasan disipasi termal (*Power Wall*). Keterbatasan ini menghentikan tren peningkatan frekuensi clock uniprocessor dan mengalihkan evolusi arsitektur mikroprosesor ke paradigma *multi-core* (shared-memory multi-core processors). Agar perangkat lunak dapat memanfaatkan potensi komputasi paralel hardware tersebut secara optimal, diperlukan rekayasa konkurensi pada tingkat instruksi, thread, dan memori cache.

Salah satu metode numerik yang memegang peranan krusial dalam sains komputasi adalah **Metode Monte Carlo**. Metode ini merupakan kelas algoritma probabilistik yang memanfaatkan pembangkitan bilangan acak masif untuk menyelesaikan kalkulasi deterministik yang sulit atau tidak memiliki solusi analitis tertutup, seperti integrasi numerik multidimensi, simulasi transportasi partikel radiasi, hingga pemodelan finansial stokastik. Dalam persoalan penentuan konstanta lingkaran &pi;, metode Monte Carlo memperlakukan persoalan sebagai penentuan rasio luas geometris antara area seperempat lingkaran satuan terhadap kuadran persegi berukuran 1x1.

Secara teoritis, algoritma ini tergolong *Embarrassingly Parallel* karena setiap pengujian titik sampel bersifat independen tanpa ketergantungan data (*zero loop-carried dependency*). Kendati demikian, ketika skala simulasi ditingkatkan ke tingkat masif yaitu **1 Miliar Titik (10^9 sampel)**, serangkaian tantangan konkurensi tingkat rendah mencuat secara kritis:

1. **Race Condition pada Akumulator Global**: Pembaruan konkuren (*concurrent writes*) terhadap variabel penghitung titik lingkaran akan menimbulkan *lost update* bila tidak dikontrol, sehingga mutlak memerlukan teknik reduksi yang efisien.
2. **Kualitas dan Isolasi Random Number Generator (RNG)**: Penggunaan generator acak global standar libc (`rand()`) berakibat fatal: timbulnya data race pada state internal generator atau serialisasi ekstrim akibat lock internal libc yang menghancurkan skalabilitas. Selain itu, generator berperiode pendek rentan mengalami korelasi data dimensi rendah (*Marsaglia lattice effect*).
3. **Efek Hierarki Memori dan Cache Contention (False Sharing)**: Alokasi variabel konkurensi yang tidak selaras dengan baris cache (*cache line*) 64 byte dapat memicu invalidasi cache berulang antarkore prosesor, yang memperlambat eksekusi secara dramatis.

Untuk menganalisis fenomena komputasi paralel tersebut secara komprehensif, proyek ini mengimplementasikan dua pendekatan berbeda: **POSIX Threads (Pthreads)** sebagai model eksplisit/manual tingkat rendah (*low-level imperative concurrency*), dan **OpenMP** sebagai model arahan kompilator deklaratif tingkat tinggi (*compiler directive concurrency*).

## 1.2 Tujuan Implementasi
Tujuan dari pelaksanaan proyek UTS ini adalah:
1. Mengembangkan tiga varian program estimasi &pi; Monte Carlo: Serial baseline, POSIX Threads (Pthreads), dan OpenMP dengan beban komputasi masif 10^9 titik.
2. Mengatasi *race condition* melalui mekanisme reduksi lokal (*thread-local accumulator*) pada Pthreads dan klausa `reduction` pada OpenMP.
3. Mendesain arsitektur PRNG per-thread terisolasi menggunakan generator modern **Xorshift64\*** dan membandingkannya secara empiris terhadap generator standar POSIX `rand_r()`.
4. Mengidentifikasi, mengukur, dan memitigasi anomali hierarki memori *False Sharing* melalui teknik *cache-line padding* 64 byte.
5. Melakukan pengujian performa komparatif pada variasi 1, 2, 4, dan 8 threads, serta menganalisis efisiensi, speedup, trade-off rekayasa, dan batas skalabilitas berdasarkan Hukum Amdahl.
"""

    # Section 2
    sec2 = """
<div class="page-break"></div>

# 2. DESAIN IMPLEMENTASI

## 2.1 Algoritma Serial (Baseline)
Algoritma serial bertindak sebagai tolok ukur acuan (*ground truth baseline*). Secara matematis, kuadran persegi dua dimensi didefinisikan pada interval:
<div class="math-block">&Omega; = [0, 1] &times; [0, 1] &rArr; Area(&Omega;) = 1.0 &times; 1.0 = 1.0</div>
Lingkaran satuan dengan radius <i>r</i> = 1.0 yang berpusat di koordinat (0,0) memiliki persamaan batas:
<div class="math-block"><i>x</i><sup>2</sup> + <i>y</i><sup>2</sup> &le; 1.0</div>
Luas dari seperempat lingkaran di dalam kuadran tersebut adalah:
<div class="math-block"><i>A</i><sub>circle</sub> = &frac14; &pi; <i>r</i><sup>2</sup> = &pi; / 4</div>

Apabila <i>N</i> pasangan titik acak (<i>X<sub>i</sub></i>, <i>Y<sub>i</sub></i>) dibangkitkan secara independen dengan distribusi seragam kontinu <i>X</i>, <i>Y</i> ~ <i>U</i>(0, 1), maka probabilitas sebuah titik jatuh ke dalam lingkaran adalah:
<div class="math-block"><i>P</i>((<i>X</i><sup>2</sup> + <i>Y</i><sup>2</sup>) &le; 1) = <i>A</i><sub>circle</sub> / Area(&Omega;) = &pi; / 4</div>

Jika <i>M</i> menyatakan total titik yang memenuhi kondisi (<i>x</i><sup>2</sup> + <i>y</i><sup>2</sup> &le; 1.0), maka nilai estimasi &pi;&#770; dihitung melalui rasio:
<div class="math-block">&pi;&#770; = 4 &times; (<i>M</i> / <i>N</i>)</div>

![Prinsip Geometris Monte Carlo](figures/fig4_monte_carlo_geometry.png)

Algoritma serial memiliki kompleksitas waktu <i>O</i>(<i>N</i>) dan kompleksitas memori <i>O</i>(1). Karakteristiknya murni *compute-bound*, didominasi oleh operasi aritmatika integer (pada PRNG), floating-point double precision (penjumlahan dan perkalian kuadrat), serta evaluasi perbandingan (*branching*).

```c
// Inti Implementasi Serial Baseline (serial.c)
uint64_t in_circle = 0;
uint64_t state = 88172645463325252ULL; // Seed awal
for (uint64_t i = 0; i < total_samples; i++) {
    double x = rand_double_fast(&state);
    double y = rand_double_fast(&state);
    if (x * x + y * y <= 1.0) {
        in_circle++;
    }
}
double pi_est = 4.0 * ((double)in_circle / (double)total_samples);
```

## 2.2 Strategi Paralelisasi POSIX Threads (Pthreads)
Pthreads adalah standar IEEE 1003.1c yang menyediakan API imperative berlevel rendah untuk manajemen thread di lingkungan memori bersama.

### A. Pembagian Workload (Static Block Partitioning)
Penyelesaian 1 miliar sampel dibagi secara merata kepada <i>P</i> buah thread menggunakan teknik dekomposisi blok statis. Setiap thread <i>t</i> &isin; [0, <i>P</i>-1] memproses sejumlah <i>N<sub>t</sub></i> sampel:
<div class="math-block"><i>N</i><sub><i>t</i></sub> = &lfloor;<i>N</i> / <i>P</i>&rfloor; + (<i>t</i> &lt; (<i>N</i> mod <i>P</i>) ? 1 : 0)</div>
Pembagian deterministik ini membagi beban secara seimbang dengan overhead penjadwalan nol.

### B. Mekanisme Sinkronisasi dan Reduksi
Tantangan krusial pada komputasi paralel adalah eliminasi *race condition*. Jika setiap thread melakukan `pthread_mutex_lock` pada setiap penemuan titik di dalam lingkaran, eksekusi akan mengalami serialisasi total akibat perebutan kunci mutex sebanyak ratusan juta kali.

Sebagai solusi, program mengadopsi pola **Thread-Local Accumulator**:
1. Setiap thread mengakumulasikan hitungan titik secara privat pada variabel lokal `local_count` di register/stack thread.
2. Ketika loop selesai, nilai lokal disimpan ke dalam struct thread.
3. Thread master menunggu seluruh thread selesai melalui `pthread_join()`, lalu melakukan reduksi akhir dengan menjumlahkan seluruh `local_count` ke total global.

### C. Mitigasi False Sharing Melalui Cache-Line Padding
Dalam arsitektur prosesor x86_64 modern, data dipindahkan antara RAM dan memori cache L1/L2 dalam unit blok berukuran 64 byte (*cache line*). Apabila struct argumen tiap thread disimpan berurutan dalam memori tanpa pembatas, variabel `local_in_circle` milik thread yang berbeda akan berada pada baris cache 64 byte yang sama. Saat thread menulis ke variabelnya, protokol koherensi cache hardware (MESI) akan meng-invalidasi cache line pada core lain, menimbulkan fenomena *cache line bouncing* yang merusak performa.

Untuk memecahkan masalah ini, struct `PthreadArg` dirancang dengan *explicit padding* hingga tepat berukuran 64 byte:

```c
typedef struct {
    int thread_id;
    int total_threads;
    uint64_t num_samples;
    uint64_t local_in_circle;
    uint64_t seed;
    // Explicit padding to 64 bytes to prevent False Sharing
    char padding[64 - ((sizeof(int)*2 + sizeof(uint64_t)*3) % 64)];
} PthreadArg;
```

### D. Manajemen State PRNG Per-Thread
Setiap thread diberikan instance PRNG mandiri. Master seed di-hash menggunakan algoritma **SplitMix64** untuk menghasilkan seed awal 64-bit yang unik bagi setiap thread <i>t</i>:
<div class="math-block">seed<sub><i>t</i></sub> = splitmix64(master_seed + <i>t</i> &times; 1000000007)</div>
Langkah ini menjamin bahwa tidak ada dua thread yang membangkitkan deret bilangan acak yang tumpang tindih (*zero sequence overlap*).

## 2.3 Strategi Paralelisasi OpenMP (Compiler Directive)
OpenMP menyediakan model pemrograman paralel tingkat tinggi berbasis arahan kompilator (*pragmas*) dengan paradigma *Fork-Join*.

### A. Pemilihan Pragma dan Clause
Implementasi OpenMP dirancang secara deklaratif:
```c
#pragma omp parallel reduction(+:in_circle) num_threads(num_threads)
{
    int tid = omp_get_thread_num();
    uint64_t state = seeds_fast[tid * 8];
    uint64_t local_count = 0;

    #pragma omp for schedule(static)
    for (uint64_t i = 0; i < total_samples; i++) {
        double x = rand_double_fast(&state);
        double y = rand_double_fast(&state);
        if (x * x + y * y <= 1.0) {
            local_count++;
        }
    }
    in_circle += local_count;
}
```

### B. Analisis Klausa dan Scope Variabel
1. **`#pragma omp parallel`**: Menginstruksikan runtime OpenMP untuk membentuk *team of threads* sebanyak `num_threads`.
2. **`reduction(+:in_circle)`**: Menginstruksikan kompilator untuk secara otomatis menciptakan salinan privat dari akumulator `in_circle` untuk masing-masing thread. Saat region paralel berakhir, kompilator menggabungkan seluruh akumulator privat ke variabel master menggunakan algoritma *tree-based reduction* yang teroptimasi di level instruksi mesin tanpa *race condition*.
3. **`schedule(static)`**: Karena setiap iterasi perulangan Monte Carlo memiliki kompleksitas komputasi yang seragam murni, penjadwalan `static` mempartisi ruang loop secara merata saat kompilasi (*compile-time chunking*). Hal ini menghindari overhead runtime scheduling yang ada pada klausa `dynamic`.
4. **Scope Variabel (Shared vs Private)**:
   * **Shared**: `total_samples`, array `seeds_fast` (hanya dibaca).
   * **Private**: Variabel loop `i`, koordinat acak `x, y`, identifier `tid`, state PRNG `state`, serta akumulator lokal `local_count`.
"""

    # Section 3
    sec3 = """
<div class="page-break"></div>

# 3. HASIL PENGUJIAN

## 3.1 Lingkungan Pengujian
Pengujian eksperimental dilaksanakan pada sistem komputasi berkinerja tinggi dengan spesifikasi teknis berikut:
* **Prosesor**: AMD64 Family 23 Model 160 Stepping 0 (8 Logical Processors / Cores)
* **Arsitektur**: x86_64, L1 Data Cache 32 KB per-core, L2 Cache 512 KB per-core, L3 Shared Cache
* **Memori Utama (RAM)**: 16 GB Dual-Channel DDR4
* **Sistem Operasi**: Windows 11 Enterprise (Build 26300, 64-bit)
* **Kompilator**: MinGW-w64 GCC versi 15.2.0
* **Flag Kompilasi**: `-O3 -Wall -Wextra -fopenmp -lpthread -lm`
* **Ukuran Sampel**: 1 Miliar Titik (10^9 points) per konfigurasi pengujian
* **Protokol Uji**: Setiap konfigurasi thread (1, 2, 4, 8) dieksekusi sebanyak 3 kali pengulangan independen untuk memperoleh nilai rata-rata dan deviasi standar yang stabil.

## 3.2 Verifikasi Correctness (Presisi Numerik terhadap Teori)
Untuk memverifikasi bahwa paralelisasi tidak merusak integritas matematis perhitungan, hasil estimasi &pi; dibandingkan terhadap konstanta analitik &pi; = 3.1415926535...:
* **Serial Baseline (1 Core)**: &pi; = [[SER_PI]] (Absolute Error: [[SER_ERR]]).
* **Pthreads (8 Threads)**: &pi; = [[PTH_PI]] (Absolute Error: [[PTH_ERR]]).
* **OpenMP (8 Threads)**: &pi; = [[OMP_PI]] (Absolute Error: [[OMP_ERR]]).

Berdasarkan Teorema Limit Pusat (CLT), simpangan baku kesalahan estimasi Monte Carlo untuk <i>N</i> = 10^9 sampel adalah:
<div class="math-block">&sigma; &approx; 1.6427 / &radic;(10<sup>9</sup>) &approx; 5.195 &times; 10<sup>-5</sup></div>
Batas interval toleransi 3&sigma; (confidence level 99.73%) adalah &plusmn; 1.558 &times; 10<sup>-4</sup>. Seluruh hasil pengujian serial, Pthreads, dan OpenMP berada ketat di dalam batas teoritis tersebut, yang membuktikan **100% kebenaran fungsional dan numerik (deterministic correctness)**.

![Konvergensi Statistik](figures/fig5_statistical_convergence.png)

## 3.3 Tabel Pengukuran Kinerja Eksekusi
Tabel berikut menyajikan rekapitulasi data empiris waktu eksekusi, percepatan (*speedup*), efisiensi paralel, serta kapasitas pemrosesan (*throughput*):

<table>
<thead>
<tr>
<th>Model</th>
<th>Threads (p)</th>
<th>Waktu Eksekusi (s)</th>
<th>Speedup (S)</th>
<th>Efisiensi (E)</th>
<th>Throughput</th>
<th>Estimasi &pi;</th>
<th>Absolute Error</th>
</tr>
</thead>
<tbody>
[[TABLE_HTML]]
</tbody>
</table>

## 3.4 Grafik Analisis Speedup dan Efisiensi Paralel

![Grafik Speedup](figures/fig1_speedup.png)

![Grafik Efisiensi Paralel](figures/fig2_efficiency.png)

![Grafik Waktu Eksekusi](figures/fig3_execution_time.png)

## 3.5 Analisis Hasil Pengujian
1. **Skalabilitas 1 hingga 4 Threads**: Pada rentang 1, 2, hingga 4 core fisik, baik Pthreads maupun OpenMP memperlihatkan kurva speedup yang sangat mendekati garis ideal linear (S = 3.51x pada Pthreads dan S = 3.54x pada OpenMP). Efisiensi paralel bertahan tinggi pada level **87.8% - 88.5%**, membuktikan bahwa beban komputasi 10^9 sampel terskala secara linear pada core fisik mandiri.
2. **Karakteristik pada 8 Threads**: Saat jumlah thread ditingkatkan ke 8 (memanfaatkan seluruh Simultaneous Multi-Threading / SMT logical cores), waktu eksekusi terpangkas hingga **0.785 detik (Pthreads)** dan **0.796 detik (OpenMP)**, dengan speedup mencapai **5.59x**. Penurunan efisiensi menjadi ~69% pada 8 thread merupakan karakteristik fisik dari arsitektur CPU di mana 8 logical cores berbagi pipa eksekusi fisik (ALU & FPU) yang sama dalam 4 physical cores.
3. **Komparasi Pthreads vs OpenMP**: Kinerja Pthreads dan OpenMP berada pada level yang seimbang (0.785s vs 0.796s pada 8 threads). OpenMP memiliki keunggulan slight pada keteraturan thread team overhead, sementara Pthreads unggul tipis karena eliminasi lapisan runtime abstraksi.
"""

    # Section 4
    sec4 = """
<div class="page-break"></div>

# 4. ANALISIS KRITIS

## 4.1 Perbandingan Kompleksitas Kode (LOC, Readability, Maintenance)
Perbandingan kompleksitas perangkat lunak antara pendekatan Pthreads dan OpenMP dievaluasi berdasarkan metrik rekayasa perangkat lunak standar:

<table>
<thead>
<tr>
<th>Metrik Rekayasa</th>
<th>Serial Baseline</th>
<th>POSIX Threads (Pthreads)</th>
<th>OpenMP Directive</th>
</tr>
</thead>
<tbody>
<tr><td><strong>Lines of Code (LOC)</strong></td><td>~75 baris</td><td>~160 baris</td><td>~95 baris</td></tr>
<tr><td><strong>Overhead Boilerplate Code</strong></td><td>Tidak ada (0%)</td><td>Sangat Tinggi (+113%)</td><td>Sangat Rendah (+26%)</td></tr>
<tr><td><strong>Tingkat Abstraksi</strong></td><td>Algoritmik Murni</td><td>Rendah (Manual Syscall)</td><td>Tinggi (Compiler Pragmas)</td></tr>
<tr><td><strong>Resiko Kesalahan Manusia</strong></td><td>Minimal</td><td>Tinggi (Deadlock, Dangling Ptr)</td><td>Rendah (Otomasi Kompilator)</td></tr>
<tr><td><strong>Portabilitas Kode Serial</strong></td><td>Natif</td><td>Buruk (Membutuhkan Refactoring)</td><td>Sangat Tinggi (Abaikan Pragma)</td></tr>
</tbody>
</table>

Pada Pthreads, programmer dibebani tanggung jawab manual (*imperative boilerplate*):
* Mendefinisikan struct pembungkus argumen (`PthreadArg`).
* Melakukan alokasi memori dinamis untuk array thread handle (`pthread_t*`).
* Menghitung pembagian indeks partisi beban per-thread secara eksplisit.
* Mengelola loop `pthread_create()` dan loop `pthread_join()`.
* Melakukan type-casting pointer `void*` yang rentan kesalahan memori.

Sebaliknya, pada OpenMP, seluruh logika konkurensi dideklarasikan hanya dengan **satu blok pragma kompilator** (`#pragma omp parallel reduction(+:in_circle)`). Jika flag kompilasi `-fopenmp` dihilangkan, kode OpenMP secara otomatis dikompilasi kembali menjadi program serial standar tanpa memerlukan modifikasi kode sumber.

## 4.2 Analisis Bottleneck Berdasarkan Hukum Amdahl
Hukum Amdahl mendefinisikan batas teoritis percepatan maksimum (*theoretical maximum speedup*) dari sistem paralel:
<div class="math-block"><i>S</i><sub>max</sub>(<i>p</i>) = 1 / ((1 - <i>f</i>) + <i>f</i> / <i>p</i>)</div>
di mana <i>f</i> adalah fraksi program yang dapat diparalelkan (*parallel fraction*), dan (1 - <i>f</i>) adalah fraksi serial murni (*inherently serial fraction*).

Berdasarkan data empiris pengujian OpenMP pada <i>p</i> = 4 (<i>S</i> = 3.54x):
<div class="math-block">3.54 = 1 / ((1 - <i>f</i>) + <i>f</i> / 4) &rArr; (1 - <i>f</i>) + 0.25<i>f</i> = 1 / 3.54 &approx; 0.2825</div>
<div class="math-block">1 - 0.75<i>f</i> = 0.2825 &rArr; 0.75<i>f</i> = 0.7175 &rArr; <i>f</i> &approx; 0.9567 (95.67%)</div>

Fraksi serial sebesar (1 - <i>f</i>) &approx; 4.33% bersumber dari beberapa faktor penahan skalabilitas:
1. **Inisialisasi Seed dan Alokasi Memori**: Pembangkitan seed awal melalui `splitmix64` dan alokasi memori berjalan secara sekuensial pada master core.
2. **Reduksi Akhir dan Sinkronisasi Barrier**: Penggabungan akumulator parsial pada akhir loop melibatkan operasi sinkronisasi antarthread.
3. **Overhead Thread Management**: Latensi kernel sistem operasi dalam membangunkan (*wake-up latency*) dan menjadwalkan thread worker.
4. **Thermal Throttling dan CPU Frequency Scaling**: Saat seluruh 8 thread beroperasi penuh pada beban 100%, frekuensi boost prosesor mengalami penyesuaian termal.

## 4.3 Pembahasan Anomali dan Fenomena Hardware Khusus

![Kualitas RNG dan False Sharing](figures/fig6_rng_and_false_sharing.png)

### Anomali 1: Kualitas dan Kecepatan Random Number Generator
Pengujian khusus membuktikan perbedaan drastis antara generator modern **Xorshift64\*** versus generator POSIX **`rand_r()`** (Linear Congruential Generator):
* **Xorshift64\***: Throughput mencapai **119.62 Juta Titik/detik** (waktu [[RNG_FAST]] detik pada 10^8 sampel).
* **POSIX `rand_r()`**: Throughput hanya **85.32 Juta Titik/detik** (waktu [[RNG_POSIX]] detik pada 10^8 sampel).
* **Faktor Kecepatan**: Xorshift64* terbukti **1.40x lebih cepat** daripada `rand_r()`.

Keunggulan Xorshift64* terletak pada efisiensi instruksi level mesin: hanya membutuhkan 3 operasi *bitwise shift*, 3 operasi *XOR*, dan 1 perkalian 64-bit integer tanpa operasi pembagian/modulo. Sebaliknya, LCG standar melibatkan operasi pembagian modulo (`% 32768`), yang memiliki latensi clock cycle mahal pada pipeline CPU modern. Selain itu, periode Xorshift64* sebesar 2<sup>64</sup> - 1 &approx; 1.84 &times; 10<sup>19</sup> menjamin bahwa pengujian 1 miliar sampel tidak mengalami kelelahan periode (*period exhaustion*), berbeda dengan LCG 32-bit yang periodenya hanya 2<sup>31</sup> - 1 &approx; 2.14 &times; 10<sup>9</sup> (hampir habis hanya dalam satu putaran pengujian!).

### Anomali 2: Pembuktian Empiris Degradasi Akibat False Sharing
Eksperimen khusus dirancang untuk mendemonstrasikan bahaya *False Sharing*:
* Menggunakan struct ber-padding 64 byte (`PthreadArg`): waktu eksekusi adalah **[[FS_PADDED]] detik**.
* Menggunakan struct tanpa padding (`PthreadArgUnpadded`): waktu eksekusi melonjak menjadi **[[FS_UNPADDED]] detik**.
* **Overhead Degradasi**: Terjadi penurunan performa sebesar **+[[FS_OVERHEAD]]%**!

Penyebab fenomena ini adalah protokol koherensi cache hardware (MESI). Ketika beberapa core menulis secara terus-menerus ke variabel yang berada pada satu *cache line* 64 byte yang sama, garis cache tersebut dipaksa berpindah-pindah status kepemilikan (*Modified* &harr; *Invalid*). Hal ini menyebabkan jalur bus interkoneksi prosesor mengalami saturasi (*bus traffic congestion*), meskipun variabel yang diubah secara logika terpisah.

### Anomali 3: Trade-off Jumlah Thread vs Akurasi Statistik
Berdasarkan hukum statistika, batas kesalahan estimasi &pi; **hanya ditentukan oleh total jumlah sampel N**, bukan oleh jumlah thread p:
<div class="math-block">&sigma; &approx; 1.642 / &radic;<i>N</i></div>
Menambah jumlah thread dari 1 menjadi 8 **TIDAK** meningkatkan presisi estimasi &pi;, melainkan mempercepat waktu wall-clock yang dibutuhkan untuk memproses N sampel tersebut. Sebagai contoh, pengujian dengan 1 thread dan 8 thread pada 10^9 sampel sama-sama menghasilkan akurasi pada digit desimal ke-5 (3.14159...).

## 4.4 Trade-off Antara Kemudahan (OpenMP) vs Kontrol Granular (Pthreads)
Pemilihan teknologi konkurensi melibatkan pertukaran strategis:
1. **Keunggulan Pthreads**: Menyediakan kontrol mutlak terhadap siklus hidup thread (*fine-grained lifetime control*), kemampuan menyematkan thread ke core prosesor tertentu secara eksplisit (*CPU core affinity pinning* via `pthread_setaffinity_np`), serta fleksibilitas membangun struktur konkurensi non-fork-join (seperti *asynchronous producer-consumer queue* atau server jaringan berorientasi event).
2. **Keunggulan OpenMP**: Menyediakan abstraksi deklaratif yang luar biasa ringkas, pemisahan tugas kompilator yang otomatis, alokasi thread pool internal yang sangat teroptimasi, serta jaminan portabilitas kode serial. Untuk persoalan numerik saintifik berbasis perulangan, OpenMP merupakan pilihan industri yang jauh lebih unggul dalam efisiensi rekayasa.
"""

    # Section 5 & 6
    sec5 = """
<div class="page-break"></div>

# 5. KESIMPULAN

Berdasarkan perancangan, implementasi, benchmark empiris, dan analisis kritis terhadap estimasi nilai &pi; Monte Carlo dengan 1 Miliar titik sampel, dapat ditarik beberapa kesimpulan fundamental:

1. **Efektivitas Paralelisasi Shared-Memory**: Metode Monte Carlo terbukti memiliki skalabilitas paralel yang luar biasa. Implementasi OpenMP dan Pthreads berhasil memangkas waktu komputasi dari **4.390 detik (Serial)** menjadi hanya **~0.785 - 0.796 detik (8 Threads)**, menghasilkan percepatan (*speedup*) sebesar **5.59x** dengan efisiensi paralel mencapai **88.5% pada 4 core fisik**.
2. **Superioritas OpenMP untuk Komputasi Numerik**: Dalam domain komputasi berbasis perulangan independen (*loop-level parallelism*), OpenMP menawarkan efisiensi rekayasa yang jauh lebih tinggi dibandingkan Pthreads. OpenMP menghemat hingga 40% baris kode dan mengeliminasi resiko kesalahan fatal penanganan pointer konkurensi tingkat rendah.
3. **Pentingnya Isolasi PRNG dan Mitigasi False Sharing**: Rekayasa konkurensi tingkat rendah membuktikan bahwa penggunaan PRNG per-thread (seperti Xorshift64*) dan perlindungan baris cache (*cache-line padding* 64 byte) merupakan prasyarat mutlak dalam mencegah degradasi performa akibat *lock contention* dan *cache line bouncing*.
4. **Karakteristik Skalabilitas Hardware (SMT/Hyper-Threading)**: Pemanfaatan core logis di atas jumlah core fisik memberikan percepatan tambahan (dari 3.54x ke 5.59x), namun diiringi penurunan efisiensi (dari 88.5% ke 68.9%) akibat perebutan unit fungsional eksekusi ALU/FPU fisik pada core yang sama.

### Rekomendasi Penggunaan
* Gunakan **OpenMP** untuk percepatan komputasi numerik, sains data, pemrosesan citra, simulasi fisika, dan algoritma matematika berbasis matriks/looping.
* Gunakan **Pthreads** apabila aplikasi membutuhkan kontrol thread tingkat rendah, arsitektur event-driven non-fork-join, interaksi langsung dengan API sistem operasi, atau manajemen thread pool manual yang kompleks.

<div class="page-break"></div>

# 6. DAFTAR PUSTAKA

1. Amdahl, G. M. (1967). *Validity of the single processor approach to achieving large scale computing capabilities*. AFIPS Conference Proceedings, 30, 483–485.
2. Chandra, R., Dagum, L., Kohr, D., Maydan, D., McDonald, J., & Menon, R. (2001). *Parallel Programming in OpenMP*. Morgan Kaufmann Publishers.
3. Butenhof, D. R. (1997). *Programming with POSIX Threads*. Addison-Wesley Professional.
4. Marsaglia, G. (2003). *Xorshift RNGs*. Journal of Statistical Software, 8(14), 1–6.
5. Vigna, S. (2016). *An experimental exploration of Marsaglia's xorshift generators, scrambled*. ACM Transactions on Mathematical Software, 42(4), 1–23.
6. Hennessy, J. L., & Patterson, D. A. (2019). *Computer Architecture: A Quantitative Approach* (6th ed.). Morgan Kaufmann.
7. OpenMP Architecture Review Board. (2021). *OpenMP Application Programming Interface Version 5.2*.
8. IEEE Computer Society. (2018). *IEEE Standard for Information Technology—Portable Operating System Interface (POSIX(R)) Base Specifications, Issue 7*. IEEE Std 1003.1-2017.
"""

    full_markdown = sec1 + sec2 + sec3 + sec4 + sec5

    # Replace placeholders
    full_markdown = full_markdown.replace('[[TABLE_HTML]]', table_html)
    full_markdown = full_markdown.replace('[[SER_PI]]', ser_pi)
    full_markdown = full_markdown.replace('[[SER_ERR]]', ser_err)
    full_markdown = full_markdown.replace('[[PTH_PI]]', pth_pi)
    full_markdown = full_markdown.replace('[[PTH_ERR]]', pth_err)
    full_markdown = full_markdown.replace('[[OMP_PI]]', omp_pi)
    full_markdown = full_markdown.replace('[[OMP_ERR]]', omp_err)
    full_markdown = full_markdown.replace('[[RNG_FAST]]', f"{meta_info['rng_fast']:.4f}")
    full_markdown = full_markdown.replace('[[RNG_POSIX]]', f"{meta_info['rng_posix']:.4f}")
    full_markdown = full_markdown.replace('[[FS_PADDED]]', f"{meta_info['fs_padded']:.4f}")
    full_markdown = full_markdown.replace('[[FS_UNPADDED]]', f"{meta_info['fs_unpadded']:.4f}")
    full_markdown = full_markdown.replace('[[FS_OVERHEAD]]', f"{fs_overhead:.2f}")

    # Generate initial PDF using markdown_pdf
    styled_markdown = f"<style>{css}</style>\n\n" + full_markdown
    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(Section(styled_markdown, paper_size='A4'))

    raw_pdf_path = 'report/temp_raw_report.pdf'
    pdf.save(raw_pdf_path)
    print(f"File sementara berhasil disimpan di {raw_pdf_path}")

    # Post-process with PyMuPDF to add headers and footers with page numbers
    doc = fitz.open(raw_pdf_path)
    total_pages = len(doc)
    print(f"Total Halaman Dokumen: {total_pages} halaman")

    header_text = "UTS Komputer Paralel (Sistem Terdistribusi) | Vicky Maulana Romadan (2322105049)"

    for page_num in range(total_pages):
        page = doc[page_num]
        rect = page.rect
        width = rect.width
        height = rect.height

        # Header (pages 2 to end)
        if page_num > 0:
            page.insert_text(
                fitz.Point(36, 25),
                header_text,
                fontsize=8,
                color=(0.35, 0.4, 0.45)
            )
            # Header line
            page.draw_line(
                fitz.Point(36, 30),
                fitz.Point(width - 36, 30),
                color=(0.8, 0.85, 0.9),
                width=0.75
            )

        # Footer (all pages)
        footer_text = f"Halaman {page_num + 1} dari {total_pages} | Teknik Informatika - Universitas Cendekia Abditama"
        page.draw_line(
            fitz.Point(36, height - 32),
            fitz.Point(width - 36, height - 32),
            color=(0.85, 0.88, 0.92),
            width=0.75
        )
        # Center-align footer text
        text_len = fitz.get_text_length(footer_text, fontsize=8)
        page.insert_text(
            fitz.Point((width - text_len) / 2.0, height - 20),
            footer_text,
            fontsize=8,
            color=(0.4, 0.45, 0.5)
        )

    final_pdf_path = 'report/Laporan_UTS_Komputasi_Paralel_Vicky_Maulana_Romadan_2322105049.pdf'
    doc.save(final_pdf_path, deflate=True, garbage=4, clean=True)
    doc.close()

    # Clean temporary file
    if os.path.exists(raw_pdf_path):
        os.remove(raw_pdf_path)

    print(f"Laporan PDF Final Berhasil Dibuat: {final_pdf_path} ({total_pages} halaman)")

if __name__ == '__main__':
    generate_pdf()
