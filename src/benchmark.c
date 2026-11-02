/**
 * ============================================================================
 * Program     : benchmark.c
 * Deskripsi   : Driver Pengujian dan Analisis Komparatif Serial vs Pthreads vs OpenMP
 * Mata Kuliah : Komputer Paralel (Sistem Terdistribusi)
 * Penulis     : Vicky Maulana Romadan (NIM: 2322105049)
 * Institusi   : Teknik Informatika, Universitas Cendekia Abditama
 * ============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <pthread.h>
#include <omp.h>
#include "../include/common.h"

// Pthreads worker for benchmark
static void* bench_pthreads_worker(void* arg) {
    PthreadArg* data = (PthreadArg*)arg;
    uint64_t count = 0;
    uint64_t samples = data->num_samples;
    uint64_t state = data->seed;

    for (uint64_t i = 0; i < samples; i++) {
        double x = rand_double_fast(&state);
        double y = rand_double_fast(&state);
        if (x * x + y * y <= 1.0) {
            count++;
        }
    }
    data->local_in_circle = count;
    data->seed = state;
    return NULL;
}

// Unpadded worker for false sharing demonstration
static void* bench_false_sharing_worker(void* arg) {
    PthreadArgUnpadded* data = (PthreadArgUnpadded*)arg;
    uint64_t samples = data->num_samples;
    uint64_t state = data->seed;

    // Directly updating struct field frequently to simulate false sharing on the same cache line
    data->local_in_circle = 0;
    for (uint64_t i = 0; i < samples; i++) {
        double x = rand_double_fast(&state);
        double y = rand_double_fast(&state);
        if (x * x + y * y <= 1.0) {
            data->local_in_circle++; // Continual write to unpadded adjacent struct field
        }
    }
    data->seed = state;
    return NULL;
}

// POSIX rand_r worker for RNG comparison
static void* bench_posix_worker(void* arg) {
    PthreadArg* data = (PthreadArg*)arg;
    uint64_t count = 0;
    uint64_t samples = data->num_samples;
    unsigned int seed = (unsigned int)(data->seed & 0xFFFFFFFFU);

    for (uint64_t i = 0; i < samples; i++) {
        double x = rand_double_posix(&seed);
        double y = rand_double_posix(&seed);
        if (x * x + y * y <= 1.0) {
            count++;
        }
    }
    data->local_in_circle = count;
    data->seed = seed;
    return NULL;
}

// Run Serial
static double run_serial(uint64_t samples, double *out_pi, uint64_t *out_circle) {
    uint64_t state = 88172645463325252ULL;
    uint64_t count = 0;
    double t0 = get_wall_time();
    for (uint64_t i = 0; i < samples; i++) {
        double x = rand_double_fast(&state);
        double y = rand_double_fast(&state);
        if (x * x + y * y <= 1.0) {
            count++;
        }
    }
    double t1 = get_wall_time();
    *out_circle = count;
    *out_pi = 4.0 * ((double)count / (double)samples);
    return t1 - t0;
}

// Run Pthreads
static double run_pthreads(uint64_t samples, int num_threads, double *out_pi, uint64_t *out_circle) {
    pthread_t *threads = (pthread_t*)malloc(sizeof(pthread_t) * num_threads);
    PthreadArg *args = (PthreadArg*)malloc(sizeof(PthreadArg) * num_threads);
    uint64_t base = samples / num_threads;
    uint64_t rem = samples % num_threads;
    uint64_t master_seed = 88172645463325252ULL;

    double t0 = get_wall_time();
    for (int t = 0; t < num_threads; t++) {
        args[t].thread_id = t;
        args[t].total_threads = num_threads;
        args[t].num_samples = base + (t < (int)rem ? 1 : 0);
        args[t].local_in_circle = 0;
        uint64_t s_in = master_seed + (uint64_t)t * 1000000007ULL;
        args[t].seed = splitmix64(&s_in);
        pthread_create(&threads[t], NULL, bench_pthreads_worker, &args[t]);
    }

    uint64_t total = 0;
    for (int t = 0; t < num_threads; t++) {
        pthread_join(threads[t], NULL);
        total += args[t].local_in_circle;
    }
    double t1 = get_wall_time();

    *out_circle = total;
    *out_pi = 4.0 * ((double)total / (double)samples);
    free(threads);
    free(args);
    return t1 - t0;
}

// Run OpenMP
static double run_openmp(uint64_t samples, int num_threads, double *out_pi, uint64_t *out_circle) {
    uint64_t in_circle = 0;
    uint64_t *seeds = (uint64_t*)malloc(sizeof(uint64_t) * num_threads * 8);
    uint64_t master_seed = 88172645463325252ULL;
    for (int t = 0; t < num_threads; t++) {
        uint64_t input = master_seed + (uint64_t)t * 1000000007ULL;
        seeds[t * 8] = splitmix64(&input);
    }

    omp_set_num_threads(num_threads);
    double t0 = omp_get_wtime();

    #pragma omp parallel reduction(+:in_circle)
    {
        int tid = omp_get_thread_num();
        uint64_t state = seeds[tid * 8];
        uint64_t local_count = 0;

        #pragma omp for schedule(static)
        for (uint64_t i = 0; i < samples; i++) {
            double x = rand_double_fast(&state);
            double y = rand_double_fast(&state);
            if (x * x + y * y <= 1.0) {
                local_count++;
            }
        }
        in_circle += local_count;
    }

    double t1 = omp_get_wtime();
    *out_circle = in_circle;
    *out_pi = 4.0 * ((double)in_circle / (double)samples);
    free(seeds);
    return t1 - t0;
}

int main(int argc, char *argv[]) {
    uint64_t total_samples = DEFAULT_SAMPLES;
    int repetitions = 3; // 3 runs for reliable average

    if (argc >= 2) total_samples = strtoull(argv[1], NULL, 10);
    if (argc >= 3) repetitions = atoi(argv[2]);

    printf("===================================================================\n");
    printf("     BENCHMARK SUITE: MONTE CARLO PI ESTIMATION (10^9 SAMPLES)     \n");
    printf("     Penulis : Vicky Maulana Romadan (NIM: 2322105049)            \n");
    printf("===================================================================\n");
    printf("Sampel Per Run : %llu\n", (unsigned long long)total_samples);
    printf("Repetisi       : %d kali per konfigurasi\n\n", repetitions);

    FILE *csv = fopen("results/benchmark_data.csv", "w");
    if (!csv) {
        fprintf(stderr, "Error: Tidak dapat membuka results/benchmark_data.csv untuk penulisan.\n");
        return 1;
    }
    fprintf(csv, "model,threads,run,time_sec,pi_estimate,abs_error,in_circle\n");

    // 1. Benchmark Serial Baseline
    printf(">>> Menjalankan Serial Baseline...\n");
    double serial_times[5] = {0};
    double serial_pi[5] = {0};
    uint64_t serial_circle[5] = {0};
    double sum_serial = 0.0;

    for (int r = 0; r < repetitions; r++) {
        serial_times[r] = run_serial(total_samples, &serial_pi[r], &serial_circle[r]);
        sum_serial += serial_times[r];
        double err = fabs(serial_pi[r] - PI_TRUE);
        fprintf(csv, "Serial,1,%d,%.6f,%.10f,%.10e,%llu\n", 
                r + 1, serial_times[r], serial_pi[r], err, (unsigned long long)serial_circle[r]);
        printf("  Run %d: Time = %.4fs, Pi = %.8f, AbsError = %.8f\n", 
               r + 1, serial_times[r], serial_pi[r], err);
    }
    double t_serial_avg = sum_serial / repetitions;
    printf("  -> Rata-rata Serial: %.4fs\n\n", t_serial_avg);

    int thread_counts[] = {1, 2, 4, 8};
    int num_configs = sizeof(thread_counts) / sizeof(thread_counts[0]);

    // 2. Benchmark Pthreads
    printf(">>> Menjalankan POSIX Threads (Pthreads)...\n");
    double pthreads_avg[4] = {0};
    for (int c = 0; c < num_configs; c++) {
        int th = thread_counts[c];
        double sum_th = 0.0;
        printf("  [Pthreads %d Thread(s)]:\n", th);
        for (int r = 0; r < repetitions; r++) {
            double pi_val = 0.0;
            uint64_t circle = 0;
            double t = run_pthreads(total_samples, th, &pi_val, &circle);
            sum_th += t;
            double err = fabs(pi_val - PI_TRUE);
            fprintf(csv, "Pthreads,%d,%d,%.6f,%.10f,%.10e,%llu\n", 
                    th, r + 1, t, pi_val, err, (unsigned long long)circle);
            printf("    Run %d: Time = %.4fs, Pi = %.8f, AbsError = %.8f\n", r + 1, t, pi_val, err);
        }
        pthreads_avg[c] = sum_th / repetitions;
        double sp = t_serial_avg / pthreads_avg[c];
        double eff = (sp / th) * 100.0;
        printf("    -> Rata-rata: %.4fs | Speedup: %.2fx | Efficiency: %.2f%%\n", 
               pthreads_avg[c], sp, eff);
    }
    printf("\n");

    // 3. Benchmark OpenMP
    printf(">>> Menjalankan OpenMP Directives...\n");
    double openmp_avg[4] = {0};
    for (int c = 0; c < num_configs; c++) {
        int th = thread_counts[c];
        double sum_th = 0.0;
        printf("  [OpenMP %d Thread(s)]:\n", th);
        for (int r = 0; r < repetitions; r++) {
            double pi_val = 0.0;
            uint64_t circle = 0;
            double t = run_openmp(total_samples, th, &pi_val, &circle);
            sum_th += t;
            double err = fabs(pi_val - PI_TRUE);
            fprintf(csv, "OpenMP,%d,%d,%.6f,%.10f,%.10e,%llu\n", 
                    th, r + 1, t, pi_val, err, (unsigned long long)circle);
            printf("    Run %d: Time = %.4fs, Pi = %.8f, AbsError = %.8f\n", r + 1, t, pi_val, err);
        }
        openmp_avg[c] = sum_th / repetitions;
        double sp = t_serial_avg / openmp_avg[c];
        double eff = (sp / th) * 100.0;
        printf("    -> Rata-rata: %.4fs | Speedup: %.2fx | Efficiency: %.2f%%\n", 
               openmp_avg[c], sp, eff);
    }
    printf("\n");

    // 4. Pengujian Khusus RNG: POSIX rand_r vs Modern Xorshift64* (10^8 samples)
    printf(">>> Pengujian Khusus: Perbandingan RNG (Xorshift64* vs POSIX rand_r)...\n");
    uint64_t test_rng_samples = 100000000ULL; // 10^8 samples
    volatile uint64_t sink1 = 0, sink2 = 0;
    uint64_t state_fast = 88172645463325252ULL;
    unsigned int state_posix = 42U;

    double t0 = omp_get_wtime();
    for (uint64_t i = 0; i < test_rng_samples; i++) {
        double x = rand_double_fast(&state_fast);
        double y = rand_double_fast(&state_fast);
        if (x * x + y * y <= 1.0) sink1++;
    }
    double t_fast = omp_get_wtime() - t0;

    t0 = omp_get_wtime();
    for (uint64_t i = 0; i < test_rng_samples; i++) {
        double x = rand_double_posix(&state_posix);
        double y = rand_double_posix(&state_posix);
        if (x * x + y * y <= 1.0) sink2++;
    }
    double t_posix = omp_get_wtime() - t0;

    printf("  Xorshift64* (10^8 titik) : %.4fs (Throughput: %.2f Mpts/s, circle: %llu)\n", 
           t_fast, (100.0 / t_fast), (unsigned long long)sink1);
    printf("  POSIX rand_r (10^8 titik): %.4fs (Throughput: %.2f Mpts/s, circle: %llu)\n", 
           t_posix, (100.0 / t_posix), (unsigned long long)sink2);
    printf("  Rasio Kecepatan          : Xorshift64* adalah %.2fx lebih cepat daripada rand_r!\n\n",
           t_posix / t_fast);

    // 5. Pengujian Khusus: Demonstrasi Dampak False Sharing (10^8 updates)
    printf(">>> Pengujian Khusus: Demonstrasi Dampak False Sharing...\n");
    uint64_t fs_samples = 100000000ULL;
    int fs_threads = 8;
    pthread_t fs_th[8];
    PthreadArg fs_padded[8];
    PthreadArgUnpadded fs_unpadded[8];

    // Padded test (independent cache lines)
    t0 = omp_get_wtime();
    for (int t = 0; t < fs_threads; t++) {
        fs_padded[t].num_samples = fs_samples / fs_threads;
        fs_padded[t].seed = 12345ULL + t * 999ULL;
        pthread_create(&fs_th[t], NULL, bench_pthreads_worker, &fs_padded[t]);
    }
    uint64_t sum_padded = 0;
    for (int t = 0; t < fs_threads; t++) {
        pthread_join(fs_th[t], NULL);
        sum_padded += fs_padded[t].local_in_circle;
    }
    double t_padded = omp_get_wtime() - t0;

    // Unpadded test (sharing same cache lines)
    t0 = omp_get_wtime();
    for (int t = 0; t < fs_threads; t++) {
        fs_unpadded[t].num_samples = fs_samples / fs_threads;
        fs_unpadded[t].seed = 12345ULL + t * 999ULL;
        pthread_create(&fs_th[t], NULL, bench_false_sharing_worker, &fs_unpadded[t]);
    }
    uint64_t sum_unpadded = 0;
    for (int t = 0; t < fs_threads; t++) {
        pthread_join(fs_th[t], NULL);
        sum_unpadded += fs_unpadded[t].local_in_circle;
    }
    double t_unpadded = omp_get_wtime() - t0;

    printf("  Waktu dengan Padded Struct (Bebas False Sharing): %.4fs (sum: %llu)\n", 
           t_padded, (unsigned long long)sum_padded);
    printf("  Waktu Unpadded Struct (Terkena False Sharing)    : %.4fs (sum: %llu)\n", 
           t_unpadded, (unsigned long long)sum_unpadded);
    printf("  Overhead Degradasi Akibat False Sharing         : +%.2f%%\n\n", 
           ((t_unpadded - t_padded) / t_padded) * 100.0);

    fprintf(csv, "# RNG Comparison: fast_time=%.6f, posix_time=%.6f\n", t_fast, t_posix);
    fprintf(csv, "# False Sharing: padded=%.6f, unpadded=%.6f\n", t_padded, t_unpadded);
    fclose(csv);

    printf("Benchmark Selesai! Data mentah disimpan di 'results/benchmark_data.csv'.\n");
    return 0;
}
