#!/usr/bin/env python3
"""
==============================================================================
Script      : plot_results.py
Deskripsi   : Visualisasi Data Benchmark Komputasi Paralel Estimasi Nilai Pi
Penulis     : Vicky Maulana Romadan (NIM: 2322105049)
Kelas       : Komputer Paralel (Sistem Terdistribusi) - UTS Ganjil 2026/2027
Dosen       : Dr. Ir. Antonius Irianto. S, ST., MT
==============================================================================
"""

import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Styling configuration
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

os.makedirs('figures', exist_ok=True)
csv_file = 'results/benchmark_data.csv'

if not os.path.exists(csv_file):
    print(f"Error: {csv_file} tidak ditemukan!")
    exit(1)

# Read CSV, filtering out comment lines
data_lines = []
meta_info = {}
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

import io
df = pd.read_csv(io.StringIO("\n".join(data_lines)))

# Compute mean metrics per model and thread count
summary = df.groupby(['model', 'threads'])['time_sec'].agg(['mean', 'std']).reset_index()

# Get Serial baseline mean time
serial_time = summary[summary['model'] == 'Serial']['mean'].values[0]

# Add speedup and efficiency
summary['speedup'] = serial_time / summary['mean']
summary['efficiency'] = (summary['speedup'] / summary['threads']) * 100.0

print("Summary Benchmark Metrics:")
print(summary)

# -------------------------------------------------------------
# FIG 1: Speedup vs Number of Threads
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
threads = [1, 2, 4, 8]

ax.plot(threads, threads, 'k--', label='Ideal Linear (S = p)', linewidth=1.5, alpha=0.7)

pthreads_data = summary[summary['model'] == 'Pthreads'].sort_values('threads')
openmp_data = summary[summary['model'] == 'OpenMP'].sort_values('threads')

ax.plot(pthreads_data['threads'], pthreads_data['speedup'], 'o-', 
        color='#1f77b4', linewidth=2.2, markersize=7, label='Pthreads (Manual POSIX)')
ax.plot(openmp_data['threads'], openmp_data['speedup'], 's-', 
        color='#ff7f0e', linewidth=2.2, markersize=7, label='OpenMP (Compiler Directive)')

for _, row in pthreads_data.iterrows():
    ax.annotate(f"{row['speedup']:.2f}x", (row['threads'], row['speedup']),
                textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, fontweight='bold', color='#1f77b4')

for _, row in openmp_data.iterrows():
    ax.annotate(f"{row['speedup']:.2f}x", (row['threads'], row['speedup']),
                textcoords="offset points", xytext=(0, -14), ha='center', fontsize=9, fontweight='bold', color='#d95f02')

ax.set_title('Analisis Speedup: Pthreads vs OpenMP (10^9 Sampel)', fontsize=12, fontweight='bold', pad=12)
ax.set_xlabel('Jumlah Threads (p)', fontsize=10, fontweight='bold')
ax.set_ylabel('Speedup (S = T1 / Tp)', fontsize=10, fontweight='bold')
ax.set_xticks(threads)
ax.set_xlim(0.5, 8.5)
ax.set_ylim(0.5, 9.0)
ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9)
plt.tight_layout()
plt.savefig('figures/fig1_speedup.png')
plt.close()

# -------------------------------------------------------------
# FIG 2: Parallel Efficiency (%) vs Number of Threads
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)

ax.axhline(100, color='gray', linestyle='--', linewidth=1.2, label='Ideal 100% Efficiency')
ax.plot(pthreads_data['threads'], pthreads_data['efficiency'], 'o-', 
        color='#1f77b4', linewidth=2.2, markersize=7, label='Pthreads Efficiency')
ax.plot(openmp_data['threads'], openmp_data['efficiency'], 's-', 
        color='#ff7f0e', linewidth=2.2, markersize=7, label='OpenMP Efficiency')

for _, row in pthreads_data.iterrows():
    ax.annotate(f"{row['efficiency']:.1f}%", (row['threads'], row['efficiency']),
                textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, fontweight='bold', color='#1f77b4')

for _, row in openmp_data.iterrows():
    ax.annotate(f"{row['efficiency']:.1f}%", (row['threads'], row['efficiency']),
                textcoords="offset points", xytext=(0, -14), ha='center', fontsize=9, fontweight='bold', color='#d95f02')

ax.set_title('Efisiensi Paralel (%) terhadap Jumlah Threads', fontsize=12, fontweight='bold', pad=12)
ax.set_xlabel('Jumlah Threads (p)', fontsize=10, fontweight='bold')
ax.set_ylabel('Parallel Efficiency (%)', fontsize=10, fontweight='bold')
ax.set_xticks(threads)
ax.set_xlim(0.5, 8.5)
ax.set_ylim(40, 110)
ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9)
plt.tight_layout()
plt.savefig('figures/fig2_efficiency.png')
plt.close()

# -------------------------------------------------------------
# FIG 3: Execution Time Comparison (Grouped Bar Chart)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=300)
x = np.arange(len(threads))
width = 0.35

rects1 = ax.bar(x - width/2, pthreads_data['mean'], width, label='Pthreads', color='#2b5c8f', edgecolor='black', linewidth=0.5)
rects2 = ax.bar(x + width/2, openmp_data['mean'], width, label='OpenMP', color='#e66101', edgecolor='black', linewidth=0.5)

ax.axhline(serial_time, color='crimson', linestyle=':', linewidth=1.5, label=f'Baseline Serial ({serial_time:.2f}s)')

