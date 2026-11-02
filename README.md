# Proyek Ujian Tengah Semester (UTS) - Komputer Paralel (Sistem Terdistribusi)
## Opsi C: Simulasi Monte Carlo Estimasi Nilai $\pi$ ($10^9$ Titik Sampel)

**Mata Kuliah** : Komputer Paralel (Sistem Terdistribusi)  
**Program Studi** : Teknik Informatika, Fakultas Teknik dan Ilmu Komputer  
**Universitas** : Universitas Cendekia Abditama  
**Dosen Pengampu** : Dr. Ir. Antonius Irianto. S, ST., MT  
**Hari / Tanggal** : Senin, 2 November 2026  
**Penulis (Mahasiswa)** : **Vicky Maulana Romadan**  
**NIM** : **2322105049**  
**Format Repositori** : `paralel-2322105049-Vicky-Maulana-Romadan`

---

## 1. Deskripsi Masalah

Program ini mengimplementasikan komputasi paralel berintensitas tinggi untuk mengestimasi nilai konstanta matematika $\pi$ menggunakan **Metode Monte Carlo** dengan ukuran sample **1 Miliar Titik ($10^9$ sampel)**. Proyek ini membandingkan dua paradigma pemrograman paralel multithreading pada arsitektur memori bersama (*shared memory*):

1. **POSIX Threads (Pthreads)**: Pendekatan paralelisme eksplisit/manual tingkat rendah (*low-level imperative concurrency*).
2. **OpenMP**: Pendekatan paralelisme berbasis arahan kompilator (*compiler directive high-level concurrency*).

Kedua implementasi dianalisis secara komprehensif terhadap baseline **Serial** dalam hal waktu eksekusi, *speedup*, efisiensi paralel, kompleksitas kode (LOC & *maintainability*), skalabilitas Hukum Amdahl, serta fenomena memori tingkat rendah seperti *false sharing* dan kualitas *Pseudo-Random Number Generator* (PRNG).

---

## 2. Struktur Proyek

```text
paralel-2322105049-Vicky-Maulana-Romadan/
├── bin/                       # Direktori biner hasil kompilasi
├── figures/                   # Grafik hasil benchmark (Speedup, Efficiency, dll)
├── include/                   # Header file C
│   └── common.h               # Timer presisi tinggi, PRNG, struct argumen padded
├── report/                    # Dokumen Laporan UTS
│   └── Laporan_UTS_Komputasi_Paralel_Vicky_Maulana_Romadan_2322105049.pdf
├── results/                   # Data mentah CSV hasil pengujian benchmark
│   └── benchmark_data.csv
├── scripts/                   # Script Python untuk visualisasi & otomasi
│   ├── generate_report_pdf.py # Generator laporan akademik PDF
│   └── plot_results.py        # Pembuat grafik analisis kinerja
├── src/                       # Source code implementasi C
│   ├── benchmark.c            # Test harness otomatis & verifikasi correctness
│   ├── openmp.c               # Implementasi OpenMP compiler directive
│   ├── pthreads.c             # Implementasi POSIX Threads eksplisit
│   └── serial.c               # Implementasi Serial baseline
├── Makefile                   # Build automation script
└── README.md                  # Dokumentasi teknis proyek
```

---

## 3. Spesifikasi Teknis & Solusi Masalah Khusus

* **Kuadran Satuan**: Titik acak $(x, y)$ dibangkitkan pada interval $[0, 1] \times [0, 1]$. Titik yang memenuhi $x^2 + y^2 \le 1.0$ diakumulasikan sebagai titik di dalam seperempat lingkaran ($M$). Nilai $\pi$ diestimasi melalui formula:
  $$\hat{\pi} = 4 \times \frac{M}{N}$$
* **Isolasi State PRNG (Non-Shared RNG)**: Program **TIDAK MENGGUNAKAN** `rand()` global standard library C karena menyebabkan *lock contention* dan *data race*. Setiap thread memiliki instance PRNG independen dengan state terisolasi. Menggunakan **Xorshift64\*** (periode $2^{64}-1$) yang diinisialisasi melalui algoritma hash **SplitMix64**.
* **Pencegahan Race Condition pada Accumulator**:
  * Pada **Pthreads**: Menggunakan *Thread-Local Accumulator* dengan reduksi akhir pada `pthread_join()` (atau mutex tunggal saat terminasi thread).
  * Pada **OpenMP**: Menggunakan klausa `reduction(+:in_circle)` yang dikelola secara otomatis dan optimal oleh kompilator.
* **Mitigasi False Sharing**: Struktur argumen thread (`PthreadArg`) dialokasikan dengan padding 64 byte (`CACHE_LINE_SIZE`) untuk memastikan setiap thread menulis pada *cache line* L1/L2 yang berbeda, mencegah degradasi *cache bouncing*.

---

## 4. Persyaratan Sistem & Kompilator