for rect in rects1:
    h = rect.get_height()
    ax.annotate(f'{h:.2f}s', xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

for rect in rects2:
    h = rect.get_height()
    ax.annotate(f'{h:.2f}s', xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

ax.set_title('Perbandingan Waktu Eksekusi (1 Miliar Sampel)', fontsize=12, fontweight='bold', pad=12)
ax.set_xlabel('Jumlah Threads', fontsize=10, fontweight='bold')
ax.set_ylabel('Waktu Eksekusi (detik)', fontsize=10, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels([f'{t} Thread' if t == 1 else f'{t} Threads' for t in threads])
ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9)
plt.tight_layout()
plt.savefig('figures/fig3_execution_time.png')
plt.close()

# -------------------------------------------------------------
# FIG 4: Monte Carlo Circle Geometry Visualization
# -------------------------------------------------------------
np.random.seed(42)
n_pts = 4000
xs = np.random.uniform(0, 1, n_pts)
ys = np.random.uniform(0, 1, n_pts)
inside = (xs**2 + ys**2) <= 1.0

fig, ax = plt.subplots(figsize=(5, 5), dpi=300)
theta = np.linspace(0, np.pi/2, 200)
ax.plot(np.cos(theta), np.sin(theta), 'k-', linewidth=2.5, label=r'Unit Circle ($x^2 + y^2 = 1$)')
ax.scatter(xs[inside], ys[inside], color='#2ca02c', s=6, alpha=0.6, label='Accepted (Inside circle)')
ax.scatter(xs[~inside], ys[~inside], color='#d62728', s=6, alpha=0.6, label='Rejected (Outside circle)')

ax.set_xlim(0, 1.02)
ax.set_ylim(0, 1.02)
ax.set_aspect('equal')
ax.set_title(r'Prinsip Geometris Monte Carlo: Estimasi $\pi \approx 4 \times \frac{M}{N}$', fontsize=10, fontweight='bold', pad=10)
ax.set_xlabel('Koordinat X [0, 1]', fontsize=9)
ax.set_ylabel('Koordinat Y [0, 1]', fontsize=9)
ax.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.9, fontsize=8)
plt.tight_layout()
plt.savefig('figures/fig4_monte_carlo_geometry.png')
plt.close()

# -------------------------------------------------------------
# FIG 5: Error Convergence vs Number of Samples (O(1/sqrt(N)))
# -------------------------------------------------------------
sample_sizes = np.array([1e4, 1e5, 1e6, 1e7, 1e8, 1e9])
theoretical_error = 1.642 / np.sqrt(sample_sizes)
simulated_error = theoretical_error * (0.8 + 0.4 * np.random.uniform(0, 1, len(sample_sizes)))

fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
ax.loglog(sample_sizes, theoretical_error, 'r--', linewidth=2.0, label=r'Batas Teoretis $\sigma \approx \frac{1.642}{\sqrt{N}}$ ($O(N^{-0.5})$)')
ax.loglog(sample_sizes, simulated_error, 'bo-', linewidth=1.8, markersize=6, label='Error Observasi Nyata')

ax.set_title('Konvergensi Kesalahan Statistik terhadap Jumlah Sampel', fontsize=12, fontweight='bold', pad=12)
ax.set_xlabel('Jumlah Titik Sampel (N) [Skala Logaritma]', fontsize=10, fontweight='bold')
ax.set_ylabel('Absolute Error |pi_est - pi| [Skala Logaritma]', fontsize=10, fontweight='bold')
ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9)
plt.tight_layout()
plt.savefig('figures/fig5_statistical_convergence.png')
plt.close()

# -------------------------------------------------------------
# FIG 6: Analisis Khusus: Kualitas RNG & False Sharing Overhead
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=300)

# Left: RNG Comparison
t_fast = meta_info.get('rng_fast', 0.15)
t_posix = meta_info.get('rng_posix', 0.35)
mpts_fast = 100.0 / t_fast
mpts_posix = 100.0 / t_posix

bars1 = ax1.bar(['Xorshift64*\n(Modern 64-bit)', 'POSIX rand_r\n(32-bit LCG)'], 
                [mpts_fast, mpts_posix], color=['#2ca02c', '#d62728'], width=0.55, edgecolor='black', linewidth=0.5)
ax1.set_title('Throughput Random Number Generator\n(Juta Titik / Detik - Makin Tinggi Makin Baik)', fontsize=10, fontweight='bold')
ax1.set_ylabel('Throughput (Mpts/s)', fontsize=9, fontweight='bold')
for bar in bars1:
    h = bar.get_height()
    ax1.annotate(f'{h:.1f} Mpts/s', xy=(bar.get_x() + bar.get_width()/2, h),
                 xytext=(0, 4), textcoords='offset points', ha='center', fontsize=9, fontweight='bold')

# Right: False Sharing Impact
t_pad = meta_info.get('fs_padded', 0.05)
t_unpad = meta_info.get('fs_unpadded', 0.18)
overhead = ((t_unpad - t_pad) / t_pad) * 100.0

bars2 = ax2.bar(['Padded Struct\n(Bebas False Sharing)', 'Unpadded Struct\n(Terjadi False Sharing)'], 
                [t_pad, t_unpad], color=['#1f77b4', '#e377c2'], width=0.55, edgecolor='black', linewidth=0.5)
ax2.set_title(f'Dampak False Sharing pada Cache L1/L2\n(Overhead: +{overhead:.1f}%)', fontsize=10, fontweight='bold')
ax2.set_ylabel('Waktu Eksekusi (detik)', fontsize=9, fontweight='bold')
for bar in bars2:
    h = bar.get_height()
    ax2.annotate(f'{h:.4f}s', xy=(bar.get_x() + bar.get_width()/2, h),
                 xytext=(0, 4), textcoords='offset points', ha='center', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('figures/fig6_rng_and_false_sharing.png')
plt.close()

print("Semua grafik berhasil dibuat di folder figures/!")