* **Sistem Operasi**: Windows 10/11 (64-bit) atau Linux Ubuntu 20.04/22.04/24.04.
* **Kompilator**: GCC (MinGW-w64 pada Windows atau GCC standar pada Linux) dengan dukungan OpenMP (`-fopenmp`) dan POSIX Threads (`-lpthread`).
* **Python**: Versi 3.8+ dengan pustaka `numpy`, `pandas`, `matplotlib`, `pymupdf`, `markdown_pdf` (untuk visualisasi dan pembuatan laporan).

---

## 5. Cara Kompilasi dan Build

### Menggunakan Makefile (Otomatis):

```bash
# Kompilasi seluruh target eksekusi
make all

# Atau kompilasi target individual:
make serial
make pthreads
make openmp
make benchmark
```

### Kompilasi Manual Menggunakan GCC:

Jika sistem tidak memiliki utilitas `make`:

```bash
# 1. Serial Baseline
gcc -O3 -Wall -Wextra -Iinclude src/serial.c -o bin/serial.exe -lm

# 2. POSIX Threads (Pthreads)
gcc -O3 -Wall -Wextra -Iinclude src/pthreads.c -o bin/pthreads.exe -lpthread -lm

# 3. OpenMP Directives
gcc -O3 -Wall -Wextra -fopenmp -Iinclude src/openmp.c -o bin/openmp.exe -fopenmp -lm

# 4. Benchmark Suite
gcc -O3 -Wall -Wextra -fopenmp -Iinclude src/benchmark.c -o bin/benchmark.exe -fopenmp -lpthread -lm
```

---

## 6. Cara Menjalankan Program (*Run*)

### 1. Menjalankan Versi Serial (Baseline):
Argumen: `[jumlah_sampel]` `[tipe_rng: 0=Xorshift64*, 1=POSIX rand_r]`
```bash
./bin/serial.exe 1000000000 0
```

### 2. Menjalankan Versi Pthreads:
Argumen: `[jumlah_sampel]` `[jumlah_thread]` `[sync_mode: 0=Local+Join, 1=Mutex]` `[tipe_rng]`
```bash
# Menjalankan 1 Miliar Titik dengan 8 Threads
./bin/pthreads.exe 1000000000 8 0 0
```

### 3. Menjalankan Versi OpenMP:
Argumen: `[jumlah_sampel]` `[jumlah_thread]` `[schedule: 0=static, 1=dynamic, 2=guided]` `[tipe_rng]`
```bash
# Menjalankan 1 Miliar Titik dengan 8 Threads
./bin/openmp.exe 1000000000 8 0 0
```

### 4. Menjalankan Benchmark Suite Otomatis:
Argumen: `[jumlah_sampel]` `[jumlah_repetisi_per_konfigurasi]`
```bash
./bin/benchmark.exe 1000000000 3
```
Perintah ini akan menguji Serial (1 core), Pthreads (1, 2, 4, 8 threads), OpenMP (1, 2, 4, 8 threads), perbandingan kualitas RNG, serta dampak *false sharing*, dan menyimpan hasil mentah ke `results/benchmark_data.csv`.

### 5. Membuat Visualisasi Grafik & Laporan PDF:
```bash
# Generate semua grafik analisis performa
python scripts/plot_results.py

# Generate dokumen laporan PDF akademik
python scripts/generate_report_pdf.py
```

---

## 7. Ringkasan Hasil Pengujian Singkat

Berdasarkan pengujian empiris pada prosesor AMD64 (8 logical processors) dengan 1 Miliar titik sampel ($10^9$):

| Implementasi | Threads | Waktu Eksekusi (s) | Speedup ($S_p$) | Efisiensi ($E_p$) | Estimasi $\pi$ | Absolute Error |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Serial Baseline** | 1 | ~3.38 s | 1.00x | 100.0% | 3.14159518 | $2.53 \times 10^{-6}$ |
| **Pthreads** | 1 | ~3.40 s | 0.99x | 99.4% | 3.14159492 | $2.27 \times 10^{-6}$ |
| **Pthreads** | 2 | ~1.73 s | 1.95x | 97.7% | 3.14158914 | $3.51 \times 10^{-6}$ |
| **Pthreads** | 4 | ~0.89 s | 3.80x | 95.0% | 3.14161102 | $1.84 \times 10^{-5}$ |
| **Pthreads** | 8 | ~0.52 s | 6.50x | 81.3% | 3.14162045 | $2.78 \times 10^{-5}$ |
| **OpenMP** | 1 | ~3.39 s | 1.00x | 99.7% | 3.14159510 | $2.45 \times 10^{-6}$ |
| **OpenMP** | 2 | ~1.72 s | 1.96x | 98.3% | 3.14159021 | $2.44 \times 10^{-6}$ |
| **OpenMP** | 4 | ~0.88 s | 3.84x | 96.0% | 3.14160890 | $1.62 \times 10^{-5}$ |
| **OpenMP** | 8 | ~0.51 s | 6.63x | 82.8% | 3.14161980 | $2.71 \times 10^{-5}$ |

*Analisis komparatif lengkap, pembahasan anomali false sharing, perbandingan RNG, dan telaah Hukum Amdahl disajikan secara mendalam pada Laporan PDF proyek.*
